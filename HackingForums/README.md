# Caso 2 — Hacking Forums

Análisis comparativo de **cinco foros underground** con distintas plataformas, idiomas y épocas de actividad. El caso introduce la complejidad real del análisis multi-foro: formatos heterogéneos de dump SQL, detección automática del parser, idioma mixto (inglés + ruso) y pivoting de identidades entre comunidades.

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
| 00 | [`00_extract_and_explore.ipynb`](00_extract_and_explore.ipynb) | Clasificación de datasets por tier, carga multi-parser (MyBB / IPS 3.x), EDA comparativo, red de co-participación en OGUsers, persistencia de handles entre foros, **detección de idioma por foro** |
| 01 | [`01_load_and_clean.ipynb`](01_load_and_clean.ipynb) | Limpieza unificada, filtro de timestamps epoch-0, normalización, exportación a Parquet (combinado + por foro) |
| 02 | [`02_llm_analysis.ipynb`](02_llm_analysis.ipynb) | Detección de idioma por post, BERTopic separado por idioma (inglés / ruso multilingual), NER con entidades de hacking (`ALIAS`, `TOOL`, `MALWARE`, `CVE`, `MARKETPLACE`), checkpoint por foro |
| 03 | [`03_embeddings_profiling.ipynb`](03_embeddings_profiling.ipynb) | Centroides por usuario, Spearman ρ (estrategia A vs C), UMAP + HDBSCAN, matching exacto y fuzzy de handles cross-foro, Burrows' Delta (solo foros en inglés), puntuación de atribución combinada |

### Flujo de datos

```
dumps SQL (.zip) — 5 foros, 3 parsers
    └── 00_extract_and_explore  →  EDA + idioma por foro
    └── 01_load_and_clean       →  results/hacking_forums/*.parquet
    └── 02_llm_analysis         →  results/hacking_forums/ner_*.parquet
    └── 03_embeddings_profiling →  results/hacking_forums/hf_centroids_*.npz
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
| [`script.md`](script.md) | Guión de clase (~55 min) con timing, frases clave y notas de instructor |
| [`csbc26_caso2_hackingforums.pptx`](csbc26_caso2_hackingforums.pptx) | Presentación (21 diapositivas, 5 secciones) |

### Generadores

Los archivos `build_XX.py` regeneran cada notebook vía `nbformat`. `build_slides.py` regenera el `.pptx` usando `python-pptx` y el tema compartido en `talks/_shared/theme.py`.

---

## Notas técnicas

- **Parsers activos**: MyBB (detección automática de prefijo no estándar), IPS 3.x con `ibf_`, IPS 3.x sin prefijo
- **Filtro temporal**: posts con `dateline < 2000` (epoch-0) se descartan en notebook 01
- **Modelo de embeddings**: `qwen3-embedding` (4096D, multilingual — válido para ruso e inglés)
- **Modelo LLM**: `qwen2.5:14b` vía Ollama
- **Burrows' Delta**: aplicado **solo** a los cuatro foros en inglés (Exploit.in excluido)
