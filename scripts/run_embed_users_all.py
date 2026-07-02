#!/usr/bin/env python3
"""Computa estrategia A (embed_users) para IronMarch y HackingForums.

Concatena todos los posts por usuario → 1 embedding por usuario.
Trunca a MAX_CHARS para evitar bloqueos con usuarios muy prolíficos.

Outputs:
  results/ironmarch/s5a_embed_users_{ts}.npz
  results/hacking_forums/hf_embed_users_{ts}.npz
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

DEFAULT_MODEL = "qwen3-embedding"
BATCH_SIZE = 32
MAX_CHARS = 50_000  # truncate per-user concatenation to avoid Ollama hangs
MIN_POSTS = 5


def embed_texts_safe(texts: list[str], model: str = DEFAULT_MODEL) -> np.ndarray:
    results = []
    batches = [texts[i:i + BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
    for batch in tqdm(batches, desc=f"Embedding [{model}]"):
        clean = [t[:MAX_CHARS] if t else "" for t in batch]
        resp = ollama.embed(model=model, input=clean)
        results.extend(resp.embeddings)
    return np.array(results, dtype=np.float32)


def embed_users_from_posts(posts_df: pd.DataFrame, text_col: str = "pagetext"):
    df = posts_df.dropna(subset=["userid", text_col]).copy()
    df[text_col] = df[text_col].astype(str).str.strip()
    df = df[df[text_col].str.len() > 0]

    post_counts = df.groupby("userid").size()
    valid_uids = post_counts[post_counts >= MIN_POSTS].index
    df = df[df["userid"].isin(valid_uids)]

    grouped = df.groupby("userid")[text_col].apply(lambda x: " ".join(x.tolist()))
    user_ids = grouped.index.tolist()
    texts = grouped.tolist()

    print(f"  Usuarios: {len(user_ids):,}")
    print(f"  Texto más largo antes de truncar: {max(len(t) for t in texts):,} chars")

    t0 = time.time()
    vectors = embed_texts_safe(texts)
    elapsed = time.time() - t0
    print(f"  Completado en {elapsed/60:.1f} min")
    return user_ids, vectors


# ── IronMarch ─────────────────────────────────────────────────────────────────
IM_RESULTS = RESULTS_DIR / "ironmarch"
IM_ZIP = DATA_DIR / "Far Right Forum" / "IronMarch_2019.11.zip"

existing_a = sorted(IM_RESULTS.glob("s5a_embed_users_*.npz"))
if existing_a:
    print(f"[SKIP] IronMarch Part A ya existe: {existing_a[-1].name}")
else:
    print("=== IronMarch — embed_users ===")
    posts = pd.read_parquet(IM_RESULTS / "posts_clean.parquet")
    text_col = "pagetext" if "pagetext" in posts.columns else "message"
    user_ids, vectors = embed_users_from_posts(posts, text_col)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = IM_RESULTS / f"s5a_embed_users_{ts}.npz"
    np.savez_compressed(out, user_ids=np.array(user_ids, dtype="U64"), vectors=vectors)
    print(f"  Guardado: {out.name}")

# ── HackingForums ─────────────────────────────────────────────────────────────
HF_RESULTS = RESULTS_DIR / "hacking_forums"
HF_RESULTS.mkdir(parents=True, exist_ok=True)

existing_hf = sorted(HF_RESULTS.glob("hf_embed_users_*.npz"))
if existing_hf:
    print(f"[SKIP] HackingForums Part A ya existe: {existing_hf[-1].name}")
else:
    print("\n=== HackingForums — embed_users ===")
    hf_parquet = HF_RESULTS / "posts_all_clean.parquet"
    if not hf_parquet.exists():
        # fallback: try combined parquet
        candidates = sorted(HF_RESULTS.glob("posts_*.parquet"))
        hf_parquet = candidates[-1] if candidates else None

    if hf_parquet is None or not hf_parquet.exists():
        print("  ERROR: no se encontró parquet de posts de HackingForums. Ejecutar notebook 01 primero.")
    else:
        print(f"  Cargando: {hf_parquet.name}")
        posts_hf = pd.read_parquet(hf_parquet)
        # Prefix userid with forum stem so IDs don't collide
        if "forum" in posts_hf.columns:
            posts_hf["userid"] = posts_hf["forum"] + "_" + posts_hf["userid"].astype(str)
        text_col = next((c for c in ("pagetext", "message", "post_content") if c in posts_hf.columns), None)
        if text_col is None:
            print("  ERROR: no se encontró columna de texto.")
        else:
            user_ids_hf, vectors_hf = embed_users_from_posts(posts_hf, text_col)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = HF_RESULTS / f"hf_embed_users_{ts}.npz"
            np.savez_compressed(out, user_ids=np.array(user_ids_hf, dtype="U64"), vectors=vectors_hf)
            print(f"  Guardado: {out.name}")

print("\nDone.")
