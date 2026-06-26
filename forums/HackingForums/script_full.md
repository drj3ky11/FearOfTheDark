Arrancamos el Caso 1. Si el caso de carding fue sobre datos de tarjetas, este es diferente: acá lo que se vende no es plata robada directamente, sino el acceso, las herramientas y los datos que permiten robar a escala. Es una capa más arriba en la cadena de ataque.

Estos foros — OGUsers, RaidForums, BreachForums — son mercados. No de tarjetas, sino de credenciales, de accesos a redes corporativas, de exploits, y en el caso de OGUsers, de algo que puede sonar trivial pero que vale miles de dólares: handles de redes sociales. Un nombre de usuario como arroba nike o arroba j en Instagram o Twitter. Handles que existían desde los primeros días de la plataforma y que nadie reclamó. Cortos, memorables, imposibles de conseguir por vía normal. Eso es un OG username, y había un ecosistema entero dedicado a robarlos y venderlos.

Pasamos a la primera sección: el ecosistema. Quiero que entiendan la diferencia entre lo que hicimos en carding y lo que vamos a hacer acá, porque no es solo una diferencia de contenido — es una diferencia de lógica de negocio criminal.

En carding el producto final era dinero: datos de tarjetas que se convertían en cash. El foro era la infraestructura para esa cadena. Acá el producto es el acceso. Un broker de accesos iniciales compromete una red corporativa y vende la entrada en RaidForums. Un actor de OGUsers roba el handle arroba apple y lo revende por Bitcoin. La reputación técnica dentro del foro vale tanto como el dinero.

OGUsers específicamente: fundado alrededor de 2017, activo durante el boom de Instagram. Su especialidad era el SIM swapping — convencer a un empleado de telecomunicaciones de transferir tu número de teléfono a una SIM que ellos controlan, lo que les da acceso a la autenticación por SMS de cualquier cuenta. Con eso toman el email, con el email toman la cuenta de Instagram, y la cuenta con el handle corto se vende en el foro.

RaidForums y BreachForums son otra cosa: plataformas de redistribución. Cada brecha corporate grande terminaba ahí. Uber, LinkedIn, Facebook, bases de datos de millones de personas — todo circulaba en clearnet, no en dark web. Eso los hacía más accesibles, más rastreables, y eventualmente más vulnerables a law enforcement. El admin de RaidForums, Pompompurin, fue arrestado por el FBI en 2022. BreachForums surgió exactamente para llenar ese vacío, y en 2023 también cayó.

Y ahí está la ironía central de este caso: los distribuidores de leaks ajenos terminan siendo leakeados ellos mismos. Y eso nos da el material de análisis.

Sección dos: los datos. Tenemos siete archivos en total. Cuatro snapshots de OGUsers — 2019, 2020, 2021 y 2022 — y los dumps de RaidForums y BreachForums en dos versiones. Mismo formato que en carding: vBulletin SQL. Mismo parser. Pero hay algo que hace a este dataset completamente único: cuatro fotografías del mismo foro tomadas en distintos momentos de su vida.

Eso no existe en ningún otro dataset underground que conozcamos. Un foro de carding tiene un solo dump, tomado en un momento dado. OGUsers tiene cuatro. Y eso nos permite hacer algo que no podíamos hacer con carding: estudiar la dinámica temporal de una comunidad criminal. Ver cómo reacciona tras cada brecha. Quiénes desaparecen, quiénes se quedan, quiénes cambian de nombre, quiénes migran a RaidForums.

El formato es el mismo vBulletin de siempre, con una complicación adicional: los cuatro snapshots no tienen exactamente el mismo schema. Entre 2019 y 2022 el foro actualizó su versión de vBulletin, lo que cambió la estructura de algunas tablas. Columnas que antes eran implícitas ahora son explícitas. El encoding también cambió entre versiones. El parser base lo maneja, pero necesitamos una capa de normalización encima que garantice que todos los snapshots hablen el mismo idioma antes de poder cruzarlos.

Eso es lo que hace normalize_snapshots: garantiza que todos los snapshots te devuelvan handle_norm, snapshot_year y joindate_epoch como columnas constantes. Sin esa normalización los joins cross-snapshot fallan silenciosamente — y eso es el peor tipo de bug que puede haber en análisis forense, porque produce resultados incorrectos sin ningún error.

Sección tres: la infraestructura. Stack idéntico al de carding. uv, Jupyter, Ollama con nomic-embed-text. No hay nada nuevo acá en herramientas. La diferencia es conceptual: en carding teníamos diez foros distintos con diez schemas distintos. Acá tenemos el mismo foro cuatro veces con un schema que evoluciona. El desafío no es parsear — es normalizar para poder comparar.

Sección cuatro: las técnicas. Vamos con cinco, igual que en carding, pero el énfasis es diferente.

La primera es el análisis temporal de OGUsers. Para cada par de snapshots consecutivos calculamos cuántos handles persisten, cuántos son nuevos y cuántos desaparecen. Son operaciones de conjunto simples — intersecciones y diferencias — pero la pregunta que responden es potente: ¿qué tan resistente es esta comunidad a una brecha? Si el porcentaje de persistencia cae drásticamente tras una brecha, la comunidad entró en pánico. Si se mantiene alto, la comunidad asumió el riesgo y siguió operando. Eso te dice algo sobre la madurez operacional del grupo.

La segunda técnica es el cross-foro identity pivoting. La hipótesis es simple: los actores activos de OGUsers no desaparecen cuando el foro cae — migran a RaidForums o BreachForums. Para encontrarlos hacemos primero un match exacto de handles normalizados. Si arroba killah420 en OGUsers aparece como killah420 en RaidForums, es una señal fuerte. Después hacemos fuzzy matching con SequenceMatcher para capturar variaciones: killah420 y xkillah420x tienen similitud de 0.85 o más y son candidatos. Y cuando disponemos de email o password hash, esas señales son aún más fuertes.

El fuzzy matching es poderoso pero tiene un problema: genera falsos positivos en handles cortos. Dos handles de tres o cuatro caracteres pueden tener similitud alta simplemente por azar. Por eso no es la conclusión — es el filtro de candidatos para la tercera técnica.

La tercera es el análisis de grafo de interacciones. Construimos el grafo de replies para cada snapshot: cada respuesta entre usuarios es una arista. Calculamos centralidad de grado y betweenness centrality — quién está en el centro de la red, quién actúa de puente entre subgrupos. Y lo más interesante: comparamos esas métricas entre snapshots. Si el mismo actor aparece como hub en el grafo de 2019 y en el de 2022, y también aparece como nodo central en el grafo de RaidForums, ese es tu target de mayor interés.

La cuarta técnica es la estilometría. El estilo de escritura es lo más difícil de cambiar conscientemente. Podés cambiar el handle, podés cambiar el email, podés cambiar de foro — pero si seguís escribiendo igual, con las mismas construcciones, las mismas palabras funcionales, el mismo ritmo de puntuación, eso te delata. compare_users() calcula features manuales sobre los posts de cada usuario — sin GPU, sin Ollama. Si dos candidatos del fuzzy matching tienen similitud estilométrica mayor a 0.90, eso confirma el match.

Y la quinta es embeddings más UMAP. nomic-embed-text convierte los posts de cada usuario en un vector de 768 dimensiones que captura no solo el estilo sino el contenido semántico — de qué habla. UMAP reduce eso a 2D para visualización. El resultado es un scatter interactivo donde podés ver clusters de usuarios con comportamiento similar. Los clusters que mezclan handles de OGUsers con handles de RaidForums son exactamente lo que buscamos.

Una aclaración importante antes de la demo: en todos los casos de embeddings para atribución de autoría, trabajamos siempre en el idioma original. La traducción destruye la huella lingüística que es exactamente lo que queremos preservar. nomic-embed-text es multilingüe — si los textos fueran en ruso y en inglés, quedarían en el mismo espacio vectorial sin necesidad de traducir. Para NER con un LLM que es predominantemente inglés, ahí sí puede tener sentido traducir primero. Pero para clustering y estilometría, el idioma original siempre.

Pasamos a la demo. Vamos a abrir el notebook y recorrerlo completo. Primero la carga de los siete dumps y la normalización — van a ver cómo normalize_snapshots() unifica los cuatro schemas de OGUsers. Después el análisis temporal: la visualización de persistencia entre snapshots. Luego el cross-foro pivoting con match exacto y fuzzy — les voy a mostrar deliberadamente un falso positivo para que vean por qué el fuzzy matching solo no alcanza. Después la estilometría sobre los candidatos. Y finalmente el scatter de UMAP con los embeddings precomputados.

Sección seis: los hallazgos.

La hipótesis queda validada: las identidades no mueren con una brecha, migran. Los actores más activos de OGUsers reaparecen en RaidForums y BreachForums, con el mismo handle o con variaciones confirmadas por estilometría. La comunidad absorbe las brechas: hay un período de contracción visible en los números, y después recuperación. Los nodos de alta centralidad son los mismos a través de los snapshots y los foros.

Hay que ser honestos sobre las limitaciones. El fuzzy matching sobre handles cortos genera ruido — siempre necesita una segunda señal. La estilometría requiere suficientes posts por usuario, y muchos candidatos no llegan a ese umbral. Los embeddings sobre texto muy corto son ruidosos. Y todo esto identifica candidatos, no prueba identidad. Eso requiere revisión manual e investigación adicional.

Lo que se lleva de este caso es el principio metodológico: ninguna técnica sola construye un caso. La convergencia de tres o más señales independientes — handle, estilo, comportamiento semántico, estructura de red — es lo que da solidez a una conclusión. Y las series temporales son oro: si alguna vez tienen cuatro snapshots del mismo objetivo, ese es el análisis prioritario.

Siguiente caso: ransomware. Conti, BlackBasta, LockBit. Del análisis de foros pasamos al análisis de chat logs internos de organizaciones criminales. Es un salto enorme en profundidad de señal.
