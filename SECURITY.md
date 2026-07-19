# Security Policy

# Política de Seguridad
 
CSBC26 — *Fear Of The Dark*
 
## Ámbito
 
Esta política cubre el **código** del repositorio: la librería de análisis
(`src/`), los scripts CLI (`scripts/`) y los notebooks de los distintos bloques.
 
**No** cubre:
 
- Los **conjuntos de datos** analizados en el curso (leaks, dumps SQL, chat
  logs). El repositorio no distribuye datos reales — `data/`, `data_bruto/` y
  `results/` están excluidos por diseño en `.gitignore` (modo *whitelist*: solo
  se versionan notebooks, scripts, presentaciones, documentación y locks). La
  obtención, custodia y tratamiento de esos datos es responsabilidad de quien
  reproduce el material.
- Vulnerabilidades en **dependencias de terceros** (PyTorch, Ollama, CrewAI,
  spaCy, etc.). Repórtalas a sus respectivos proyectos; si afectan al uso que
  hace este repo, avísanos para actualizar la versión fijada.
## Versiones soportadas
 
Al tratarse de material formativo en evolución continua, solo se da soporte a la
última versión de la rama `master`. No se mantienen ramas ni tags anteriores.
 
| Versión              | Soportada |
|----------------------|-----------|
| `master` (HEAD)      | ✅        |
| Commits/tags previos | ❌        |
 
## Cómo reportar una vulnerabilidad
 
**No abras un issue público** para reportar problemas de seguridad.
 
Canal preferente: **GitHub Private Vulnerability Reporting**
 
1. Ve a la pestaña **Security** del repositorio.
2. Pulsa **Report a vulnerability**.
3. Completa el formulario con los detalles.
Esto abre un aviso privado visible solo para ti y para quien mantiene el repo.
 
### Qué incluir en el reporte
 
- Descripción del problema y componente afectado (`src/…`, `scripts/…`, notebook).
- Pasos para reproducir o prueba de concepto.
- Impacto potencial.
- Commit / versión y entorno (SO, versión de Python, librerías relevantes).
- Cualquier mitigación que hayas identificado.
### Qué esperar
 
Es un proyecto mantenido de forma individual con fines educativos, así que los
plazos son *best-effort*:
 
- **Acuse de recibo:** ~5 días laborables.
- **Evaluación inicial:** ~15 días laborables.
- **Divulgación coordinada:** acordaremos una fecha una vez exista corrección o
  mitigación. Se te dará crédito si lo deseas.
## Datos sensibles y privacidad
 
Por su temática, este repositorio gravita en torno a material especialmente
sensible (credenciales, PII de brechas, comunicaciones de grupos criminales,
foros de radicalización). Por eso:
 
- **El repo no contiene datos reales**, y no deben añadirse.
- **Nunca hagas commit** de datasets, volcados, credenciales, claves de API ni
  PII. Antes de subir cambios, revisa `git status` y mantén activadas la
  *secret scanning* y la *push protection* del repositorio.
- Si detectas que se ha filtrado por error algún dato sensible en el historial,
  trátalo como incidente de seguridad y repórtalo por el canal privado de arriba
  para poder purgar el historial.
## Uso responsable
 
El material se publica con fines de **formación, investigación y análisis
forense**, para trabajar sobre datos ya filtrados públicamente y en contextos
legítimos (investigación, docencia, *threat intelligence*). No debe emplearse
para reidentificar o revictimizar a personas afectadas por las brechas, ni para
ningún fin ilícito. La responsabilidad legal del tratamiento de los datos recae
en quien los utiliza y en su base jurídica.
 
## Fuera de ámbito
 
- Los propios conjuntos de datos y su contenido.
- Vulnerabilidades de dependencias de terceros (reportar *upstream*).
- Problemas de configuración del entorno local (Ollama, GPU/CUDA, `uv`, etc.).
---
 
*Última actualización: 2026-07-19*
