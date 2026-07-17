# BlackBasta

Análisis académico de los chats filtrados del grupo de ransomware **Black Basta** usando LLMs locales (Ollama).

Segundo módulo del proyecto [FearOfTheDark](../README.md).

## Dataset

Los chats fueron filtrados en 2024 por un actor desconocido. Contienen comunicaciones internas del grupo en la plataforma Matrix entre septiembre de 2023 y septiembre de 2024.

- **Plataforma**: Matrix (matrix.bestflowers247.online)
- **Mensajes**: ~196 000
- **Actores**: 49 alias únicos
- **Canales**: 79 rooms
- **Idioma**: Ruso principalmente
- **Fuente pública**: PRODAFT / VXUnderground

## Notebooks

| Notebook | Descripción |
|---|---|
| `00_explore` | Inspección del formato pseudo-JSON y estadísticas iniciales |
| `01_load_and_clean` | Parser custom + limpieza → `data/processed/blackbasta_unified.parquet` |
| `02_llm_analysis` | Clasificación y perfilado de actores con Ollama |
| `03_embeddings_profiling` | Embeddings + clustering para detección de roles |

## Setup

```bash
pip install -r ../ContiLeaks/requirements.txt
# Requiere Ollama corriendo localmente:
# ollama pull qwen2.5:14b && ollama pull nomic-embed-text-v2-moe
```

## Ética y uso responsable

Uso exclusivamente académico y de threat intelligence. Datos públicamente documentados por investigadores de seguridad. No redistribuir datos originales.
