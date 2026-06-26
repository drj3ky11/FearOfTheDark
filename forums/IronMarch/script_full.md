Bueno, arrancamos con el Caso 3, y este es distinto a los anteriores. No estamos hablando de carding ni de hacking. Estamos hablando de un foro neonazi, y eso requiere que ajustemos el modo en que nos paramos frente a los datos. No porque el análisis técnico cambie mucho — de hecho van a ver que las herramientas son prácticamente las mismas. Sino porque el contexto importa, y este contexto tiene peso.

IronMarch fue el principal foro de aceleracionismo neonazi en habla inglesa. Estuvo activo entre 2011 y 2017, y lo que lo hace relevante para nosotros no es solo que haya leakeado — es que varios de sus miembros terminaron en investigaciones judiciales reales. Hay personas en ese dump que están vinculadas a asesinatos. Eso cambia la naturaleza del análisis.

Empecemos por entender de qué se trata ideológicamente, porque si no entienden el contexto no van a poder interpretar lo que encuentren en los datos.

El aceleracionismo neonazi no es el nazismo clásico de Mein Kampf. El nazismo clásico tenía un objetivo político: tomar el estado, construir un reich. El aceleracionismo dice que eso es imposible dentro del sistema actual, y que la única salida es colapsar el sistema. No ganar políticamente, sino destruir las instituciones. La violencia no es un medio hacia un fin político, es el fin en sí mismo — el acelerador del colapso.

El texto fundacional es Siege, de James Mason, de 1992. Es una compilación de panfletos que básicamente argumenta que el movimiento de derecha perdió porque intentó jugar dentro de las reglas del sistema. La propuesta alternativa es la guerra de guerrillas individual, sin estructura organizativa que pueda ser infiltrada o desmantelada. Lo que hoy llamaríamos "lone wolf", pero sistematizado como estrategia.

IronMarch fue el punto de convergencia online de esta ideología en el mundo angloparlante. Y a diferencia de otros foros, tenía una cultura de rigor ideológico. No era un lugar para publicar memes — era un lugar donde se esperaba que defendieras tu posición con argumentos. Eso generó una comunidad pequeña pero extremadamente radicalizada.

El fundador, Alexander Slavros, era un ciudadano ruso que operaba desde Moscú. El foro cerró en noviembre de 2017 sin explicación pública. Dos años después, en noviembre de 2019, la base de datos completa se filtró. Y ahí entramos nosotros.

De IronMarch emergió Atomwaffen Division — un grupo que está vinculado a al menos cinco asesinatos en Estados Unidos entre 2017 y 2019. Los miembros de Atomwaffen se reclutaron en el foro. Las conversaciones previas al reclutamiento están, posiblemente, en ese dump. Eso es lo que hace este dataset excepcional desde el punto de vista forense: la distancia entre el foro y la violencia real es documentable.

Ahora, los datos. El archivo se llama IronMarch_2019.11.zip, pesa 191 megabytes comprimido, y es un dump de vBulletin SQL en UTF-8, igual que los casos anteriores. El mismo parser que escribimos para carding lo levanta sin modificación. Eso no es casualidad — es el resultado de haber diseñado el parser correctamente desde el principio.

El dataset tiene usuarios, posts, mensajes privados, hilos, secciones del foro y campos de perfil extendidos. Lo que lo diferencia de un dump de carding o hacking es que acá el contenido del texto importa mucho más. En carding nos interesaban los metadatos — quién, cuándo, con quién. En IronMarch lo que dicen los posts es central para entender la red.

Hay una cosa que quiero decir explícitamente antes de arrancar la demo, y la voy a repetir durante la sesión: no copiar texto de este foro, no citarlo fuera de contexto, no compartir screenshots de posts individuales. El análisis es legítimo porque es forense y académico. Pero la reproducción del contenido de odio fuera de ese contexto no tiene ningún valor analítico y sí tiene daño potencial. Los datos se quedan en la máquina. Los resultados agregados — grafos, métricas, distribuciones — son los que se pueden compartir.

El stack técnico es idéntico a los casos anteriores: uv, Jupyter, Ollama corriendo local. La única diferencia es que acá la razón de usar local es doble. Primero, los datos son sensibles. Segundo, mandar texto de odio explícito a APIs externas viola los términos de servicio de todas las plataformas y los expone a contenido que no deberían ver. Ollama resuelve ambos problemas.

Ahora sí, las técnicas. Vamos a usar cinco encadenadas, y el orden tiene lógica.

Primero, construimos el grafo de interacciones. Cada vez que un usuario responde un post de otro usuario, eso es una arista en el grafo. La columna parentid de la tabla post nos permite reconstruir esa estructura completa. Calculamos betweenness centrality sobre el grafo no dirigido.

Y acá viene el resultado contraintuitivo que quiero que lleven de esta sesión. La intuición naive dice que el que más postea es el más influyente. La realidad computacional dice que el que conecta grupos es el más influyente estructuralmente. En un foro que tiene secciones ideológicamente diferenciadas — y IronMarch las tenía — los brokers son los usuarios que participan en múltiples secciones, no solo en una. Un usuario con cincuenta posts muy distribuidos entre secciones distintas puede tener mayor betweenness que alguien con dos mil posts todos en el mismo subforo.

Esto tiene consecuencias prácticas. Si están priorizando a quién mirar más de cerca en una investigación, el top poster en "Debate ideológico" puede ser un echo chamber sin influencia real fuera de esa burbuja. El broker entre "Reclutamiento" y alguna sección de coordinación de actividades reales es el nodo crítico.

Segundo, el análisis temporal. Graficamos posts por mes de 2011 a 2017 y marcamos eventos externos conocidos: el ataque de Breivik en Utøya en julio de 2011, el ataque en Charleston en junio de 2015, la elección de Trump en noviembre de 2016, Charlottesville en agosto de 2017. La hipótesis es que el foro respondía activamente al entorno. La correlación no implica causalidad, pero sí nos dice algo sobre cómo la comunidad procesaba las noticias del mundo real.

El heatmap de actividad por hora UTC y día de la semana nos da información geográfica sin tener que inferir timezones individualmente. Si la actividad se concentra en ciertos horarios, eso nos dice dónde estaban los usuarios.

Tercero, NER zero-shot con Ollama usando qwen2.5:14b. El NER estándar de spaCy o BERT no sirve acá porque no fue entrenado con texto extremista ni con la jerga del movimiento. Así que le pedimos al modelo que extraiga entidades con un prompt que le da el contexto del dominio. Los tipos de entidades que nos interesan son PERSON, ORGANIZATION, LOCATION, EVENT, IDEOLOGY y WEAPON. El output es JSON por post, lo agregamos, y obtenemos la frecuencia de cada entidad en el corpus.

La limitación honesta acá es que el NER en texto de odio produce falsos positivos. Palabras comunes en ese vocabulario pueden ser interpretadas como entidades. Los resultados requieren revisión manual antes de cualquier conclusión. Son una herramienta de priorización, no una lista definitiva.

Cuarto, clustering por embeddings. Usamos nomic-embed-text para convertir el corpus de posts de cada usuario en un vector de 768 dimensiones. UMAP reduce esas 768 dimensiones a 2 para visualización. El scatter plot resultante muestra clusters: grupos de usuarios con vocabulario y estilo de escritura similar. Esto nos dice que IronMarch no era ideológicamente homogéneo, lo cual es un resultado en sí mismo. Había facciones. Grupos con agendas diferenciadas dentro del mismo foro.

Quinto, estilometría. El objetivo es atribuir posts anónimos o bajo pseudónimo a usuarios conocidos. La función compare_users del módulo de estilometría genera una matriz de similitud coseno entre usuarios activos. Los pares con similitud mayor a 0.95 son candidatos para atribución o para identidades duplicadas — el mismo actor con dos cuentas distintas.

Y acá es donde el ground truth entra con fuerza. Si el modelo atribuye un post a un usuario X, y X es una persona públicamente identificada en un caso judicial, eso no solo resuelve la atribución — valida el método. Si el modelo no lo encuentra, entendemos los límites de la técnica.

La conclusión principal de este caso es que la red de radicalización de IronMarch tiene estructura hub-and-spoke. No es una red plana donde todos se conectan con todos. Hay un pequeño conjunto de brokers que son el tejido conectivo de la comunidad. Si se eliminan esos nodos, el grafo se fragmenta. Esto explica cómo funciona la radicalización online: no es exposición uniforme a una comunidad, es acceso mediado por actores específicos que conectan distintos subgrupos.

Las limitaciones del análisis hay que decirlas con claridad. El betweenness con sampling es una aproximación. El ground truth es parcial: no sabemos qué porcentaje de nodos relevantes están identificados públicamente. Las técnicas son herramientas de priorización, no de acusación. Ningún resultado computacional solo es suficiente para identificar a una persona real.

Y las consideraciones éticas específicas de este dataset. El análisis es legítimo en contexto académico y de investigación defensiva. Al publicar resultados, hay que anonimizar: no nombrar individuos salvo que sean ya de conocimiento público. No amplificar: publicar el análisis sin reproducir el texto original. No usar este dataset para propósitos fuera del análisis forense. Y si en algún punto el análisis los lleva a información que parece operacional — información sobre planes actuales o personas en riesgo — el protocolo es parar y consultar, no seguir.

El objetivo de esta sesión es entender cómo opera una red de radicalización online. No construir perfiles, no identificar personas, no amplificar mensajes. Eso es lo que distingue el análisis forense del periodismo amarillista y de la curiosidad no fundamentada.
