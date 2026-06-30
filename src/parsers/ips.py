"""
IPS (Invision Power Suite) SQL Dump Parser
===========================================
Supports IPS 3.x (ibf_ prefix) and IPS 4.x (no prefix).

IPS 4.x → standard mapping:
  forums_posts.pid / topic_id / author_id / author_name / post_date / post
  core_members.member_id / name / email / joined / ip_address / language
  forums_topics.tid / forum_id / title / start_date / starter_id
  orig_forums.id / name
  core_message_posts + core_message_topics → private_message

IPS 3.x → standard mapping:
  ibf_posts.pid / topic_id / author_id / author_name / post_date / post
  ibf_members.member_id / members_display_name / email / joined / ip_address
  ibf_topics.tid / forum_id / title / start_date / starter_id
  ibf_forums.id / name
  ibf_msg_posts + ibf_msg_topics → private_message
"""

import zipfile
import io
import re
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

from src.parsers.vbulletin import parse as _vb_parse

# Timestamps Unix válidos: 2000-01-01 a 2030-01-01
_TS_MIN = 946684800
_TS_MAX = 1893456000


def _ts(val: str | None) -> datetime | None:
    if val is None or val == "0":
        return None
    try:
        ts = int(val)
        if not (_TS_MIN <= ts <= _TS_MAX):
            return None
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def _detect_version(zip_path: str | Path) -> str:
    """
    Returns:
      '3_ibf' — IPS 3.x with ibf_ prefix (e.g. Exploit.in)
      '3'     — IPS 3.x without prefix (e.g. Nulled.io)
      '4'     — IPS 4.x (core_members / forums_posts)
      ''      — unknown
    """
    try:
        with zipfile.ZipFile(zip_path) as zf:
            sql_names = [n for n in zf.namelist() if n.lower().endswith(".sql")]
            if not sql_names:
                return ""
            biggest = max(sql_names, key=lambda n: zf.getinfo(n).file_size)
            with zf.open(biggest) as f:
                stream = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
                # Regex to match table name in CREATE TABLE or INSERT INTO
                _tbl = re.compile(r'(?:create table|insert into)\s+`(\w+)`', re.I)
                in_members_table = False
                for i, line in enumerate(stream):
                    ll = line.lower()
                    if "ibf_members" in ll or "ibf_posts" in ll or "ibf_topics" in ll:
                        return "3_ibf"
                    m = _tbl.search(line)
                    if m:
                        tname = m.group(1).lower()
                        if tname in ("core_members", "forums_posts"):
                            return "4"
                        if tname == "members":
                            in_members_table = True
                    # IPS 3.x without prefix: CREATE TABLE `members` followed by member_id column
                    if in_members_table and "`member_id`" in ll:
                        return "3"
                    if in_members_table and "engine=" in ll:
                        in_members_table = False
                    if i > 500_000:
                        break
    except Exception:
        pass
    return ""


def _parse_v4(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    raw = _vb_parse(zip_path, tables=[
        "forums_posts", "core_members",
        "forums_topics", "orig_forums",
        "core_message_posts", "core_message_topics",
    ])

    dfs: dict[str, pd.DataFrame] = {}

    # --- Posts (v4) ---
    if "forums_posts" in raw:
        p = raw["forums_posts"].copy()
        rename = {
            "pid":         "postid",
            "topic_id":    "threadid",
            "author_id":   "userid",
            "author_name": "username",
            "post_date":   "dateline",
            "post":        "pagetext",
        }
        p = p.rename(columns={k: v for k, v in rename.items() if k in p.columns})
        if "dateline" in p.columns:
            p["dateline"] = p["dateline"].apply(_ts)
        if "queued" in p.columns:
            p = p[p["queued"].astype(str) == "0"].copy()
        dfs["post"] = p[
            [c for c in ["postid", "threadid", "userid", "username", "dateline", "pagetext"]
             if c in p.columns]
        ]

    # --- Users (v4) ---
    if "core_members" in raw:
        u = raw["core_members"].copy()
        rename = {
            "member_id":  "userid",
            "name":       "username",
            "joined":     "joindate",
            "ip_address": "ipaddress",
        }
        u = u.rename(columns={k: v for k, v in rename.items() if k in u.columns})
        if "joindate" in u.columns:
            u["joindate"] = u["joindate"].apply(_ts)
        dfs["user"] = u[
            [c for c in ["userid", "username", "email", "joindate", "ipaddress", "language"]
             if c in u.columns]
        ]

    # --- Threads (v4) ---
    if "forums_topics" in raw:
        t = raw["forums_topics"].copy()
        rename = {
            "tid":        "threadid",
            "forum_id":   "forumid",
            "title":      "title",
            "start_date": "dateline",
            "starter_id": "userid",
            "posts":      "post_count",
            "views":      "views",
        }
        t = t.rename(columns={k: v for k, v in rename.items() if k in t.columns})
        if "dateline" in t.columns:
            t["dateline"] = t["dateline"].apply(_ts)
        dfs["thread"] = t[
            [c for c in ["threadid", "forumid", "title", "dateline", "userid", "post_count", "views"]
             if c in t.columns]
        ]

    # --- Forums (v4) ---
    if "orig_forums" in raw:
        f = raw["orig_forums"].copy()
        rename = {"id": "forumid", "name": "name", "topics": "topic_count", "posts": "post_count"}
        f = f.rename(columns={k: v for k, v in rename.items() if k in f.columns})
        dfs["forum"] = f[
            [c for c in ["forumid", "name", "topic_count", "post_count"] if c in f.columns]
        ]

    # --- PMs (v4) ---
    if "core_message_posts" in raw and "core_message_topics" in raw:
        mp = raw["core_message_posts"].copy()
        mt = raw["core_message_topics"].copy()

        # Renombrar columnas de posts
        mp_rename = {
            "msg_topic_id":    "topic_id",
            "msg_date":        "dateline",
            "msg_post":        "text",
            "msg_author_id":   "sender_id",
            "msg_ip_address":  "ipaddress",
            "msg_is_first_post": "is_first",
        }
        mp = mp.rename(columns={k: v for k, v in mp_rename.items() if k in mp.columns})
        if "dateline" in mp.columns:
            mp["dateline"] = mp["dateline"].apply(_ts)

        # Renombrar columnas de topics para obtener receiver
        mt_rename = {
            "mt_id":            "topic_id",
            "mt_title":         "subject",
            "mt_starter_id":    "sender_id",
            "mt_to_member_id":  "receiver_id",
        }
        mt = mt.rename(columns={k: v for k, v in mt_rename.items() if k in mt.columns})
        mt_map = mt[["topic_id", "receiver_id"]].drop_duplicates("topic_id")

        # Join para añadir receiver_id a cada mensaje
        pm = mp.merge(mt_map, on="topic_id", how="left")
        dfs["private_message"] = pm[
            [c for c in ["topic_id", "sender_id", "receiver_id", "dateline", "text"]
             if c in pm.columns]
        ]

    return dfs


def _parse_v3(zip_path: str | Path, prefix: str = "ibf_") -> dict[str, pd.DataFrame]:
    """Parse IPS 3.x dump. prefix='ibf_' for standard installs, '' for no-prefix installs."""
    px = prefix
    raw = _vb_parse(zip_path, tables=[
        f"{px}posts", f"{px}members",
        f"{px}topics", f"{px}forums",
        f"{px}msg_posts", f"{px}msg_topics",
    ])

    dfs: dict[str, pd.DataFrame] = {}

    # --- Posts (v3) ---
    if f"{px}posts" in raw:
        df = raw[f"{px}posts"].copy()
        df = df.rename(columns={k: v for k, v in {
            "pid":         "postid",
            "topic_id":    "threadid",
            "author_id":   "userid",
            "author_name": "username",
            "post_date":   "dateline",
            "post":        "pagetext",
        }.items() if k in df.columns})
        if "dateline" in df.columns:
            df["dateline"] = df["dateline"].apply(_ts)
        if "queued" in df.columns:
            df = df[df["queued"].astype(str) == "0"].copy()
        dfs["post"] = df[
            [c for c in ["postid", "threadid", "userid", "username", "dateline", "pagetext"]
             if c in df.columns]
        ]

    # --- Users (v3) ---
    if f"{px}members" in raw:
        df = raw[f"{px}members"].copy()
        # IPS 3.x stores display name in members_display_name, fallback to name
        if "members_display_name" in df.columns and "name" not in df.columns:
            df = df.rename(columns={"members_display_name": "name"})
        elif "members_display_name" in df.columns:
            df["name"] = df["members_display_name"].where(df["members_display_name"].notna(), df["name"])
        df = df.rename(columns={k: v for k, v in {
            "member_id":  "userid",
            "name":       "username",
            "joined":     "joindate",
            "ip_address": "ipaddress",
        }.items() if k in df.columns})
        if "joindate" in df.columns:
            df["joindate"] = df["joindate"].apply(_ts)
        dfs["user"] = df[
            [c for c in ["userid", "username", "email", "joindate", "ipaddress"]
             if c in df.columns]
        ]

    # --- Threads (v3) ---
    if f"{px}topics" in raw:
        df = raw[f"{px}topics"].copy()
        df = df.rename(columns={k: v for k, v in {
            "tid":        "threadid",
            "forum_id":   "forumid",
            "title":      "title",
            "start_date": "dateline",
            "starter_id": "userid",
            "posts":      "post_count",
            "views":      "views",
        }.items() if k in df.columns})
        if "dateline" in df.columns:
            df["dateline"] = df["dateline"].apply(_ts)
        dfs["thread"] = df[
            [c for c in ["threadid", "forumid", "title", "dateline", "userid", "post_count", "views"]
             if c in df.columns]
        ]

    # --- Forums (v3) ---
    if f"{px}forums" in raw:
        df = raw[f"{px}forums"].copy()
        df = df.rename(columns={k: v for k, v in {
            "id": "forumid", "name": "name", "topics": "topic_count", "posts": "post_count"
        }.items() if k in df.columns})
        dfs["forum"] = df[
            [c for c in ["forumid", "name", "topic_count", "post_count"] if c in df.columns]
        ]

    # --- PMs (v3) ---
    if f"{px}msg_posts" in raw and f"{px}msg_topics" in raw:
        mp = raw[f"{px}msg_posts"].copy()
        mt = raw[f"{px}msg_topics"].copy()
        mp = mp.rename(columns={k: v for k, v in {
            "msg_topic_id":  "topic_id",
            "msg_date":      "dateline",
            "msg_post":      "text",
            "msg_author_id": "sender_id",
        }.items() if k in mp.columns})
        if "dateline" in mp.columns:
            mp["dateline"] = mp["dateline"].apply(_ts)
        mt = mt.rename(columns={k: v for k, v in {
            "mt_id":           "topic_id",
            "mt_to_member_id": "receiver_id",
        }.items() if k in mt.columns})
        if "topic_id" in mt.columns and "receiver_id" in mt.columns:
            mt_map = mt[["topic_id", "receiver_id"]].drop_duplicates("topic_id")
            pm = mp.merge(mt_map, on="topic_id", how="left")
        else:
            pm = mp
        dfs["private_message"] = pm[
            [c for c in ["topic_id", "sender_id", "receiver_id", "dateline", "text"]
             if c in pm.columns]
        ]

    return dfs


def parse(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Parse an IPS SQL dump zip and return standard-schema DataFrames.
    Auto-detects IPS 3.x ibf_ prefix, IPS 3.x no-prefix, and IPS 4.x.

    Returns a dict with keys: 'post', 'user', 'thread', 'forum', 'private_message'.
    """
    version = _detect_version(zip_path)
    if version == "3_ibf":
        return _parse_v3(zip_path, prefix="ibf_")
    if version == "3":
        return _parse_v3(zip_path, prefix="")
    return _parse_v4(zip_path)


def load_forum(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    """Same as parse(), but adds a 'forum' column with the filename stem."""
    dfs = parse(zip_path)
    forum_name = Path(zip_path).stem
    for df in dfs.values():
        df.insert(0, "forum", forum_name)
    return dfs
