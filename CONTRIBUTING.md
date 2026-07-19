# Guía de contribución
 
Gracias por tu interés en contribuir a **CSBC26 — *Fear Of The Dark***. Toda
ayuda es bienvenida: correcciones, mejoras de contenido docente, nuevos casos
prácticos, arreglos en la librería o simplemente reportar un problema.
 
## Cómo puedes contribuir
 
- **Reportar errores** en el código, los notebooks o el material.
- **Sugerir mejoras**: nuevas técnicas, casos, o aclaraciones en las explicaciones.
- **Corregir** erratas, enlaces rotos o inconsistencias entre bloques.
- **Aportar código** a la librería (`src/`) o a los scripts (`scripts/`).
Si es un cambio grande (un caso práctico nuevo, un refactor de `src/`, etc.),
abre primero un *issue* para comentarlo antes de ponerte a trabajar. Así
evitamos duplicar esfuerzo o llevar el material en una dirección no deseada.
 
## Antes de empezar
 
1. Revisa los *issues* abiertos por si ya existe lo que quieres proponer.
2. Para bugs, comprueba que se reproduce con la última versión de `master`.
3. Para vulnerabilidades de seguridad, **no** abras un issue público: sigue la
   [Política de Seguridad](SECURITY.md).
## Configuración del entorno
 
El proyecto usa [`uv`](https://docs.astral.sh/uv/) para gestionar dependencias y
Python (≥ 3.12).
 
```bash
# Clona tu fork
git clone https://github.com/<tu-usuario>/FearOfTheDark.git
cd FearOfTheDark
 
# Instala dependencias en un entorno aislado
uv sync
 
# Lanza Jupyter (o abre los notebooks en tu editor)
uv run jupyter lab
```
 
Algunos bloques usan **LLMs locales con Ollama**; consulta el `bloque3_setup/`
para los detalles de instalación y los modelos necesarios.
 
## Flujo de trabajo
 
1. Haz un *fork* del repositorio y clónalo.
2. Crea una rama descriptiva desde `master`:
```bash
   git checkout -b fix/parser-vbulletin-encoding
```
3. Haz tus cambios en *commits* pequeños y con mensajes claros.
4. Asegúrate de que los notebooks se ejecutan de principio a fin sin errores.
5. Abre un *Pull Request* contra `master` describiendo **qué** cambias y **por qué**.
## Estilo y convenciones
 
- **Código Python**: sigue PEP 8. Nombres y comentarios pueden ir en español o
  inglés, pero mantén la coherencia dentro de cada archivo.
- **Notebooks**: antes de hacer *commit*, **limpia las salidas** (`Kernel →
  Restart & Clear Output`) salvo que la salida sea parte del material didáctico.
  Evita dejar rutas absolutas o datos locales en las celdas.
- **Mensajes de commit**: en imperativo y concisos, p. ej.
  `Añade detección de encoding cp1251 en parser vBulletin`. Se agradece el estilo
  [Conventional Commits](https://www.conventionalcommits.org/) (`fix:`, `feat:`,
  `docs:`…), aunque no es obligatorio.
## Datos: nunca los subas
 
Este repositorio **no contiene ni debe contener datos reales** (leaks, dumps,
credenciales, PII). Las carpetas `data/`, `data_bruto/` y `results/` están
ignoradas por diseño. Antes de subir cambios:
 
- Revisa `git status` y confirma que no arrastras ficheros de datos.
- No incluyas rutas, credenciales ni fragmentos de datasets reales en el código,
  los notebooks ni los ejemplos.
Si tienes dudas sobre el tratamiento de material sensible, consulta la
[Política de Seguridad](SECURITY.md).
 
## Código de conducta
 
Sé respetuoso y constructivo en *issues*, *pull requests* y discusiones. Se
espera un trato cordial y profesional por parte de todas las personas que
participan.
 
## Licencia
 
Al contribuir, aceptas que tus aportaciones se publiquen bajo la misma licencia
del proyecto ([MIT](LICENSE)).
 
---
 
¿Dudas? Abre un *issue* con la etiqueta `question` y te responderemos.
