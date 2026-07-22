"""
Shared encoding-detection helper for SQL dump parsers.
=======================================================
All three SQL/flat parsers (vbulletin.py, mybb.py, flat.py) previously
duplicated the same "peek at the first 2KB and try to decode as utf-8"
heuristic. That heuristic is broken for vBulletin-family dumps: the file
always starts with a pure-ASCII CREATE TABLE schema block, which decodes
as valid utf-8 regardless of the actual encoding of the data rows further
down. As a result, genuinely cp1251 (Windows Cyrillic) dumps were always
misdetected as utf-8, and their Cyrillic text was replaced with garbage
via `errors="replace"` — silent mojibake with no exception raised.

This helper scans a much larger, bounded window (default 8MB, comfortably
past the schema header and into the INSERT data rows) using an incremental
UTF-8 decoder so multibyte characters split across chunk boundaries do not
produce false negatives. If genuinely invalid utf-8 bytes are found within
the scan window, we fall back to cp1251. If the scan window is exhausted
without finding any non-utf-8 bytes, we default to utf-8.
"""

import codecs
import zipfile


def detect_member_encoding(
    zf: zipfile.ZipFile,
    name: str,
    *,
    scan_bytes: int = 8_000_000,
    fallback: str = "cp1251",
) -> str:
    """
    Decide whether a zip member is utf-8 or a fallback encoding (cp1251 by
    default) by incrementally decoding up to `scan_bytes` of its content.

    Args:
        zf: Open ZipFile containing the member.
        name: Name of the member inside the zip.
        scan_bytes: How many bytes to scan before giving up and assuming
            utf-8. Bounds both I/O and decompression work (also acts as a
            mild zip-bomb guard) while still comfortably reaching the
            INSERT data rows past the ASCII CREATE TABLE schema block.
        fallback: Encoding to return if invalid utf-8 bytes are found.

    Returns:
        "utf-8" if the scanned window decodes cleanly as utf-8, otherwise
        `fallback`.
    """
    decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
    read_total = 0
    with zf.open(name) as f:
        while read_total < scan_bytes:
            chunk = f.read(min(65536, scan_bytes - read_total))
            if not chunk:
                break
            read_total += len(chunk)
            try:
                decoder.decode(chunk)
            except UnicodeDecodeError:
                return fallback
    try:
        decoder.decode(b"", final=True)
    except UnicodeDecodeError:
        return fallback
    return "utf-8"
