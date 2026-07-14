# `src/` — Librería de análisis

Código reutilizable que los notebooks importan. Todo se usa desde un notebook como:

```python
import sys
sys.path.insert(0, "..")  # o la ruta relativa a la raíz del repo

from src.utils import load_forum, load_all_forums, merge_tables
from src.embeddings import embed_users, embed_texts, cosine_similarity
from src.stylometry import extract_features, compare_users
from src.timezone import build_user_timezone_profile
```

## `utils.py` — carga de datos y caché

- **`load_forum(zip_path, tables=None)`** — punto de entrada principal. Detecta automáticamente el formato del dump (vBulletin, MyBB, IPS o flat file) y devuelve un `dict[str, pd.DataFrame]` con claves como `"user"`, `"post"`, `"thread"`. Úsalo siempre en vez de llamar a los parsers de `src/parsers/` directamente — la detección de formato ya está resuelta aquí.
- **`list_forums(category)`** — lista los `.zip` de una categoría de `data/` (p. ej. `"Carding Forums"`), ignorando metadatos de macOS (`._archivo.zip`).
- **`load_all_forums(category, verbose=True)`** — carga todos los foros de una categoría, saltando los que fallan y reportando por consola.
- **`merge_tables(dfs_list, table)`** — une una tabla (p. ej. `"user"`) de varios foros ya cargados en un único DataFrame con columna `forum` de origen.
- **`load_or_compute(path, compute_fn, *args, **kwargs)`** — patrón de caché: si `path` existe lo carga (`.npz` o `.parquet`), si no ejecuta `compute_fn` y lo guarda. Es lo que permite que los notebooks corran sin GPU/Ollama una vez que los resultados ya están precomputados en `results/`.

```python
embeddings = load_or_compute(
    RESULTS_DIR / "hacking_forums" / "user_embeddings.npz",
    embed_users, posts_df, min_posts=3,
)
```

## `embeddings.py` — embeddings semánticos vía Ollama

Modelo por defecto: `qwen3-embedding` (4096 dims, multilingüe, corre local — nunca se manda texto a APIs externas).

- **`embed_texts(texts, model=..., batch_size=32)`** — embebe una lista de textos, en batches. Función de bajo nivel; úsala para semantic search o casos ad-hoc.
- **`embed_users(posts_df, min_posts=3, max_chars=50_000)`** — un embedding por usuario, concatenando todos sus posts (hasta `max_chars`). Mejor para capturar estilo global; usuarios con menos de `min_posts` se excluyen.
- **`compute_actor_centroids(posts_df, min_posts=5)`** — un embedding por post, luego promedio L2-normalizado por usuario. Más robusto que concatenar cuando el corpus es grande o hay outliers.
- **`cosine_similarity(a, b)`** — similitud coseno par a par entre dos matrices de vectores; base de cualquier comparación cross-foro.

Elegir entre `embed_users` y `compute_actor_centroids` es el mismo tradeoff que se explica en Bloque 2: concatenar da más contexto de estilo, promediar es más barato y estable con corpora grandes.

## `stylometry.py` — estilometría computacional

No requiere GPU ni LLM — son features estadísticas puras sobre el texto.

- **`extract_features(text)`** — extrae 8 features (longitud media/desviación de oración, ratios de puntuación, ratio de palabras funcionales bilingüe ES/EN, ratio de capitalización) de un texto.
- **`compare_users(df, user_col="user", text_col="text")`** — matriz cuadrada de similitud coseno entre todos los pares de usuarios de un DataFrame, a partir de sus features estilométricas agregadas.

Esta es la implementación base; el caso HackingForums usa además Burrows' Delta (ver ese notebook) como señal complementaria más robusta a cambios de tema.

## `timezone.py` — inferencia de zona horaria

- **`infer_utc_offset(post_hours_utc)`** — dado un listado de horas UTC de los posts de un usuario, busca el offset (-12 a +12) que mejor alinea su actividad con una ventana de vigilia típica (08:00–23:00 local). Requiere ≥5 posts.
- **`build_user_timezone_profile(posts_df)`** — aplica lo anterior a todos los usuarios de un DataFrame de posts (columnas requeridas: `userid`, `dateline` tz-aware UTC). Devuelve offset inferido, región aproximada y el histograma horario.
- **`peak_hours(activity_hours_str)`** — top-3 horas UTC más activas a partir del string de histograma que devuelve la función anterior.

Comparar `inferred_utc_offset` contra el campo `timezoneoffset` autodeclarado del usuario es una señal de posible uso de VPN u ofuscación deliberada.

## `parsers/` — un parser por motor de foro

`load_forum()` en `utils.py` ya elige el parser correcto automáticamente — normalmente no necesitas importar estos módulos directamente. Documentados aquí porque entender sus limitaciones importa si vas a procesar un dump nuevo que no cargue bien:

| Parser | Motor | Notas |
|---|---|---|
| `vbulletin.py` | vBulletin SQL | El formato más común en foros rusos/underground 2000-2020. Maneja encoding cp1251 (cirílico) y mezclas cp1251/UTF-8 dentro del mismo dump. |
| `mybb.py` | MyBB SQL | Prefijo de tabla configurable (`mybb_`, o random tipo `QLqEqiMsDA_`) — `_detect_prefix()` lo infiere del propio dump. Si un dump MyBB devuelve tablas vacías, sospecha primero de esta detección. |
| `ips.py` | IPS (Invision Power Suite) SQL | Soporta IPS 3.x (prefijo `ibf_`) y 4.x (sin prefijo). El orden de detección en `load_forum()` prueba IPS antes que MyBB porque IPS 3.x sin prefijo puede dar falso positivo en `is_mybb()`. |
| `flat.py` | Texto plano delimitado | Para leaks distribuidos como filas de usuario sin dump SQL completo (ver Bloque 0, tier B "flat files de credenciales"). Solo produce tabla `user`, sin `post`. |

Cada `load_forum()` de parser devuelve el mismo contrato: `dict[str, pd.DataFrame]` con claves de tabla en minúsculas (`"user"`, `"post"`, `"thread"`, etc.), timestamps ya convertidos a UTC tz-aware.
