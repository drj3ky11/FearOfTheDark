# Enfoque de los 4 casos prácticos

Documento de trabajo, no material de curso. Objetivo: que cada caso gire en torno
a **una pregunta y una técnica protagonista**, y que la mayoría de las 1h40 de
cada sesión se dedique a explicar bien esa técnica (el porqué y el para qué),
no a repetir limpieza/EDA genéricos que ya se vieron en los bloques teóricos.

## Matriz de 4 casos — sin solapes

| Caso | Pregunta que responde | Técnica protagonista |
|---|---|---|
| Ransomware | ¿Cómo se organiza jerárquicamente un grupo criminal? | Clasificación de roles con LLM + similitud de embeddings entre grupos (linaje) |
| IronMarch | ¿Quién influye más en la red? | Centralidad/brokers + validación contra ground truth judicial |
| HackingForums | ¿Una identidad sobrevive a una brecha, o migra? | Persistencia temporal cross-foro + atribución multi-señal |
| CardingForums | ¿Cómo se reparte el trabajo en un mercado sin jerarquía única? | Comunidades (Leiden) + topics por comunidad → especialización de mercado |

La distinción que sostiene esto: Ransomware mira una organización jerárquica,
IronMarch mira quién influye más — es un foro ideológico, no de mando, la
gente se influye y retroalimenta y luego suele actuar de forma aislada —,
HackingForums mira si una persona persiste en el tiempo, Carding mira cómo se
divide el trabajo en un mercado sin jerarquía. Evita que "grafos" o
"embeddings" se sientan como la misma lección repetida cuatro veces — la
pregunta y la conclusión cambian en cada caso, aunque alguna herramienta se
reutilice.

---

## Auditoría de contenido — ¿hay suficiente para profundizar?

Verificado contra los notebooks reales y `results/`, no solo contra las
diapositivas:

| Caso | Notebook protagonista | Código | Resultados precomputados |
|---|---|---|---|
| CardingForums | `02_analisis_estructural` + `03_analisis_semantico` | 12+16 celdas | Sí — `02_centrality.parquet`, `03_user_embeddings.npz` (150MB), viz reales |
| HackingForums | `03_analisis_semantico` | 14 celdas | Sí — embeddings, centroides muestreados, gráficos de persistencia |
| IronMarch | `02_analisis_estructural` + `03_analisis_semantico` | 12+20 celdas | Sí — 5 variantes de embeddings/muestreo ya ejecutadas, NER comparado |
| Ransomware | `comparative/01_cross_group_similarity` + `02_llm_analysis` por grupo | 10-14 celdas c/u | No hay `data/` ni `results/` en el repo — sin verificar ejecución end-to-end |

**Pregunta**: si el pipeline de ransomware se ha corrido de punta a punta en
algún entorno y si los números del `GUION_TALLER.md` (matriz de cohesión
0.914, etc.) vienen de una ejecución real reproducible, o si aún falta
correrlo.

**Formato de notebook**: no dejar código en blanco para rellenar en vivo — con
LLM local (25-30 min por clasificación) no da tiempo en 1h40. Mejor: notebook
completo con lo costoso ya precomputado, y checkpoints de "punto de discusión"
(el patrón que ya usa el guion de ransomware) donde interpretan resultados
reales y, como mucho, tocan 2-3 líneas de pandas al final de la sección
protagonista.

**Presupuesto horario**: el README declara Bloque 4 = 5h para 3 casos × 1h40.
Si CardingForums pasa a caso completo, son 6h40 solo en casos prácticos.
Decidir: ¿se acorta cada caso a ~1h15, o Carding se queda con un formato más
ligero (su rol actual en el README es "demo en vivo del Bloque 3", no caso con
sesión propia)?

---

## Desarrollo por caso

### Ransomware — anatomía de una organización

**Profundizar de verdad — pieza única, no aparece en ningún otro sitio**:
el parsing del formato Jabber (NDJSON "roto": objetos JSON concatenados sin
comas ni array wrapper, hay que iterar con `JSONDecoder.raw_decode()` en vez
de `json.loads()`). Ni los bloques teóricos ni los otros tres casos tocan un
formato tan mal formado como este — si se resume o se salta, esta técnica
concreta desaparece del taller entero.

**Resumir, no profundizar**:
- Limpieza general (dedup, vacíos, normalización de username) — mismo patrón
  que ya se ve en Carding/Hacking/IronMarch.
- Detección de idioma con `langdetect` — la implementación concreta (muestreo,
  truncado, decisión por foro) ya se profundiza en HackingForums. Aquí basta
  mencionar de pasada el matiz nuevo: búlgaro/macedonio se confunden con ruso
  por proximidad lingüística.

**Profundizar (protagonista)**:
- Por qué LLM y no reglas/keywords para clasificar rol de un mensaje —
  el lenguaje es ambiguo, depende de contexto, está en ruso con jerga.
- Por qué centroides L2-normalizados por actor y no comparar mensajes
  sueltos — reduce ruido, captura el "estilo medio" de la persona en vez de un
  mensaje aislado no representativo.
- Para qué sirve la matriz de cohesión 4×4 — validar o refutar con evidencia
  semántica (no solo cronológica) la hipótesis de que BlackBasta es una
  escisión/sucesión directa de Conti.
- Matiz metodológico crítico a remarcar siempre: similitud alta no prueba
  identidad, solo estilo/argot compartido. Ya está en el guion — no se puede
  perder al resumir.

### IronMarch — quién influye más

**Reducir**: reconocimiento/limpieza genéricos, BERTopic (apoyo, no protagonista).

**Profundizar**:
- Por qué degree Y betweenness, no solo uno — degree mide alcance directo,
  betweenness mide de quién depende que dos subgrupos que si no, no se
  hablarían entre sí. Son dos formas de influencia distintas.
- Por qué betweenness se calcula por muestreo (k=500) y no exacto — coste
  computacional en grafos grandes, trade-off precisión/tiempo a explicar.
- Para qué sirve comparar red pública (posts) vs. privada (PMs) — este es el
  corazón pedagógico: el usuario 255 tiene 53% del betweenness en PMs pero es
  invisible en la actividad pública. Influencia visible ≠ influencia
  estructural real.
- Para qué sirve el ground truth judicial — es la única vía del curso para
  demostrar que el análisis computacional dice la verdad, no solo produce un
  grafo bonito sin forma de verificarlo.

### HackingForums — identidad y tiempo

**Reducir**: EDA comparativo, limpieza epoch-0 (ya visto en Carding).

**Profundizar**:
- Por qué 4 snapshots de la misma comunidad (OGUsers), no solo comparar dos
  foros distintos una vez — permite ver evolución tras cada brecha, no una
  foto fija.
- La detección de idioma con `langdetect` (muestreo, truncado, decisión por
  foro) tiene aquí su desarrollo completo — es la referencia del taller para
  esta técnica; los demás casos solo la mencionan de pasada.
- Por qué ninguna señal sola basta — handle es trivial de cambiar, embeddings
  solos no distinguen argot compartido de identidad compartida. Justifica el
  score combinado.
- Por qué Burrows' Delta específicamente — palabras función (no vocabulario
  de contenido) es la técnica de atribución de autoría más resistente a que
  el autor cambie de tema o de plataforma.
- Para qué sirve el trade-off exacto vs. fuzzy matching — la tensión
  precisión/cobertura que aparece en cualquier pivoting real de threat intel.

### CardingForums — anatomía de un mercado

**Reducir**: la ingeniería de datos (dump duplicado, flat file, cp1251) sirve
de gancho de apertura breve — explica por qué el dataset es fiable — pero no
es el "para qué" central del caso. Quitar o bajar a una sola mención de
contraste: el perfilado LLM de roles individuales (es exactamente lo que hace
Ransomware con otro vocabulario).

**Profundizar**:
- Por qué Leiden y no k-means u otro clustering sobre el grafo — optimiza
  modularidad, encuentra comunidades naturales sin fijar K de antemano, y
  escala a grafos grandes.
- Por qué filtrar aristas de un solo thread compartido antes de correr Leiden
  — sin filtrar, aparecen comunidades falsas por coincidencias triviales.
- Para qué sirve cruzar comunidad de red con topics de contenido (TF-IDF/
  BERTopic por subforo) — confirma que las comunidades estructurales
  corresponden a especialización real del mercado (vendedores de dumps vs.
  cashers vs. tutoriales), no es un artefacto del grafo.
- Se puede mencionar de pasada la comunidad mixta (varios foros) como
  candidata a red cross-foro, pero sin repetir en profundidad la atribución
  de HackingForums — es solo una nota, no el hilo conductor.
