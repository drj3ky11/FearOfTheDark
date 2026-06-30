#!/usr/bin/env python3
"""Añade centroides muestreados (top-5000 usuarios, top-50 posts) de los foros
Tier 1 nuevos. Crea un nuevo npz consolidado con todos los foros."""

import sys
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.utils import load_forum, RESULTS_DIR, DATA_DIR
from src.embeddings import compute_actor_centroids

HF_RESULTS = RESULTS_DIR / 'hacking_forums'
HF_DIR = DATA_DIR / 'Hacking Forums'

NEW_FORUMS = [
    "Exploit.in_2013.12.13.zip",
    "Cracked.to_2019.01.zip",
    "Nulled.io_2016.05.zip",
]

# Cargar centroides existentes (OGUsers_2019)
existing = sorted(HF_RESULTS.glob('hf_centroids_sampled_*.npz'))
if not existing:
    print("ERROR: no hay centroides base — corre run_centroids_hf.py primero")
    sys.exit(1)

base_path = existing[-1]
cached = np.load(base_path, allow_pickle=False)
all_user_ids = list(cached['user_ids'])
all_vectors  = [cached['vectors']]
print(f"Centroides base: {base_path.name} ({len(all_user_ids):,} usuarios)\n")

t_global = time.time()

for fname in NEW_FORUMS:
    stem = Path(fname).stem
    if any(stem.lower() in uid.lower() for uid in all_user_ids[:10]):
        print(f"[SKIP] {stem} — ya está en los centroides")
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

    # Top-5000 más activos
    post_counts = posts.groupby('userid').size()
    top_users   = post_counts.nlargest(5000).index
    posts_top   = posts[posts['userid'].isin(top_users)].copy()
    print(f"  Top-5000 usuarios: {len(top_users):,} — {len(posts_top):,} posts")

    # Muestrear top-50 por usuario
    posts_sampled = (
        posts_top
        .sort_values('dateline', ascending=False, na_position='last')
        .groupby('userid')
        .head(50)
        .reset_index(drop=True)
    )
    print(f"  Posts muestreados (top-50/usuario): {len(posts_sampled):,}")

    t1 = time.time()
    user_ids, vectors = compute_actor_centroids(posts_sampled, min_posts=5)
    print(f"  Usuarios: {len(user_ids):,} ({time.time()-t1:.0f}s)")

    all_user_ids.extend(user_ids)
    all_vectors.append(vectors.astype(np.float32))
    print(f"  Acumulado total: {len(all_user_ids):,} usuarios\n")

# Guardar con timestamp nuevo
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = HF_RESULTS / f'hf_centroids_sampled_{ts}.npz'
final_vectors = np.vstack(all_vectors)
np.savez_compressed(
    out_path,
    user_ids=np.array(all_user_ids, dtype='U64'),
    vectors=final_vectors.astype(np.float32),
)
print(f"\nGuardado: {out_path.name}")
print(f"  Shape final: {final_vectors.shape}")
print(f"  Tiempo total: {time.time()-t_global:.0f}s")
