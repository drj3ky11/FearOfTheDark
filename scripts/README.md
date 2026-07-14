# `scripts/` — Precómputo pesado fuera del notebook

Los notebooks nunca calculan embeddings, centroides o NER en vivo sobre el dataset completo — sería demasiado lento para una sesión de clase. En su lugar, estos scripts se corren una vez desde la terminal, escriben sus resultados en `results/` (vía `src.utils.load_or_compute`), y los notebooks solo leen esos artefactos cacheados.

Si quieres reproducir o extender un análisis con datos propios, estos scripts son el mejor punto de partida: son ejemplos reales de cómo se usa `src/embeddings.py` y `src/utils.py` fuera de un notebook.

```bash
uv run python3 scripts/<script>.py
```

Requieren Ollama corriendo en local con el modelo `qwen3-embedding` descargado — no hace falta si solo vas a leer los artefactos ya precomputados en `results/`.

## Scripts de embeddings y centroides

| Script | Qué hace |
|---|---|
| `run_embed_users_all.py` | Estrategia A (`embed_users`, concatenación) para IronMarch y HackingForums. |
| `run_embed_users_hf.py` | Estrategia A solo para HackingForums (top-N usuarios más prolíficos por foro). |
| `run_embeddings_hf_new.py` | Añade `embed_users` de foros Tier 1 nuevos al `.npz` existente de HackingForums, sin recalcular los que ya estaban. |
| `run_centroids_hf_all.py` | Centroides muestreados (`compute_actor_centroids`) para todos los foros de HackingForums. |
| `run_centroids_hf_new.py` | Igual que el anterior pero solo para foros nuevos (top-5000 usuarios, top-50 posts por usuario). |
| `run_centroids_hf_comparison.py` | Comparativa de estrategias A/C/D/E (distintas combinaciones de muestreo) para HackingForums, incluyendo RaidForums. |
| `run_centroids_im_comparison.py` | Compara centroides de IronMarch variando el tamaño de muestra, para decidir el tradeoff calidad/tiempo. |

## NER

| Script | Qué hace |
|---|---|
| `run_ner.py` | Pre-genera la caché de NER (entidades: IPs, dominios, handles, herramientas) para el notebook de IronMarch, usando el LLM local vía Ollama. |

## `run_weekend.sh`

Orquesta una corrida larga (~60h) de varios scripts en secuencia, pensada para lanzarse un viernes y tener los resultados listos el lunes (ver comentarios en el propio script para el desglose de tiempos por paso). Sirve de referencia de cuánto tarda cada estrategia de muestreo en una GPU modesta — útil si estás calibrando cuánto puedes precomputar tú mismo antes de una sesión.

## Por qué existen estas variantes (A/C/D/E, "all" vs "new" vs "comparison")

No es desorden — reflejan decisiones de tradeoff que se discuten en Bloque 2 (concatenar vs. promediar, cuántos usuarios/posts muestrear) y quedaron como scripts separados porque cada corrida se lanzó en un momento distinto del proyecto (foro nuevo añadido, necesidad de comparar estrategias, etc.). Si vas a precomputar para un dataset propio, `run_embed_users_hf.py` y `run_centroids_hf_all.py` son las plantillas más simples de las que partir.
