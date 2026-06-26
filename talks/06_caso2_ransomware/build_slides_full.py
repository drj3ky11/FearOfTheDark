#!/usr/bin/env python3
"""
Build PPTX for "Caso 2 — Ransomware: Anatomía de una Organización Criminal".
Covers Conti / BlackBasta / LockBit chat log analysis.

Run with:
    uv run python talks/06_caso2_ransomware/build_slides_full.py
"""

import sys
from pathlib import Path

# Make the repo root importable so talks._shared resolves correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pptx import Presentation
from talks._shared.theme import (
    W, H,
    C_BG, C_BG_SEC, C_ACCENT, C_TITLE, C_BODY, C_MUTED, C_CODE_BG, C_BADGE,
    _set_bg, _add_rect, _add_txbox, _add_bullets,
    title_slide, section_slide, content_slide,
    two_col_slide, table_slide, code_slide, demo_slide,
)
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


# ─── Slide content ────────────────────────────────────────────────────────────

def build(prs: Presentation) -> None:

    # ── Title ──────────────────────────────────────────────────────────────────
    title_slide(prs,
        "Ransomware: Anatomía de una Organización Criminal",
        "Conti · BlackBasta · LockBit — del chat log al organigrama",
        "CSBC26  ·  Caso 2  ·  Conti 2022 · BlackBasta 2024 · LockBit 2025",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: EL ECOSISTEMA RANSOMWARE
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "01", "El ecosistema ransomware",
                  "RaaS, afiliados, operadores y los grupos más prolíficos de la última década")

    content_slide(prs, "Ransomware-as-a-Service (RaaS)", [
        "El ransomware moderno no es obra de un hacker solitario — es una cadena de producción",
        "Operadores: desarrollan y mantienen el malware, gestionan la infraestructura de pagos",
        "Afiliados: compran acceso al 'programa', ejecutan las intrusiones, comparten el rescate",
        "Negociadores: especializados en comunicarse con víctimas, maximizar el pago",
        "IABs (Initial Access Brokers): venden accesos comprometidos sin participar en el cifrado",
        ("El split típico afiliado/operador: 70/30 o 80/20 — el afiliado se lleva más", 1),
        ("Esto crea un marketplace: los operadores compiten por afiliados talentosos", 1),
    ], note="La misma lógica de marketplace que Carding Forums, pero con cifrado de archivos como producto")

    content_slide(prs, "Conti: la corporación criminal (2020–2022)", [
        "El grupo de ransomware más prolífico entre 2020 y 2022 — más de 400 víctimas confirmadas",
        "Recaudación estimada: +$2.7B en rescates durante su operación",
        "Estructura semi-corporativa: departamentos de IT, RRHH, finanzas, negociación, desarrollo",
        "Salarios fijos para empleados (no solo comisiones): entre $1,500 y $4,000 USD/mes",
        "Proceso de onboarding documentado: entrevistas, período de prueba, tareas asignadas",
        "Objetivo declarado: hospitales, infraestructura crítica, gobierno — sin límites éticos",
        ("Enero 2022: ataque al gobierno de Costa Rica → declaración de guerra al Estado costarricense", 1),
    ], note="Febrero 2022: la filtración ucraniana expone todo esto")

    content_slide(prs, "BlackBasta: el sucesor (2022–presente)", [
        "Aparece en abril 2022 — meses después del colapso de Conti post-filtración",
        "Solapamiento significativo en TTPs, vocabulario interno y estructura con Conti",
        "Hipótesis dominante en threat intel: ex-operadores de Conti reconstituyeron bajo nuevo nombre",
        "Más de 500 víctimas confirmadas entre 2022 y 2024 — incluye Ascension Health, ABB",
        "Modelo más cerrado que Conti: menos afiliados, más control central",
        "Enero 2025: un insider publica los chat logs internos (Matrix protocol) — mismo patrón",
        ("El leak de BlackBasta fue más completo que el de Conti: incluye canales privados", 1),
    ])

    content_slide(prs, "LockBit: el más longevo (2019–2024)", [
        "Operando desde 2019 — el grupo de ransomware activo más antiguo hasta su desarticulación",
        "Modelo de afiliados más abierto: panel web de autoservicio, documentación técnica",
        "Versiones: LockBit 1.0 → 2.0 (2021) → 3.0/LockBit Black (2022) con bug bounty propio",
        "Más de 2,000 víctimas en 75 países — incluye Boeing, Royal Mail, ICBC",
        "Febrero 2024: Operación Cronos (FBI, Europol, NCA) derrumba la infraestructura",
        "Mayo 2025: panel de administración filtrado — revela víctimas, ransoms, afiliados",
        ("LockBit-BB (LockBit Black) es una variante que se distribuyó como builder suelto — aún activa", 1),
    ], note="LockBit se declaró 'de vuelta' múltiples veces — la infraestructura es resiliente por diseño")

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: LOS DATOS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "02", "Los datos",
                  "La filtración ucraniana, los chat logs y lo que hay en cada dataset")

    content_slide(prs, "La filtración ucraniana — febrero 2022", [
        "24 de febrero de 2022: Rusia invade Ucrania",
        "48 horas después: Conti publica un mensaje de apoyo al gobierno ruso",
        "Respuesta: un investigador ucraniano (o simpatizante) filtra todo el material interno de Conti",
        "Primero: los chat logs de Jabber (2020-2021) → luego: Rocket Chat y archivos internos",
        "168,000+ mensajes en total — conversaciones de trabajo reales, en ruso",
        "No es un leak de BD de foro — es el equivalente a filtrar el Slack de una empresa",
        ("El timing político importa: la filtración fue un acto deliberado de respuesta, no un accidente", 1),
    ])

    table_slide(prs, "Los datasets — Conti, BlackBasta, LockBit", [
        "Grupo", "Período", "Formato", "Tamaño", "Fuente / Evento",
    ], [
        ["Conti Jabber",    "2020 – 2021",      "XML por conversación",  "~300 MB (7z)",  "ContiLeaks (Feb 2022)"],
        ["Conti Rocket Chat", "2021 – 2022",    "JSON estructurado",     "~150 MB",       "ContiLeaks (Feb 2022)"],
        ["Conti Telegram",  "2021 – 2022",      "Logs de texto",         "~50 MB",        "ContiLeaks (Feb 2022)"],
        ["BlackBasta",      "Sep 2023 – Sep 2024", "JSON no-estándar",   "~75 MB",        "Leak anónimo (Ene 2025)"],
        ["LockBit Panel",   "2019 – 2024",      "SQLite / MySQL dump",   "~200 MB",       "Op. Cronos follow-up (May 2025)"],
    ], note="Total: ~775 MB comprimidos · 196,000+ mensajes solo BlackBasta · múltiples plataformas")

    content_slide(prs, "Conti: tres plataformas, tres schemas", [
        "Jabber (XMPP) — chats 1 a 1 y grupos pequeños: archivo XML por conversación",
        ("Campos: from, to, timestamp (delay stamp), body del mensaje", 1),
        ("Limitación: conversaciones bilaterales — no hay canales de grupo", 1),
        "Rocket Chat — el 'Slack interno' de Conti: JSON por canal con historial completo",
        ("Campos: _id, ts (timestamp), u.username, msg, rid (room/canal)", 1),
        ("Más rico: incluye reactions, edits, menciones, archivos adjuntos", 1),
        "Telegram interno — logs de texto plano, formato menos estructurado",
        ("Tres schemas distintos → tres parsers distintos → normalización a schema común", 1),
    ])

    content_slide(prs, "BlackBasta: JSON no-estándar", [
        "El archivo blackbasta_chats.json NO es JSON válido — json.loads() falla",
        "Formato: claves sin comillas, similar a un objeto JavaScript o Python dict literal",
        "Cuatro campos por registro: timestamp, chat_id, sender_alias, message",
        "chat_id: ID del canal Matrix (protocol usado, no WhatsApp ni Telegram)",
        "sender_alias: @username:matrix.servidor — hay que extraer el username limpio",
        "196,045 mensajes · Sep 2023 a Sep 2024 · en ruso dominante con inglés técnico",
        ("Solución: regex para extraer cada bloque {} y parsear campo por campo", 1),
    ], note="Matrix es un protocol de mensajería federado, open source — más difícil de rastrear que Telegram")

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: FORMATO — CHAT LOGS VS DUMPS SQL
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "03", "Formato: chat logs vs dumps SQL",
                  "La diferencia fundamental entre foros públicos y comunicaciones internas privadas")

    content_slide(prs, "Foros vs chat logs — diferencia estructural", [
        "Dumps SQL de foros (Caso 1): interacción PÚBLICA entre miles de usuarios",
        ("Posts diseñados para ser vistos por toda la comunidad — texto performativo", 1),
        ("Muchos usuarios, posts cortos, lenguaje formal del foro", 1),
        "Chat logs (Caso 2): comunicaciones PRIVADAS internas entre operadores",
        ("Mensajes diseñados para colegas — texto funcional, operacional, sin filtro", 1),
        ("Menos usuarios (~50-200 activos), mensajes más largos, lenguaje coloquial ruso", 1),
        "El valor forense es distinto: foros dan red social, chats dan cultura organizacional",
        ("Un post en un foro es marketing; un mensaje interno es información sin editar", 1),
    ])

    content_slide(prs, "Lo que esto significa para el análisis", [
        "Menos usuarios → podemos hacer análisis profundo de cada individuo, no solo top-N",
        "Más contexto por mensaje → NER real (víctimas, herramientas, montos) en lugar de keywords",
        "Roles más claros → vocabulario especializado por función: negociador, técnico, admin",
        "Jerarquía visible → quién le da órdenes a quién, quién reporta a quién",
        "Conflictos internos → disputas salariales, desacuerdos operacionales, rotación de personal",
        "Timeline operacional → correlación directa entre picos de actividad y ataques externos",
        ("Conti tenía estructura de empresa: RRHH contrataba, IT daba soporte, management aprobaba targets", 1),
    ])

    code_slide(prs, "Estructura JSON de BlackBasta", "Un registro real del archivo (con datos anonimizados)", [
        "// Formato del archivo — NO es JSON válido (claves sin comillas)",
        "{",
        "    timestamp: 2023-09-18 13:35:07,",
        "    chat_id: !VdvDXHFZwWDpIAtpCj:matrix.bestflowers247.online,",
        "    sender_alias: @lapa:matrix.bestflowers247.online,",
        "    message: BAZA",
        "},",
        "{",
        "    timestamp: 2023-09-18 13:36:22,",
        "    chat_id: !VdvDXHFZwWDpIAtpCj:matrix.bestflowers247.online,",
        "    sender_alias: @boss777:matrix.bestflowers247.online,",
        "    message: пока не готова, жди",
        "},",
        "",
        "// Parser: re.findall(r'\\{([^{}]+)\\}', text)  → extraer cada bloque",
        "// Luego re.search() para cada campo dentro del bloque",
    ], note="El hostname matrix.bestflowers247.online es el servidor Matrix privado de BlackBasta")

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4: TÉCNICAS DE ANÁLISIS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "04", "Técnicas de análisis",
                  "Estructura organizacional, roles, timeline y NER con modelos locales")

    content_slide(prs, "Plan de análisis — 5 técnicas", [
        "1. Análisis exploratorio  —  volumen, usuarios activos, distribución de mensajes",
        "2. Estructura organizacional  —  grafo de co-participación, centralidad, roles inferidos",
        "3. Timeline operacional  —  actividad semanal correlacionada con ataques conocidos",
        "4. Vocabulario por usuario  —  TF-IDF por actor + LDA para topics latentes",
        "5. NER y comparativa  —  extracción de entidades con Ollama + Conti vs BlackBasta",
        ("Las primeras 4 técnicas funcionan sin GPU ni Ollama — solo pandas + networkx + sklearn", 1),
        ("La técnica 5 requiere Ollama con qwen2.5:14b (~8GB) o nomic-embed-text (~300MB)", 1),
    ])

    content_slide(prs, "1. Estructura organizacional — grafo de comunicación", [
        "Modelo: grafo no dirigido — nodos = usuarios, aristas = co-participación en canales",
        "Peso de aristas: cuántas veces dos usuarios aparecieron en el mismo canal",
        "Métricas de centralidad calculadas sobre el componente principal:",
        ("Degree centrality: cuántos contactos directos — usuarios muy conectados", 1),
        ("Betweenness centrality: cuántas veces aparece en el camino más corto entre otros dos", 1),
        ("Betweenness alta + degree moderado = BROKER: conecta silos, posible manager", 1),
        "Cuadrantes del scatter degree vs betweenness → 4 arquetipos de rol",
        ("Alto/Alto: LÍDERES  ·  Alto/Bajo: HUBS  ·  Bajo/Alto: BROKERS  ·  Bajo/Bajo: OPERATIVOS", 1),
    ])

    content_slide(prs, "2. Análisis de roles por vocabulario", [
        "TF-IDF por usuario: un documento = todos los mensajes de un usuario concatenados",
        "Los términos con mayor peso TF-IDF son la 'firma léxica' del usuario",
        "Negociador: payment, decryptor, deadline, victim, usd, btc, contact, deal",
        "Técnico: exploit, lateral, av, evasion, rdp, vpn, cobalt, beacon, implant",
        "Administrador/HR: salary, task, team, hire, deadline, report, meeting, week",
        "Crypter/Builder: build, stub, pack, loader, fud, bypass, test, compile",
        ("LDA sobre el corpus completo → temas latentes sin etiquetar manualmente", 1),
        ("Ejercicio: ¿cuántos temas encontrás? ¿se mapean a roles operacionales?", 1),
    ], note="El corpus es en ruso — TF-IDF con token_pattern que acepta caracteres cirílicos")

    content_slide(prs, "3. Timeline: correlación con ataques conocidos", [
        "Premisa: los picos de mensajes internos preceden o coinciden con ataques externos",
        "Fuentes para validar: CISA, Bleeping Computer, HHS Health-ISAC, threat intel públicos",
        "Técnica: actividad semanal (más suave que diaria) + líneas verticales en fechas de ataque",
        "Heatmap hora × día de la semana → ¿horario laboral de 09:00–18:00 MSK?",
        ("Si el pico UTC es 06:00–15:00, es horario laboral Moscú (UTC+3)", 1),
        ("Los gaps en la actividad son tan interesantes como los picos", 1),
        ("Conti: gap visible en enero 2022 justo antes del colapso post-filtración", 1),
    ], note="El heatmap día/hora es el análisis de timezone del Caso 1 pero sobre comunicaciones internas")

    content_slide(prs, "4. NER zero-shot con Ollama", [
        "Named Entity Recognition estándar (spaCy, BERT genérico) falla en este dominio",
        "Solución: qwen2.5:14b en modo zero-shot con prompt específico al dominio",
        "Entidades target: victims (empresas), tools (malware/exploits), infrastructure (IPs/dominios), ransom_amounts",
        "El modelo recibe el mensaje y devuelve JSON con listas por categoría",
        "Cache de resultados: una vez procesado, guardar en parquet para no re-procesar",
        ("200 mensajes de muestra ya revelan patrones: qué herramientas usan, qué sectores atacan", 1),
        ("Limitación crítica: el corpus es en ruso — qwen2.5:14b funciona mejor en inglés", 1),
        ("Solución parcial: traducir antes de pasar al modelo — pero se pierde jerga técnica", 1),
    ], note="Ver programa.md Bloque 2: embeddings → idioma original; NER con LLM → traducir si es necesario")

    content_slide(prs, "5. Comparativa Conti vs BlackBasta", [
        "Si tenés ambos datasets: embeber muestras y proyectar juntos con UMAP",
        "Pregunta: ¿se separan en el espacio semántico o se solapan?",
        "Solapamiento alto en embeddings = vocabulario operacional similar = posible herencia de personas",
        "Diferencias clave conocidas de threat intel:",
        ("Conti: más grande, más ruidoso, más jerárquico; BlackBasta: más cerrado, más disciplinado", 1),
        ("Conti debatía targets internamente; BlackBasta los asignaba top-down", 1),
        ("Conti tenía disputas salariales en chat; BlackBasta no muestra ese patrón", 1),
        "TF-IDF comparativo: términos exclusivos de cada grupo vs términos compartidos",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 5: DEMO EN VIVO
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "05", "Demo en vivo",
                  "Recorremos el notebook con los datos reales de BlackBasta")

    demo_slide(prs, "03_ransomware.ipynb — recorrido completo", [
        "Parsear BlackBasta JSON no-estándar con regex y verificar volumen",
        "Explorar usuarios: top posters, distribución de mensajes, longitud",
        "Análisis temporal: timeline diaria/semanal y heatmap hora × día",
        "Grafo de comunicación: betweenness y degree → scatter de roles",
        "TF-IDF por usuario: vocabulario característico de los top actores",
        "NER con Ollama: extraer víctimas, herramientas e infraestructura",
    ], notebook_path="notebooks/cases/03_ransomware.ipynb")

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 6: HALLAZGOS Y CONCLUSIÓN
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "06", "Hallazgos y conclusión",
                  "Qué revela el análisis de chat logs que el análisis de malware no puede")

    two_col_slide(prs, "Malware vs chat logs — qué puede cada uno",
        "Lo que revela el malware", [
            "Técnicas de cifrado y persistencia",
            "Indicadores de compromiso (IoCs)",
            "Funcionalidades: qué puede hacer",
            "Versiones y evolución del código",
            "Similitudes con otros grupos (code reuse)",
        ],
        "Lo que revelan los chat logs", [
            "Quiénes son las personas y sus roles",
            "Jerarquía organizacional real",
            "Motivaciones, conflictos, cultura",
            "Proceso de reclutamiento y onboarding",
            "Coordinación de ataques en tiempo real",
        ],
    )

    content_slide(prs, "Hallazgo clave: Conti como empresa criminal", [
        "RRHH real: proceso de entrevistas, asignación de tareas, evaluaciones de desempeño",
        "Salarios fijos en USD: $1,500–$4,000/mes pagados en crypto — estructura de nómina",
        "Departamentos: desarrollo de malware, IT support, negociación, crypter, OSINT",
        "Onboarding documentado: nuevos miembros reciben tareas de introducción con deadlines",
        "Management separado de operaciones: hay quienes aprueban targets y quienes los ejecutan",
        "Conflictos internos visibles: debates sobre targets (algunos resistían atacar hospitales)",
        ("Conti era más parecido a una startup de tech con malas prácticas éticas que a una banda criminal", 1),
    ], note="Esto es imposible de inferir del malware — solo visible en los chat logs")

    content_slide(prs, "Limitaciones del análisis", [
        "Idioma: los chat logs de Conti y BlackBasta son dominantemente en ruso",
        ("NER con modelos base inglés pierde calidad — entidades implícitas en ruso se escapan", 1),
        ("TF-IDF con stopwords inglesas es inútil — hay que usar stopwords rusas o ninguna", 1),
        "Filtraciones incompletas: hay brechas temporales, mensajes eliminados, canales privados faltantes",
        "Aliases anónimos: los usernames no son atribución directa — requieren cruce con otras fuentes",
        "LDA sobre texto operacional: los temas cambian rápido, la coherencia de topics es baja",
        "BlackBasta: una sola fuente sin validación independiente — los datos pueden estar parcialmente alterados",
        ("La filtración fue un acto político además de un leak — eso genera preguntas sobre integridad", 1),
    ])

    # ── Cierre ────────────────────────────────────────────────────────────────
    title_slide(prs,
        "Preguntas",
        "github.com/csbc26  ·  notebooks/cases/03_ransomware.ipynb",
        "CSBC26  ·  Caso 2  ·  Ransomware",
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

    out = Path(__file__).parent / "csbc26_caso2_ransomware.pptx"
    prs.save(str(out))
    print(f"Saved: {out}  ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
