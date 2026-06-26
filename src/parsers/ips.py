"""
IPS (Invision Power Suite) SQL Dump Parser
===========================================
IronMarch ran on IPS, not vBulletin. The schema is different but the dump
format (MySQL INSERT INTO) is identical, so we reuse the vBulletin SQL
parsing machinery and just remap the IPS table/column names to our standard
schema.

IPS → standard mapping:
  forums_posts.pid         → postid
  forums_posts.topic_id    → threadid
  forums_posts.author_id   → userid
  forums_posts.author_name → username
  forums_posts.post_date   → dateline  (Unix timestamp)
  forums_posts.post        → pagetext

  core_members.member_id   → userid
  core_members.name        → username
  core_members.email       → email
  core_members.joined      → joindate  (Unix timestamp)
  core_members.ip_address  → ipaddress
  core_members.language    → language

  forums_topics.tid        → threadid
  forums_topics.forum_id   → forumid
  forums_topics.title      → title
  forums_topics.start_date → dateline
  forums_topics.starter_id → userid

  orig_forums.id           → forumid
  orig_forums.name         → name

  core_message_posts + core_message_topics → private_message
    sender_id, receiver_id, dateline, text
"""

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


def parse(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Parse an IPS SQL dump zip and return standard-schema DataFrames.

    Returns a dict with keys: 'post', 'user', 'thread', 'forum', 'private_message'.
    """
    raw = _vb_parse(zip_path, tables=[
        "forums_posts", "core_members",
        "forums_topics", "orig_forums",
        "core_message_posts", "core_message_topics",
    ])

    dfs: dict[str, pd.DataFrame] = {}

    # --- Posts ---
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

    # --- Users ---
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

    # --- Threads (forums_topics) ---
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

    # --- Forums (orig_forums tiene el campo name; forums_forums no lo tiene) ---
    if "orig_forums" in raw:
        f = raw["orig_forums"].copy()
        rename = {"id": "forumid", "name": "name", "topics": "topic_count", "posts": "post_count"}
        f = f.rename(columns={k: v for k, v in rename.items() if k in f.columns})
        dfs["forum"] = f[
            [c for c in ["forumid", "name", "topic_count", "post_count"] if c in f.columns]
        ]

    # --- Mensajes privados ---
    # core_message_posts tiene sender; core_message_topics tiene receiver (mt_to_member_id)
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


def load_forum(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    """Same as parse(), but adds a 'forum' column with the filename stem."""
    dfs = parse(zip_path)
    forum_name = Path(zip_path).stem
    for df in dfs.values():
        df.insert(0, "forum", forum_name)
    return dfs
