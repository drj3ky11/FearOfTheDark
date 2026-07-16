# Bloque 3 — Agentes de IA con CrewAI y Ollama

Este módulo introduce la orquestación de agentes de IA usando modelos locales (Ollama) y el framework CrewAI. Es el puente entre el uso de LLMs como clasificadores (bloque 2/4) y el análisis forense profundo con equipos de agentes especializados.

## Notebooks

| Notebook | Concepto | Duración estimada |
|---|---|---|
| `00_conceptos_agentes.ipynb` | Qué es un agente, los tres primitivos de CrewAI, primer agente funcional | ~10 min |
| `01_crew_investigacion.ipynb` | Crew de 3 agentes sobre datos reales de ContiLeaks | ~10-15 min ejecución |
| `02_agentes_con_herramientas.ipynb` | Tool-use: agentes que llaman funciones pandas | ~15-20 min ejecución |

## Requisitos

### Software
- Ollama corriendo localmente: `ollama serve`
- Modelo descargado: `ollama pull qwen2.5:14b`
- Dependencias Python: `uv sync` en la raíz del repositorio (incluye `crewai>=0.130`)

### Datos
Los notebooks leen de `data_para_alumnos/ContiLeaks/data/processed/`:
- `actor_profiles.json` (20 KB)
- `conti_sample_classified.parquet` (88 KB)
- `message_embeddings.npy` (24 MB) — solo necesario en el notebook 02

## Sin datos brutos

Este módulo **no requiere los datasets brutos** (Jabber logs, Rocket.Chat). Trabaja exclusivamente con los datos ya procesados del bloque 4, por lo que es ejecutable por alumnos con equipos limitados.

## Nota sobre tiempos

Con `qwen2.5:14b` y CPU:
- Notebook 01 (3 agentes): ~3-5 minutos
- Notebook 02 (5 preguntas): ~5-10 minutos

Con GPU dedicada: 3-5× más rápido.
