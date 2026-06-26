"""
Precomputa partes B y C del experimento de embeddings de IronMarch.

Parte B — compute_actor_centroids completo: 1 embedding/post, promedio por usuario
Parte C — compute_actor_centroids muestreado: top 50 posts/usuario (los más largos)

Los archivos se guardan en results/ironmarch/ con la convención del notebook:
  s5b_centroids_full_{YYYYMMDD_HHMMSS}.npz
  s5c_centroids_sampled_{YYYYMMDD_HHMMSS}.npz

load_latest() en el notebook los carga automáticamente.
"""

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.utils import DATA_DIR, RESULTS_DIR, load_forum
from src.embeddings import compute_actor_centroids

IM_RESULTS = RESULTS_DIR / "ironmarch"
IM_RESULTS.mkdir(parents=True, exist_ok=True)

MAX_POSTS_PER_USER = 50


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def save_timestamped(data: dict, section: str, name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = IM_RESULTS / f"{section}_{name}_{ts}.npz"
    np.savez_compressed(path, **data)
    log(f"Guardado: {path.name}")
    return path


def load_posts() -> pd.DataFrame:
    far_right_dir = DATA_DIR / "Far Right Forum"
    candidates = [
        p for p in far_right_dir.glob("*.zip")
        if ("ironmarch" in p.name.lower() or "iron" in p.name.lower())
        and not p.name.startswith("._")
    ]
    if not candidates:
        raise FileNotFoundError(f"IronMarch zip no encontrado en {far_right_dir}")

    path = candidates[0]
    log(f"Dataset: {path.name} ({path.stat().st_size / 1e6:.0f} MB)")

    raw = load_forum(path)
    posts = raw.get("post", pd.DataFrame())

    text_col = "pagetext" if "pagetext" in posts.columns else "message"
    posts_embed = posts[["userid", text_col]].copy()
    posts_embed = posts_embed.dropna(subset=[text_col])
    posts_embed = posts_embed[posts_embed[text_col].astype(str).str.strip().str.len() > 20]
    posts_embed = posts_embed.rename(columns={text_col: "pagetext"})

    if "userid" in posts_embed.columns:
        posts_embed["userid"] = pd.to_numeric(posts_embed["userid"], errors="coerce")
        posts_embed = posts_embed.dropna(subset=["userid"])
        posts_embed["userid"] = posts_embed["userid"].astype(int).astype(str)

    log(f"Posts con texto válido: {len(posts_embed):,} de {posts_embed['userid'].nunique():,} usuarios")
    return posts_embed


def already_computed(pattern: str) -> bool:
    matches = sorted(IM_RESULTS.glob(pattern))
    if matches:
        log(f"SKIP — ya existe: {matches[-1].name}")
        return True
    return False


def run_parte_b(posts_embed: pd.DataFrame) -> None:
    log("--- Parte B: centroids completo ---")
    if already_computed("s5b_centroids_full_*.npz"):
        return
    log(f"Procesando {len(posts_embed):,} posts...")
    user_ids, vectors = compute_actor_centroids(posts_embed, min_posts=5)
    save_timestamped(
        {"user_ids": np.array(user_ids, dtype="U64"), "vectors": vectors},
        "s5b", "centroids_full",
    )
    log(f"Parte B lista: {len(user_ids):,} usuarios, dim={vectors.shape[1]}")


def run_parte_c(posts_embed: pd.DataFrame) -> None:
    log("--- Parte C: centroids muestreado (top 50 posts/usuario) ---")
    if already_computed("s5c_centroids_sampled_*.npz"):
        return
    posts_sampled = (
        posts_embed
        .assign(text_len=posts_embed["pagetext"].str.len())
        .sort_values("text_len", ascending=False)
        .groupby("userid")
        .head(MAX_POSTS_PER_USER)
        .drop(columns="text_len")
        .reset_index(drop=True)
    )
    log(f"Muestra: {len(posts_sampled):,} posts de {posts_sampled['userid'].nunique():,} usuarios")
    user_ids, vectors = compute_actor_centroids(posts_sampled, min_posts=5)
    save_timestamped(
        {"user_ids": np.array(user_ids, dtype="U64"), "vectors": vectors},
        "s5c", "centroids_sampled",
    )
    log(f"Parte C lista: {len(user_ids):,} usuarios, dim={vectors.shape[1]}")


if __name__ == "__main__":
    log("=== IronMarch embeddings — Partes B y C ===")
    posts_embed = load_posts()
    run_parte_b(posts_embed)
    run_parte_c(posts_embed)
    log("=== Completado ===")
