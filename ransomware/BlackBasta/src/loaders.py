"""
Loader para los chats filtrados de Black Basta (Matrix, 2023-2024).

Formato de origen: pseudo-JSON con claves sin comillas y valores sin comillas,
objetos concatenados (no array). Ejemplo:

    {
        timestamp: 2023-09-18 13:35:07,
        chat_id: !VdvDXHFZwWDpIAtpCj:matrix.bestflowers247.online,
        sender_alias: @usernamenn:matrix.bestflowers247.online,
        message: texto del mensaje
    }

Schema de salida unificado:
    timestamp  : datetime64[ns, UTC]
    username   : str   — parte local del sender_alias (antes de ':matrix.')
    channel    : str   — parte local del chat_id (sin '!' ni dominio)
    message    : str   — texto del mensaje (puede ser multilínea)
    source     : str   — siempre "blackbasta"
"""

import re
from pathlib import Path

import pandas as pd

_RE_BLOCK = re.compile(r'\{([^{}]*?)\}', re.DOTALL)
_RE_TS    = re.compile(r'timestamp:\s*(.+?),\s*\n')
_RE_CHAT  = re.compile(r'chat_id:\s*(.+?),\s*\n')
_RE_ALIAS = re.compile(r'sender_alias:\s*(.+?),\s*\n')
_RE_MSG   = re.compile(r'message:\s*(.*)', re.DOTALL)


def _local_part(matrix_id: str) -> str:
    """'@usernamenn:matrix.bestflowers247.online' → 'usernamenn'"""
    local = matrix_id.lstrip('!@').split(':')[0]
    return local


def load_blackbasta(raw_dir: Path) -> pd.DataFrame:
    """
    Carga blackbasta_chats.json desde raw_dir.
    Acepta tanto el directorio contenedor como la ruta al fichero directamente.
    """
    raw_dir = Path(raw_dir)
    if raw_dir.is_file():
        fpath = raw_dir
    else:
        candidates = list(raw_dir.rglob('blackbasta_chats.json'))
        if not candidates:
            raise FileNotFoundError(f'No se encontró blackbasta_chats.json en {raw_dir}')
        fpath = candidates[0]

    content = fpath.read_text(encoding='utf-8', errors='replace')

    records = []
    for m in _RE_BLOCK.finditer(content):
        block = m.group(1)

        ts_m    = _RE_TS.search(block)
        chat_m  = _RE_CHAT.search(block)
        alias_m = _RE_ALIAS.search(block)
        msg_m   = _RE_MSG.search(block)

        if not (ts_m and chat_m and alias_m and msg_m):
            continue

        records.append({
            'timestamp': ts_m.group(1).strip(),
            'username':  _local_part(alias_m.group(1).strip()),
            'channel':   _local_part(chat_m.group(1).strip()),
            'message':   msg_m.group(1).strip(),
            'source':    'blackbasta',
        })

    df = pd.DataFrame(records)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    return df
