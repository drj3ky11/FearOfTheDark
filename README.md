# CSBC26 — Fear Of The Dark

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](LICENSE)
![PyTorch](https://img.shields.io/badge/PyTorch-2.4.1-orange) 
![CUDA](https://img.shields.io/badge/CUDA-12.4-green)

Python, Big Data, IA y rock & roll!!!!

![portada](/images/fearofthedark.png)

Curso de ~10h sobre análisis de datos filtrados de comunidades underground (foros de hacking, carding y grupos de ransomware) mediante técnicas de Big Data e IA con LLMs locales.


---

## Estructura del repositorio

### Bloques teóricos (Bloques 0-4)

| Bloque | Contenido | Duración |
|---|---|---|
| [`bloque0_ecosistema/`](bloque0_ecosistema/) | De dónde vienen los leaks, qué se suele encontrar, formatos y su realidad técnica | 45 min |
| [`bloque1_bigdata/`](bloque1_bigdata/) | Estadística descriptiva, análisis de red social, pivoting cross-foro, análisis temporal, text mining clásico | 1h 30min |
| [`bloque2_ia/`](bloque2_ia/) | Embeddings, estilometría computacional, NER en dominio específico, LLMs locales con Ollama | 1h |
| [`bloque3_setup/`](bloque3_setup/) | Setup del entorno: `uv`, Ollama (qué es, para qué se usa) y el stack de librerías del proyecto | 45 min |
| [`bloque4_agentes/`](bloque4_agentes/) | Orquestación de agentes IA con CrewAI y Ollama — del clasificador al equipo de agentes | 45 min |

Cada bloque incluye su presentación (`.pptx`) y, donde aplica, un notebook de demostración.

### Casos prácticos (Bloque 5)

Los casos son independientes entre sí y no repiten limpieza/EDA genéricos — cada uno gira en torno a **una pregunta y una técnica protagonista** distinta, para que las horas de sesión no se dupliquen entre casos.

| Caso | Pregunta que responde | Técnica protagonista | Duración |
|---|---|---|---|
| [`bloque5_hackingforums/`](bloque5_hackingforums/) | ¿Una identidad underground sobrevive a una brecha, o migra? | Atribución cross-foro multi-señal (handle + embeddings + Burrows' Delta) | 1h 40min |
| [`bloque5_ransomware/`](bloque5_ransomware/) | ¿Cómo se organiza jerárquicamente un grupo criminal? | Clasificación de roles con LLM + similitud de embeddings entre grupos | 1h 40min |
| [`bloque5_ironmarch/`](bloque5_ironmarch/) | ¿Quién influye más en una red de radicalización? | Centralidad (degree + betweenness) validada contra ground truth judicial | 1h 40min |
| [`bloque5_cardingforums/`](bloque5_cardingforums/) | ¿Cómo se reparte el trabajo en un mercado sin jerarquía única? | Comunidades (Leiden) + cruce con topics de contenido | 1h 40min |

Cada caso sigue la misma estructura de 5 notebooks (`00_reconocimiento` → `04_sintesis_informe`), tiene su propia presentación y su `README.md` con el objetivo del caso, el detalle de datasets y los hallazgos.

### Librería del proyecto

| Carpeta | Contenido |
|---|---|
| [`src/`](src/) — [ver `src/README.md`](src/README.md) | Librería de análisis: parsers de foros (vBulletin, MyBB, IPS, flat files), embeddings, estilometría, utilidades de timezone |
| [`scripts/`](scripts/) — [ver `scripts/README.md`](scripts/README.md) | Ejecutables CLI que usan `src/` para precomputar resultados pesados (embeddings, centroides, NER) fuera del notebook |

---

## Programa de contenidos (~10h)

### Bloque 0 — El ecosistema de leaks (45 min)

#### De dónde vienen los datos

Los leaks de comunidades underground no aparecen de la nada: siguen patrones bastante predecibles. La mayoría se originan de dos formas: 
- **Hackeo directo** del foro o servicio: alguien explota una vulnerabilidad en el servidor, extrae la base de datos y la publica como producto o como reivindicación.
- **Filtraciones internas**: un miembro descontento, un administrador que abandona el proyecto o alguien que quiere notoriedad publica los datos desde dentro.
Además de esto, también existen los **repositorios de breaches acumulados**: sitios como eran RaidForums o BreachForums, que actúan como mercados de redistribución donde los leaks circulan, se intercambian y se reempaquetan a lo largo del tiempo.

Tras los primeros momentos de distribución y comercialización, los datos se suelen difundir de forma abierta por todo tipo de canales: grupos de Telegram especializados, foros underground (que a su vez generan sus propios leaks, como veremos), repositorios en dark web y paste sites. Una simple búsqueda en internet puede dar resultados de este tipo.

#### Qué se suele encontrar

No todos los leaks son iguales. Lo más común, por orden de frecuencia: **dumps de bases de datos** (el grueso del material), **logs de chat** internos de organizaciones o grupos, **flat files** de credenciales o registros de usuarios, **source code** filtrado de herramientas o paneles, y ocasionalmente **configuraciones** de infraestructura.

**Tier list de utilidad para investigación:**

- **S — Chat logs internos** (como los ejemplos de Conti y BlackBasta): son comunicaciones sin filtro entre operadores. Revelan estructura, TTPs, roles, conflictos internos. Irremplazables.
- **A — Dumps SQL de foros**: contienen usuarios, posts, IPs, emails, fechas. Permiten análisis de red, atribución, correlación cross-foro.
- **B — Flat files de credenciales**: útiles para pivoting pero pobres en contexto. Sin narrativa.
- **C — Source code / configs**: muy específicos, requieren expertise técnico para extraer valor.

#### Formatos y su realidad técnica

Los datos muy rara vez llegan limpios y preparados para analizar. Hay una gran variedad de formas en las que se pueden encontrar, pero, al ser bases de datos, se suelen encontrar bases SQL o formatos JSON. ¡Ojo!¡El encoding puede no ser UTF-8!

**Tier list de facilidad técnica:**

- **S — JSON estructurado** (por ejemplo, Telegram): schema conocido, fácil de parsear.
- **A — vBulletin SQL estándar**: schema predecible, bien documentado, hay parsers.
- **B — vBulletin con variantes**: requiere detección automática de formato y múltiples estrategias de parsing.
- **C — Flat files delimitados**: hay que inferir el schema caso a caso.
- **D — Dumps custom / propietarios**: sin documentación, requieren ingeniería inversa.

---

### Bloque 1 — Técnicas de análisis: Big Data (1h 30min)

#### El problema de escala

Los datasets underground tampoco es que entren dentro del Big Data — estamos hablando de millones de registros, no billones o trillones — pero sí presentan los problemas de big data (limpieza de datos, duplicados, vacíos, etc.) y se pueden estudiar de una forma parecida. La primera habilidad es aprender a explorar antes de analizar.

#### Estadística descriptiva

El punto de partida siempre es entender la forma del dataset: distribución de usuarios por actividad (la curva power-law es universal en foros — el 1% de usuarios genera el 80% del contenido), evolución temporal del foro (cuándo creció, cuándo murió, eventos que marcaron inflexiones), distribución geográfica inferida por timezone, y métricas de densidad de contenido por usuario. Esto no es trivial: un usuario con 1 post puede ser más relevante que uno con 10.000 si ese post es, por ejemplo, una venta de accesos a infraestructura crítica.

#### Análisis de red social

Los foros no hay que analizarlos de forma aislada, son comunidades, son personas. Cada respuesta es una relación entre dos nodos (usuarios). Con eso se pueden calcular métricas de centralidad: **degree centrality** (quién tiene más conexiones), **betweenness centrality** (quién actúa de puente entre comunidades), y algoritmos de detección de comunidades como Leiden. En este contexto, permite identificar quién es el operador central de una red, quién la conecta con otras redes, y qué subgrupos existen dentro de un foro aparentemente homogéneo.

#### Correlación cross-foro y pivoting de identidades

El análisis más potente y que veremos muy potenciado con las técnicas del siguiente bloque: cruzar usuarios entre múltiples foros. La hipótesis es que los operadores activos reutilizan usernames, emails o patrones de comportamiento. El proceso es: normalizar identidades (lowercase, eliminar variaciones), buscar coincidencias exactas y fuzzy, y construir un grafo de identidades donde un nodo puede ser el mismo actor en cinco foros distintos bajo cinco nombres distintos. Aquí veremos que, gracias al análisis estilométrico, podemos obtener nuevos resultados y confirmar o rechazar hipótesis.

#### Análisis temporal

La dimensión tiempo es una de las grandes olvidadas y puede dar información de gran relevancia. Los patrones horarios revelan timezone real (independientemente del que el usuario declara), los patrones semanales diferencian profesionales (activos en horario laboral) de aficionados, y la evolución anual de un foro muestra su ciclo de vida: crecimiento, madurez, declive (por ejemplo, por arrestos). Con OGUsers, que tiene cuatro snapshots entre 2019 y 2022, se puede ver en detalle cómo una comunidad se fragmenta y reconstituye tras cada brecha.

#### Text mining clásico

TF-IDF (Term frequency – Inverse document frequency) para identificar términos dominantes por foro y por período. LDA (Latent Dirichlet Allocation) para topic modeling: qué temas discute cada subgrupo, cómo evolucionan los topics a lo largo del tiempo. No requiere GPU ni modelos grandes (que es una ventaja... $$) — es estadística sobre frecuencias de términos, funciona bien incluso con texto ruidoso.

#### Idioma original vs. traducción

Los datasets underground, en muchas ocasiones, son multilingües: ruso, inglés, árabe, español mezclados en el mismo foro (distintas comunidades, mensajes privados, etc.). Aunque se verá el porqué de la negativa a traducir en el siguiente bloque, para este... (en principio) da igual. Se buscan términos, temática, etc., no se busca estilometría. Por lo general, se utilizará el idioma original, pero si el modelo de tokenización o la lista de stopwords no soporta el idioma del texto, trabajar con traducciones está bien. 

---

### Bloque 2 — Técnicas de análisis: IA (1h)

#### Por qué los métodos clásicos no son suficientes

El text mining clásico trata las palabras como símbolos independientes. Pero en comunidades underground el lenguaje es opaco por diseño: abreviaciones, leetspeak, mezcla de idiomas, eufemismos que cambian semana a semana. Dos posts que hablan de lo mismo pueden no compartir ni una sola palabra. Aquí es donde los embeddings cambian el juego.

#### Embeddings: representaciones densas de significado

Un embedding convierte texto en un vector numérico donde la distancia geométrica refleja similitud semántica. "rat" y "trojan" en contexto underground estarán cerca aunque no compartan letras; "password" y "contraseña" también. Esto permite clustering de usuarios por comportamiento de escritura sin depender del vocabulario exacto, y es la base de la estilometría computacional.

El modelo que usamos es `qwen3-embedding` vía Ollama — completamente local, lo cual es **obligatorio** con datos de este tipo. Nunca se mandan leaks a APIs externas.

#### Estilometría: la huella digital del escritor

Todo el mundo escribe diferente. La longitud media de oraciones, la frecuencia de signos de puntuación, el uso de mayúsculas, las palabras funcionales preferidas (artículos, preposiciones, conjunciones) — estos rasgos son estables a través del tiempo y difíciles de suprimir conscientemente. La estilometría computacional extrae estos features y los usa para atribución de autoría: ¿este usuario de HackForums es el mismo que este de RaidForums bajo otro nombre?

#### NER en dominio específico

Named Entity Recognition estándar (spaCy, BERT) falla en este contexto porque no fue entrenado con texto underground. Pero se puede adaptar: entrenar o fine-tunear para reconocer entidades relevantes del dominio — IPs, dominios, handles, herramientas (Cobalt Strike, Metasploit, nombres de RATs), wallets crypto, nombres de operaciones. Con un LLM local como `qwen2.5:14b` se puede hacer zero-shot NER con prompts específicos, que para volúmenes moderados es suficiente.

#### Idioma original vs. traducción (con IA)

Aquí el argumento es más matizado que en Big Data. Los modelos de embeddings multilingües como `qwen3-embedding` o `multilingual-e5` trabajan en un espacio vectorial compartido entre idiomas: un post en ruso sobre exploits y uno en inglés sobre el mismo tema quedarán cerca en ese espacio aunque no compartan ninguna palabra. Esto significa que para **embeddings, clustering y estilometría la regla es clara: trabajar siempre en el idioma original**. Traducir antes de embedear destruye la huella lingüística — que es precisamente lo que queremos preservar para atribución de autoría.

Para **NER y topic modeling con LLMs**, en cambio, los modelos genéricos rinden mejor en inglés. Si el modelo base no tiene suficiente cobertura del idioma original, traducir primero mejora la calidad de extracción. El tradeoff es aceptable porque para NER no nos importa el estilo, solo las entidades.

La regla práctica: **embeddings y estilometría → original siempre. NER y topic modeling con LLM → traducir si el modelo base es predominantemente inglés.**

#### LLMs locales: Ollama como infraestructura

La regla es simple: si los datos son sensibles, el modelo es local. Ollama permite correr modelos de lenguaje en hardware modesto (con cuantización Q4/Q8), sin datos que salgan de la máquina. En la demo veremos cómo se lanza, cómo se integra con Python, y por qué la latencia es el tradeoff aceptable frente a la alternativa de mandar leaks a la nube.

---

### Bloque 3 — Setup del entorno y herramientas (45 min)

#### Gestión de dependencias con `uv`

Todo el proyecto corre con `uv` — el gestor de dependencias moderno para Python que reemplaza pip/venv/poetry en un solo comando. No requiere instalación de Conda ni entornos virtuales manuales. Un `uv sync` instala todo; un `uv run jupyter notebook` arranca el entorno. El objetivo es que cualquiera pueda replicar el setup en 10 minutos. Veremos uso muy básico y lo que importa para utilizar el repositorio.

#### Ollama: el LLM que corre en tu máquina

El curso está preparado para no tener que correr LLMs, está todo lo necesario precomputado. Ollama es una plataforma que permite descargar, administrar y correr modelos de lenguaje directamente en la máquina donde se instale, es decir, utilizar "IA" sin mandar datos a una empresa externa. Descarga el modelo cuantizado (que veremos lo que es), lo carga en memoria y expone un servidor local (`http://localhost:11434`) al que hacer peticiones — igual que a una API en la nube, pero en `localhost`. Es la pieza que hace viable trabajar con datos propios/secretos/privados sin "meterse en líos".

Veremos que vamos a usar dos modelos con propósitos distintos: `qwen3-embedding` para generar embeddings (clustering, estilometría, correlación cross-foro) y `qwen2.5:14b` como LLM generativo (NER, clasificación, perfilado de roles). Ambos se descargan con `ollama pull <modelo>`. Como no se van a procesar los datos durante la clase, no hace falta tenerlos descargados, pero hay que tener en cuenta que entre los dos son unos 9GB (¡Por si os animáis a usarlos y luego no tenéis Internet!).

#### El stack de librerías

`uv sync` instala ~18 dependencias. Además de las genéricas (`pandas`, `matplotlib`, `scikit-learn`), hay un grupo específico del curso que vale la pena entender: `ollama` (cliente Python del servidor local), `umap-learn` (reduce embeddings de alta dimensión a 2D para visualizar clusters), `hdbscan` (clustering por densidad sin fijar K), `bertopic` (topic modeling sobre embeddings), `langdetect` (detección de idioma) y `crewai` (orquestación de agentes, Bloque 4).

#### Requisitos de hardware

Para lo que se va a hacer y con precomputos, no hace falta potencia. Un portátil con 8GB RAM corre sin problemas (aunque lo mismo tarda un poco) todo el análisis pandas/networkx/matplotlib. Los embeddings en CPU son lentos para un dataset completo (razón por la que se precomputan) pero sobre una muestra pequeña (p. ej. 500 mensajes) son inmediatos. Para `qwen2.5:14b` con cuantización Q4 se recomiendan 16GB RAM, aunque parte se han procesado en una de 12GB; una GPU es técnicamente opcional... pero prácticamente necesaria porque acelera muchísimo el computo.

---

### Bloque 4 — Agentes de IA con CrewAI (45 min)

#### Del clasificador al equipo de razonadores

En los bloques anteriores usamos LLMs como herramientas puntuales: le damos un texto y devuelve una etiqueta o un embedding. Un **agente** da un paso más: el modelo tiene un rol, un objetivo y puede tomar decisiones sobre qué hacer a continuación — incluyendo llamar a herramientas externas o pedir información adicional.

Una **crew** (equipo de agentes) permite dividir una tarea compleja entre varios agentes especializados que se pasan el contexto entre sí. El resultado es un sistema que puede razonar, buscar datos y redactar un informe en una sola ejecución.

#### Los tres primitivos de CrewAI

- **`Agent`**: define el rol, el objetivo y el backstory del modelo. El backstory moldea el tono y la especialización de las respuestas.
- **`Task`**: describe qué tiene que hacer el agente y en qué formato debe entregar el resultado.
- **`Crew`**: une agentes y tareas, controla el orden de ejecución (`Process.sequential` o `Process.hierarchical`) y gestiona el flujo de contexto entre tareas.

#### Herramientas (tool-use)

Los agentes pueden invocar funciones Python durante su razonamiento. El LLM decide *cuándo* y *con qué argumentos* llamarlas, leyendo el docstring de cada herramienta. Esto permite que el agente consulte datos reales (pandas DataFrames, bases de datos) en vez de "recordar" datos de su entrenamiento — eliminando alucinaciones en contextos donde la precisión numérica importa.

#### Notebooks

| Notebook | Contenido |
|---|---|
| [`00_conceptos_agentes`](bloque4_agentes/00_conceptos_agentes.ipynb) | Qué es un agente, los tres primitivos de CrewAI, primer agente funcional |
| [`01_crew_investigacion`](bloque4_agentes/01_crew_investigacion.ipynb) | Crew de 3 agentes (investigador → analista → redactor) sobre datos de ContiLeaks |
| [`02_agentes_con_herramientas`](bloque4_agentes/02_agentes_con_herramientas.ipynb) | Tool-use con `@tool`: el agente consulta DataFrames pandas según la pregunta |

Trabaja con los datos ya procesados de ContiLeaks (`data_para_alumnos/`). No requiere regenerar embeddings ni clasificaciones — ejecutable en equipos con recursos limitados.

---

### Bloque 5 — Casos prácticos (~6h40, 4 casos × 1h40)

#### Caso Hacking Forums: identidad y tiempo (1h 40min)

**Dataset**: subconjunto curado de Hacking Forums — RaidForums, Cracked.to, Nulled.io, Exploit.in, y los cuatro snapshots reales de OGUsers (2019, 2020, 2021, 2022).

**Narrativa**: OGUsers era la comunidad más activa de robo y venta de handles de redes sociales ("OG usernames"). Fue brecheada cuatro veces en tres años. Esto nos da algo único: una serie temporal de la misma comunidad, lo que permite ver cómo evoluciona tras cada exposición — qué usuarios desaparecen, quiénes son nuevos, cómo se reconstituye la red. La persistencia real entre los 4 snapshots (111,621 handles de 2019 siguen presentes en 2022, solo 1,332 desaparecen) está verificada contra los datos reales, no estimada.

**Análisis**:
- Persistencia de handles entre los 4 snapshots reales de OGUsers (2019→2022)
- Pivoting cross-foro: usuarios de OGUsers que reaparecen en otros foros bajo el mismo o distinto handle (exacto + fuzzy matching)
- Similitud de embeddings cross-foro como señal complementaria
- Burrows' Delta (estilometría) como tercera señal, resistente a que el actor cambie de tema o de plataforma
- Score combinado: ninguna señal sola basta para confirmar identidad

**Conclusión**: demostrar que una identidad underground no muere con una brecha — migra, y se puede confirmar combinando varias señales independientes.

---

#### Caso Ransomware: anatomía de una organización criminal (1h 40min)

**Dataset**: Conti (chat logs 2020, Jabber 2021-2022, Rocket Chat), BlackBasta (JSON 2025), LockBit (panel DB 2025).

**Narrativa**: en 2022, un investigador ucraniano filtró los chats internos de Conti — la organización de ransomware más prolífica de su momento. Por primera vez se podía ver cómo funcionaba una empresa criminal desde dentro: turnos de trabajo, salarios, jerarquías, discusiones sobre objetivos, conflictos entre departamentos. BlackBasta y LockBit añaden perspectiva temporal y comparativa.

**Análisis**:
- Estructura organizacional inferida de los patrones de comunicación: quién habla con quién, quién toma decisiones
- Análisis de roles por vocabulario y frecuencia de interacción
- Timeline de operaciones correlacionado con ataques conocidos públicamente
- NER: extracción de víctimas, herramientas, infraestructura mencionada
- Comparativa Conti vs BlackBasta: diferencias operacionales

**Conclusión**: el análisis de chat logs revela más sobre la estructura interna de una organización que cualquier análisis de malware.

---

#### Caso IronMarch: radicalización y red social (1h 40min)

**Dataset**: IronMarch (dump 2019, foro activo 2011-2017).

**Narrativa**: IronMarch fue el principal foro de neonazis aceleracionistas en habla inglesa. Fue desmantelado en 2017 y su base de datos filtrada en 2019. Lo que hace este dataset único es que varios de sus miembros son ahora individuos **públicamente identificados** vinculados a ataques terroristas reales — lo que permite validar el análisis con ground truth conocida. Es un foro ideológico, no de mando: sus miembros se influyen y retroalimentan entre sí y luego suelen actuar de forma aislada, así que la pregunta no es quién manda, sino quién influye más.

**Análisis**:
- Centralidad (degree + betweenness) sobre la red pública y la red privada (mensajes)
- Comparación red pública vs. privada: la influencia visible no siempre coincide con la influencia estructural real
- Evolución temporal: cómo creció la comunidad y qué eventos externos correlacionan con picos de actividad
- NER: extracción de personas, organizaciones y eventos mencionados, cruzado con información pública
- Estilometría (Burrows' Delta) para detectar sockpuppets, validada contra el ground truth judicial

**Conclusión**: la red social de un foro extremista no es homogénea — hay brokers de influencia identificables computacionalmente, y el liderazgo visible no siempre coincide con quién realmente conecta la red.

---

#### Caso CardingForums: anatomía de un mercado (1h 40min)

**Dataset**: 10 dumps de foros de carding (2009–2021), el mayor volumen del curso (~950K usuarios, ~1.5M posts).

**Narrativa**: a diferencia de HackingForums (identidad que persiste) o IronMarch (quién influye), CardingForums no tiene una jerarquía ni una comunidad única — es un mercado de fraude financiero repartido en foros independientes a lo largo de más de una década. La pregunta no es quién manda ni quién es quién, sino cómo se organiza el trabajo dentro de un mercado sin mando central.

**Análisis**:
- Comunidades (Leiden, no k-means) sobre la red de co-participación — no fija K de antemano y escala a grafos de decenas de miles de nodos
- Filtrado de aristas de un solo thread compartido antes de detectar comunidades, para evitar fusiones espurias
- Cruce de la comunidad de red con los topics de contenido (TF-IDF/BERTopic) para confirmar especialización real (vendedores de dumps, cashers, tutoriales) y no un artefacto del grafo
- El perfilado de roles individuales con LLM se explora en el notebook pero se profundiza en el caso Ransomware, no aquí

**Conclusión**: se puede mapear la anatomía completa de un mercado criminal — quién se especializa en qué — sin necesitar perfilar a cada actor individualmente.

---

*Total estimado: ~10h de bloques teóricos + demo, más ~6h40 de casos prácticos (4 × 1h40, pendiente de ajustar) | Formato: bloque teórico + demo en vivo + caso práctico por sesión*

---

## Dataset

Los datos de origen se distribuyen fuera del repositorio por razones éticas y de tamaño. Se proporciona acceso por vías alternativas a los alumnos.

Estructura esperada en local:

```
csbc26/
└── data/                ← no incluido en el repo (.gitignore)
    ├── Carding Forums/
    ├── Hacking Forums/
    └── ransomware/...   ← cada módulo de ransomware/ tiene su propio data/raw local
```

---

## Requisitos generales

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) como gestor de dependencias
- [Ollama](https://ollama.com) corriendo en local — **solo necesario si vas a regenerar embeddings, NER o clasificación desde cero**; si usas los artefactos ya precomputados, no hace falta

```bash
uv sync
uv run jupyter notebook

# Solo si vas a recalcular embeddings/NER en vez de usar los precomputados:
ollama pull qwen3-embedding    # embeddings semánticos
ollama pull qwen2.5:14b        # NER, perfilado y clasificación LLM
```

### Sin `git` instalado

Si el puesto no tiene `git` (p. ej. equipos de aula con solo navegador + Anaconda), no hace falta clonar: descarga el repositorio como ZIP desde GitHub — botón **Code → Download ZIP** en https://github.com/drj3ky11/FearOfTheDark, o directamente:

```
https://github.com/drj3ky11/FearOfTheDark/archive/refs/heads/master.zip
```

Descomprímelo y copia dentro las carpetas `data/` y `results/` que te haya distribuido la organización (no vienen en el ZIP, ver [Dataset](#dataset)).

---

## Ética y uso responsable

Este material se distribuye exclusivamente con fines académicos y de threat intelligence. Los datasets utilizados son leaks públicamente documentados por investigadores de seguridad. Queda prohibido:

- Redistribuir los datos originales
- Intentar descifrar hashes presentes en los dumps
- Usar la infraestructura identificada (C2, BTC) para ningún propósito

---

## Licencia

[Creative Commons BY-NC-SA 4.0](LICENSE) — libre para uso académico y educativo, sin fines comerciales, con atribución.
