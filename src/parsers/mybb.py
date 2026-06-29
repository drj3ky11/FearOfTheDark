"""
MyBB SQL Dump Parser
====================
MyBB (MyBulletinBoard) was common in English-speaking underground forums.
These dumps have a configurable table prefix (e.g. 'mybb_', 'QLqEqiMsDA_').

Key differences from vBulletin:
- Table names are plural: users, posts, threads, privatemessages
- Primary keys differ: uid (not userid), pid (not postid), tid (not threadid)
- Post body column is 'message' (not 'pagetext')
- Registration date is 'regdate' (not 'joindate')
- Last active is 'lastactive' (not 'lastactivity')
- Post count is 'postnum' (not 'posts')
- Registration IP is 'regip' (not 'ipaddress')
- Thread title is 'subject' (not 'title')
- Reply count is 'replies' (not 'replycount')

We detect the prefix by scanning the first CREATE TABLE statement, strip it,
then normalize column names to the same canonical schema as the vBulletin parser.
"""

import re
import zipfile
import io
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path


# Canonical → MyBB column name mappings per table (canonical name on the left)
_COL_MAP = {
    "user": {
        "userid": "uid",
        "ipaddress": "regip",
        "joindate": "regdate",
        "lastactivity": "lastactive",
        "posts": "postnum",
        "homepage": "website",
    },
    "post": {
        "postid": "pid",
        "threadid": "tid",
        "forumid": "fid",   # MyBB posts carry fid; vBulletin does not
        "userid": "uid",
        "pagetext": "message",
    },
    "thread": {
        "threadid": "tid",
        "forumid": "fid",
        "userid": "uid",
        "title": "subject",
        "replycount": "replies",
        "visible": "closed",    # approximation: closed=0 means visible
    },
    "pmtext": {
        "pmtextid": "pmid",
        "fromuserid": "fromid",
        "touserarray": "toid",
        "title": "subject",
    },
}

# Columns to keep per canonical table (using canonical names)
_WANT_COLS = {
    "user": [
        "userid", "username", "password", "salt", "email",
        "ipaddress", "joindate", "lastvisit", "lastactivity", "lastpost",
        "posts", "reputation", "timezone",
        "icq", "skype", "aim", "yahoo",
        "homepage", "birthday", "usertitle",
    ],
    "post": [
        "postid", "threadid", "forumid", "userid", "username",
        "dateline", "pagetext", "ipaddress", "visible",
    ],
    "thread": [
        "threadid", "forumid", "userid", "username",
        "title", "dateline", "lastpost", "replycount", "views", "visible",
    ],
    "pmtext": [
        "pmtextid", "fromuserid", "fromusername",
        "title", "message", "touserarray", "dateline",
    ],
    "userfield": ["userid"],   # MyBB userfields are sparse; include uid for join
}

# MyBB table name (without prefix) → canonical name
_TABLE_MAP = {
    "users": "user",
    "posts": "post",
    "threads": "thread",
    "privatemessages": "pmtext",
    "userfields": "userfield",
}

_UNIX_TS_COLS = {"joindate", "lastvisit", "lastactivity", "lastpost", "dateline"}


def _detect_prefix(stream: io.TextIOWrapper) -> str:
    """
    Scan the first CREATE TABLE statement to extract the table prefix.
    Returns the prefix string (e.g. 'mybb_' or 'QLqEqiMsDA_'), or '' if none found.
    """
    for line in stream:
        m = re.match(r"CREATE TABLE `(\w+)`", line.strip())
        if m:
            raw = m.group(1)
            # The prefix ends at the last '_' before a known MyBB table name
            for canonical_suffix in _TABLE_MAP:
                if raw.endswith("_" + canonical_suffix) or raw == canonical_suffix:
                    prefix = raw[: len(raw) - len(canonical_suffix)]
                    stream.seek(0)
                    return prefix
            # Unknown table name — try generic prefix detection (everything before last segment)
            parts = raw.rsplit("_", 1)
            if len(parts) == 2:
                stream.seek(0)
                return parts[0] + "_"
    stream.seek(0)
    return ""


def _open_sql_stream(path: Path) -> io.TextIOWrapper:
    zf = zipfile.ZipFile(path)
    sql_names = [n for n in zf.namelist() if n.endswith(".sql") or n.endswith(".txt")]
    if not sql_names:
        raise ValueError(f"No .sql/.txt file found inside {path.name}")
    # Pick the largest SQL file when there are multiple (e.g. OGUsers_2022 has a tiny
    # auxiliary file alongside the main dump)
    name = max(sql_names, key=lambda n: zf.getinfo(n).file_size)
    with zf.open(name) as f:
        sample = f.read(2048)
    try:
        sample.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        encoding = "cp1251"
    raw = zf.open(name)
    return io.TextIOWrapper(raw, encoding=encoding, errors="replace")


def _to_datetime(val: str | None) -> datetime | None:
    if val is None or val == "0":
        return None
    try:
        ts = int(val)
        return datetime.fromtimestamp(ts, tz=timezone.utc) if ts > 0 else None
    except (ValueError, OSError, OverflowError):
        return None


def _split_sql_values(row: str) -> list[str | None]:
    """Same state-machine parser as the vBulletin parser."""
    row = row.strip().lstrip("(").rstrip(");").rstrip(",")
    values: list[str | None] = []
    i = 0
    n = len(row)
    while i < n:
        while i < n and row[i] == " ":
            i += 1
        if i >= n:
            break
        if row[i] == "'":
            j = i + 1
            buf: list[str] = []
            while j < n:
                if row[j] == "\\" and j + 1 < n:
                    next_c = row[j + 1]
                    buf.append({"'": "'", "\\": "\\", "n": "\n", "r": "\r"}.get(next_c, next_c))
                    j += 2
                elif row[j] == "'":
                    j += 1
                    break
                else:
                    buf.append(row[j])
                    j += 1
            values.append("".join(buf))
            i = j
            if i < n and row[i] == ",":
                i += 1
        elif row[i:i+4] == "NULL":
            values.append(None)
            i += 4
            if i < n and row[i] == ",":
                i += 1
        else:
            j = i
            while j < n and row[j] != ",":
                j += 1
            values.append(row[i:j])
            i = j + 1
    return values


def _paren_balanced(s: str) -> bool:
    if not s.startswith("("):
        return False
    depth = 0
    in_str = False
    i = 0
    while i < len(s):
        c = s[i]
        if in_str:
            if c == "\\" and i + 1 < len(s):
                i += 2
                continue
            if c == "'":
                in_str = False
        else:
            if c == "'":
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return True
        i += 1
    return False


def parse(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Parse a MyBB SQL dump zip. Returns canonical dict matching vBulletin parser output:
    {"user": df, "post": df, "thread": df, "pmtext": df}
    """
    zip_path = Path(zip_path)
    stream = _open_sql_stream(zip_path)
    prefix = _detect_prefix(stream)

    # Build reverse map: raw table name (with prefix) → canonical name
    raw_to_canonical = {prefix + mybb_name: canon for mybb_name, canon in _TABLE_MAP.items()}
    target_raws = set(raw_to_canonical.keys())

    # First pass: collect CREATE TABLE column order
    schemas: dict[str, list[str]] = {}   # keyed by canonical name
    current_canon: str | None = None
    cols_buf: list[str] = []

    for line in stream:
        stripped = line.strip()
        m = re.match(r"CREATE TABLE `(\w+)`", stripped)
        if m:
            raw = m.group(1)
            current_canon = raw_to_canonical.get(raw)
            cols_buf = []
            continue
        if current_canon:
            col_m = re.match(r"`(\w+)`\s+", stripped)
            if col_m:
                cols_buf.append(col_m.group(1))
            if stripped.startswith(")"):
                schemas[current_canon] = cols_buf
                current_canon = None

    stream.seek(0)

    # Second pass: collect INSERT rows
    results: dict[str, list[list]] = {c: [] for c in _TABLE_MAP.values()}
    insert_columns: dict[str, list[str]] = {}
    current_canon = None
    in_insert = False
    row_buffer: list[str] = []

    def _flush_buffer() -> None:
        if row_buffer and current_canon:
            combined = " ".join(row_buffer)
            results[current_canon].append(_split_sql_values(combined.rstrip(",;")))
        row_buffer.clear()

    for line in stream:
        stripped = line.strip()
        m = re.match(r"INSERT INTO `(\w+)`(\s*\(([^)]+)\))?\s*VALUES", stripped)
        if m:
            _flush_buffer()
            raw = m.group(1)
            current_canon = raw_to_canonical.get(raw)
            in_insert = current_canon is not None
            if in_insert and m.group(3):
                cols = re.findall(r"`(\w+)`", m.group(3))
                if cols:
                    insert_columns[current_canon] = cols
            if in_insert and not stripped.endswith("VALUES"):
                values_part = stripped[m.end():]
                for row_match in re.finditer(r"\(([^)]*(?:\([^)]*\)[^)]*)*)\)", values_part):
                    results[current_canon].append(_split_sql_values(row_match.group(0)))
            continue

        if in_insert and current_canon:
            if stripped.startswith("("):
                _flush_buffer()
                row_buffer.append(stripped)
                if _paren_balanced(stripped):
                    _flush_buffer()
            elif row_buffer:
                row_buffer.append(stripped)
                combined = " ".join(row_buffer)
                if _paren_balanced(combined):
                    _flush_buffer()
            elif stripped and not stripped.startswith("--") and not stripped.startswith("/*"):
                in_insert = False
                current_canon = None

    _flush_buffer()

    # Build DataFrames with canonical column names
    dfs: dict[str, pd.DataFrame] = {}
    for canon, rows in results.items():
        if not rows:
            continue

        # Column names as they appear in the SQL (MyBB names)
        mybb_cols = insert_columns.get(canon) or schemas.get(canon, [])
        ncols = len(mybb_cols)
        padded = [(r + [None] * max(0, ncols - len(r)))[:ncols] for r in rows]
        df = pd.DataFrame(padded, columns=mybb_cols if mybb_cols else None)

        # Rename MyBB columns to canonical names
        col_rename = {v: k for k, v in _COL_MAP.get(canon, {}).items() if v in df.columns}
        df = df.rename(columns=col_rename)

        # Keep only wanted canonical columns
        want = [c for c in _WANT_COLS.get(canon, list(df.columns)) if c in df.columns]
        df = df[want].copy()

        for col in _UNIX_TS_COLS:
            if col in df.columns:
                df[col] = df[col].apply(_to_datetime)

        dfs[canon] = df

    return dfs


def load_forum(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    """Parse and add 'forum' source column to every table."""
    dfs = parse(zip_path)
    forum_name = Path(zip_path).stem
    for df in dfs.values():
        df.insert(0, "forum", forum_name)
    return dfs


def is_mybb(zip_path: str | Path) -> bool:
    """
    Quick check: does this zip contain a MyBB-style SQL dump?
    Streams through the SQL looking for a CREATE TABLE that matches a known MyBB table suffix.
    """
    try:
        zip_path = Path(zip_path)
        zf = zipfile.ZipFile(zip_path)
        sql_names = [n for n in zf.namelist() if n.endswith(".sql") or n.endswith(".txt")]
        if not sql_names:
            return False
        largest = max(sql_names, key=lambda n: zf.getinfo(n).file_size)
        with zf.open(largest) as raw:
            stream = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
            for line in stream:
                m = re.match(r"CREATE TABLE `(\w+)`", line.strip())
                if m:
                    t = m.group(1)
                    if any(t == s or t.endswith("_" + s) for s in _TABLE_MAP):
                        return True
        return False
    except Exception:
        return False
