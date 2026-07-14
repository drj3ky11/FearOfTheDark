# `scripts/` — Precómputo pesado fuera del notebook

Los notebooks nunca calculan embeddings, centroides o NER en vivo sobre el dataset completo — sería demasiado lento para una sesión de clase. En su lugar, `scripts/precompute.py` se corre una vez desde la terminal, escribe sus resultados en `results/`, y los notebooks solo leen esos artefactos cacheados.

Si quieres reproducir o extender un análisis con datos propios, `precompute.py` es el mejor punto de partida: es un ejemplo real de cómo se usa `src/embeddings.py` y `src/utils.py` fuera de un notebook, y es genérico — no tiene nombres de foro ni de dataset hardcodeados, funciona con cualquier carpeta de `.zip` de foros.

```bash
uv run python3 scripts/precompute.py <embed|compare|ner> [flags]
```

Requiere Ollama corriendo en local con el modelo `qwen3-embedding` (o el que pases con `--model`) descargado — no hace falta si solo vas a leer los artefactos ya precomputados en `results/`. Usa `--dry-run` en cualquier subcomando para probar la selección de dataset y la construcción del nombre de salida sin llamar a Ollama/GPU.

## Selección de dataset (compartida por los tres subcomandos)

- `--file PATH` — un solo foro (carga con `src.utils.load_forum`).
- `--dir DIRPATH [--forums F1 F2 ...]` — todos los `.zip` que haya directamente dentro de `DIRPATH`, o un subconjunto por nombre de archivo (sin `.zip`). Al combinar varios foros, el `userid` se prefija `{stem}_{userid}` para evitar colisiones.

Flags comunes: `--min-posts` (default 5), `--model`, `--batch-size` (default 32), `--output-dir` (default `results/<slug(dir-name|file-stem)>`), `--output-name`, `--timestamp`/`--no-timestamp` (timestamp activado por default), `--dry-run`.

## `embed` — embeddings por usuario (estrategias A/B/C)

```bash
# Estrategia A (embed_users): concatena todos los posts del usuario, 1 embedding/usuario
uv run python3 scripts/precompute.py embed --strategy embed_users \
    --dir "data/Hacking Forums" --top-users 1000 --min-posts 5 \
    --output-name hf_embed_users

# Estrategia C (centroids, muestreada): centroide de los top-N posts más largos por usuario
uv run python3 scripts/precompute.py embed --strategy centroids \
    --dir "data/Hacking Forums" --top-users 5000 --top-n 50

# Estrategia B (centroids, full — todos los posts, sin --top-n): equivalente a la
# antigua bloque4_ironmarch/embeddings.py "parte B"
uv run python3 scripts/precompute.py embed --strategy centroids \
    --file "data/Far Right Forum/IronMarch_2019.11.zip" \
    --output-name s5b_centroids_full

# Añadir foros nuevos a un .npz existente sin recalcular los que ya estaban
uv run python3 scripts/precompute.py embed --strategy embed_users \
    --dir "data/Hacking Forums" --extend
```

Flags propios de `embed`: `--strategy {embed_users,centroids}` (requerido), `--top-users N` (cap de usuarios más prolíficos por foro, default: todos los que cumplen `--min-posts`), `--top-n N` (solo `centroids`: cap de posts más largos por usuario, default: todos), `--max-chars` (solo `embed_users`, default 50000), `--extend` (agrega foros nuevos a un `.npz` existente, saltando los ya presentes).

`--strategy embed_users` delega en `src.embeddings.embed_users`/`embed_texts`; `--strategy centroids` delega en `src.embeddings.compute_actor_centroids`. Ninguno reimplementa el batching.

## `compare` — comparativa de estrategias de muestreo

Camino independiente de `embed`: no requiere `--strategy`. Compara una estrategia de muestreo más barata contra una referencia (`centroids` o `full`) vía correlación de Spearman sobre similitud coseno pairwise.

```bash
uv run python3 scripts/precompute.py compare --dir "data/Hacking Forums" \
    --forums OGUsers_2019 Exploit.in_2013.12.13 Cracked.to_2019.01 Nulled.io_2016.05 RaidForums_2021 \
    --reference centroids --top-users-c 5000 \
    --sample-sizes 100,150 --top-sample 300 \
    --output-name hf_centroids_sampled
```

Flags propios de `compare`: `--reference {centroids,full}` (requerido), `--top-users-c` (usuarios/foro para la referencia `centroids`, default 5000), `--top-sample` (usuarios/foro para la muestra comparativa, default 300), `--sample-sizes` (lista separada por comas de tamaños de muestra top-N-posts-más-largos a comparar, default `100,150`).

## `ner` — extracción de entidades

```bash
uv run python3 scripts/precompute.py ner \
    --file "data/Far Right Forum/IronMarch_2019.11.zip" --sample-size 500
```

Flags propios de `ner`: `--sample-size` (default 500). Escribe siempre el nombre canónico `ner_results.parquet`, el que consume `bloque4_ironmarch/03_analisis_semantico.ipynb`.

## Nombres de salida

Por default, el archivo se escribe en `<output-dir>/<output-name>[_<timestamp>].{npz|parquet}`, con `output-dir` = `results/<slug(dir-name|file-stem)>` y `output-name` derivado del strategy/prefijo del dataset (p. ej. `hf_centroids_sampled_<ts>.npz`). Usa `--output-name` (y opcionalmente `--no-timestamp`) para reproducir un nombre exacto, como `hacking_forums_user_embeddings.npz` o la familia `s5[abcde]_*_*.npz` que leen los notebooks de IronMarch.

## Sobre el tamaño del archivo

`precompute.py` tiene ~555 líneas en un único archivo. Es deliberado: los tres subcomandos comparten resolución de dataset, filtrado y guardado (`resolve_forums`, `resolve_output_path`, `save_npz`/`save_parquet`), y partirlo en varios módulos obligaría a un paquete (`__init__.py` + imports cruzados) solo para separar ~80-100 líneas por subcomando — más indirección para navegar sin reducir la duplicación real. Se mantiene como un único archivo.
