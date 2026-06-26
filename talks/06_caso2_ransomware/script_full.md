Buenas. En el caso anterior miramos foros underground — comunidades donde miles de actores interactúan públicamente para comprar y vender datos. Hoy cambiamos completamente de perspectiva. Vamos a mirar hacia adentro de una organización criminal. No su página web, no sus foros, no lo que dicen al mundo. Sus conversaciones internas. Sus mensajes de trabajo.

Esto cambia todo.

---

Arrancamos con el ecosistema ransomware, porque hay mucha confusión sobre cómo funcionan estos grupos. La imagen popular es la del hacker solitario que cifra una computadora y pide Bitcoin. La realidad en 2020 en adelante es completamente distinta.

El ransomware moderno es Ransomware-as-a-Service. Hay operadores, que desarrollan y mantienen el malware y la infraestructura de pagos. Hay afiliados, que son básicamente contratistas que compran acceso al "programa", ejecutan las intrusiones, y se llevan un porcentaje del rescate. Hay negociadores especializados en hablar con las víctimas. Hay Initial Access Brokers que venden accesos comprometidos a redes corporativas sin participar en el cifrado.

El split típico entre afiliado y operador es 70/30 o 80/20 a favor del afiliado. Esto crea un marketplace: los grupos más grandes compiten por tener los mejores afiliados, los mejores negociadores, el mejor soporte técnico. Es una cadena de producción criminal con lógica de mercado.

---

Conti es el caso de estudio central de esta clase. Fueron el grupo de ransomware más prolífico entre 2020 y 2022. Más de 400 víctimas confirmadas, más de $2.7 billones de dólares en rescates durante su operación. Atacaron hospitales durante la pandemia. Atacaron infraestructura crítica. Cuando Rusia invadió Ucrania en febrero de 2022 y Conti publicó un mensaje de apoyo al gobierno ruso, alguien desde adentro decidió que era suficiente.

En 48 horas empezaron a aparecer online los chat logs internos de Conti. Primero los Jabber, luego los Rocket Chat, luego archivos internos. En total, 168,000 mensajes de comunicaciones internas. No era un reporte de threat intelligence. Era el Slack de una empresa criminal.

---

BlackBasta aparece en abril de 2022, pocas semanas después del colapso de Conti. El solapamiento en TTPs, en vocabulario, en estructura organizacional con Conti es tan grande que la hipótesis dominante en threat intel es que varios operadores de Conti simplemente se fueron y reconstituyeron el grupo bajo un nombre nuevo.

Más de 500 víctimas entre 2022 y 2024. En enero de 2025, un insider publicó los chat logs internos. Mismo patrón que Conti. El leak fue incluso más completo: incluye canales privados, conversaciones que en Conti no habían salido.

LockBit es el caso de mayor longevidad. Operando desde 2019, el modelo de afiliados más abierto del ecosistema: panel web de autoservicio, documentación técnica detallada, incluso un bug bounty propio. En febrero de 2024, la Operación Cronos del FBI y Europol desarticuló su infraestructura. En mayo de 2025, el panel de administración se filtró, revelando víctimas, montos de rescate y datos de afiliados.

---

Antes de hablar del análisis, necesitamos entender qué hay en cada dataset.

El leak de Conti tiene tres partes. Los chats de Jabber son conversaciones uno-a-uno en formato XML, un archivo por conversación. Los chats de Rocket Chat son el canal de grupo, el equivalente al Slack empresarial, en JSON por canal. Y hay logs de Telegram interno en texto plano.

Tres plataformas, tres schemas distintos, tres parsers que luego hay que normalizar a un formato común para poder analizar todo junto.

El archivo de BlackBasta es un solo JSON de 75 megabytes que tiene un problema: no es JSON válido. Las claves no tienen comillas. json.loads() falla. La solución es usar expresiones regulares para extraer cada bloque de mensaje y parsear campo por campo.

---

Acá viene la diferencia conceptual más importante del día.

En el Caso 1 analizamos dumps SQL de foros: miles de usuarios, posts diseñados para ser vistos por toda la comunidad, texto performativo. El foro es un espacio público. Cada post es una actuación hacia la audiencia.

Los chat logs son lo opuesto. Son comunicaciones privadas entre colegas. El texto es funcional y operacional. No hay audiencia: es "che, el build del loader está rompiendo en Windows Defender, necesito que lo revises" o "el target de esta semana es X, esperamos Y millones". Sin filtro, sin performance.

Esto tiene consecuencias para el análisis. Tenemos menos usuarios —entre 50 y 200 activos, no millones— pero cada mensaje tiene más contexto. Los roles son más visibles. La jerarquía es observable. Los conflictos internos son detectables. Y podemos extraer entidades reales: víctimas, herramientas, infraestructura, montos.

---

Pasamos a las técnicas. Son cinco.

La primera es el grafo de comunicación para inferir estructura organizacional. Modelamos quién habló con quién en los mismos canales. Dos usuarios están conectados si participaron en el mismo chat. El peso de la conexión es cuántas veces lo hicieron. Luego calculamos centralidad: degree es cuántos contactos directos tiene un usuario, betweenness es con qué frecuencia aparece en el camino más corto entre otros dos.

Un nodo con betweenness alta y degree moderado es un broker: alguien que conecta silos dentro de la organización. Ese es el manager o coordinador que queremos identificar.

---

La segunda técnica es TF-IDF por usuario. Un documento es todos los mensajes de un usuario concatenados. Los términos con mayor peso son la firma léxica de esa persona.

Un negociador habla de payment, decryptor, deadline, victim. Un técnico habla de exploit, lateral, beacon, rdp, av evasion. Un administrador habla de salary, task, hire, report. Esto funciona incluso sin modelos de lenguaje —es estadística pura sobre frecuencia de términos.

El corpus está en ruso, así que el tokenizador tiene que aceptar caracteres cirílicos y no puede usar stopwords en inglés. Este es un detalle técnico que rompe el análisis si no se atiende.

---

La tercera técnica es el timeline: correlación entre actividad interna y ataques externos confirmados.

Tomamos los mensajes agrupados por semana, graficamos la actividad, y marcamos las fechas de ataques confirmados que podemos encontrar en fuentes públicas como CISA o Bleeping Computer. Un pico de actividad que precede en una semana a un ataque confirmado es evidencia de coordinación operacional.

El heatmap de hora por día de la semana es el análisis de timezone del Caso 1 aplicado aquí. Si el pico está entre las 06:00 y las 15:00 UTC, estamos hablando del horario laboral de Moscú: UTC+3, de nueve de la mañana a seis de la tarde.

---

La cuarta técnica es NER con Ollama. Named Entity Recognition estándar falla en este contexto porque los modelos genéricos no fueron entrenados con texto de ransomware.

Usamos qwen2.5:14b en modo zero-shot: le pasamos un mensaje y le pedimos que devuelva un JSON con cuatro listas —víctimas, herramientas, infraestructura, montos de rescate. No necesitamos fine-tuning. Con 200 mensajes de muestra ya aparecen patrones claros sobre qué herramientas usan, qué sectores atacan.

Acá viene la limitación más importante de esta sesión: el corpus es en ruso, y qwen2.5:14b rinde mejor en inglés. La regla que vimos en el bloque teórico aplica acá: para embeddings y estilometría, trabajamos en el idioma original. Para NER con LLMs predominantemente ingleses, traducir primero mejora la calidad de extracción, aunque perdemos la jerga técnica en ruso.

---

La quinta técnica es la comparativa entre Conti y BlackBasta.

Si tenemos ambos datasets cargados, podemos embeber muestras de mensajes de cada grupo con nomic-embed-text y proyectarlos juntos con UMAP. La pregunta es: ¿se separan en el espacio semántico? Si hay mucho solapamiento, el vocabulario operacional es similar, lo que es evidencia de continuidad entre grupos.

TF-IDF comparativo también revela qué términos son exclusivos de cada grupo y cuáles comparten. Conti era más grande y más ruidoso, con debates internos sobre targets. BlackBasta es más cerrado y más disciplinado: los targets se asignan top-down, no se debaten.

---

Abrimos el notebook ahora. Vamos a parsear el JSON de BlackBasta, verificar el volumen de datos, explorar los usuarios más activos, armar el grafo de comunicación, calcular centralidad y graficar el scatter de roles. Después vamos a hacer el timeline, el TF-IDF por usuario, y si Ollama está disponible, correr NER sobre una muestra.

---

Llegamos al cierre.

El análisis de malware te dice qué puede hacer un grupo. Los chat logs te dicen quiénes son las personas. Esa diferencia importa.

El hallazgo más significativo de los leaks de Conti es que tenían estructura de empresa. RRHH real con entrevistas y períodos de prueba. Salarios fijos pagados en crypto. Departamentos con funciones separadas: los que desarrollaban el malware no eran los mismos que negociaban los rescates ni los mismos que hacían el IT support interno. Había managers que aprobaban targets, había debates sobre si atacar hospitales era éticamente aceptable dentro del grupo, había empleados que se quejaban de los salarios.

Nada de eso es visible en el malware. Todo eso está en los chat logs.

Las limitaciones son reales. El ruso domina el corpus, los aliases son anónimos, las filtraciones son incompletas. Pero lo que sí podemos ver —la estructura, los roles, los patrones temporales— es información que ninguna otra fuente de threat intelligence puede dar.

Preguntas.
