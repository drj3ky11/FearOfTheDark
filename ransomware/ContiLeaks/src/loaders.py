"""
Loaders para los tres formatos de los chats filtrados de Conti.

Todos devuelven un DataFrame con el schema unificado:
    timestamp  : datetime64[ns, UTC]
    username   : str   — alias del actor (sin dominio)
    to_user    : str   — destinatario (Jabber) o sala (Rocket.Chat)
    message    : str   — texto del mensaje
    source     : str   — "jabber_2020" | "jabber_2021" | "rocketchat"
    channel    : str   — identificador de conversación derivado del nombre de archivo
"""

import json
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Jabber (Chat Logs 2020 y Jabber Chat Logs 2021-2022)
# ---------------------------------------------------------------------------

def _iter_jabber_objects(text: str):
    """Parsea un archivo de objetos JSON concatenados (no array)."""
    decoder = json.JSONDecoder()
    pos = 0
    text = text.strip()
    while pos < len(text):
        while pos < len(text) and text[pos] in " \t\n\r":
            pos += 1
        if pos >= len(text):
            break
        obj, end = decoder.raw_decode(text, pos)
        pos = end
        yield obj


def _username(jid: str) -> str:
    return jid.split("@")[0] if "@" in jid else jid


def load_jabber(directory: Path, source_label: str) -> pd.DataFrame:
    """
    Carga todos los archivos JSON de un directorio Jabber.
    Los archivos son NDJSON multilínea: objetos JSON concatenados, no arrays.
    """
    records = []
    for fpath in sorted(directory.rglob("*.json")):
        channel = fpath.stem          # ej. "185.25.51.173-20200622"
        text = fpath.read_text(encoding="utf-8", errors="replace")
        for obj in _iter_jabber_objects(text):
            records.append({
                "timestamp": obj.get("ts"),
                "username":  _username(obj.get("from", "")),
                "to_user":   _username(obj.get("to", "")),
                "message":   obj.get("body", ""),
                "source":    source_label,
                "channel":   channel,
            })

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


def load_jabber_2020(raw_dir: Path) -> pd.DataFrame:
    directory = raw_dir / "Conti Chat Logs 2020" / "Conti Chat Logs 2020"
    return load_jabber(directory, source_label="jabber_2020")


def load_jabber_2021(raw_dir: Path) -> pd.DataFrame:
    directory = raw_dir / "Conti Jabber Chat Logs 2021 - 2022" / "Conti Jabber Chat Logs 2021 - 2022"
    return load_jabber(directory, source_label="jabber_2021")


# ---------------------------------------------------------------------------
# Rocket.Chat
# ---------------------------------------------------------------------------

def load_rocketchat(raw_dir: Path) -> pd.DataFrame:
    """
    Carga todos los archivos JSON de Rocket.Chat.
    Formato: {"messages": [...]}
    Filtra system events (mensajes con campo "t").
    El nombre de archivo sigue el patrón YYYY-MM-DD-{channel}.json
    """
    root = raw_dir / "Conti Rocket Chat Leaks" / "Conti Rocket Chat Leaks"
    records = []
    for fpath in sorted(root.rglob("*.json")):
        # Extraer nombre de canal del archivo: "2022-02-17-general" → "general"
        parts = fpath.stem.split("-", maxsplit=3)
        channel = parts[3] if len(parts) == 4 else fpath.stem

        try:
            data = json.loads(fpath.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue

        for msg in data.get("messages", []):
            if msg.get("t"):          # system event (uj = user joined, etc.)
                continue
            user_obj = msg.get("u") or {}
            records.append({
                "timestamp": msg.get("ts"),
                "username":  user_obj.get("username", ""),
                "to_user":   msg.get("rid", ""),
                "message":   msg.get("msg", ""),
                "source":    "rocketchat",
                "channel":   channel,
            })

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Loader unificado
# ---------------------------------------------------------------------------

def load_all(raw_dir: Path) -> pd.DataFrame:
    """Carga y concatena las tres fuentes en un único DataFrame."""
    raw_dir = Path(raw_dir)
    frames = [
        load_jabber_2020(raw_dir),
        load_jabber_2021(raw_dir),
        load_rocketchat(raw_dir),
    ]
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df
