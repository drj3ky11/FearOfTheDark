#!/usr/bin/env python3
"""Comparativa de estrategias A/C/D/E para HackingForums.

La estrategia B (centroids full, todos los posts) es inviable a escala de HF
(~25K usuarios × cientos de posts = semanas de GPU). Se usa C (top-50) como
referencia en lugar de B.

Flujo:
  1. Añade RaidForums a centroides C si no está presente
  2. Para una muestra de TOP_SAMPLE usuarios por foro:
     - Genera D (top-100) y E (top-150)
     - Genera A (embed_users, truncado a MAX_CHARS)
  3. Calcula Spearman: A vs C, D vs C, E vs C

Outputs:
  results/hacking_forums/hf_centroids_sampled_{ts}.npz    ← C completo (con RaidForums)
  results/hacking_forums/hf_sample_centroids_D_{ts}.npz   ← D sobre muestra
  results/hacking_forums/hf_sample_centroids_E_{ts}.npz   ← E sobre muestra
  results/hacking_forums/hf_sample_embed_users_{ts}.npz   ← A sobre muestra
  results/hacking_forums/hf_sampling_comparison_{ts}.parquet
"""

import sys, time, random
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import ollama
from tqdm import tqdm
from scipy.stats import spearmanr
from sklearn.metrics.pairwise import cosine_similarity

from src.utils import load_forum, RESULTS_DIR, DATA_DIR
from src.embeddings import compute_actor_centroids

HF_RESULTS = RESULTS_DIR / "hacking_forums"
HF_RESULTS.mkdir(parents=True, exist_ok=True)
HF_DIR = DATA_DIR / "Hacking Forums"

DEFAULT_MODEL = "qwen3-embedding"
BATCH_SIZE    = 32
MAX_CHARS     = 50_000   # truncate per-user text for embed_users
MIN_POSTS     = 5
TOP_USERS_C   = 5_000    # users per forum for C centroids (main analysis)
TOP_SAMPLE    = 300      # users per forum for D/E/A comparison (~55h total in weekend run)

FORUMS = [
    "OGUsers_2019.zip",
    "Exploit.in_2013.12.13.zip",
    "Cracked.to_2019.01.zip",
    "Nulled.io_2016.05.zip",
    "RaidForums_2021.zip",
]

random.seed(42)
np.random.seed(42)


def embed_texts(texts: list[str]) -> np.ndarray:
    results = []
    batches = [texts[i:i + BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
    for batch in tqdm(batches, desc=f"Embedding [{DEFAULT_MODEL}]"):
        resp = ollama.embed(model=DEFAULT_MODEL, input=batch)
        results.extend(resp.embeddings)
    return np.array(results, dtype=np.float32)


def pairwise_sims(user_ids, vectors):
    sim = cosine_similarity(vectors)
    np.fill_diagonal(sim, 0)
    ii, jj = np.triu_indices(len(user_ids), k=1)
    return pd.Series(sim[ii, jj], index=pd.MultiIndex.from_arrays(
        [[str(user_ids[i]) for i in ii], [str(user_ids[j]) for j in jj]]
    ))


def save_npz(data: dict, name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = HF_RESULTS / f"{name}_{ts}.npz"
    np.savez_compressed(out, **data)
    print(f"  Guardado: {out.name}")
    return out


# ── Step 1: Load or extend C centroids ───────────────────────────────────────
print("=" * 60)
print("PASO 1 — Centroides C (top-50) completos")

existing_c = sorted(HF_RESULTS.glob("hf_centroids_sampled_*.npz"))
base_c = np.load(existing_c[-1], allow_pickle=True) if existing_c else None

current_forums = set()
c_user_ids = []
c_vectors   = []

if base_c is not None:
    c_user_ids = base_c["user_ids"].tolist()
    c_vectors  = list(base_c["vectors"])
    current_forums = set(uid.split("_")[0] for uid in c_user_ids)
    print(f"  Base C: {len(c_user_ids):,} usuarios, foros: {sorted(current_forums)}")

sample_uids_all = []  # for D/E/A comparison
sample_posts    = {}  # stem → DataFrame for computing D/E centroids
sample_texts    = {}  # stem → {uid: text} for embed_users

for fname in FORUMS:
    zip_path = HF_DIR / fname
    stem = Path(fname).stem
    if not zip_path.exists():
        print(f"  [SKIP] {stem}: archivo no encontrado")
        continue

    t0 = time.time()
    print(f"\n  [{stem}]")
    try:
        dfs = load_forum(zip_path)
    except Exception as e:
        print(f"    ERROR: {e}")
        continue

    post_df = dfs.get("post", pd.DataFrame())
    if post_df.empty:
        print(f"    Sin posts")
        continue

    text_col = next((c for c in ("pagetext", "message", "post_content") if c in post_df.columns), None)
    if text_col is None:
        print(f"    Sin columna de texto")
        continue

    df = post_df[["userid", text_col]].dropna().copy()
    df[text_col] = df[text_col].astype(str).str.strip()
    df = df[df[text_col].str.len() > 0]
    df = df.rename(columns={text_col: "pagetext"})

    post_counts = df.groupby("userid").size()
    top_uids_c  = post_counts[post_counts >= MIN_POSTS].nlargest(TOP_USERS_C).index

    # ── C centroids (full forum, only if missing) ─────────────────────────────
    if stem not in current_forums:
        print(f"    Computando centroides C para {len(top_uids_c):,} usuarios...")
        df_c = df[df["userid"].isin(top_uids_c)].copy()
        ids, vecs = compute_actor_centroids(df_c, min_posts=MIN_POSTS)
        prefixed = [f"{stem}_{uid}" for uid in ids]
        c_user_ids.extend(prefixed)
        c_vectors.extend(vecs)
        current_forums.add(stem)
        print(f"    C: +{len(ids):,} usuarios ({(time.time()-t0)/60:.1f} min)")

    # ── Sample for D/E/A comparison ───────────────────────────────────────────
    # Sample strategy: TOP_SAMPLE users with MOST POSTS (not random).
    # Rationale: prolific users drive the stylometric signal; they are also
    # the actors we actually want to profile. Using random users would sample
    # mostly low-volume accounts with <10 posts — noisy and uninteresting.
    top_uids_sample = post_counts[post_counts >= MIN_POSTS].nlargest(TOP_SAMPLE).index
    df_sample = df[df["userid"].isin(top_uids_sample)].copy()
    sample_posts[stem] = df_sample
    grouped = df_sample.groupby("userid")["pagetext"].apply(lambda x: " ".join(x.tolist()))
    sample_texts[stem] = {uid: text[:MAX_CHARS] for uid, text in grouped.items()}
    sample_uids_all.extend([f"{stem}_{uid}" for uid in grouped.index])
    print(f"    Muestra D/E/A: {len(top_uids_sample):,} usuarios")

# Save updated C
c_vectors_arr = np.array(c_vectors, dtype=np.float32)
save_npz({"user_ids": np.array(c_user_ids, dtype="U128"), "vectors": c_vectors_arr},
         "hf_centroids_sampled")
print(f"\n  C completo: {len(c_user_ids):,} usuarios")

# ── Step 2: D centroids (top-100) on sample ───────────────────────────────────
print("\n" + "=" * 60)
print(f"PASO 2 — Centroides D (top-100), {len(sample_uids_all):,} usuarios")

d_user_ids, d_vectors = [], []
for stem, df_s in sample_posts.items():
    print(f"  [{stem}]")
    df_d = (
        df_s.assign(_len=df_s["pagetext"].str.len())
        .sort_values("_len", ascending=False)
        .groupby("userid").head(100)
        .drop(columns="_len")
        .reset_index(drop=True)
    )
    ids, vecs = compute_actor_centroids(df_d, min_posts=MIN_POSTS)
    d_user_ids.extend([f"{stem}_{uid}" for uid in ids])
    d_vectors.extend(vecs)

d_vectors_arr = np.array(d_vectors, dtype=np.float32)
save_npz({"user_ids": np.array(d_user_ids, dtype="U128"), "vectors": d_vectors_arr},
         "hf_sample_centroids_D")

# ── Step 3: E centroids (top-150) on sample ───────────────────────────────────
print("\n" + "=" * 60)
print(f"PASO 3 — Centroides E (top-150), {len(sample_uids_all):,} usuarios")

e_user_ids, e_vectors = [], []
for stem, df_s in sample_posts.items():
    print(f"  [{stem}]")
    df_e = (
        df_s.assign(_len=df_s["pagetext"].str.len())
        .sort_values("_len", ascending=False)
        .groupby("userid").head(150)
        .drop(columns="_len")
        .reset_index(drop=True)
    )
    ids, vecs = compute_actor_centroids(df_e, min_posts=MIN_POSTS)
    e_user_ids.extend([f"{stem}_{uid}" for uid in ids])
    e_vectors.extend(vecs)

e_vectors_arr = np.array(e_vectors, dtype=np.float32)
save_npz({"user_ids": np.array(e_user_ids, dtype="U128"), "vectors": e_vectors_arr},
         "hf_sample_centroids_E")

# ── Step 4: A (embed_users) on sample ─────────────────────────────────────────
print("\n" + "=" * 60)
print(f"PASO 4 — embed_users A, {len(sample_uids_all):,} usuarios")

a_user_ids, a_texts = [], []
for stem, texts_dict in sample_texts.items():
    for uid, text in texts_dict.items():
        a_user_ids.append(f"{stem}_{uid}")
        a_texts.append(text)

print(f"  Texto más largo: {max(len(t) for t in a_texts):,} chars")
a_vectors_arr = embed_texts(a_texts)
save_npz({"user_ids": np.array(a_user_ids, dtype="U128"), "vectors": a_vectors_arr},
         "hf_sample_embed_users")

# ── Step 5: Spearman comparison ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PASO 5 — Spearman vs C (referencia)")

def get_shared_vecs(ref_ids, ref_vecs, cmp_ids, cmp_vecs):
    ref_map = {uid: v for uid, v in zip(ref_ids, ref_vecs)}
    cmp_map = {uid: v for uid, v in zip(cmp_ids, cmp_vecs)}
    shared = sorted(set(ref_map) & set(cmp_map))
    r = np.array([ref_map[u] for u in shared], dtype=np.float32)
    c = np.array([cmp_map[u] for u in shared], dtype=np.float32)
    return shared, r, c

# Use sample subset of C as reference
c_map = {uid: v for uid, v in zip(c_user_ids, c_vectors_arr)}
sample_c_ids = [uid for uid in sample_uids_all if uid in c_map]
sample_c_vecs = np.array([c_map[uid] for uid in sample_c_ids], dtype=np.float32)
ref_sims = pairwise_sims(sample_c_ids, sample_c_vecs)

rows = []
for label, ids, vecs in [
    ("A: embed_users",    a_user_ids, a_vectors_arr),
    ("D: sampled_top100", d_user_ids, d_vectors_arr),
    ("E: sampled_top150", e_user_ids, e_vectors_arr),
]:
    shared, r_vecs, c_vecs = get_shared_vecs(sample_c_ids, sample_c_vecs, ids, vecs)
    if len(shared) < 10:
        print(f"  {label}: sin suficientes usuarios en común")
        continue
    sims_r = pairwise_sims(shared, r_vecs)
    sims_c = pairwise_sims(shared, c_vecs)
    common = sims_r.index.intersection(sims_c.index)
    rho, p = spearmanr(sims_r[common], sims_c[common])
    rows.append({"strategy": label, "n_users": len(shared), "spearman_rho": round(rho, 4)})
    print(f"  {label}: ρ={rho:.4f}  (n_users={len(shared):,}, pares={len(common):,})")

comparison = pd.DataFrame(rows)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out = HF_RESULTS / f"hf_sampling_comparison_{ts}.parquet"
comparison.to_parquet(out, index=False)
print(f"\nGuardado: {out.name}")
print(comparison.to_string(index=False))
print("\nDone.")
