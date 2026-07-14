"""
Flat file parser for forum dumps that are not SQL.

Some leaks were distributed as plain text files with a delimiter-separated
row per user, rather than full database dumps. The format varies:

  Cardingmafia.ws: colon-delimited, first line is the header.
  Example:
    userid:username:email:ipaddress:birthday:homepage:icq:password:salt

  OGUsers2021_BF.zip (*_users.csv): proper comma-delimited RFC4180 CSV with
  quoted fields, some of which contain embedded commas (e.g. an argon2 hash
  like `"$argon2id$v=19$m=65536,t=4,p=1$..."`). A naive `str.split(delimiter)`
  would shear those quoted fields apart, so we always parse through Python's
  `csv` module (which is quote-aware) rather than splitting by hand — this
  also makes the colon/pipe/tab/semicolon dumps just as safe if they ever
  contain a quoted field.

These files contain only user data (no posts or PMs), so analysis is limited
to user profiling and cross-forum correlation — not timezone inference or stylometry.
"""

import csv
import zipfile
import io
import pandas as pd
from pathlib import Path


# Map flat-file column names to our canonical names (same as vbulletin._COLUMNS['user']).
# Includes MyBB-style names (uid/regdate/lastactive/postnum) because some dumps
# (e.g. OGUsers2021_BF.zip) are a MyBB `users` table exported as CSV rather than
# a SQL dump — the columns are otherwise identical to the mybb.py parser's schema.
_COLUMN_ALIASES = {
    "userid":     "userid",
    "id":         "userid",
    "uid":        "userid",
    "username":   "username",
    "user":       "username",
    "nick":       "username",
    "login":      "username",
    "email":      "email",
    "mail":       "email",
    "ipaddress":  "ipaddress",
    "ip":         "ipaddress",
    "reg_ip":     "ipaddress",
    "regip":      "ipaddress",
    "regdate":    "joindate",
    "lastactive": "lastactivity",
    "postnum":    "posts",
    "password":   "password",
    "pass":       "password",
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
    first_line = stream.readline()

    # Auto-detect delimiter from the header line. Comma is checked last so
    # existing colon/pipe/tab/semicolon-delimited dumps keep picking their
    # original delimiter even if a quoted field happens to contain a comma.
    delimiter = ":"
    for candidate in [":", "|", "\t", ";", ","]:
        if candidate in first_line:
            delimiter = candidate
            break

    headers = [h.strip().lower() for h in next(csv.reader([first_line], delimiter=delimiter))]

    rows = []
    for parts in csv.reader(stream, delimiter=delimiter):
        if not parts:
            continue
        parts = parts + [None] * max(0, len(headers) - len(parts))
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
