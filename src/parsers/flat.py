"""
Flat file parser for forum dumps that are not SQL.

Some leaks were distributed as plain text files with a delimiter-separated
row per user, rather than full database dumps. The format varies:

  Cardingmafia.ws: colon-delimited, first line is the header.
  Example:
    userid:username:email:ipaddress:birthday:homepage:icq:password:salt

These files contain only user data (no posts or PMs), so analysis is limited
to user profiling and cross-forum correlation — not timezone inference or stylometry.
"""

import zipfile
import io
import pandas as pd
from pathlib import Path


# Map flat-file column names to our canonical names (same as vbulletin._COLUMNS['user'])
_COLUMN_ALIASES = {
    "userid":    "userid",
    "id":        "userid",
    "username":  "username",
    "user":      "username",
    "nick":      "username",
    "login":     "username",
    "email":     "email",
    "mail":      "email",
    "ipaddress": "ipaddress",
    "ip":        "ipaddress",
    "reg_ip":    "ipaddress",
    "password":  "password",
    "pass":      "password",
    "hash":      "password",
    "salt":      "salt",
    "icq":       "icq",
    "skype":     "skype",
    "birthday":  "birthday",
    "homepage":  "homepage",
    "url":       "homepage",
}


def parse_flat(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Parse a zip containing a colon- or pipe-delimited flat user file.
    Returns a dict with a single 'user' key for API compatibility with vbulletin.parse().
    """
    zip_path = Path(zip_path)
    zf = zipfile.ZipFile(zip_path)
    txt_names = [n for n in zf.namelist() if n.endswith(".txt") or n.endswith(".csv")]
    if not txt_names:
        raise ValueError(f"No .txt/.csv file found inside {zip_path.name}")

    raw = zf.open(txt_names[0])
    # Try UTF-8 first, fall back to cp1251
    sample = raw.read(2048)
    raw.seek(0)
    try:
        sample.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        encoding = "cp1251"

    stream = io.TextIOWrapper(raw, encoding=encoding, errors="replace")
    first_line = stream.readline().strip()

    # Auto-detect delimiter from the header line
    delimiter = ":"
    for candidate in [":", "|", "\t", ";"]:
        if candidate in first_line:
            delimiter = candidate
            break

    headers = [h.strip().lower() for h in first_line.split(delimiter)]

    rows = []
    for line in stream:
        line = line.rstrip("\n\r")
        if not line:
            continue
        parts = line.split(delimiter, len(headers) - 1)
        parts += [None] * max(0, len(headers) - len(parts))
        rows.append(parts[:len(headers)])

    df = pd.DataFrame(rows, columns=headers)

    # Rename columns to canonical names
    df = df.rename(columns={k: v for k, v in _COLUMN_ALIASES.items() if k in df.columns})

    return {"user": df}


def load_flat_forum(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    """Same as parse_flat() but adds a 'forum' column."""
    dfs = parse_flat(zip_path)
    forum_name = Path(zip_path).stem
    for df in dfs.values():
        df.insert(0, "forum", forum_name)
    return dfs
