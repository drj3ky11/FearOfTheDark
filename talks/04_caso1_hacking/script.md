Primer caso práctico. Acá es donde todo lo que vimos — Big Data, embeddings, estilometría — se aplica sobre datos reales con una pregunta concreta.

La pregunta es esta: cuando un foro underground es brecheado, ¿qué le pasa a sus usuarios?

La respuesta obvia sería "se van". Pero eso no es lo que vemos en los datos.

---

El caso se llama "Identidad y Tiempo" porque esas son las dos dimensiones que nos interesan. La identidad de un actor underground — ese conjunto de handles, estilos, patrones de comportamiento que permiten reconocerlo — y el tiempo como el eje donde podemos ver cómo esa identidad se mueve y transforma.

Para eso necesitamos una serie temporal. Y tenemos una de las pocas que existen en este dominio.

---

El dataset central es OGUsers. Si no lo conocen: era la comunidad más activa en el mundo del robo de "OG usernames" — handles cortos y valiosos en plataformas como Instagram, Twitter, o Roblox. Un handle como "@adam" en Instagram puede valer miles de dólares en este mercado.

La operación típica era SIM swapping: convencer a una empresa de telefonía de que vos sos el titular de un número, tomar control de ese número, y usarlo para resetear la contraseña de la cuenta objetivo. Criminal y muy lucrativo.

Lo que hace a OGUsers único no es la actividad criminal en sí — es que fue brecheado cuatro veces entre 2019 y 2022. Cuatro veces, la misma comunidad. Eso nos da cuatro snapshots de la misma red social con tres años de distancia entre el primero y el último.

Eso es una serie temporal de una comunidad criminal. Casi no existe otra igual.

---

Además de OGUsers, tenemos RaidForums y BreachForums. RaidForums fue el hub central de redistribución de leaks hasta que el DOJ lo cerró en 2022 y arrestó a su admin. BreachForums apareció casi inmediatamente como sucesor — y también fue brecheado. Dos veces.

La conexión entre estos foros es el corazón del análisis cross-foro: ¿los usuarios que desaparecen de OGUsers después de una brecha reaparecen en RaidForums o BreachForums?

---

La hipótesis central del caso es simple de enunciar y no trivial de demostrar: una identidad underground no muere con una brecha. Migra.

Cuando OGUsers fue brecheado en 2019, algunos usuarios desaparecieron. La hipótesis es que no se retiraron del underground — se movieron a otro foro. Y que ese movimiento es detectable. Y que una fracción de ellos mantuvo el mismo handle — lo que hace la detección directa. Y que otra fracción cambió de handle — pero mantuvo el mismo estilo de escritura.

Si eso es cierto, la conclusión práctica es importante: arrestar a un foro no interrumpe la actividad de sus miembros más activos. Solo los desplaza. Y si podés rastrear el desplazamiento, podés construir un historial de actividad que cruza múltiples foros y múltiples años.

Eso vale mucho en contexto de inteligencia de amenazas y en contexto legal.

---

El notebook tiene cuatro secciones.

La primera es estadística comparada entre los cuatro snapshots de OGUsers. Quiero que vean cómo cambia la distribución de actividad después de cada brecha. Qué porcentaje de usuarios activos permanece. Cómo cambia la estructura del foro — si los usuarios que desaparecen eran periféricos o si eran parte del núcleo.

La segunda es pivoting cross-foro. Buscamos usuarios de OGUsers que aparecen en RaidForums o BreachForums. El match más simple es por username exacto. El más sofisticado es por email, cuando está disponible. Después vemos qué hacer cuando ninguno de los dos funciona.

La tercera es el grafo de evolución temporal. Construimos la red de interacciones de OGUsers en cada snapshot y comparamos. La pregunta: ¿los nodos centrales siguen siendo los mismos después de cada brecha? ¿O hay rotación?

La cuarta es estilometría. Para los usuarios que cambiaron de handle, usamos los embeddings de su estilo de escritura para ver si el vector de OGUsers se parece al vector del mismo actor en RaidForums bajo otro nombre.

---

Los resultados los descubrimos en vivo. No les adelanto los números porque el punto es que vean el proceso — cómo se formula la pregunta en código, cómo se interpreta el resultado, qué se hace cuando el resultado es inesperado.

[ABRIR NOTEBOOK]
