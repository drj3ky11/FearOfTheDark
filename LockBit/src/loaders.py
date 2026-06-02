"""
Parser for the LockBit panel DB SQL dump (MySQL 8.0 / phpMyAdmin format).
Returns a dict of DataFrames, one per target table, with no MySQL server required.
"""

import re
import zipfile
import pandas as pd
from pathlib import Path

TABLES_OF_INTEREST = {
    'users', 'clients', 'chats', 'builds', 'btc_addresses', 'invites', 'pkeys'
}


def _tokenize_row(row_str: str) -> list:
    """Parse a single SQL row string '(v1, v2, NULL, ...)' into a Python list."""
    s = row_str.strip()
    # Strip outer parens and trailing punctuation
    if s.startswith('('):
        s = s[1:]
    for suffix in (');', '),', ')'):
        if s.endswith(suffix):
            s = s[:-len(suffix)]
            break

    values = []
    current = []
    in_string = False
    escaped = False

    for ch in s:
        if escaped:
            current.append(ch)
            escaped = False
        elif in_string:
            if ch == '\\':
                current.append(ch)
                escaped = True
            elif ch == "'":
                in_string = False
                current.append(ch)
            else:
                current.append(ch)
        else:
            if ch == "'":
                in_string = True
                current.append(ch)
            elif ch == ',':
                values.append(''.join(current).strip())
                current = []
            else:
                current.append(ch)

    if current:
        values.append(''.join(current).strip())

    cleaned = []
    for v in values:
        v = v.strip()
        if v.upper() == 'NULL':
            cleaned.append(None)
        elif v.startswith("'") and v.endswith("'"):
            inner = v[1:-1]
            inner = (inner
                     .replace("\\'", "'")
                     .replace('\\n', '\n')
                     .replace('\\r', '\r')
                     .replace('\\\\', '\\')
                     .replace('\\"', '"')
                     .replace('\\t', '\t')
                     .replace('\\0', '\x00'))
            cleaned.append(inner)
        elif v.upper().startswith('0X'):
            # Hex BLOB — decode to UTF-8 string (public keys, etc.)
            try:
                cleaned.append(bytes.fromhex(v[2:]).decode('utf-8', errors='replace'))
            except Exception:
                cleaned.append(v)
        else:
            try:
                cleaned.append(int(v))
            except ValueError:
                try:
                    cleaned.append(float(v))
                except ValueError:
                    cleaned.append(v if v else None)

    return cleaned


def _extract_columns(line_iter) -> dict[str, list[str]]:
    """
    Scan lines to find CREATE TABLE blocks and return {table: [col, ...]} for
    tables we care about.
    """
    schemas: dict[str, list[str]] = {}
    current_table = None
    cols = []

    for line in line_iter:
        line = line.rstrip('\n')
        stripped = line.strip()

        m = re.match(r"CREATE TABLE `(\w+)`", stripped)
        if m:
            current_table = m.group(1)
            cols = []
            continue

        if current_table:
            col_m = re.match(r'`(\w+)`', stripped)
            if col_m:
                cols.append(col_m.group(1))
            elif stripped.startswith(') ENGINE='):
                schemas[current_table] = cols
                current_table = None
                cols = []

    return schemas


def _parse_sql(path: Path) -> dict[str, pd.DataFrame]:
    """Read SQL dump (plain file or inside a zip) and return dict of DataFrames."""

    def open_sql():
        if path.suffix == '.zip':
            zf = zipfile.ZipFile(path)
            name = next(n for n in zf.namelist() if n.endswith('.sql'))
            return zf.open(name)
        return open(path, 'rb')

    # --- Pass 1: extract schemas ---
    with open_sql() as fh:
        schemas = _extract_columns(
            line.decode('utf-8', errors='replace') for line in fh
        )

    # --- Pass 2: extract rows ---
    raw_rows: dict[str, list] = {t: [] for t in TABLES_OF_INTEREST}
    current_table: str | None = None
    in_insert = False

    with open_sql() as fh:
        for raw_line in fh:
            line = raw_line.decode('utf-8', errors='replace').rstrip('\n')
            stripped = line.strip()

            m = re.match(r"INSERT INTO `(\w+)` VALUES", stripped)
            if m:
                current_table = m.group(1)
                in_insert = True
                continue

            if in_insert:
                if stripped.startswith('(') and current_table in TABLES_OF_INTEREST:
                    raw_rows[current_table].append(_tokenize_row(stripped))
                elif not stripped.startswith('('):
                    in_insert = False
                    current_table = None

    # --- Build DataFrames ---
    tables: dict[str, pd.DataFrame] = {}
    for table, rows in raw_rows.items():
        if not rows:
            tables[table] = pd.DataFrame(columns=schemas.get(table, []))
            continue
        cols = schemas.get(table, [])
        # Align row length to schema
        aligned = [r[:len(cols)] + [None] * max(0, len(cols) - len(r)) for r in rows]
        tables[table] = pd.DataFrame(aligned, columns=cols)

    return tables


def _post_process(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Type coercions and derived columns."""
    import pandas as pd

    clients = tables.get('clients')
    if clients is not None and 'date_first' in clients.columns:
        clients['date_first'] = pd.to_datetime(
            pd.to_numeric(clients['date_first'], errors='coerce'), unit='s', utc=True
        )
        clients['date_last'] = pd.to_datetime(
            pd.to_numeric(clients['date_last'], errors='coerce'), unit='s', utc=True
        )
        clients['last_download'] = pd.to_datetime(
            pd.to_numeric(clients['last_download'], errors='coerce').replace(0, None), unit='s', utc=True
        )
        tables['clients'] = clients

    chats = tables.get('chats')
    if chats is not None and 'created_at' in chats.columns:
        chats['created_at'] = pd.to_datetime(chats['created_at'], errors='coerce', utc=True)
        chats['date'] = pd.to_datetime(
            pd.to_numeric(chats['date'], errors='coerce'), unit='s', utc=True
        )
        # Sender label: flag=1 → operator, flag=0 → victim
        chats['sender'] = chats['flag'].map({1: 'operator', 0: 'victim'})
        tables['chats'] = chats

    builds = tables.get('builds')
    if builds is not None and 'date' in builds.columns:
        builds['date'] = pd.to_datetime(
            pd.to_numeric(builds['date'], errors='coerce'), unit='s', utc=True
        )
        tables['builds'] = builds

    users = tables.get('users')
    if users is not None and 'last_online' in users.columns:
        users['last_online_dt'] = pd.to_datetime(
            pd.to_numeric(users['last_online'], errors='coerce'), unit='s', utc=True
        )
        users['reg_date_dt'] = pd.to_datetime(
            pd.to_numeric(users['reg_date'], errors='coerce'), unit='s', utc=True
        )
        tables['users'] = users

    invites = tables.get('invites')
    if invites is not None and 'created_at' in invites.columns:
        invites['created_at'] = pd.to_datetime(invites['created_at'], errors='coerce', utc=True)
        tables['invites'] = invites

    return tables


def load_lockbit(path) -> dict[str, pd.DataFrame]:
    """
    Load the LockBit panel DB dump.

    Args:
        path: Path to the .sql file or the .zip archive containing it.

    Returns:
        dict with keys: users, clients, chats, builds, btc_addresses, invites, pkeys
        Values are pandas DataFrames.
    """
    path = Path(path)
    tables = _parse_sql(path)
    tables = _post_process(tables)
    return tables
