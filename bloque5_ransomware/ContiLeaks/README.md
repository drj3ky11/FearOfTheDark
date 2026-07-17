# ContiLeaks

Análisis académico de los chats filtrados del grupo de ransomware **Conti** usando LLMs locales (Ollama).

Primer módulo del proyecto [FearOfTheDark](../README.md).

## Dataset

Los chats de Conti fueron filtrados en febrero de 2022 por un investigador ucraniano tras la declaración de apoyo de Conti a la invasión rusa. Contienen comunicaciones internas del grupo entre 2020 y 2022.

Fuentes incluidas:
- **Jabber Chat Logs 2020** — chats XMPP del primer año del grupo
- **Jabber Chat Logs 2021–2022** — hasta el momento de la filtración
- **Rocket.Chat Leaks** — comunicaciones en la plataforma de mensajería interna

## Notebooks

| Notebook | Descripción |
|---|---|
| `00_extract_and_explore` | Extracción de archivos comprimidos e inspección de formatos |
| `01_load_and_clean` | Pipeline de carga unificado y limpieza → `conti_unified.parquet` |
| `02_llm_analysis` | Clasificación y análisis de mensajes con Ollama |
| `03_embeddings_profiling` | Embeddings + clustering para detección de roles |

## Setup

```bash
pip install -r requirements.txt
# Requiere p7zip-full instalado en el sistema:
# sudo apt install p7zip-full
# Requiere Ollama corriendo localmente:
# ollama pull qwen2.5 && ollama pull llama3.1 && ollama pull nomic-embed-text
```

## Ética y uso responsable

Este proyecto tiene fines exclusivamente académicos y de threat intelligence. Los datos utilizados son leaks públicamente documentados por investigadores de seguridad (PRODAFT, VXUnderground). No redistribuir datos originales.
