"""
vBulletin SQL Dump Parser
=========================
vBulletin was the most common forum engine in underground communities during the 2000s–2010s.
When these forums were hacked or shut down, the leaked data came in the form of MySQL database
dumps — plain-text SQL files with CREATE TABLE + INSERT INTO statements.

Key quirks of these dumps:
- Encoding: cp1251 (Windows Cyrillic). Most of these forums were Russian-speaking.
  If you open them as UTF-8, text will be garbage. We must decode as cp1251.
- They are zipped. We read directly from the .zip without extracting to disk.
- They follow the standard vBulletin schema, so the same parser works across all dumps.
- Timestamps are Unix epoch integers (seconds since 1970-01-01 UTC), not human-readable dates.
"""

import re
import zipfile
import io
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path


# Which columns to keep from each table.
# We intentionally discard system/config columns and keep only forensically relevant ones.
_COLUMNS = {
    "user": [
        "userid",           # Primary key — used to join with posts/PMs
        "username",         # Display name (often reused across forums — key for correlation)
        "password",         # MD5 hash (no salt on older vBulletin). Useful for cross-forum matching.
        "salt",             # Salt added in vBulletin 3.8+
        "email",            # Often a strong identifier, even with throwaway domains
        "ipaddress",        # Registration IP — may reveal true location if no VPN was used
        "joindate",         # Unix timestamp → registration date
        "lastvisit",        # Unix timestamp → last login
        "lastactivity",     # Unix timestamp → last action (more granular than lastvisit)
        "lastpost",         # Unix timestamp → last post
        "posts",            # Post count — proxy for activity level
        "reputation",       # Community reputation score
        "timezoneoffset",   # Self-reported timezone (unreliable, but worth checking)
        "icq",              # ICQ number — very common in Russian underground, often reused
        "skype",            # Skype handle
        "aim", "yahoo", "msn",  # Legacy messengers, rarely filled but occasionally useful
        "homepage",         # Personal URL — sometimes links to other personas
        "birthday",         # Self-reported birthday (dd-mm-yyyy or mm-dd-yyyy depending on locale)
        "usertitle",        # Custom title — can reveal role ("Vendor", "Trusted", etc.)
    ],
    "post": [
        "postid",
        "threadid",
        "userid",
        "username",
        "dateline",     # Unix timestamp of the post — used for timezone inference
        "pagetext",     # Full post content — used for stylometric analysis
        "ipaddress",    # Poster's IP at time of post (often empty in older dumps)
        "visible",      # 0=deleted, 1=visible, 2=moderated. We usually want only visible=1.
    ],
    "thread": [
        "threadid",
        "forumid",
        "userid",
        "username",
        "title",
        "dateline",
        "lastpost",
        "replycount",
        "views",
        "visible",
    ],
    "pmtext": [
        # Private messages — extremely valuable for attribution.
        # Many users drop their guard in PMs: real names, phone numbers, payment details.
        "pmtextid",
        "fromuserid",
        "fromusername",
        "title",
        "message",
        "touserarray",  # Serialized PHP array of recipient userids
        "dateline",
    ],
    "userfield": [
        # Custom profile fields. The meaning of field1–field4 varies per forum.
        # Common uses: country, city, messenger handle, "about me" text.
        "userid",
        "field1", "field2", "field3", "field4",
    ],
}

# These columns store Unix timestamps and will be converted to datetime objects.
_UNIX_TS_COLS = {"joindate", "lastvisit", "lastactivity", "lastpost", "dateline"}


def _open_sql_stream(path: Path) -> io.TextIOWrapper:
    """
    Open the .zip and return a text stream of the SQL file inside.

    Encoding detection: most Russian underground forums used cp1251, but some
    later dumps (post-2015) are UTF-8. We try UTF-8 first by peeking at the
    first 2KB — if it decodes cleanly, we use it; otherwise fall back to cp1251.
    The file extension can be .sql or .txt (Cardingmafia.ws uses .txt).
    """
    zf = zipfile.ZipFile(path)
    sql_names = [n for n in zf.namelist() if n.endswith(".sql") or n.endswith(".txt")]
    if not sql_names:
        raise ValueError(f"No .sql/.txt file found inside {path.name}")

    name = sql_names[0]
    # Peek to detect encoding
    with zf.open(name) as f:
        sample = f.read(2048)
    try:
        sample.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        encoding = "cp1251"

    raw = zf.open(name)
    return io.TextIOWrapper(raw, encoding=encoding, errors="replace")


def _parse_create_table(stream: io.TextIOWrapper) -> dict[str, list[str]]:
    """
    Read the CREATE TABLE statements to learn the column order for each table.
    We need this because INSERT INTO ... VALUES rows are positional — there are
    no column names in the INSERT, just values in the same order as the CREATE TABLE.
    After reading, we seek back to the start of the stream.
    """
    schemas: dict[str, list[str]] = {}
    current_table = None
    columns: list[str] = []

    for line in stream:
        line = line.strip()
        m = re.match(r"CREATE TABLE `(\w+)`", line)
        if m:
            # Normalize table name: strip common prefixes like 'vb_' (used in Carder.su)
            # so the rest of the parser can use the canonical names ('user', 'post', etc.)
            raw_name = m.group(1)
            current_table = re.sub(r"^vb_", "", raw_name)
            columns = []
            continue
        if current_table:
            col_m = re.match(r"`(\w+)`\s+", line)
            if col_m:
                columns.append(col_m.group(1))
            if line.startswith(")"):
                schemas[current_table] = columns
                current_table = None

    stream.seek(0)
    return schemas


def _split_sql_values(row: str) -> list[str | None]:
    """
    Parse a single SQL VALUES row like (1,'hello',NULL,'it\\'s fine')
    into a Python list.

    Why not use a CSV parser or split on commas?
    Because SQL strings can contain commas, escaped quotes, and newlines.
    We need a small state machine that tracks whether we're inside a string.

    NULL becomes Python None.
    Escape sequences (\\', \\n, \\r, \\\\) are resolved.
    """
    row = row.strip().lstrip("(").rstrip(");").rstrip(",")
    values: list[str | None] = []
    i = 0
    n = len(row)

    while i < n:
        # Skip whitespace between values (e.g. after a comma: ", 'value'")
        while i < n and row[i] == " ":
            i += 1
        if i >= n:
            break
        if row[i] == "'":
            # We're entering a quoted string — scan until the closing unescaped quote.
            j = i + 1
            buf: list[str] = []
            while j < n:
                if row[j] == "\\" and j + 1 < n:
                    next_c = row[j + 1]
                    escape_map = {"'": "'", "\\": "\\", "n": "\n", "r": "\r"}
                    buf.append(escape_map.get(next_c, next_c))
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
            # Unquoted value — numeric or keyword. Read until the next comma.
            j = i
            while j < n and row[j] != ",":
                j += 1
            values.append(row[i:j])
            i = j + 1

    return values


def _to_datetime(val: str | None) -> datetime | None:
    """Convert a Unix timestamp string to a timezone-aware UTC datetime."""
    if val is None or val == "0":
        return None
    try:
        ts = int(val)
        return datetime.fromtimestamp(ts, tz=timezone.utc) if ts > 0 else None
    except (ValueError, OSError, OverflowError):
        return None


def parse(zip_path: str | Path, tables: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """
    Parse a vBulletin SQL dump zip and return a dict of DataFrames.

    We do a single streaming pass over the file:
    1. First pass: read CREATE TABLE statements to learn column order.
    2. Second pass (after seek(0)): read INSERT INTO rows and parse them.

    This avoids loading the entire SQL file into memory, which can be several GB.

    Args:
        zip_path: Path to the .zip file containing the .sql dump.
        tables: Which tables to extract. Defaults to all in _COLUMNS.

    Returns:
        Dict of {table_name: DataFrame}. Only tables with data are included.
    """
    zip_path = Path(zip_path)
    target_tables = set(tables or _COLUMNS.keys())

    stream = _open_sql_stream(zip_path)
    schemas = _parse_create_table(stream)  # seek(0) happens inside

    results: dict[str, list[list]] = {t: [] for t in target_tables}
    # When an INSERT specifies columns explicitly (INSERT INTO `t` (`c1`,`c2`) VALUES),
    # we store those column names here so we can map values correctly —
    # regardless of the column order in the CREATE TABLE statement.
    insert_columns: dict[str, list[str]] = {}
    current_table: str | None = None
    in_insert = False
    # Buffer for multi-line rows: vBulletin text fields can contain literal newlines,
    # so a single INSERT row may span many lines. We accumulate lines until the
    # row's parentheses are balanced, then parse it as one unit.
    row_buffer: list[str] = []

    def _flush_buffer() -> None:
        if row_buffer and current_table:
            combined = " ".join(row_buffer)
            results[current_table].append(_split_sql_values(combined.rstrip(",;")))
        row_buffer.clear()

    def _paren_balanced(s: str) -> bool:
        """Return True if s starts with '(' and its parentheses are balanced."""
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

    for line in stream:
        stripped = line.strip()

        # Match both forms:
        #   INSERT INTO `table` VALUES (...)          — implicit column order
        #   INSERT INTO `table` (`col1`,`col2`) VALUES — explicit column list
        m = re.match(r"INSERT INTO `(\w+)`(\s*\(([^)]+)\))?\s*VALUES", stripped)
        if m:
            _flush_buffer()
            raw_table = m.group(1)
            # Normalize vb_ prefix (Carder.su uses vb_user, vb_post, etc.)
            current_table = re.sub(r"^vb_", "", raw_table)
            in_insert = current_table in target_tables
            # If the INSERT lists columns explicitly, record them
            if in_insert and m.group(3):
                cols = re.findall(r"`(\w+)`", m.group(3))
                if cols:
                    insert_columns[current_table] = cols
            if in_insert and not stripped.endswith("VALUES"):
                values_part = stripped[m.end():]
                for row_match in re.finditer(r"\(([^)]*(?:\([^)]*\)[^)]*)*)\)", values_part):
                    results[current_table].append(_split_sql_values(row_match.group(0)))
            continue

        if in_insert and current_table:
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
                current_table = None

    _flush_buffer()

    # Build DataFrames, keeping only the columns we care about
    dfs: dict[str, pd.DataFrame] = {}
    for table, rows in results.items():
        if not rows:
            continue

        # Column source priority:
        # 1. Explicit INSERT column list (most reliable — maps values regardless of CREATE order)
        # 2. CREATE TABLE schema (standard case)
        # 3. No columns known (produce integer-indexed DataFrame)
        all_cols = insert_columns.get(table) or schemas.get(table, [])
        want_cols = _COLUMNS.get(table, all_cols)
        ncols = len(all_cols)

        # Normalize row length: pad short rows, truncate oversized ones.
        # Oversized rows occur when the paren-balancing heuristic over-captures —
        # truncating is safe because the extra values are always beyond our wanted columns.
        padded = [
            (r + [None] * max(0, ncols - len(r)))[:ncols]
            for r in rows
        ]
        df = pd.DataFrame(padded, columns=all_cols if all_cols else None)

        keep = [c for c in want_cols if c in df.columns]
        df = df[keep].copy()

        for col in _UNIX_TS_COLS:
            if col in df.columns:
                df[col] = df[col].apply(_to_datetime)

        dfs[table] = df

    return dfs


def load_forum(zip_path: str | Path, tables: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """
    Same as parse(), but adds a 'forum' column with the filename stem to every table.
    Use this when loading multiple forums and merging them — you'll always know
    which forum each row came from.
    """
    dfs = parse(zip_path, tables)
    forum_name = Path(zip_path).stem
    for df in dfs.values():
        df.insert(0, "forum", forum_name)
    return dfs
