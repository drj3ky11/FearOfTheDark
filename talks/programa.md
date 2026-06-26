# CSBC26 — Análisis Forense de Leaks Underground
## Programa de contenidos (~10h)

---

## Bloque 0 — El ecosistema de leaks (45 min)

### De dónde vienen los datos

Los leaks de comunidades underground no aparecen de la nada: siguen patrones bastante predecibles. La mayoría llegan al espacio público a través de tres vías principales. La primera es el **hackeo directo** del foro o servicio: alguien explota una vulnerabilidad en el servidor, extrae la base de datos y la publica como credencial o como represalia. La segunda vía son las **filtraciones internas**: un miembro descontento, un administrador que abandona el proyecto o alguien que quiere notoriedad publica los datos desde dentro. La tercera, menos obvia, son los **repositorios de breaches acumulados**: sitios como RaidForums o BreachForums actuaban como mercados de redistribución donde los leaks circulaban, se intercambiaban y se reempaquetaban durante años.

Una vez en circulación, los datos se difunden por canales bien conocidos: canales de Telegram especializados, foros underground (que a su vez generan sus propios leaks, como veremos), repositorios en dark web y paste sites. Haremos una demo en vivo de algunos de estos canales donde sea seguro mostrarlo directamente.

### Qué se suele encontrar

No todos los leaks son iguales. Lo más común, por orden de frecuencia: **dumps de bases de datos** (el grueso del material), **logs de chat** internos de organizaciones o grupos, **flat files** de credenciales o registros de usuarios, **source code** filtrado de herramientas o paneles, y ocasionalmente **configuraciones** de infraestructura.

**Tier list de utilidad para investigación:**

- **S — Chat logs internos** (Conti, BlackBasta): son comunicaciones sin filtro entre operadores. Revelan estructura, TTPs, roles, conflictos internos. Irremplazables.
- **A — Dumps SQL de foros**: contienen usuarios, posts, IPs, emails, fechas. Permiten análisis de red, atribución, correlación cross-foro.
- **B — Flat files de credenciales**: útiles para pivoting pero pobres en contexto. Sin narrativa.
- **C — Source code / configs**: muy específicos, requieren expertise técnico para extraer valor.

### Formatos y su realidad técnica

Los datos rara vez llegan limpios. El formato más común en foros rusos y underground de los 2000-2020 es **vBulletin SQL**, con encoding cp1251 (cirílico). Hay variantes: prefijos de tabla distintos, columnas explícitas o implicitadas, separadores por tabulación, mezcla de encodings UTF-8 y cp1251 dentro del mismo dump. Los chat logs modernos suelen ser JSON estructurado pero con campos inconsistentes entre plataformas. Los flat files son el formato más caótico: delimitadores arbitrarios, sin schema, calidad variable.

**Tier list de facilidad técnica:**

- **S — JSON estructurado** (Telegram exports, BlackBasta): schema conocido, fácil de parsear.
- **A — vBulletin SQL estándar**: schema predecible, bien documentado, hay parsers.
- **B — vBulletin con variantes**: requiere detección automática de formato y múltiples estrategias de parsing.
- **C — Flat files delimitados**: hay que inferir el schema caso a caso.
- **D — Dumps custom / propietarios**: sin documentación, requieren ingeniería inversa.

---

## Bloque 1 — Técnicas de análisis: Big Data (1h 30min)

### El problema de escala

Los datasets underground no son grandes en el sentido de Hadoop o Spark — estamos hablando de millones de registros, no billones — pero sí presentan los problemas clásicos de big data aplicado a inteligencia: datos sucios, esquemas inconsistentes, duplicados, campos vacíos y texto en múltiples idiomas e idiomas inventados (slang, leetspeak, mezclas). La primera habilidad es aprender a explorar antes de analizar.

### Estadística descriptiva

El punto de partida siempre es entender la forma del dataset: distribución de usuarios por actividad (la curva power-law es universal en foros — el 1% de usuarios genera el 80% del contenido), evolución temporal del foro (cuándo creció, cuándo murió, eventos que marcaron inflexiones), distribución geográfica inferida por timezone, y métricas de densidad de contenido por usuario. Esto no es trivial: un usuario con 1 post puede ser más relevante que uno con 10.000 si ese post es una venta de accesos a infraestructura crítica.

### Análisis de red social

Los foros son grafos. Cada respuesta es una arista dirigida entre dos nodos (usuarios). Con eso se pueden calcular métricas de centralidad: **degree centrality** (quién tiene más conexiones), **betweenness centrality** (quién actúa de puente entre comunidades), y algoritmos de detección de comunidades como Louvain. En contexto forense, esto permite identificar quién es el operador central de una red, quién la conecta con otras redes, y qué subgrupos existen dentro de un foro aparentemente homogéneo.

### Correlación cross-foro y pivoting de identidades

El análisis más potente: cruzar usuarios entre múltiples foros. La hipótesis es que los operadores activos reutilizan usernames, emails o patrones de comportamiento. El proceso es: normalizar identidades (lowercase, eliminar variaciones), buscar coincidencias exactas y fuzzy, y construir un grafo de identidades donde un nodo puede ser el mismo actor en cinco foros distintos bajo cinco nombres distintos. Esto es pivoting de identidad manual — lo que hacen los investigadores antes de escalar con IA.

### Análisis temporal

La dimensión tiempo es frecuentemente ignorada y es de las más ricas. Los patrones horarios revelan timezone real (independientemente del que el usuario declara), los patrones semanales diferencian profesionales (activos en horario laboral) de aficionados, y la evolución anual de un foro muestra su ciclo de vida: crecimiento, madurez, declive por arrestos o competencia. Con OGUsers, que tiene cuatro snapshots entre 2019 y 2022, se puede ver en tiempo casi real cómo una comunidad se fragmenta y reconstituye tras cada brecha.

### Text mining clásico

TF-IDF para identificar términos dominantes por foro y por período. LDA (Latent Dirichlet Allocation) para topic modeling: qué temas discute cada subgrupo, cómo evolucionan los topics a lo largo del tiempo. No requiere GPU ni modelos grandes — es estadística sobre frecuencias de términos, funciona bien incluso con texto ruidoso.

### Idioma original vs. traducción

Los datasets underground son multilingües por naturaleza: ruso, inglés, árabe, español mezclados en el mismo foro. La pregunta de si trabajar en el idioma original o traducir primero tiene una respuesta práctica en Big Data: depende de la herramienta. TF-IDF y LDA operan sobre tokens — si el modelo de tokenización o la lista de stopwords no soporta el idioma del texto, los resultados son basura. Para texto en ruso con TF-IDF en inglés, por ejemplo, las stopwords no se eliminan y los términos más frecuentes son preposiciones y artículos cirílicos sin valor analítico. La solución en Big Data es usar herramientas multilingües (spaCy tiene modelos para +15 idiomas) o traducir antes de aplicar el pipeline. La discusión más profunda sobre este tradeoff — especialmente cuando la fidelidad lingüística importa — se retoma en el Bloque 2.

---

## Bloque 2 — Técnicas de análisis: IA (1h)

### Por qué los métodos clásicos no son suficientes

El text mining clásico trata las palabras como símbolos independientes. Pero en comunidades underground el lenguaje es opaco por diseño: abreviaciones, leetspeak, mezcla de idiomas, eufemismos que cambian semana a semana. Dos posts que hablan de lo mismo pueden no compartir ni una sola palabra. Aquí es donde los embeddings cambian el juego.

### Embeddings: representaciones densas de significado

Un embedding convierte texto en un vector numérico donde la distancia geométrica refleja similitud semántica. "rat" y "trojan" en contexto underground estarán cerca aunque no compartan letras; "password" y "contraseña" también. Esto permite clustering de usuarios por comportamiento de escritura sin depender del vocabulario exacto, y es la base de la estilometría computacional.

El modelo que usamos es `nomic-embed-text` vía Ollama — completamente local, lo cual es **obligatorio** con datos de este tipo. Nunca se mandan leaks a APIs externas.

### Estilometría: la huella digital del escritor

Todo el mundo escribe diferente. La longitud media de oraciones, la frecuencia de signos de puntuación, el uso de mayúsculas, las palabras funcionales preferidas (artículos, preposiciones, conjunciones) — estos rasgos son estables a través del tiempo y difíciles de suprimir conscientemente. La estilometría computacional extrae estos features y los usa para atribución de autoría: ¿este usuario de HackForums es el mismo que este de RaidForums bajo otro nombre?

### NER en dominio específico

Named Entity Recognition estándar (spaCy, BERT) falla en este contexto porque no fue entrenado con texto underground. Pero se puede adaptar: entrenar o fine-tunear para reconocer entidades relevantes del dominio — IPs, dominios, handles, herramientas (Cobalt Strike, Metasploit, nombres de RATs), wallets crypto, nombres de operaciones. Con un LLM local como `qwen2.5:14b` se puede hacer zero-shot NER con prompts específicos, que para volúmenes moderados es suficiente.

### Idioma original vs. traducción (con IA)

Aquí el argumento es más matizado que en Big Data. Los modelos de embeddings multilingües como `nomic-embed-text` o `multilingual-e5` trabajan en un espacio vectorial compartido entre idiomas: un post en ruso sobre exploits y uno en inglés sobre el mismo tema quedarán cerca en ese espacio aunque no compartan ninguna palabra. Esto significa que para **embeddings, clustering y estilometría la regla es clara: trabajar siempre en el idioma original**. Traducir antes de embedear destruye la huella lingüística — que es precisamente lo que queremos preservar para atribución de autoría.

Para **NER y topic modeling con LLMs**, en cambio, los modelos genéricos rinden mejor en inglés. Si el modelo base no tiene suficiente cobertura del idioma original, traducir primero mejora la calidad de extracción. El tradeoff es aceptable porque para NER no nos importa el estilo, solo las entidades.

La regla práctica: **embeddings y estilometría → original siempre. NER y topic modeling con LLM → traducir si el modelo base es predominantemente inglés.**

### LLMs locales: Ollama como infraestructura

La regla es simple: si los datos son sensibles, el modelo es local. Ollama permite correr modelos de lenguaje en hardware modesto (con cuantización Q4/Q8), sin datos que salgan de la máquina. En la demo veremos cómo se lanza, cómo se integra con Python, y por qué la latencia es el tradeoff aceptable frente a la alternativa de mandar leaks a la nube.

---

## Bloque 3 — Setup y demo en vivo (45 min)

### El entorno

Todo el proyecto corre con `uv` — el gestor de dependencias moderno para Python que reemplaza pip/venv/poetry en un solo comando. No requiere instalación de Conda ni entornos virtuales manuales. Un `uv sync` instala todo; un `uv run jupyter notebook` arranca el entorno. El objetivo es que cualquiera pueda replicar el setup en 10 minutos.

Para los modelos, `ollama pull nomic-embed-text` y `ollama pull qwen2.5:14b`. La descarga la lanzaremos en vivo y la cortaremos — los modelos ya estarán descargados para continuar sin esperar. Es el mismo truco que los videotutoriales de instalación de software: se muestra el proceso, se salta la espera.

### El pipeline completo

La demo recorre el pipeline de principio a fin usando los datos de Carding Forums (ya procesados):

1. **Load**: `load_forum()` con auto-detect de formato y encoding
2. **Normalize**: limpieza de usuarios, deduplicación, normalización de fechas a UTC
3. **Analyze**: estadística descriptiva, red de interacciones, análisis temporal
4. **Embed**: generación de embeddings por usuario (precomputados, se muestra el código y se ejecuta sobre una muestra pequeña)
5. **Visualize**: grafos, heatmaps temporales, clusters

Todo desde un único notebook de Jupyter, celda por celda, sin cambiar de herramienta.

### Requisitos de hardware

No hace falta potencia. Un portátil con 8GB RAM corre sin problemas todo el análisis pandas/networkx/matplotlib. Los embeddings en CPU son lentos para el dataset completo (razón por la que se precomputan) pero en demo con 1.000 usuarios son inmediatos. Para `qwen2.5:14b` con cuantización Q4 se recomiendan 16GB RAM, pero la demo de NER también puede correr sobre una muestra.

---

## Bloque 4 — Casos prácticos (5h)

### Caso 1 — Hacking Forums: identidad y tiempo (1h 40min)

**Dataset**: subconjunto curado de Hacking Forums — RaidForums (2020), BreachForums (2022, 2023), OGUsers (2019, 2020, 2021, 2022).

**Narrativa**: OGUsers era la comunidad más activa de robo y venta de handles de redes sociales ("OG usernames"). Fue brecheada cuatro veces en tres años. Esto nos da algo único: una serie temporal de la misma comunidad, lo que permite ver cómo evoluciona tras cada exposición — qué usuarios desaparecen, quiénes migran a RaidForums o BreachForums, cómo se reconstituye la red.

**Análisis**: 
- Estadística descriptiva comparada entre los cuatro snapshots de OGUsers
- Pivoting cross-foro: usuarios de OGUsers que reaparecen en RaidForums/BreachForums bajo el mismo o distinto handle
- Grafo de evolución temporal: cómo cambia la estructura de la red tras cada brecha
- Estilometría para confirmar identidades cruzadas

**Conclusión**: demostrar que una identidad underground no muere con una brecha — migra.

---

### Caso 2 — Ransomware: anatomía de una organización criminal (1h 40min)

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

### Caso 3 — IronMarch: radicalización y red social (1h 40min)

**Dataset**: IronMarch (dump 2019, foro activo 2011-2017).

**Narrativa**: IronMarch fue el principal foro de neonazis aceleracionsitas en habla inglesa. Fue desmantelado en 2017 y su base de datos filtrada en 2019. Lo que hace este dataset único es que varios de sus miembros son ahora individuos **públicamente identificados** vinculados a ataques terroristas reales — lo que permite validar el análisis con ground truth conocida.

**Análisis**:
- Grafo de interacciones: identificar los nodos de mayor influencia en la red de radicalización
- Evolución temporal: cómo creció la comunidad y qué eventos externos correlacionan con picos de actividad
- NER: extracción de personas, organizaciones y eventos mencionados, cruzado con información pública
- Clustering por embeddings: identificar subgrupos ideológicos dentro del foro
- Estilometría: atribución de posts anónimos a usuarios conocidos

**Conclusión**: la red social de un foro extremista no es homogénea — hay brokers de radicalización identificables computacionalmente.

---

*Total estimado: ~10h | Formato: bloque teórico + demo en vivo + caso práctico por sesión*
