"""
Common utilities shared across parsers and notebooks.

DATA_DIR and RESULTS_DIR are resolved relative to this file's location,
so the notebooks work regardless of where they're run from.
"""

from pathlib import Path
from typing import Any, Callable
import pandas as pd
import numpy as np


DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent / "results"

# Crear el directorio de resultados al importar el módulo
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_or_compute(path: Path | str, compute_fn: Callable, *args, **kwargs) -> Any:
    """
    Carga un resultado precomputado si existe; si no, lo calcula y lo guarda.

    El formato de serialización se infiere por extensión de archivo:
    - .npz  → numpy.savez / numpy.load
    - .parquet → DataFrame de pandas (parquet)
    - cualquier otro → error (extensión no soportada)

    Esto permite que los notebooks de demo y casos funcionen sin Ollama
    una vez que los resultados fueron generados por primera vez.

    Parámetros:
        path:       ruta al archivo de caché (puede no existir todavía).
        compute_fn: función que produce el resultado cuando el caché no existe.
        *args:      argumentos posicionales para compute_fn.
        **kwargs:   argumentos de palabra clave para compute_fn.

    Retorna:
        El objeto cargado o calculado (numpy.lib.npyio.NpzFile o pd.DataFrame).
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if path.exists():
        if suffix == ".npz":
            return np.load(path, allow_pickle=False)
        elif suffix == ".parquet":
            return pd.read_parquet(path)
        else:
            raise ValueError(f"Extensión no soportada para caché: {suffix!r}")

    # No existe todavía — calcular y guardar
    result = compute_fn(*args, **kwargs)
    path.parent.mkdir(parents=True, exist_ok=True)

    if suffix == ".npz":
        if isinstance(result, dict):
            np.savez(path, **result)
        else:
            raise TypeError("Para .npz, compute_fn debe retornar un dict de arrays numpy.")
    elif suffix == ".parquet":
        if isinstance(result, pd.DataFrame):
            result.to_parquet(path, index=False)
        else:
            raise TypeError("Para .parquet, compute_fn debe retornar un pd.DataFrame.")
    else:
        raise ValueError(f"Extensión no soportada para caché: {suffix!r}")

    return result


def list_forums(category: str) -> list[Path]:
    """
    Return all zip files for a given category folder (e.g. 'Carding Forums').

    macOS metadata files (._filename.zip) are automatically excluded —
    they appear alongside real files when the data was created on a Mac,
    and will cause parse errors if passed to the parsers.
    """
    cat_dir = DATA_DIR / category
    return sorted(p for p in cat_dir.glob("*.zip") if not p.name.startswith("._"))


def load_forum(zip_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Load a single forum zip, auto-detecting format.

    vBulletin SQL dumps → src.parsers.vbulletin.load_forum
    MyBB SQL dumps      → src.parsers.mybb.load_forum
    IPS SQL dumps       → src.parsers.ips.load_forum
    Flat text files     → src.parsers.flat.load_flat_forum

    Detection order:
    1. MyBB: SQL contains tables matching known MyBB suffixes (users/posts/threads)
    2. IPS: vBulletin parser returns no posts → try IPS
    3. vBulletin: default for .sql dumps
    """
    from src.parsers.vbulletin import load_forum as _load_vb
    from src.parsers.ips import load_forum as _load_ips
    from src.parsers.flat import load_flat_forum as _load_flat
    from src.parsers.mybb import load_forum as _load_mybb, is_mybb
    import zipfile

    zip_path = Path(zip_path)
    zf = zipfile.ZipFile(zip_path)
    names = zf.namelist()

    has_sql = any(n.endswith(".sql") for n in names)
    has_txt = any(n.endswith(".txt") or n.endswith(".csv") for n in names)

    if has_sql:
        if is_mybb(zip_path):
            return _load_mybb(zip_path)
        result = _load_vb(zip_path)
        post_df = result.get("post")
        if post_df is None or len(post_df) == 0:
            # vBulletin parser found no posts — try IPS (e.g. IronMarch)
            ips_result = _load_ips(zip_path)
            if ips_result:
                return ips_result
        return result
    elif has_txt:
        return _load_flat(zip_path)
    else:
        raise ValueError(f"Unknown format in {zip_path.name}: {names}")


def load_all_forums(category: str, verbose: bool = True) -> list[dict[str, pd.DataFrame]]:
    """
    Load all forums in a category, skipping ones that fail.
    Returns a list of forum dicts (each with 'user', 'post', etc. keys).
    """
    results = []
    for path in list_forums(category):
        try:
            dfs = load_forum(path)
            results.append(dfs)
            if verbose:
                u = len(dfs.get("user", []))
                p = len(dfs.get("post", []))
                print(f"  ✓ {path.name}: {u:,} users, {p:,} posts")
        except Exception as e:
            if verbose:
                print(f"  ✗ {path.name}: {e}")
    return results


def merge_tables(dfs_list: list[dict[str, pd.DataFrame]], table: str) -> pd.DataFrame:
    """
    Merge a single table from multiple parsed forum dicts into one DataFrame.

    Example:
        all_forums = load_all_forums("Carding Forums")
        all_users  = merge_tables(all_forums, "user")
        # → one DataFrame with a 'forum' column identifying the source
    """
    frames = [dfs[table] for dfs in dfs_list if table in dfs and len(dfs[table]) > 0]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
