Esta presentación dura diez minutos. El objetivo no es explicar ransomware como concepto — eso lo sabemos. El objetivo es preparar el ojo para lo que vamos a ver en el notebook: comunicaciones internas de una organización criminal real, filtradas en uno de los eventos más importantes de la historia de la ciberseguridad.

---

Empecemos por los datos. Tenemos tres fuentes principales.

Conti es el grupo más documentado: chat logs de 2020 en formato Jabber, la filtración ucraniana de 2021 y 2022, y además Rocket Chat — el canal interno de comunicaciones técnicas. En total, estamos hablando de unos doscientos mil mensajes en ruso, escritos por personas que en ese momento no sabían que alguien los estaba mirando.

Después tenemos BlackBasta: un dump en JSON de 2025, aproximadamente doscientos mil mensajes. Y LockBit: la base de datos del panel de afiliados y víctimas, también de 2025.

Lo que hace que este conjunto de datos sea excepcional es que Conti y BlackBasta no son dos grupos distintos. Son el mismo grupo humano en distintas etapas de su historia. Eso nos va a permitir algo que casi nunca es posible: comparar la cultura organizacional de una misma organización criminal antes y después de una fractura.

---

Para entender por qué estos datos son tan raros, hay que entender qué pasó en febrero de 2022.

El 24 de febrero, Rusia invade Ucrania. Al día siguiente, Conti publica un comunicado oficial apoyando a Rusia. Es un error político de proporciones épicas, porque resulta que dentro del grupo había personas con simpatías ucranianas — o al menos con sentido de la oportunidad.

Un investigador ucraniano con acceso interno a los sistemas de Conti filtra todo. No parte — todo. Los chats, el código fuente del ransomware, la infraestructura, las claves de los paneles.

Y lo que aparece es algo que nadie esperaba ver: una empresa.

Sesenta, noventa empleados a tiempo completo. Departamentos diferenciados. Un área de desarrollo, otra de OSINT, otra de negociación con víctimas, infraestructura, hasta algo que se parecía a recursos humanos. Salarios fijos pagados en crypto, entre mil quinientos y cuatro mil dólares por mes. Procesos de onboarding para nuevos empleados. Evaluaciones de desempeño. Conflictos por pagos.

No era una banda con capuchas. Era una organización con cultura corporativa propia, horarios laborales y fricciones entre líderes.

---

Acá vale la pena detenerse un segundo en algo conceptual, porque importa para entender por qué este dataset es diferente a cualquier otra cosa que exista sobre grupos de ransomware.

Cuando analizás malware — el payload, el ejecutable, el código — podés extraer capacidades técnicas. Sabés cómo cifra, cómo evade detección, qué infraestructura de C2 usa. Podés atribuir por código reutilizado. Es análisis forense técnico de primer nivel.

Pero no te dice nada de quién está del otro lado. No sabés cómo toman decisiones. No sabés si hay un líder fuerte o un colectivo horizontal. No sabés si los operadores son independientes o empleados. No sabés qué los motiva más allá del dinero.

Los chat logs te dan todo eso. Quién reporta a quién. Cómo se negocia internamente un rescate. Qué pasa cuando una operación sale mal. Cómo reaccionan ante presión externa. Cuándo trabajan y cuándo no.

El malware te dice qué puede hacer el grupo. Los chats te dicen cómo funciona el grupo. Son dos tipos de inteligencia completamente distintos, y casi nunca los tenemos juntos.

---

En el notebook vamos a explorar cinco ejes.

Primero, estructura organizacional: usando el grafo de comunicaciones, vamos a intentar inferir quién tiene qué rol sin conocer los nombres reales. Los nodos centrales en un grafo de chat no son necesariamente los líderes formales — pero sí son los que mueven información.

Segundo, análisis temporal: a qué hora trabajan, qué días, si hay estacionalidad. Y la pregunta más interesante: ¿la invasión de Ucrania aparece en los datos como una disrupción en los patrones de actividad?

Tercero, NLP de roles: los técnicos hablan distinto que los negociadores, que hablan distinto que los managers. El vocabulario es una señal. Vamos a usar eso para clasificar usuarios sin etiquetas.

Cuarto, NER — Named Entity Recognition: extraer víctimas mencionadas, montos de rescate, fechas de operaciones. Convertir texto en ruso no estructurado en datos estructurados.

Y quinto, la comparativa: ¿qué sobrevivió de Conti a BlackBasta? ¿La misma estructura? ¿El mismo estilo de comunicación? ¿Las mismas personas?

---

Abrimos el notebook.
