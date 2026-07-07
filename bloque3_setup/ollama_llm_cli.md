# Ollama + `llm` CLI — limpieza de datos ad-hoc desde terminal

Notas de referencia rápida para usar un LLM local desde la línea de comandos,
sin escribir código, como alternativa puntual a `src/utils.py` para tareas
de limpieza rápidas y no repetibles.

## Instalación

```bash
# Ollama
curl -fsSL https://ollama.com/install.sh | sh

# CLI `llm` (Simon Willison) + plugin de Ollama
pip install llm llm-ollama
```

## Ejemplo: limpiar un CSV con un prompt

```bash
cat datos_sucios.csv | llm -m ollama/qwen2.5:14b \
  "Normaliza estos datos: estandariza fechas a ISO 8601, \
   corrige codificación UTF-8 y elimina duplicados obvios"
```
