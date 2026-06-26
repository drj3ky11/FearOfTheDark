"""
precompute.py — Genera archivos precomputados en results/ antes de la demo en vivo.

Uso:
    uv run python scripts/precompute.py [--case all|demo|hacking|ironmarch]

Cada caso embebe un conjunto de usuarios y guarda el resultado en results/ como .npz.
Si el archivo ya existe, lo saltea para no regenerar innecesariamente.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Agregar la raíz del proyecto al path para importar src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.utils import DATA_DIR, RESULTS_DIR, load_all_forums, merge_tables, load_or_compute
from src.embeddings import compute_actor_centroids


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def skip_if_exists(path: Path) -> bool:
    if path.exists():
        log(f"SKIP — ya existe: {path.name}")
        return True
    return False


# Mensajes por actor que se samplea antes de embeber (estrategia del colega).
# Suficiente para un perfil estilométrico fiable, manejable en tiempo de cómputo.
MSGS_PER_ACTOR = 80


# ---------------------------------------------------------------------------
# Helpers de carga y muestreo
# ---------------------------------------------------------------------------

def _sample_actor(actor_posts: pd.DataFrame, n: int) -> pd.DataFrame:
    """Muestra uniforme en el tiempo de hasta n posts de un actor."""
    actor_posts = actor_posts.sort_values("dateline").reset_index(drop=True)
    if len(actor_posts) <= n:
        return actor_posts
    indices = [int(i * len(actor_posts) / n) for i in range(n)]
    return actor_posts.iloc[indices]


def _load_and_sample(category: str, label: str, sample_n_actors: int | None = None) -> pd.DataFrame:
    """
    Carga todos los posts de una categoría, filtra los top N actores (si aplica)
    y samplea MSGS_PER_ACTOR mensajes por actor distribuidos en el tiempo.
    """
    log(f"Cargando {label}...")
    forums = load_all_forums(category, verbose=False)
    posts = merge_tables(forums, "post")

    if posts.empty:
        raise ValueError(f"No se encontraron posts en {label}")

    log(f"  {len(posts):,} posts de {posts['userid'].nunique():,} usuarios")

    # Opcional: limitar a los N usuarios con más posts
    if sample_n_actors is not None:
        top_users = (
            posts.groupby("userid").size()
            .sort_values(ascending=False)
            .head(sample_n_actors)
            .index
        )
        posts = posts[posts["userid"].isin(top_users)].copy()

    # Samplear MSGS_PER_ACTOR por actor, distribuidos en el tiempo
    sampled = pd.concat(
        [_sample_actor(g, MSGS_PER_ACTOR) for _, g in posts.groupby("userid")],
        ignore_index=True,
    )
    log(f"  Sample: {len(sampled):,} posts de {sampled['userid'].nunique():,} actores ({MSGS_PER_ACTOR} msgs/actor)")
    return sampled


# ---------------------------------------------------------------------------
# Funciones de cómputo por caso
# ---------------------------------------------------------------------------

def compute_demo_embeddings() -> dict:
    """Centroides por actor para la demo — top 1000 usuarios de Carding Forums."""
    posts = _load_and_sample("Carding Forums", "Carding Forums", sample_n_actors=1000)
    log("  Generando embeddings por mensaje y centroides por actor...")
    user_ids, vectors = compute_actor_centroids(posts, min_posts=3)
    log(f"  Centroides: {len(user_ids):,} actores, dim={vectors.shape[1]}")
    return {"user_ids": np.array(user_ids, dtype="U64"), "vectors": vectors}


def compute_hacking_embeddings() -> dict:
    """Centroides por actor para Hacking Forums — top 2000 usuarios."""
    posts = _load_and_sample("Hacking Forums", "Hacking Forums", sample_n_actors=2000)
    log("  Generando embeddings por mensaje y centroides por actor...")
    user_ids, vectors = compute_actor_centroids(posts, min_posts=3)
    log(f"  Centroides: {len(user_ids):,} actores, dim={vectors.shape[1]}")
    return {"user_ids": np.array(user_ids, dtype="U64"), "vectors": vectors}


def compute_ironmarch_embeddings() -> dict:
    """Centroides por actor para IronMarch — todos los usuarios."""
    posts = _load_and_sample("Far Right Forum", "IronMarch")
    log("  Generando embeddings por mensaje y centroides por actor...")
    user_ids, vectors = compute_actor_centroids(posts, min_posts=3)
    log(f"  Centroides: {len(user_ids):,} actores, dim={vectors.shape[1]}")
    return {"user_ids": np.array(user_ids, dtype="U64"), "vectors": vectors}


# ---------------------------------------------------------------------------
# Definición de casos
# ---------------------------------------------------------------------------

CASES: dict[str, tuple[Path, callable]] = {
    "demo": (
        RESULTS_DIR / "demo_embeddings.npz",
        compute_demo_embeddings,
    ),
    "hacking": (
        RESULTS_DIR / "hacking_forums_embeddings.npz",
        compute_hacking_embeddings,
    ),
    "ironmarch": (
        RESULTS_DIR / "ironmarch_embeddings.npz",
        compute_ironmarch_embeddings,
    ),
}


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def run_case(case_name: str) -> None:
    if case_name not in CASES:
        log(f"ERROR: caso desconocido '{case_name}'. Opciones: {list(CASES.keys())}")
        sys.exit(1)

    output_path, compute_fn = CASES[case_name]

    log(f"--- Caso: {case_name} ---")

    if skip_if_exists(output_path):
        return

    try:
        load_or_compute(output_path, compute_fn)
        log(f"  Guardado en: {output_path}")
    except Exception as e:
        log(f"  ERROR en '{case_name}': {e}")
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Precomputa embeddings para los casos del curso CSBC26.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  uv run python scripts/precompute.py                # todo
  uv run python scripts/precompute.py --case demo    # solo demo
  uv run python scripts/precompute.py --case hacking # solo hacking
        """,
    )
    parser.add_argument(
        "--case",
        choices=["all"] + list(CASES.keys()),
        default="all",
        help="Caso a precomputar (default: all)",
    )
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    log(f"Directorio de resultados: {RESULTS_DIR}")
    log(f"Caso(s) a procesar: {args.case}")
    log("")

    cases_to_run = list(CASES.keys()) if args.case == "all" else [args.case]

    errors = []
    for case_name in cases_to_run:
        try:
            run_case(case_name)
        except Exception as e:
            errors.append((case_name, str(e)))
            log(f"  FALLO en '{case_name}' — continuando con el siguiente...")
        log("")

    log("=== Resumen ===")
    for case_name in cases_to_run:
        output_path, _ = CASES[case_name]
        status = "OK" if output_path.exists() else "FALLO"
        log(f"  [{status}] {case_name} → {output_path.name}")

    if errors:
        log("")
        log("Errores encontrados:")
        for case_name, err in errors:
            log(f"  {case_name}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
