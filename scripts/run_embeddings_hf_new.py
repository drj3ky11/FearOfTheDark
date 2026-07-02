#!/usr/bin/env python3
"""Añade embed_users de los foros Tier 1 nuevos al npz existente de HackingForums.
Procesa Exploit.in, Cracked.to y Nulled.io secuencialmente y hace append."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.utils import load_forum, RESULTS_DIR, DATA_DIR
from src.embeddings import embed_users

HF_RESULTS = RESULTS_DIR / 'hacking_forums'
HF_DIR = DATA_DIR / 'Hacking Forums'
EMBED_PATH = HF_RESULTS / 'hacking_forums_user_embeddings.npz'

NEW_FORUMS = [
    "Exploit.in_2013.12.13.zip",
    "Cracked.to_2019.01.zip",
    "Nulled.io_2016.05.zip",
]

# Cargar embeddings existentes
cached = np.load(EMBED_PATH, allow_pickle=False)
all_user_ids = list(cached['user_ids'])
all_vectors  = [cached['vectors']]
already_done = set(uid.split('_')[0] for uid in all_user_ids)
print(f"Embeddings existentes: {len(all_user_ids):,} usuarios")
print(f"Foros ya procesados: {already_done}\n")

t_global = time.time()

for fname in NEW_FORUMS:
    stem = Path(fname).stem
    if any(stem.lower() in uid.lower() for uid in all_user_ids[:10]):
        print(f"[SKIP] {stem} — ya está en el npz")
        continue

    path = HF_DIR / fname
    print(f"=== {fname} ===")
    t0 = time.time()

    dfs = load_forum(path)
    posts = dfs.get('post', pd.DataFrame()).copy()
    print(f"  Posts cargados: {len(posts):,} ({time.time()-t0:.0f}s)")

    if len(posts) == 0:
        print("  Sin posts — saltando")
        continue

    posts['userid'] = stem + '_' + posts['userid'].astype(str)

    t1 = time.time()
    user_ids, vectors = embed_users(posts, min_posts=5)
    print(f"  Usuarios embebidos: {len(user_ids):,} ({time.time()-t1:.0f}s)")

    # Normalizar L2
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / np.where(norms > 0, norms, 1)

    all_user_ids.extend(user_ids)
    all_vectors.append(vectors.astype(np.float32))
    print(f"  Acumulado total: {len(all_user_ids):,} usuarios\n")

# Guardar
final_vectors = np.vstack(all_vectors)
np.savez(
    EMBED_PATH,
    user_ids=np.array(all_user_ids, dtype='U64'),
    vectors=final_vectors.astype(np.float32),
)
print(f"\nGuardado: {EMBED_PATH.name}")
print(f"  Shape final: {final_vectors.shape}")
print(f"  Tiempo total: {time.time()-t_global:.0f}s")
