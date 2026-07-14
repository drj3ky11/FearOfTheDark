#!/usr/bin/env python3
"""Unified precompute CLI.

Replaces the 8 hardcoded `scripts/run_*.py` scripts plus
`bloque4_ironmarch/embeddings.py` with one parametrized entrypoint, generic
across any forum dataset.

Subcommands:
  embed    Compute per-user embeddings. --strategy embed_users|centroids.
           Delegates to src.embeddings.embed_users / compute_actor_centroids.
  compare  Sampling-strategy comparison (Spearman correlation of pairwise
           cosine similarity between a cheaper sampling strategy and a
           reference). Self-contained — does not require --strategy.
  ner      Named-entity extraction over sampled posts. Writes the canonical
           `ner_results.parquet` consumed by the analysis notebooks.

Dataset selection (shared by all subcommands):
  --file PATH                 single forum zip, loaded via src.utils.load_forum.
  --dir DIRPATH [--forums F ...]
                               all (or a subset of) the zips found directly
                               under DIRPATH. userid is prefixed
                               "{forum_stem}_{userid}" to avoid collisions
                               once forums are combined.

Examples:
  python scripts/precompute.py embed --strategy embed_users \\
      --dir "data/Hacking Forums" --top-users 1000 --min-posts 5 \\
      --output-name hf_embed_users

  python scripts/precompute.py embed --strategy centroids --file \\
      "data/Far Right Forum/IronMarch_2019.11.zip" --top-n 50 \\
      --output-name s5c_centroids_sampled50

  python scripts/precompute.py compare --dir "data/Hacking Forums" \\
      --reference centroids --top-users-c 5000 --sample-sizes 100,150

  python scripts/precompute.py ner --file \\
      "data/Far Right Forum/IronMarch_2019.11.zip" --sample-size 500

Use --dry-run on any subcommand to exercise dataset resolution, filtering,
and output-path construction without calling Ollama/GPU.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.utils import RESULTS_DIR

DEFAULT_EMBED_MODEL = "qwen3-embedding"
DEFAULT_NER_MODEL = "qwen2.5:14b"
DEFAULT_BATCH_SIZE = 32
DEFAULT_MAX_CHARS = 50_000


# ── Naming helpers ───────────────────────────────────────────────────────────

def _slug(text: str) -> str:
    """Lowercase, non-alphanumeric runs collapsed to a single underscore."""
    return re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")


def _dataset_slug(dir_path: str | None, file_path: str | None) -> str:
    """Slug used for the default output directory: results/<slug>/."""
    if dir_path:
        return _slug(Path(dir_path).name)
    return _slug(Path(file_path).stem)


def _prefix_of(dir_path: str | None, file_path: str | None) -> str:
    """Short prefix used in default output filenames.

    Multi-word directory names collapse to initials ("Hacking Forums" -> "hf"),
    matching the existing hf_*/s5*_* filename families the notebooks already
    glob-read. Single-word directory names and --file mode use their own slug.
    """
    if dir_path:
        words = Path(dir_path).name.split()
        if len(words) > 1:
            return "".join(w[0] for w in words if w).lower()
        return _slug(Path(dir_path).name)
    return _slug(Path(file_path).stem)


# ── Dataset resolution ───────────────────────────────────────────────────────

def _extract_posts(dfs: dict) -> pd.DataFrame:
    """Normalize a parsed forum dict into a userid/pagetext DataFrame."""
    posts = dfs.get("post", pd.DataFrame())
    if posts.empty:
        return pd.DataFrame(columns=["userid", "pagetext"])

    text_col = next((c for c in ("pagetext", "message", "post_content") if c in posts.columns), None)
    if text_col is None:
        return pd.DataFrame(columns=["userid", "pagetext"])

    df = posts[["userid", text_col]].dropna().copy()
    df = df.rename(columns={text_col: "pagetext"})
    df["pagetext"] = df["pagetext"].astype(str).str.strip()
    df = df[df["pagetext"].str.len() > 0]
    df["userid"] = df["userid"].astype(str)
    return df.reset_index(drop=True)


def resolve_forums(args) -> list[tuple[str, pd.DataFrame]]:
    """
    Resolve --file or --dir(+--forums) into [(stem, posts_df), ...].

    --file: a single forum, userid left as-is (no prefixing).
    --dir: one entry per matching forum zip found directly under DIRPATH
    (all of them, or the subset named by --forums), userid prefixed
    "{stem}_{userid}" so ids don't collide once forums are combined
    downstream. This is the one place the file-vs-dir branching happens —
    no subcommand duplicates it.
    """
    from src.utils import load_forum

    if args.file:
        zip_path = Path(args.file)
        stem = zip_path.stem
        dfs = load_forum(zip_path)
        return [(stem, _extract_posts(dfs))]

    dir_path = Path(args.dir)
    paths = sorted(p for p in dir_path.glob("*.zip") if not p.name.startswith("._"))
    if args.forums:
        wanted = set(args.forums)
        paths = [p for p in paths if p.stem in wanted]

    results: list[tuple[str, pd.DataFrame]] = []
    for path in paths:
        stem = path.stem
        try:
            dfs = load_forum(path)
        except Exception as e:
            print(f"  [SKIP] {stem}: {e}")
            continue
        posts = _extract_posts(dfs)
        if not posts.empty:
            posts["userid"] = stem + "_" + posts["userid"]
        results.append((stem, posts))

    return results


# ── Filtering helpers ────────────────────────────────────────────────────────

def _filter_min_posts(posts: pd.DataFrame, min_posts: int) -> pd.DataFrame:
    if posts.empty:
        return posts
    counts = posts.groupby("userid").size()
    valid = counts[counts >= min_posts].index
    return posts[posts["userid"].isin(valid)].reset_index(drop=True)


def _apply_top_users(posts: pd.DataFrame, top_users: int | None) -> pd.DataFrame:
    """Keep only the `top_users` most prolific users (by post count)."""
    if posts.empty or top_users is None:
        return posts
    counts = posts.groupby("userid").size()
    top_uids = counts.nlargest(top_users).index
    return posts[posts["userid"].isin(top_uids)].reset_index(drop=True)


def _apply_top_n_longest(posts: pd.DataFrame, top_n: int | None) -> pd.DataFrame:
    """Keep only the `top_n` longest posts per user (centroids sampling)."""
    if posts.empty or top_n is None:
        return posts
    df = posts.assign(_len=posts["pagetext"].str.len())
    sampled = (
        df.sort_values("_len", ascending=False)
        .groupby("userid")
        .head(top_n)
        .drop(columns="_len")
        .reset_index(drop=True)
    )
    return sampled


# ── Output / save helpers ────────────────────────────────────────────────────

def resolve_output_path(args, default_name: str, ext: str) -> Path:
    """
    <output-dir>/<output-name>[_{ts}].<ext>

    output-dir defaults to results/<slug(dir-name|file-stem)>.
    output-name defaults to `default_name` (per-strategy, computed by caller).
    """
    output_dir = Path(args.output_dir) if args.output_dir else RESULTS_DIR / _dataset_slug(args.dir, args.file)
    name = args.output_name or default_name
    if name.endswith(ext):
        name = name[: -len(ext)]
    if args.timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{name}_{ts}"
    return output_dir / f"{name}{ext}"


def _find_extend_target(args, default_name: str, ext: str) -> Path | None:
    """Locate the existing output file to append to for --extend."""
    output_dir = Path(args.output_dir) if args.output_dir else RESULTS_DIR / _dataset_slug(args.dir, args.file)
    name = args.output_name or default_name
    if name.endswith(ext):
        name = name[: -len(ext)]
    if not args.timestamp:
        candidate = output_dir / f"{name}{ext}"
        return candidate if candidate.exists() else None
    matches = sorted(output_dir.glob(f"{name}_*{ext}"))
    return matches[-1] if matches else None


def save_npz(data: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **data)
    print(f"  Saved: {path}")
    return path


def save_parquet(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"  Saved: {path}")
    return path


# ── embed ─────────────────────────────────────────────────────────────────

def cmd_embed(args):
    if args.top_n is not None and args.strategy == "embed_users":
        raise SystemExit("--top-n is only valid with --strategy centroids (embed_users has no top-n sampling).")

    print(f"Resolving dataset ({'--file ' + args.file if args.file else '--dir ' + args.dir})...")
    forums = resolve_forums(args)

    parts = []
    for stem, posts in forums:
        posts = _filter_min_posts(posts, args.min_posts)
        posts = _apply_top_users(posts, args.top_users)
        print(f"  {stem}: {posts['userid'].nunique():,} users after filtering")
        parts.append(posts)

    combined = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["userid", "pagetext"])

    strategy_default = "embed_users" if args.strategy == "embed_users" else "centroids_sampled"
    default_name = f"{_prefix_of(args.dir, args.file)}_{strategy_default}"
    out_path = resolve_output_path(args, default_name, ".npz")

    if args.dry_run:
        print(
            f"[dry-run] strategy={args.strategy} total_users={combined['userid'].nunique():,} "
            f"total_rows={len(combined):,} -> would write {out_path}"
        )
        return

    existing_user_ids: list = []
    existing_vectors: list = []
    if args.extend:
        target = _find_extend_target(args, default_name, ".npz")
        if target is not None:
            cached = np.load(target, allow_pickle=False)
            existing_user_ids = list(cached["user_ids"])
            existing_vectors = [cached["vectors"]]
            done_stems = {str(uid).split("_")[0] for uid in existing_user_ids}
            print(f"  --extend: loaded {len(existing_user_ids):,} users from {target.name}; forums done: {sorted(done_stems)}")
            combined = combined[~combined["userid"].apply(lambda u: u.split("_")[0]).isin(done_stems)].reset_index(drop=True)

    if args.strategy == "embed_users":
        from src.embeddings import embed_users
        user_ids, vectors = embed_users(combined, model=args.model, min_posts=args.min_posts, max_chars=args.max_chars)
    else:
        if args.top_n is not None:
            combined = _apply_top_n_longest(combined, args.top_n)
        from src.embeddings import compute_actor_centroids
        user_ids, vectors = compute_actor_centroids(combined, model=args.model, min_posts=args.min_posts, batch_size=args.batch_size)

    vectors = np.asarray(vectors, dtype=np.float32)
    if args.extend and existing_user_ids:
        user_ids = list(existing_user_ids) + list(user_ids)
        vectors = np.vstack(existing_vectors + [vectors]) if len(vectors) else np.vstack(existing_vectors)

    save_npz({"user_ids": np.array(user_ids, dtype="U128"), "vectors": vectors}, out_path)


# ── compare ───────────────────────────────────────────────────────────────

def cmd_compare(args):
    print(f"Resolving dataset ({'--file ' + args.file if args.file else '--dir ' + args.dir})...")
    forums = resolve_forums(args)
    sample_sizes = [int(x) for x in args.sample_sizes.split(",") if x.strip()]
    prefix = _prefix_of(args.dir, args.file)

    ref_suffix = "centroids_sampled" if args.reference == "centroids" else "centroids_full"
    ref_default_name = f"{prefix}_{ref_suffix}"
    ref_path = resolve_output_path(args, ref_default_name, ".npz")

    filtered = {}
    for stem, posts in forums:
        posts = _filter_min_posts(posts, args.min_posts)
        filtered[stem] = posts
        print(f"  {stem}: {posts['userid'].nunique():,} users after filtering")

    if args.dry_run:
        print(
            f"[dry-run] reference={args.reference} sample_sizes={sample_sizes} "
            f"top_sample={args.top_sample} -> reference would write {ref_path}"
        )
        return

    from src.embeddings import compute_actor_centroids, embed_users

    ref_user_ids: list = []
    ref_vectors_parts: list = []
    sample_posts: dict[str, pd.DataFrame] = {}

    for stem, posts in filtered.items():
        if posts.empty:
            continue

        # --reference centroids: capped to --top-users-c most prolific users
        #   (mirrors the HF-style comparison — full-corpus centroids are
        #   infeasible at that scale, C serves as the reference instead).
        # --reference full: all qualifying users/posts (viable at smaller
        #   scale, e.g. IronMarch — mirrors the B/D/E comparison).
        ref_posts = _apply_top_users(posts, args.top_users_c) if args.reference == "centroids" else posts
        ids, vecs = compute_actor_centroids(ref_posts, model=args.model, min_posts=args.min_posts, batch_size=args.batch_size)
        ref_user_ids.extend(ids)
        ref_vectors_parts.append(vecs)

        sample_uids = _apply_top_users(posts, args.top_sample)["userid"].unique().tolist()
        sample_posts[stem] = posts[posts["userid"].isin(sample_uids)].reset_index(drop=True)

    ref_vectors = np.vstack(ref_vectors_parts).astype(np.float32) if ref_vectors_parts else np.empty((0, 0), dtype=np.float32)
    save_npz({"user_ids": np.array(ref_user_ids, dtype="U128"), "vectors": ref_vectors}, ref_path)

    results: dict[str, tuple[list, np.ndarray]] = {}

    for n in sample_sizes:
        s_ids, s_vecs_parts = [], []
        for stem, df_s in sample_posts.items():
            sampled = _apply_top_n_longest(df_s, n)
            ids, vecs = compute_actor_centroids(sampled, model=args.model, min_posts=args.min_posts, batch_size=args.batch_size)
            s_ids.extend(ids)
            s_vecs_parts.append(vecs)
        s_vecs = np.vstack(s_vecs_parts).astype(np.float32) if s_vecs_parts else np.empty((0, 0), dtype=np.float32)
        label = f"sample{n}"
        results[label] = (s_ids, s_vecs)
        save_npz({"user_ids": np.array(s_ids, dtype="U128"), "vectors": s_vecs},
                  resolve_output_path(args, f"{prefix}_sample_centroids_{label}", ".npz"))

    if args.reference == "centroids":
        # A: embed_users over the same sample, for the 3-way sampling
        # comparison (A vs D vs E). Not applicable to --reference full,
        # where the original B/D/E comparison never included it.
        a_ids, a_vecs_parts = [], []
        for stem, df_s in sample_posts.items():
            ids, vecs = embed_users(df_s, model=args.model, min_posts=args.min_posts)
            a_ids.extend(ids)
            a_vecs_parts.append(vecs)
        a_vecs = np.vstack(a_vecs_parts).astype(np.float32) if a_vecs_parts else np.empty((0, 0), dtype=np.float32)
        results["embed_users"] = (a_ids, a_vecs)
        save_npz({"user_ids": np.array(a_ids, dtype="U128"), "vectors": a_vecs},
                  resolve_output_path(args, f"{prefix}_sample_embed_users", ".npz"))

    _spearman_report(ref_user_ids, ref_vectors, results, resolve_output_path(args, f"{prefix}_sampling_comparison", ".parquet"))


def _pairwise_sims(user_ids: list, vectors: np.ndarray) -> pd.Series:
    from sklearn.metrics.pairwise import cosine_similarity

    if len(user_ids) < 2:
        return pd.Series(dtype=float)
    sim = cosine_similarity(vectors)
    np.fill_diagonal(sim, 0)
    ii, jj = np.triu_indices(len(user_ids), k=1)
    idx = pd.MultiIndex.from_arrays([[str(user_ids[i]) for i in ii], [str(user_ids[j]) for j in jj]])
    return pd.Series(sim[ii, jj], index=idx)


def _spearman_report(ref_user_ids, ref_vectors, results: dict, out_path: Path):
    from scipy.stats import spearmanr

    ref_map = {uid: v for uid, v in zip(ref_user_ids, ref_vectors)}
    rows = []
    for label, (ids, vecs) in results.items():
        shared = [u for u in ids if u in ref_map]
        if len(shared) < 10:
            print(f"  {label}: not enough shared users for comparison")
            continue
        ref_shared = np.array([ref_map[u] for u in shared], dtype=np.float32)
        cmp_map = {uid: v for uid, v in zip(ids, vecs)}
        cmp_shared = np.array([cmp_map[u] for u in shared], dtype=np.float32)

        sims_ref = _pairwise_sims(shared, ref_shared)
        sims_cmp = _pairwise_sims(shared, cmp_shared)
        common = sims_ref.index.intersection(sims_cmp.index)
        rho, _p = spearmanr(sims_ref[common], sims_cmp[common])
        rows.append({"strategy": label, "n_users": len(shared), "spearman_rho": round(float(rho), 4)})
        print(f"  {label}: rho={rho:.4f} (n_users={len(shared):,})")

    comparison = pd.DataFrame(rows)
    save_parquet(comparison, out_path)


# ── ner ───────────────────────────────────────────────────────────────────

NER_SYSTEM = (
    "You are a threat intelligence analyst. Extract named entities from forum posts.\n"
    'Reply ONLY with valid JSON object: {"entities": [{"entity": "...", "type": "..."}]}\n'
    "Allowed types: PERSON, ORGANIZATION, LOCATION, EVENT, IDEOLOGY\n"
    'If no entities found, reply: {"entities": []}'
)


def _extract_entities(text: str, model: str) -> list[dict]:
    import json
    import ollama

    try:
        response = ollama.generate(
            model=model,
            system=NER_SYSTEM,
            prompt=str(text)[:1500],
            format="json",
            options={"temperature": 0},
        )
        result = json.loads(response["response"])
        entities = result.get("entities", result) if isinstance(result, dict) else result
        return entities if isinstance(entities, list) else []
    except Exception:
        return []


def cmd_ner(args):
    print(f"Resolving dataset ({'--file ' + args.file if args.file else '--dir ' + args.dir})...")
    forums = resolve_forums(args)
    combined = pd.concat([posts for _, posts in forums], ignore_index=True) if forums else pd.DataFrame(columns=["userid", "pagetext"])
    combined = combined[combined["pagetext"].str.len() > 100].reset_index(drop=True)

    n = min(args.sample_size, len(combined))
    sample_random = combined.sample(n, random_state=42) if n else combined

    sample_stratified = sample_random
    if "forumid" in combined.columns and len(combined):
        forum_sizes = combined["forumid"].value_counts(normalize=True)
        parts = []
        for fid, prop in forum_sizes.items():
            k = max(1, int(args.sample_size * prop))
            sub = combined[combined["forumid"] == fid]
            parts.append(sub.sample(min(k, len(sub)), random_state=42))
        if parts:
            sample_stratified = pd.concat(parts).head(args.sample_size)

    top_uids = combined.groupby("userid").size().nlargest(25).index if len(combined) else []
    sample_top_users = (
        combined[combined["userid"].isin(top_uids)].groupby("userid").head(20).reset_index(drop=True)
        if len(top_uids) else combined.iloc[0:0]
    )

    out_path = resolve_output_path(args, "ner_results", ".parquet")

    if args.dry_run:
        print(
            f"[dry-run] samples: random={len(sample_random)}, stratified={len(sample_stratified)}, "
            f"top_users={len(sample_top_users)} -> would write {out_path}"
        )
        return

    def run_on_sample(sample_df: pd.DataFrame, label: str) -> pd.DataFrame:
        records = []
        for _, row in sample_df.iterrows():
            for ent in _extract_entities(row["pagetext"], args.model):
                records.append({
                    "sample": label,
                    "entity": str(ent.get("entity", "")).strip(),
                    "type": ent.get("type", "UNKNOWN"),
                    "userid": row.get("userid", ""),
                })
        return pd.DataFrame(records, columns=["sample", "entity", "type", "userid"])

    parts = [
        run_on_sample(sample_random, "random"),
        run_on_sample(sample_stratified, "stratified"),
        run_on_sample(sample_top_users, "top_users"),
    ]
    ner_all = pd.concat(parts, ignore_index=True)
    if len(ner_all):
        ner_all = ner_all[ner_all["entity"].str.len() > 1]

    save_parquet(ner_all, out_path)


# ── CLI wiring ────────────────────────────────────────────────────────────

def add_common_arguments(parser: argparse.ArgumentParser, default_model: str, default_batch_size: int = DEFAULT_BATCH_SIZE):
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--dir", help="Directory containing forum zips (e.g. 'data/Hacking Forums').")
    source.add_argument("--file", help="Path to a single forum zip.")
    parser.add_argument("--forums", nargs="+", default=None, help="Subset of forum stems within --dir (default: all).")
    parser.add_argument("--min-posts", type=int, default=5)
    parser.add_argument("--model", default=default_model)
    parser.add_argument("--batch-size", type=int, default=default_batch_size)
    parser.add_argument("--output-dir", default=None, help="Default: results/<slug(dir-name|file-stem)>")
    parser.add_argument("--output-name", default=None, help="Default: per-strategy name preserving current glob patterns.")
    parser.add_argument("--timestamp", dest="timestamp", action="store_true", default=True)
    parser.add_argument("--no-timestamp", dest="timestamp", action="store_false")
    parser.add_argument("--dry-run", action="store_true", help="Exercise dataset resolution/output naming; no Ollama/GPU calls.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="precompute.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_embed = sub.add_parser("embed", help="Compute per-user embeddings (embed_users or centroids).")
    add_common_arguments(p_embed, default_model=DEFAULT_EMBED_MODEL)
    p_embed.add_argument("--strategy", choices=["embed_users", "centroids"], required=True)
    p_embed.add_argument("--top-users", type=int, default=None, help="Cap to N most prolific users/forum (default: all qualifying users).")
    p_embed.add_argument("--top-n", type=int, default=None, help="centroids only: cap to N longest posts/user.")
    p_embed.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="embed_users only: truncate concatenated text/user.")
    p_embed.add_argument("--extend", action="store_true", help="Append new forums to an existing output file, skipping forums already present.")
    p_embed.set_defaults(func=cmd_embed)

    p_compare = sub.add_parser("compare", help="Sampling-strategy comparison (Spearman rho vs a reference).")
    add_common_arguments(p_compare, default_model=DEFAULT_EMBED_MODEL)
    p_compare.add_argument("--reference", choices=["centroids", "full"], required=True)
    p_compare.add_argument("--top-users-c", type=int, default=5000)
    p_compare.add_argument("--top-sample", type=int, default=300)
    p_compare.add_argument("--sample-sizes", default="100,150", help="Comma-separated top-N-longest-posts sample sizes to compare.")
    p_compare.set_defaults(func=cmd_compare)

    p_ner = sub.add_parser("ner", help="Named-entity extraction over sampled posts. Writes ner_results.parquet.")
    add_common_arguments(p_ner, default_model=DEFAULT_NER_MODEL)
    p_ner.add_argument("--sample-size", type=int, default=500)
    p_ner.set_defaults(func=cmd_ner)

    return parser


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.forums and not args.dir:
        parser.error("--forums is only valid together with --dir")

    args.func(args)


if __name__ == "__main__":
    main()
