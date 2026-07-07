# Caso IronMarch

Análisis forense del foro neo-nazi **Iron March** (2011–2017), filtrado en noviembre de 2019. El dump contiene 1,207 usuarios y ~1.5M de posts en formato IPS 4.x.

El objetivo es aplicar el pipeline completo de análisis de foros underground: detección de idioma, limpieza, modelado de tópicos, NER y perfilado de usuarios por embeddings semánticos.

---

## Notebooks

| # | Notebook | Contenido |
|---|----------|-----------|
| 00 | [`00_extract_and_explore.ipynb`](00_extract_and_explore.ipynb) | Carga del dump IPS 4.x, EDA (usuarios, posts, actividad temporal), red de co-participación, persistencia de handles, **detección de idioma** |
| 01 | [`01_load_and_clean.ipynb`](01_load_and_clean.ipynb) | Limpieza del texto (HTML, BBCode), filtro de posts vacíos, normalización, exportación a Parquet |
| 02 | [`02_llm_analysis.ipynb`](02_llm_analysis.ipynb) | BERTopic (modelado de tópicos), NER con `qwen2.5:14b` (personas, organizaciones, ideología), checkpoint por usuario, picos de actividad |
| 03 | [`03_embeddings_profiling.ipynb`](03_embeddings_profiling.ipynb) | Estrategias A–E de centroide por usuario, Spearman ρ (comparativa de sampling), UMAP + HDBSCAN, Burrows' Delta estilométrico, puntuación de atribución |

### Flujo de datos

```
dump IPS 4.x (.zip)
    └── 00_extract_and_explore  →  EDA + idioma
    └── 01_load_and_clean       →  results/ironmarch/*.parquet
    └── 02_llm_analysis         →  results/ironmarch/ner_*.parquet
    └── 03_embeddings_profiling →  results/ironmarch/im_centroids_*.npz
```

---

## Estrategias de centroide

| ID | Descripción |
|----|-------------|
| A | `embed_users` — concatenar todos los posts del usuario en un solo embedding |
| B | Centroide full — media de embeddings de todos los posts |
| C | Top-50 posts más largos |
| D | Top-100 posts más largos |
| E | Top-150 posts más largos |

La comparativa Spearman (notebook 03) determina qué estrategia preserva mejor la estructura de similitud respecto al centroide full (B).

---

## Material de clase

| Archivo | Descripción |
|---------|-------------|
| [`script.md`](script.md) | Guión de clase (~55 min) con timing por sección, frases clave y notas de instructor |
| [`csbc26_caso_ironmarch.pptx`](csbc26_caso_ironmarch.pptx) | Presentación (25 diapositivas, 5 secciones) |

### Generadores

Los archivos `build_XX.py` regeneran cada notebook programáticamente vía `nbformat`. `build_slides.py` regenera el `.pptx` usando `python-pptx` y el tema compartido en `talks/_shared/theme.py`.

---

## Notas técnicas

- **Parser**: IPS 4.x — tablas sin prefijo, columna `member_id` en `core_members`
- **Idioma**: inglés (verificado en notebook 00 — pipeline estándar válido)
- **Modelo de embeddings**: `qwen3-embedding` (4096D, multilingual)
- **Modelo LLM**: `qwen2.5:14b` vía Ollama
- **Burrows' Delta**: válido (corpus en inglés)
