curl -fsSL https://ollama.com/install.sh | sh

La libreríapara scripting y limpieza de datos:
pip install llm llm-ollama

# Ejemplo: limpiar un CSV con un prompt
cat datos_sucios.csv | llm -m ollama/qwen2.5:14b \
  "Normaliza estos datos: estandariza fechas a ISO 8601, \
   corrige codificación UTF-8 y elimina duplicados obvios"
