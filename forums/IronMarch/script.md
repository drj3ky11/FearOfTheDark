El tercer caso es diferente a los anteriores en un aspecto fundamental. En los casos de hacking forums y ransomware, estábamos analizando actividad criminal económica — robo de handles, extorsión, cibersecuestro de datos. En IronMarch estamos analizando un vector de radicalización que termina en violencia física.

Eso cambia el tono. No porque el análisis técnico sea distinto — es exactamente el mismo stack, los mismos algoritmos — sino porque el "para qué" tiene un peso diferente.

---

IronMarch estuvo activo entre 2011 y 2017. Era el principal foro de neonazis aceleracionistas en habla inglesa. "Aceleracionismo" es la ideología que plantea que el colapso del sistema occidental es deseable y que hay que acelerarlo para poder reconstruir algo diferente. No es una posición marginal en el extremismo moderno — es la base ideológica de varios de los grupos más violentos de la última década.

El foro fue fundado por un ruso que operaba bajo el seudónimo Slavros. Tenía alrededor de 2.000 miembros registrados y más de 150.000 posts en seis años de actividad. En términos de tamaño, no era el foro extremista más grande. En términos de impacto, es uno de los más documentados como punto de origen de violencia real.

En noviembre de 2017, el fundador cerró el foro abruptamente sin dar explicaciones. Dos años después, en noviembre de 2019, un hacker filtró la base de datos completa. Incluye usuarios, posts públicos, mensajes privados y perfiles completos.

---

El elemento que hace este dataset único en el campo del análisis de extremismo es el ground truth.

En la mayoría de los casos, cuando analizamos un foro — de hacking, de ransomware, de cualquier tipo — no sabemos quiénes son los usuarios en la vida real. El análisis puede identificar nodos centrales, clusters, brokers. Pero no podemos verificar si esos nodos corresponden a personas que luego hicieron cosas concretas.

Con IronMarch, tenemos verificación. Periodistas de Vice, ProPublica y otros medios investigaron quiénes eran los miembros de Atomwaffen Division — un grupo terrorista que surgió directamente de IronMarch. Varios de sus fundadores y miembros fueron identificados públicamente, algunos arrestados. Sus perfiles en IronMarch fueron correlacionados con nombres reales.

Eso nos permite hacer algo que es relativamente raro en este tipo de análisis: preguntar si el algoritmo llega a los mismos nodos que los investigadores llegaron manualmente. Si betweenness centrality pone en el top 10 a alguien que sabemos fue un broker de reclutamiento en Atomwaffen — el modelo funciona. Si no llega — hay que entender por qué no.

Aclaración importante antes de abrir el notebook: en el análisis vamos a trabajar con IDs internos del foro, no con nombres reales. La validación contra ground truth se hace contra una lista pre-procesada. El objetivo es verificar el algoritmo, no construir un perfil público de personas identificadas.

---

El mapa del análisis tiene cinco dimensiones.

La primera es el grafo de interacciones. Quién responde a quién, quién cita a quién, quién inicia los threads con más respuestas. A partir de eso calculamos degree centrality — quién tiene más conexiones directas — y betweenness centrality — quién actúa de puente entre grupos dentro del foro.

La segunda es evolución temporal. IronMarch existió seis años. No creció de manera uniforme. Hubo picos de actividad que queremos correlacionar con eventos externos — ataques terroristas, eventos políticos, publicaciones de manifiestos. La pregunta: ¿qué empuja el reclutamiento hacia arriba?

La tercera es NER. Extracción de personas, organizaciones, eventos y lugares mencionados en los posts. Cruzado con información pública para mapear el ecosistema de referencias del foro — qué figuras citaban, qué textos mencionaban, qué organizaciones externas aparecían.

La cuarta es clustering por embeddings. ¿El foro era ideológicamente homogéneo o había subgrupos con diferencias detectables? Los embeddings agrupan a los usuarios por similitud en el estilo y contenido de lo que escribían. Si hay clusters claros, es evidencia de que la comunidad no era monolítica.

La quinta es estilometría. Algunos posts en el foro no tienen firma clara o provienen de usuarios con poca actividad. Con los embeddings del estilo de escritura podemos preguntar: ¿este post anónimo se parece al vector de algún usuario conocido?

---

La conclusión que buscamos demostrar es esta: la red de radicalización de IronMarch no era homogénea, y los brokers — los nodos que conectaban a personas nuevas con el núcleo ideológico — son identificables computacionalmente.

Eso es contraintuitivo. El instinto sería buscar al usuario más activo, el que tiene más posts, el que domina más threads. Pero ese usuario ya está en el núcleo. El que importa para entender cómo crecía la red es el que estaba entre el núcleo y la periferia — el que traía gente de afuera y la integraba adentro.

Eso es betweenness centrality. Y es exactamente lo que el análisis de red puede encontrar de manera computacional donde un investigador humano tardaría semanas.

[ABRIR NOTEBOOK]
