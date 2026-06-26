#!/usr/bin/env python3
"""
Build PPTX for "Caso 3 — IronMarch: radicalización y red social".

Run with:
    uv run python talks/05_caso3_ironmarch/build_slides_full.py

When you have a branded template, pass it as the first argument:
    uv run python talks/05_caso3_ironmarch/build_slides_full.py template.pptx
"""

import sys
from pathlib import Path

# Ensure the project root is in sys.path so that talks._shared.theme is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pptx import Presentation
from talks._shared.theme import (
    W, H,
    C_BG, C_BG_SEC, C_ACCENT, C_TITLE, C_BODY, C_MUTED, C_CODE_BG, C_BADGE,
    _set_bg, _add_rect, _add_txbox, _add_bullets, _add_multiline,
    title_slide, section_slide, content_slide, two_col_slide,
    table_slide, code_slide, demo_slide,
)
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


# ─── Slide content ────────────────────────────────────────────────────────────

def build(prs: Presentation) -> None:

    # ── Title ──────────────────────────────────────────────────────────────────
    title_slide(prs,
        "IronMarch: radicalización y red social",
        "Análisis forense de un foro neonazi aceleracionista (2011–2017)",
        "CSBC26  ·  OpHarvestSeason  ·  Caso 3  ·  Far Right Forum",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: EL ECOSISTEMA
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "01", "El ecosistema",
                  "Aceleracionismo, IronMarch y los grupos que emergieron del foro")

    content_slide(prs, "¿Qué es el aceleracionismo neonazi?", [
        "Ideología que sostiene que el colapso del sistema capitalista liberal aceleraría un nuevo orden",
        "Objetivo: no ganar políticamente, sino destruir las instituciones — el caos como herramienta",
        "Diferencia con extremismo tradicional: no busca reforma, busca colapso total del sistema",
        ("El nazismo clásico apuntaba al estado — el aceleracionismo apunta a la civilización", 1),
        ("La violencia no es un medio: es el fin en sí mismo y el acelerador del colapso", 1),
        "Figuras clave: James Mason (Siege, 1992), Brenton Tarrant (Christchurch, 2019)",
        "La ideología vive en la red: foros, canales de Telegram, podcasts, memes",
    ])

    content_slide(prs, "IronMarch (2011–2017): el foro fundacional", [
        "Fundado en 2011 por Alexander Slavros (Alisher Mukhitdinov, Moscú)",
        "Principal comunidad angloparlante de fascismo aceleracionista hasta 2017",
        "Secciones diferenciadas: debate ideológico, reclutamiento, coordinación en el mundo real",
        "Idioma: inglés — comunidad internacional (EE.UU., UK, Australia, Europa, Rusia)",
        "No era un foro de odio casual: exigía articulación ideológica para participar",
        ("El filtro ideológico generó una comunidad pequeña pero altamente radicalizada", 1),
        "Publicó el manual Fascism 101 — texto de referencia del movimiento aceleracionista",
    ])

    content_slide(prs, "Atomwaffen Division y otros grupos emergentes", [
        "Atomwaffen Division (AWD): grupo terrorista fundado ~2015 por miembros de IronMarch",
        "AWD vinculado a al menos 5 asesinatos en EE.UU. entre 2017 y 2019",
        "Varios miembros fueron identificados judicialmente — y estaban en IronMarch",
        "Otros grupos: The Base (EE.UU.), National Action (UK), Feuerkrieg Division (Est.)",
        "El patrón: el foro era el punto de contacto; los grupos offline emergían de ahí",
        ("IronMarch como infraestructura social del extremismo, no como comunidad casual", 1),
        ("El paso del foro a la célula real está documentado en los chats internos", 1),
    ])

    content_slide(prs, "2017: cierre y la filtración de 2019", [
        "Noviembre 2017: IronMarch cierra sin explicación pública",
        "Teorías: presión de plataformas, conflictos internos, operación de inteligencia",
        "Noviembre 2019: la base de datos completa del foro se filtra públicamente",
        "Formato: dump de vBulletin — usuarios, posts, mensajes privados, perfiles",
        "La filtración ocurrió dos años después del cierre — los datos dormían en algún lugar",
        ("Lo que hace este dataset único: no es solo un foro — es una red con ground truth real", 1),
        ("Varios nodos en el grafo están vinculados a casos judiciales documentados", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: LOS DATOS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "02", "Los datos",
                  "IronMarch_2019.11.zip — ground truth forense en un foro extremista")

    content_slide(prs, "El dataset: IronMarch_2019.11.zip", [
        "Dump completo del foro publicado en noviembre de 2019",
        "191 MB comprimido — tamaño manejable, contenido denso",
        "Formato: vBulletin SQL — mismo schema que carding y hacking forums",
        "Encoding: UTF-8 (a diferencia de los foros rusos de carding que usaban cp1251)",
        "Contenido: usuarios, posts, mensajes privados (PMs), perfiles completos",
        ("El mismo parser de los casos anteriores lo levanta sin modificación", 1),
        ("Esto valida el diseño del parser: un solo código para todos los foros vBulletin", 1),
    ])

    table_slide(prs, "Estadísticas del dataset IronMarch", [
        "Tabla", "Registros", "Columnas clave", "Notas",
    ], [
        ["user",    "~1,200",    "userid, username, email, joindate, posts, ipaddress", "Usuarios registrados"],
        ["post",    "~200,000",  "postid, userid, threadid, parentid, dateline, pagetext", "Posts del foro"],
        ["pmtext",  "~50,000+",  "pmtextid, fromuserid, touserarray, message, dateline", "Mensajes privados"],
        ["thread",  "~10,000+",  "threadid, forumid, title, postuserid, dateline", "Hilos del foro"],
        ["forum",   "~30",       "forumid, title, parentid, description", "Secciones del foro"],
        ["userfield","~1,200",   "profilefield_*, field1, field2", "Campos extra de perfil"],
    ], note="La tabla post con parentid permite reconstruir el grafo de respuestas usuario-a-usuario")

    content_slide(prs, "Lo que hace este dataset único: ground truth", [
        "La mayoría de los foros underground son anónimos — no podemos validar atribuciones",
        "IronMarch es diferente: varios miembros fueron públicamente identificados",
        "Casos judiciales documentados mencionan usernames de IronMarch explícitamente",
        "Periodismo de investigación (ProPublica, Bellingcat) cruzó el dump con registros reales",
        "Esto nos permite algo infrecuente en este campo: VALIDAR el análisis computacional",
        ("Si el modelo pone a X en el top de betweenness y X está en un caso judicial — el método funciona", 1),
        ("Si no lo pone, entendemos los límites del método", 1),
    ])

    content_slide(prs, "Consideración especial: contenido extremadamente sensible", [
        "El texto del foro es contenido de odio explícito, no eufemístico",
        "Los posts hablan de violencia, objetivos reales, ideología racial con nombres propios",
        "Regla de oro para este dataset: no copiar, no citar fuera de contexto académico",
        "No publicar perfiles individuales — aun cuando los datos sean públicos",
        "El análisis es forense: entender la red, no amplificar el mensaje",
        ("Tratar cada celda como si la vieras en el stand de una conferencia de seguridad", 1),
        ("Si encontrás información que parece operacional o actual — pará y consultá", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: LA INFRAESTRUCTURA
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "03", "La infraestructura",
                  "El mismo stack, con una consideración de seguridad adicional")

    two_col_slide(prs, "Stack de análisis: idéntico a los casos anteriores", "Entorno", [
        "uv — gestor de entornos Python",
        "Python 3.12 — type hints modernos",
        "Jupyter Lab — análisis exploratorio y demo",
        "uv run jupyter — sin activar venv manualmente",
    ], "Librerías clave", [
        "pandas + numpy — manipulación de datos",
        "networkx — análisis de grafos y centralidad",
        "matplotlib + seaborn — visualización",
        "plotly — scatter UMAP interactivo",
        "scikit-learn — clustering y métricas",
        "ollama — NER y embeddings locales",
    ])

    content_slide(prs, "Por qué todo en local (con énfasis especial aquí)", [
        "Regla general: datos sensibles no salen de la máquina — nunca a APIs externas",
        "Para IronMarch esto aplica con mayor fuerza: el texto es contenido de odio explícito",
        "Mandar este corpus a OpenAI, Cohere o Google viola sus ToS y los expone a datos tóxicos",
        "Ollama corre completamente local: nomic-embed-text para embeddings, qwen2.5:14b para NER",
        "Sin latencia de red, sin logging externo, sin riesgo de fuga de datos",
        ("El análisis tiene que ser reproducible offline — importa para investigación académica", 1),
        ("Un paper que depende de una API externa no es reproducible en el tiempo", 1),
    ])

    content_slide(prs, "Separación física de resultados", [
        "Los resultados del análisis se guardan en results/ironmarch/ — separados del dataset",
        "El dataset (IronMarch_2019.11.zip) vive en data/Far Right Forum/ — no se versiona",
        "Los resultados precomputados (embeddings, NER, UMAP) sí se pueden compartir en contexto",
        "Diferencia crítica: compartir el análisis no es lo mismo que compartir los datos originales",
        "load_or_compute() del notebook permite regenerar desde cero o cargar desde caché",
        ("Si el caché existe: la demo es instantánea — sin necesidad de Ollama activo", 1),
        ("Si no existe: el código está ahí para regenerarlo cuando Ollama esté disponible", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4: TÉCNICAS DE ANÁLISIS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "04", "Técnicas de análisis",
                  "Red social, tiempo, NER, embeddings y estilometría")

    content_slide(prs, "Plan de análisis — 5 técnicas encadenadas", [
        "1. Grafo de interacciones  —  betweenness centrality, brokers de radicalización",
        "2. Análisis temporal  —  correlación actividad ↔ eventos externos reales",
        "3. NER zero-shot con Ollama  —  personas, organizaciones, eventos del corpus",
        "4. Clustering por embeddings  —  subgrupos ideológicos dentro del foro",
        "5. Estilometría  —  atribución de posts anónimos a usuarios conocidos",
        ("El orden importa: la red nos dice quiénes son relevantes", 1),
        ("Las técnicas de texto nos dicen qué decían y si dos 'quiénes' son el mismo", 1),
    ])

    content_slide(prs, "1. Grafo de interacciones y betweenness centrality", [
        "Construimos un dígrafo: cada respuesta a un post crea una arista userid_A → userid_B",
        "parentid en la tabla post permite reconstruir quién respondió a quién",
        "Betweenness centrality: qué nodos aparecen con más frecuencia en los caminos más cortos",
        "Interpretación en este contexto: el broker no es el más visible, es el que conecta",
        "Resultado contraintuitivo: los mayores 'radicalizadores' no son los más prolíficos",
        ("Son los que tienen puentes entre distintas subcomunidades ideológicas del foro", 1),
        ("Un usuario con 50 posts muy distribuidos puede tener mayor betweenness que uno con 2000", 1),
    ])

    content_slide(prs, "Resultado contraintuitivo: brokers vs. top posters", [
        "Intuición naive: el que más postea es el más influyente",
        "Realidad computacional: el que conecta grupos es el más influyente estructuralmente",
        "En IronMarch hay secciones ideológicamente diferenciadas — no es un foro plano",
        "Los brokers son usuarios que participan en múltiples secciones, no solo en una",
        "Esto tiene consecuencias prácticas para priorizar investigación",
        ("El top poster en 'Debate ideológico' puede ser un echo chamber con poca influencia real", 1),
        ("El broker entre 'Reclutamiento' y 'Acción real' es el nodo crítico", 1),
    ])

    content_slide(prs, "2. Evolución temporal: correlación con eventos externos", [
        "Hipótesis: los picos de actividad del foro responden a eventos del mundo real",
        "Metodología: series temporales de posts por mes + líneas de eventos sobre el gráfico",
        "Eventos marcados: Breivik (2011), Charleston (2015), Elección Trump (2016), Charlottesville (2017)",
        "La correlación no implica causalidad pero sí revela cómo el foro procesa el entorno",
        "El cierre en 2017 aparece como fin abrupto de la serie — visible a simple vista",
        ("El heatmap hora/día-de-semana revela la distribución geográfica real de usuarios", 1),
        ("Picos en horario angloamericano → confirma que era una comunidad principalmente US/UK", 1),
    ])

    content_slide(prs, "3. NER zero-shot con Ollama (qwen2.5:14b)", [
        "Objetivo: extraer personas, organizaciones, eventos, ideologías mencionadas en los posts",
        "NER estándar falla aquí: no fue entrenado con texto extremista ni jerga del movimiento",
        "Solución: NER zero-shot con LLM local — le damos el contexto en el prompt",
        "Tipos de entidades: PERSON, ORGANIZATION, LOCATION, EVENT, IDEOLOGY, WEAPON",
        "Output: JSON por post → agregar → frecuencia por tipo de entidad",
        ("Los resultados se cruzan con registros públicos: ¿aparecen nombres conocidos?", 1),
        ("Limitación: falsos positivos en texto de odio son altos — requiere revisión manual", 1),
    ])

    code_slide(prs, "NER zero-shot: el prompt y su estructura", "El prompt define el dominio — el LLM extrae con ese contexto", [
        'NER_PROMPT = """',
        "Extrae entidades del siguiente texto de un foro extremista de 2011-2017.",
        'Responde SOLO con JSON válido: [{"entity": "...", "type": "...", "context": "..."}]',
        "Tipos: PERSON, ORGANIZATION, LOCATION, EVENT, IDEOLOGY, WEAPON",
        "Texto: {text}",
        '"""',
        "",
        "def extract_ner_from_post(text: str, model='qwen2.5:14b') -> list:",
        "    response = ollama.generate(model=model,",
        "                               prompt=NER_PROMPT.format(text=str(text)[:2000]),",
        "                               format='json')",
        "    return json.loads(response.response)",
    ], note="Los resultados se guardan en results/ironmarch/ironmarch_ner.parquet con load_or_compute()")

    content_slide(prs, "4. Clustering por embeddings: subgrupos ideológicos", [
        "Premisa: IronMarch no era ideológicamente homogéneo — había facciones dentro del foro",
        "nomic-embed-text convierte el corpus de posts de cada usuario en un vector de 768D",
        "UMAP reduce 768D → 2D preservando la estructura local del espacio vectorial",
        "Output: scatter plot interactivo — clusters visibles = grupos de estilo/vocabulario similar",
        "Los clusters revelan subgrupos: neonazismo clásico vs. aceleracionismo puro, etc.",
        ("Hover sobre un punto: username, foro de origen, número de posts", 1),
        ("Un cluster muy aislado puede indicar un subgrupo con agenda propia dentro del foro", 1),
    ])

    content_slide(prs, "5. Estilometría: atribución de posts anónimos", [
        "IronMarch tenía secciones donde se podía postear con menor identificación",
        "La estilometría extrae features de estilo: longitud de oraciones, puntuación, vocabulario",
        "src/stylometry.py: features manuales (ratio puntuación/palabras, avg word length, etc.)",
        "compare_users() genera una matriz de similitud coseno entre usuarios",
        "Pares con similitud > 0.95: candidatos para atribución o identidades duplicadas",
        ("El estilo de escritura bajo presión es difícil de suprimir consistentemente", 1),
        ("Validación: si el modelo atribuye un post a X y X está en el ground truth — funciona", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 5: DEMO EN VIVO
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "05", "Demo en vivo",
                  "Recorremos el notebook end-to-end con los datos reales")

    demo_slide(prs, "03_ironmarch.ipynb — recorrido completo", [
        "Cargar el dump y verificar usuarios, posts y rango temporal (2011–2017)",
        "Distribución power-law: quiénes son los top posters y cuánto concentra el top-1%",
        "Construir el grafo y calcular betweenness — los brokers de radicalización",
        "Timeline con eventos externos correlacionados y heatmap hora/día",
        "NER desde caché: entidades más frecuentes por tipo",
        "UMAP interactivo: clusters ideológicos y usuarios outliers",
    ], notebook_path="notebooks/cases/03_ironmarch.ipynb")

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 6: HALLAZGOS, VALIDACIÓN Y ÉTICA
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "06", "Hallazgos, validación y ética",
                  "Qué encontramos, qué podemos afirmar y cómo manejamos estos datos")

    content_slide(prs, "Hallazgo principal: hub-and-spoke, no red plana", [
        "La red de radicalización de IronMarch tiene estructura hub-and-spoke",
        "No es una red distribuida donde todos se conectan con todos",
        "Hay un pequeño conjunto de brokers que son el tejido conectivo de la comunidad",
        "Si se eliminan esos nodos, el grafo se fragmenta en comunidades desconectadas",
        "Esto tiene implicaciones para entender cómo opera la radicalización online",
        ("El acceso al foro no implicaba exposición a todo: los brokers mediaban el contacto", 1),
        ("Esto también explica por qué algunos miembros escalaron a violencia y otros no", 1),
    ])

    content_slide(prs, "Validación con ground truth", [
        "Los nodos con mayor betweenness centrality correlacionan con miembros en casos reales",
        "Esta correlación es la validación más sólida posible de la técnica computacional",
        "Mecanismo: los brokers reales en una red de radicalización son exactamente los conectores",
        "El análisis de estilometría también encuentra pares consistentes con identidades conocidas",
        "Limitación crítica: el ground truth es parcial — no todos los miembros están identificados",
        ("La ausencia de alguien en el ground truth no implica que no sea relevante", 1),
        ("El modelo puede identificar nodos importantes que aún no tienen nombre público", 1),
    ])

    content_slide(prs, "Limitaciones técnicas", [
        "NER en texto de odio produce falsos positivos: nombres comunes como entidades PERSON",
        "Los modelos de embeddings no están optimizados para este tipo de jerga ideológica",
        "Betweenness con sampling (k=500) es una aproximación — no el valor exacto",
        "El grafo de co-participación en threads es menos preciso que el grafo de respuestas",
        "Ground truth parcial: no sabemos qué porcentaje de nodos relevantes están identificados",
        ("Las técnicas son herramientas de priorización, no de acusación", 1),
        ("Ningún resultado computacional solo es suficiente para identificar a una persona real", 1),
    ])

    content_slide(prs, "Consideraciones éticas específicas de este dataset", [
        "El análisis es legítimo en contexto académico y de investigación defensiva",
        "Anonimizar en publicaciones: no nombrar individuos salvo que sean ya conocimiento público",
        "No amplificar: publicar el análisis sin reproducir el texto original del foro",
        "No usar este dataset para 'doxing' ni para identificar personas no involucradas en violencia",
        "Contexto de este material: formación interna — no investigación publicable sin revisión ética",
        ("Si en algún punto el análisis te lleva a información que parece operacional — parás", 1),
        ("El objetivo es entender la red, no construir perfiles para uso fuera del análisis", 1),
    ])

    # ── Cierre ────────────────────────────────────────────────────────────────
    title_slide(prs,
        "Preguntas",
        "github.com/csbc26  ·  notebooks/cases/03_ironmarch.ipynb",
        "CSBC26  ·  OpHarvestSeason  ·  Caso 3",
    )


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    template_path = sys.argv[1] if len(sys.argv) > 1 else None

    if template_path:
        prs = Presentation(template_path)
    else:
        prs = Presentation()
        prs.slide_width  = W
        prs.slide_height = H

    build(prs)

    out = Path(__file__).parent / "csbc26_caso3_ironmarch.pptx"
    prs.save(str(out))
    print(f"Saved: {out}  ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
