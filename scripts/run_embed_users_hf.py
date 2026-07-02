#!/usr/bin/env python3
"""Estrategia A (embed_users) para HackingForums.

Concatena todos los posts por usuario → 1 embedding por usuario.
Limitado a top-1000 usuarios por foro (por volumen de posts) para
mantener el tiempo de cómputo en ~4-5h.
Trunca la concatenación a MAX_CHARS para evitar bloqueos de Ollama.

Output:
  results/hacking_forums/hf_embed_users_{ts}.npz
  user_ids con prefijo {forum}_{userid}
"""

import sys, time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import ollama
from tqdm import tqdm

from src.utils import load_forum, RESULTS_DIR, DATA_DIR

HF_RESULTS = RESULTS_DIR / "hacking_forums"
HF_RESULTS.mkdir(parents=True, exist_ok=True)
HF_DIR = DATA_DIR / "Hacking Forums"

DEFAULT_MODEL = "qwen3-embedding"
BATCH_SIZE = 32
MAX_CHARS = 50_000
MIN_POSTS = 5
TOP_USERS_PER_FORUM = 1000

FORUMS = [
    "OGUsers_2019.zip",
    "Exploit.in_2013.12.13.zip",
    "Cracked.to_2019.01.zip",
    "Nulled.io_2016.05.zip",
    "RaidForums_2021.zip",
]

# ── Check cache ───────────────────────────────────────────────────────────────
existing = sorted(HF_RESULTS.glob("hf_embed_users_*.npz"))
if existing:
    print(f"[SKIP] Ya existe: {existing[-1].name}")
    sys.exit(0)

# ── Load and concatenate per forum ────────────────────────────────────────────
all_user_ids = []
all_texts = []

for fname in FORUMS:
    zip_path = HF_DIR / fname
    stem = Path(fname).stem
    if not zip_path.exists():
        print(f"[SKIP] No encontrado: {fname}")
        continue

    print(f"\n=== {stem} ===")
    t0 = time.time()
    try:
        dfs = load_forum(zip_path)
    except Exception as e:
        print(f"  ERROR cargando: {e}")
        continue

    post_df = dfs.get("post", pd.DataFrame())
    if post_df.empty:
        print(f"  Sin posts — saltando")
        continue

    text_col = next((c for c in ("pagetext", "message", "post_content") if c in post_df.columns), None)
    if text_col is None:
        print(f"  Sin columna de texto — saltando")
        continue

    df = post_df[["userid", text_col]].dropna().copy()
    df[text_col] = df[text_col].astype(str).str.strip()
    df = df[df[text_col].str.len() > 0]

    # Top-N users by post count
    post_counts = df.groupby("userid").size()
    top_uids = post_counts[post_counts >= MIN_POSTS].nlargest(TOP_USERS_PER_FORUM).index
    df = df[df["userid"].isin(top_uids)]

    grouped = df.groupby("userid")[text_col].apply(lambda x: " ".join(x.tolist()))
    for uid, text in grouped.items():
        all_user_ids.append(f"{stem}_{uid}")
        all_texts.append(text[:MAX_CHARS])

    elapsed = time.time() - t0
    print(f"  {len(grouped):,} usuarios seleccionados ({elapsed:.0f}s carga)")

print(f"\nTotal usuarios a embedir: {len(all_user_ids):,}")
print(f"Texto más largo (tras truncar): {max(len(t) for t in all_texts):,} chars")

# ── Embed ─────────────────────────────────────────────────────────────────────
t_embed = time.time()
results = []
batches = [all_texts[i:i + BATCH_SIZE] for i in range(0, len(all_texts), BATCH_SIZE)]
for batch in tqdm(batches, desc=f"Embedding [{DEFAULT_MODEL}]"):
    resp = ollama.embed(model=DEFAULT_MODEL, input=batch)
    results.extend(resp.embeddings)

elapsed_embed = time.time() - t_embed
vectors = np.array(results, dtype=np.float32)
print(f"\nEmbedding completado en {elapsed_embed/3600:.2f}h  |  shape: {vectors.shape}")

# ── Save ──────────────────────────────────────────────────────────────────────
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out = HF_RESULTS / f"hf_embed_users_{ts}.npz"
np.savez_compressed(out, user_ids=np.array(all_user_ids, dtype="U128"), vectors=vectors)
print(f"Guardado: {out}")
