# Caso Carding Forums

Análisis de un mercado de fraude financiero a través de **diez dumps** de foros de carding (2009–2021). El caso pone a prueba el pipeline del curso a la mayor escala de datos (casi un millón de usuarios) y combina los tres formatos de dump vistos en clase: vBulletin estándar, vBulletin con encoding no-UTF8 y flat file delimitado.

---

## Datasets

| Foro | Fecha del dump | Formato | Notas |
|------|----------------|---------|-------|
| **Carder.su** | 2009-02 | vBulletin SQL | |
| **Carding.biz** | 2009-11 | vBulletin SQL | |
| **Cardersplanet.biz** | 2010-05 | vBulletin SQL | |
| **Carders.cc** | 2010-12 | vBulletin SQL | |
| **Carder.pro** | 2013-04 | vBulletin SQL | Encoding cp1251 (cirílico) |
| **Cardingmafia.ws** | 2016-02 | Flat file | Colon-delimited, solo tabla `user` |
| **Crdshop.su** | 2016-11 | vBulletin SQL | |
| **Elitecarders.name** | 2016-08 | vBulletin SQL | |
| **CardingMafia** | 2021-03 | vBulletin SQL | Duplicado byte a byte de Cardmafia.cc — ver nota |
| **Cardmafia.cc** | 2021-03 | vBulletin SQL | Duplicado byte a byte de CardingMafia — ver nota |

> `CardingMafia_2021.03.zip` y `Cardmafia.cc_2021.03.zip` son el mismo leak subido bajo dos nombres distintos (mismo tamaño exacto, mismo `INSERT INTO user`, sin tabla `post` en ninguno). El reconocimiento inicial documentaba 9 foros; `list_forums()` devuelve 10 archivos.

---

## Notebooks

| # | Notebook | Contenido |
|---|----------|-----------|
| 00 | [`00_reconocimiento.ipynb`](00_reconocimiento.ipynb) | Glosario del dominio (carding), carga con auto-detección de formato, EDA comparativo de los 10 dumps, validación de calidad, preguntas de investigación |
| 01 | [`01_ingenieria_datos.ipynb`](01_ingenieria_datos.ipynb) | Limpieza de usuarios y posts, filtro de timestamps epoch-0, deduplicación, exportación a Parquet |
| 02 | [`02_analisis_estructural.ipynb`](02_analisis_estructural.ipynb) | Red de co-participación, centralidad (degree + betweenness), detección de comunidades (Louvain), TF-IDF por subforo |
| 03 | [`03_analisis_semantico.ipynb`](03_analisis_semantico.ipynb) | Embeddings por usuario (`qwen3-embedding`), UMAP + HDBSCAN, BERTopic, NER de dominio con `qwen2.5:14b`, perfilado de roles |
| 04 | [`04_sintesis_informe.ipynb`](04_sintesis_informe.ipynb) | Tabla final de actores, conclusiones, exportación del informe |

### Flujo de datos

```
dumps (.zip) — 10 archivos, 3 formatos
    └── 00_reconocimiento       →  results/00_reconocimiento_summary.json
    └── 01_ingenieria_datos     →  results/01_*.parquet
    └── 02_analisis_estructural →  results/02_centrality.parquet, results/02_network_viz.html
    └── 03_analisis_semantico   →  results/03_user_embeddings.npz, results/03_actor_profiles.parquet
    └── 04_sintesis_informe     →  results/04_final_actor_table.csv
```

---

## Bugs encontrados durante el procesamiento

| Problema | Causa | Fix |
|----------|-------|-----|
| `Cardingmafia.ws` cargaba con 0 filas | El zip contiene un flat file colon-delimited, no un dump SQL — el parser vBulletin no lo reconocía | `load_forum()` en `src/utils.py` auto-detecta flat/MyBB/IPS/vBulletin antes de elegir parser |
| 10 archivos donde se esperaban 9 | `CardingMafia_2021.03.zip` y `Cardmafia.cc_2021.03.zip` son el mismo leak subido dos veces | Ninguno — es un dato real del dataset, documentado en el reconocimiento |
| Merge `posts_x`/`posts_y` en NER (notebook 03) | `corpus.merge(users[...])` con columna `posts` en ambos lados — pandas la renombra al colisionar, pero el chequeo de sufijo miraba el dataframe pre-merge | Chequear el sufijo sobre el dataframe ya mergeado |

---

## Material de clase

| Archivo | Descripción |
|---------|-------------|
| [`script.md`](script.md) | Guión de clase con timing por sección, frases clave y notas de instructor |
| [`csbc26_caso_cardingforums.pptx`](csbc26_caso_cardingforums.pptx) | Presentación (22 diapositivas, 5 secciones) |

### Generadores

`build_slides.py` regenera el `.pptx` usando `python-pptx` y el tema compartido en `_shared/theme.py`.

---

## Notas técnicas

- **Parsers activos**: vBulletin (con y sin cp1251), flat file colon-delimited
- **Filtro temporal**: usuarios/posts con fecha `< 2000` (epoch-0 o inválida) se descartan en notebook 01 — 178,420 usuarios afectados
- **Red**: filtro de aristas débiles (`MIN_SHARED_THREADS = 2`), betweenness centrality por muestreo (`k=500`)
- **Modelo de embeddings**: `qwen3-embedding` (4096D) — 9,550 usuarios con ≥10 posts
- **Modelo LLM**: `qwen2.5:14b` vía Ollama, para NER y perfilado de roles (limitado a los 100 usuarios más activos por contador propio del foro)
- **Limitación conocida**: el contador `posts` de la tabla `user` de vBulletin no siempre coincide con los posts reales extraídos — varios usuarios "top" aparecen con 0 posts en el corpus y se clasifican como `lurker` por falta de señal, no necesariamente por comportamiento real
