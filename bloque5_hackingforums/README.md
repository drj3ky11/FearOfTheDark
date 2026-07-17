# Caso Hacking Forums

Análisis comparativo de **cinco foros underground** con distintas plataformas, idiomas y épocas de actividad. El caso introduce la complejidad real del análisis multi-foro: formatos heterogéneos de dump SQL, detección automática del parser, idioma mixto (inglés + ruso) y pivoting de identidades entre comunidades.

---

## Objetivo de este caso

**Pregunta**: ¿una identidad underground sobrevive a una brecha, o migra?

**Técnica protagonista**: atribución cross-foro multi-señal — handle exacto/fuzzy + similitud de embeddings + Burrows' Delta combinados en un solo score, porque ninguna señal por sí sola basta para confirmar identidad. Se valida contra la persistencia real de usernames entre los 4 snapshots de OGUsers (2019–2022): 111,621 handles de 2019 siguen presentes en 2022, solo 1,332 desaparecen.

La detección de idioma (notebook `00`) es la referencia canónica de esta técnica para todo el curso — los demás casos solo la mencionan de pasada.

---

## Datasets

| Foro | Archivo | Parser | Idioma | Tier |
|------|---------|--------|--------|------|
| **OGUsers** | `OGUsers_2019.zip` | MyBB (prefijo no estándar) | Inglés | A |
| **Exploit.in** | `Exploit.in_2013.12.13.zip` | IPS 3.x (`ibf_`) | **Ruso** | A |
| **Cracked.to** | `Cracked.to_2019.01.zip` | MyBB | Inglés | A |
| **Nulled.io** | `Nulled.io_2016.05.zip` | IPS 3.x (sin prefijo) | Inglés | A |
| **RaidForums** | `RaidForums_2021.zip` | MyBB | Inglés | A |

> Tier A = dump SQL completo: usuarios + posts + threads. Permite análisis de red, atribución y estilometría.

Foros descartados: `Hackforums.net` (solo tabla de usuarios, sin posts) y `Void.to` (schema-only, sin datos).

---

## Notebooks

| # | Notebook | Contenido |
|---|----------|-----------|
| 00 | [`00_reconocimiento.ipynb`](00_reconocimiento.ipynb) | Clasificación de datasets por tier, carga multi-parser (MyBB / IPS 3.x), EDA comparativo, red de co-participación en OGUsers, persistencia de handles entre foros, **detección de idioma por foro** |
| 01 | [`01_ingenieria_datos.ipynb`](01_ingenieria_datos.ipynb) | Limpieza unificada, filtro de timestamps epoch-0, normalización, exportación a Parquet (combinado + por foro) |
| 02 | [`02_analisis_estructural.ipynb`](02_analisis_estructural.ipynb) | Red de co-participación, pivoting de handles (exacto + fuzzy), TF-IDF por subforo |
| 03 | [`03_analisis_semantico.ipynb`](03_analisis_semantico.ipynb) | Detección de idioma por post, BERTopic separado por idioma (inglés / ruso multilingual), NER con entidades de hacking (`ALIAS`, `TOOL`, `MALWARE`, `CVE`, `MARKETPLACE`), embeddings y perfilado |
| 04 | [`04_sintesis_informe.ipynb`](04_sintesis_informe.ipynb) | Convergencia de señales de atribución cross-foro, conclusiones, exportación del informe final |

### Flujo de datos

```
dumps SQL (.zip) — 5 foros, 3 parsers
    └── 00_reconocimiento       →  EDA + idioma por foro
    └── 01_ingenieria_datos     →  results/hacking_forums/*.parquet
    └── 02_analisis_estructural →  results/hacking_forums/*.html (red, TF-IDF)
    └── 03_analisis_semantico   →  results/hacking_forums/*.npz (embeddings, centroides)
    └── 04_sintesis_informe     →  informe final de atribución cross-foro
```

---

## Decisión de pipeline por idioma

La detección de idioma (notebook 00) es el paso previo obligatorio. El resultado determina qué técnicas son aplicables:

| Técnica | OGUsers | Exploit.in | Cracked.to | Nulled.io | RaidForums |
|---------|---------|-----------|-----------|----------|-----------|
| BERTopic (en) | ✓ | — | ✓ | ✓ | ✓ |
| BERTopic (multilingual) | — | ✓ | — | — | — |
| NER inglés | ✓ | — | ✓ | ✓ | ✓ |
| Burrows' Delta | ✓ | — | ✓ | ✓ | ✓ |
| qwen3-embedding | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Bug destacado — IPS 3.x sin prefijo (Nulled.io)

El parser `is_mybb()` devolvía `True` para Nulled.io porque `_TABLE_MAP` contiene la clave `"posts"` y la IPS 3.x sin prefijo tiene exactamente una tabla llamada `posts`. El fix fue ejecutar `_detect_version()` (IPS-específico, comprueba la columna `member_id`) **antes** de `is_mybb()` en `src/utils.py`.

---

## Material de clase

| Archivo | Descripción |
|---------|-------------|
| [`csbc26_caso_hackingforums.pptx`](csbc26_caso_hackingforums.pptx) | Presentación (21 diapositivas, 5 secciones) |

---

## Librería y scripts usados

Este caso reutiliza funciones de `src/`:

- **`load_forum` / `list_forums`** (`src/utils.py`, notebooks `00` y `01`) — carga de dumps con auto-detección de formato (MyBB/IPS 3.x/flat) y listado de `.zip` por categoría.
- **`embed_users` / `compute_actor_centroids`** (`src/embeddings.py`, notebook `03`) — embedding por concatenación vs. por promedio de posts. El notebook solo reproduce el cálculo en vivo sobre una muestra; los `.npz` completos que carga vienen precomputados.

Esos artefactos precomputados (`hacking_forums_user_embeddings.npz`, `hf_centroids_sampled_*.npz`) se generaron con `scripts/precompute.py embed --strategy embed_users --dir "data/Hacking Forums" ...` y `scripts/precompute.py embed --strategy centroids --dir "data/Hacking Forums" ...` (con `--extend` en corridas sucesivas para foros añadidos), lanzados en momentos distintos del proyecto para foros distintos.

Detalle completo de la API y de cada script: [`src/README.md`](../src/README.md) y [`scripts/README.md`](../scripts/README.md).

---

## Notas técnicas

- **Parsers activos**: MyBB (detección automática de prefijo no estándar), IPS 3.x con `ibf_`, IPS 3.x sin prefijo
- **Filtro temporal**: posts con `dateline < 2000` (epoch-0) se descartan en notebook 01
- **Modelo de embeddings**: `qwen3-embedding` (4096D, multilingual — válido para ruso e inglés)
- **Modelo LLM**: `qwen2.5:14b` vía Ollama
- **Burrows' Delta**: aplicado **solo** a los cuatro foros en inglés (Exploit.in excluido)
