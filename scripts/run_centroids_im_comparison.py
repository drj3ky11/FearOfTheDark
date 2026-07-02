#!/usr/bin/env python3
"""Compara centroides de IronMarch con distintos tamaños de muestra.

Genera centroides con top-100 y top-150 posts más largos por usuario,
y calcula correlación de Spearman contra los centroides completos (parte B).

Outputs (convención del notebook):
  results/ironmarch/s5d_centroids_sampled100_{ts}.npz
  results/ironmarch/s5e_centroids_sampled150_{ts}.npz
  results/ironmarch/s5_sampling_comparison_{ts}.parquet
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics.pairwise import cosine_similarity

from src.utils import load_forum, RESULTS_DIR, DATA_DIR
from src.embeddings import compute_actor_centroids

IM_RESULTS = RESULTS_DIR / "ironmarch"
IM_ZIP = DATA_DIR / "Far Right Forum" / "IronMarch_2019.11.zip"


def load_latest(pattern: str) -> dict | None:
    matches = sorted(IM_RESULTS.glob(pattern))
    if not matches:
        return None
    path = matches[-1]
    print(f"  Cargando: {path.name}")
    return dict(np.load(path, allow_pickle=True))


def save_npz(data: dict, section: str, name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = IM_RESULTS / f"{section}_{name}_{ts}.npz"
    np.savez_compressed(path, **data)
    print(f"  Guardado: {path.name}")
    return path


def pairwise_sims(user_ids: list, vectors: np.ndarray) -> pd.Series:
    sim = cosine_similarity(vectors)
    np.fill_diagonal(sim, 0)
    ii, jj = np.triu_indices(len(user_ids), k=1)
    idx = pd.MultiIndex.from_arrays([
        [str(user_ids[i]) for i in ii],
        [str(user_ids[j]) for j in jj],
    ])
    return pd.Series(sim[ii, jj], index=idx)


def spearman_vs_full(sims_full: pd.Series, sims_x: pd.Series, label: str) -> float:
    common = sims_full.index.intersection(sims_x.index)
    rho, p = spearmanr(sims_full[common], sims_x[common])
    print(f"  full vs {label}: ρ={rho:.4f}  p={p:.2e}  pares={len(common):,}")
    return float(rho)


# ── Cargar centroides completos (B) ──────────────────────────────────────────
print("\n[1] Centroides completos (parte B)...")
cached_b = load_latest("s5b_centroids_full_*.npz")
if cached_b is None:
    print("ERROR: no se encontró s5b_centroids_full_*.npz")
    print("       Ejecutá primero la parte B del notebook.")
    sys.exit(1)
user_ids_b = cached_b["user_ids"].tolist()
vectors_b = cached_b["vectors"]
print(f"  {len(user_ids_b):,} usuarios, dim={vectors_b.shape[1]}")

# ── Cargar posts de IronMarch ─────────────────────────────────────────────────
print("\n[2] Cargando posts IronMarch...")
dfs = load_forum(IM_ZIP)
posts = dfs["post"].copy()
# Filtrar usuarios presentes en centroides completos para comparación justa
posts = posts[posts["userid"].astype(str).isin(user_ids_b)].copy()
print(f"  {len(posts):,} posts, {posts['userid'].nunique():,} usuarios")

# ── Generar centroides muestreados ────────────────────────────────────────────
results = {}

for n_posts, section, name in [(50, "s5c", "centroids_sampled50"),
                                (100, "s5d", "centroids_sampled100"),
                                (150, "s5e", "centroids_sampled150")]:
    pat = f"{section}_*{n_posts if n_posts != 50 else 'sampled'}*.npz"
    # Para 50 ya existe (parte C); para 100 y 150 hay que generar
    existing = load_latest(pat) if n_posts == 50 else None

    if existing is not None:
        user_ids_x = existing["user_ids"].tolist()
        vectors_x = existing["vectors"]
        print(f"\n[cached] top-{n_posts}: {len(user_ids_x):,} usuarios")
    else:
        print(f"\n[3] Generando centroides top-{n_posts} posts más largos...")
        posts["_len"] = posts["pagetext"].fillna("").str.len()
        sampled = (
            posts
            .sort_values("_len", ascending=False)
            .groupby("userid")
            .head(n_posts)
            .drop(columns=["_len"])
            .reset_index(drop=True)
        )
        print(f"  Posts en muestra: {len(sampled):,}")
        user_ids_x, vectors_x = compute_actor_centroids(sampled, min_posts=5)
        save_npz(
            {"user_ids": np.array(user_ids_x, dtype="U64"), "vectors": vectors_x.astype(np.float32)},
            section, name,
        )
        print(f"  {len(user_ids_x):,} usuarios con centroides")

    results[n_posts] = (user_ids_x, vectors_x)

# ── Comparativa Spearman ──────────────────────────────────────────────────────
print("\n[4] Calculando similitudes pairwise para centroides completos...")
sims_b = pairwise_sims(user_ids_b, vectors_b)

print("\nCorrelaciones de Spearman vs centroides completos:")
rows = []
for n_posts, (uid_x, vec_x) in results.items():
    # Restringir B a los usuarios que están en esta muestra
    uid_set = set(str(u) for u in uid_x)
    mask = [str(u) in uid_set for u in user_ids_b]
    uid_b_sub = [u for u, m in zip(user_ids_b, mask) if m]
    vec_b_sub = vectors_b[[i for i, m in enumerate(mask) if m]]

    sims_b_sub = pairwise_sims(uid_b_sub, vec_b_sub)
    sims_x = pairwise_sims(list(uid_x), vec_x)
    rho = spearman_vs_full(sims_b_sub, sims_x, f"top-{n_posts}")
    rows.append({"n_posts": n_posts, "n_users": len(uid_x), "spearman_rho": rho})

comparison = pd.DataFrame(rows)
print("\nResumen:")
print(comparison.to_string(index=False))

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out = IM_RESULTS / f"s5_sampling_comparison_{ts}.parquet"
comparison.to_parquet(out, index=False)
print(f"\nGuardado: {out.name}")
