# Caso IronMarch

Análisis forense del foro neo-nazi **Iron March** (2011–2017), filtrado en noviembre de 2019. El dump contiene ~1.207 usuarios registrados y ~194.000 posts públicos (tras filtrar cola de moderación) en formato IPS 4.x — conteo verificado ejecutando el parser del proyecto contra el ZIP crudo (ver `00_reconocimiento.ipynb`, sección de validación de integridad); no es una cifra publicada externamente.

---

## Objetivo de este caso

**Pregunta**: ¿quién influye más en una red de radicalización? Es un foro ideológico, no de mando — sus miembros se influyen y retroalimentan entre sí y luego suelen actuar de forma aislada, así que la pregunta no es quién manda.

**Técnica protagonista**: centralidad (degree + betweenness) sobre la red pública y la red privada (mensajes), validada contra ground truth judicial real (el fundador, MOONLORD, fue doxxeado e identificado como Alexander Slavros). El hallazgo central: la influencia visible en la red pública no siempre coincide con la influencia estructural real en la red privada.

---

## Notebooks

| # | Notebook | Contenido |
|---|----------|-----------|
| 00 | [`00_reconocimiento.ipynb`](00_reconocimiento.ipynb) | Carga del dump IPS 4.x, EDA (usuarios, posts, actividad temporal), red de co-participación, persistencia de handles, **detección de idioma** |
| 01 | [`01_ingenieria_datos.ipynb`](01_ingenieria_datos.ipynb) | Limpieza del texto (HTML, BBCode), filtro de posts vacíos, normalización, exportación a Parquet |
| 02 | [`02_analisis_estructural.ipynb`](02_analisis_estructural.ipynb) | Red de co-participación (pública y privada), métricas de centralidad |
| 03 | [`03_analisis_semantico.ipynb`](03_analisis_semantico.ipynb) | BERTopic, NER con `qwen2.5:14b` (personas, organizaciones, ideología), estrategias de centroide por usuario, Burrows' Delta y Cosine Delta estilométricos |
| 04 | [`04_sintesis_informe.ipynb`](04_sintesis_informe.ipynb) | Señal combinada de atribución, conclusiones, limitaciones éticas del caso |

### Flujo de datos

```
dump IPS 4.x (.zip)
    └── 00_reconocimiento       →  EDA + idioma
    └── 01_ingenieria_datos     →  results/ironmarch/*.parquet
    └── 02_analisis_estructural →  results/ironmarch/*.parquet (centralidad)
    └── 03_analisis_semantico   →  results/ironmarch/*.npz (embeddings, centroides)
    └── 04_sintesis_informe     →  informe final de atribución
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
| [`csbc26_caso_ironmarch.pptx`](csbc26_caso_ironmarch.pptx) | Presentación (25 diapositivas, 5 secciones) |

---

## Notas técnicas

- **Parser**: IPS 4.x — tablas sin prefijo, columna `member_id` en `core_members`
- **Idioma**: inglés (verificado en notebook 00 — pipeline estándar válido)
- **Modelo de embeddings**: `qwen3-embedding` (4096D, multilingual)
- **Modelo LLM**: `qwen2.5:14b` vía Ollama
- **Burrows' Delta / Cosine Delta**: válidos (corpus en inglés)

---

## Dependencias de `src/` y `scripts/`

| Función (`src/`) | Uso en este caso |
|---|---|
| `load_forum` | Carga el dump IPS 4.x (notebooks 00 y 01) auto-detectando el formato |
| `embed_users` | Estrategia A de centroide: un embedding por usuario concatenando sus posts (notebook 03) |
| `compute_actor_centroids` | Estrategias C/D/E: un embedding por post, promediado por usuario (notebook 03) |

| Comando (`scripts/precompute.py`) | Artefacto que produce |
|---|---|
| `embed --strategy embed_users --file "data/Far Right Forum/IronMarch_2019.11.zip"` | `.npz` de la Estrategia A precomputada sobre todo el dataset |
| `compare --file "data/Far Right Forum/IronMarch_2019.11.zip" --reference centroids` | Comparativa de tamaños de muestra para los centroides de IronMarch |
| `ner --file "data/Far Right Forum/IronMarch_2019.11.zip" --sample-size 500` | `ner_results.parquet` — caché de entidades extraídas con LLM local vía Ollama |

Nota: el notebook 03 reutiliza `_FUNCTION_WORDS` de `src/stylometry.py` como vocabulario de Delta, pero el resto de la implementación (z-score, matriz de distancias, Burrows' Delta y Cosine Delta) es específica del notebook — `src/stylometry.py` en sí implementa un método distinto (`extract_features`/`compare_users`, cosine similarity de embeddings semánticos).

Ver [`src/README.md`](../src/README.md) y [`scripts/README.md`](../scripts/README.md) para la API completa.
