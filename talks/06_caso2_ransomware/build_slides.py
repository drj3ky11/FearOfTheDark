#!/usr/bin/env python3
"""
Build PPTX para "Caso 2 — Anatomía de una Organización Criminal" — Intro Caso 2 (10 min).

Ejecutar con:
    uv run python talks/06_caso2_ransomware/build_slides.py
"""

import sys
from pathlib import Path

# Asegurar que la raíz del proyecto esté en sys.path para importar talks._shared
_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from pptx import Presentation
from talks._shared.theme import (
    W, H,
    title_slide, section_slide, content_slide,
    two_col_slide, table_slide, demo_slide,
)


def build(prs: Presentation) -> None:

    # ── Portada ───────────────────────────────────────────────────────────────
    title_slide(prs,
        "Caso 2 — Anatomía de una Organización Criminal",
        "Cómo funciona una empresa de ransomware por dentro",
        "CSBC26  ·  Bloque 6  ·  10 min intro + notebook",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: LOS DATASETS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "01", "Los datasets",
                  "Conti, BlackBasta y LockBit — tres grupos, tres filtraciones")

    content_slide(prs, "Los datasets de este caso", [
        "Conti — chat logs internos 2020 (Matrix/Jabber)",
        ("~170k mensajes de operaciones internas: asignaciones, pagos, conflictos", 1),
        "Conti — Jabber 2021–2022 (filtración ucraniana — el leak más famoso del sector)",
        ("Período crítico: invasión de Ucrania, fractura interna del grupo, disolución", 1),
        "Conti — Rocket Chat (canal público-interno de comunicaciones técnicas)",
        "BlackBasta — JSON 2025 (~200k mensajes, grupo sucesor directo de Conti)",
        "LockBit — panel DB 2025 (base de datos del panel de afiliados y víctimas)",
    ])

    table_slide(prs, "Los datasets — resumen",
        ["Grupo", "Fuente", "Período", "Volumen aprox."],
        [
            ["Conti", "Chat logs (Jabber)", "2020", "~70k mensajes"],
            ["Conti", "Jabber (filtración ucraniana)", "2021–2022", "~100k mensajes"],
            ["Conti", "Rocket Chat", "2020–2022", "~30k mensajes"],
            ["BlackBasta", "JSON dump", "2025", "~200k mensajes"],
            ["LockBit", "Panel DB (SQLite)", "2025", "Víctimas, afiliados, pagos"],
        ],
        note="Conti + BlackBasta son el mismo grupo humano en distintas etapas — eso es lo que hace la comparativa única"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: CONTEXTO — LA FILTRACIÓN DE CONTI
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "02", "La filtración de Conti",
                  "Febrero 2022 — un investigador ucraniano abre la caja negra")

    content_slide(prs, "Por qué 2022 fue un punto de quiebre", [
        "24 de febrero de 2022 — Rusia invade Ucrania",
        "Conti publica un comunicado de apoyo a Rusia — error político fatal",
        "Un investigador ucraniano con acceso interno filtra todo: chats, código, infraestructura",
        "Primera vez en la historia que se ven los internos de un grupo de ransomware",
        ("No un análisis externo — los mensajes reales, en ruso, con nombres y salarios", 1),
        ("Turnos laborales, jerarquías, conflictos entre líderes, bonos por rendimiento", 1),
    ])

    content_slide(prs, "Lo que reveló la filtración", [
        "Conti operaba como una empresa: 60–100 empleados a tiempo completo",
        "Departamentos diferenciados: desarrollo, OSINT, negociación, infraestructura, RR.HH.",
        "Salarios en USD, pagados en crypto — entre $1,500 y $4,000 mensuales",
        "Proceso de onboarding para nuevos empleados, evaluaciones de desempeño",
        "Conflictos internos documentados: disputas por pagos, desacuerdos estratégicos",
        ("El grupo no era una banda — era una organización con cultura corporativa propia", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: POR QUÉ ESTE DATASET ES ÚNICO
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "03", "Por qué este dataset es único",
                  "Chat logs vs análisis de malware — dos mundos distintos")

    two_col_slide(prs,
        "Qué revela cada tipo de análisis",
        "Análisis de malware", [
            "Capacidades técnicas del payload",
            "Vectores de infección y evasión",
            "Infraestructura de C2",
            "Indicadores de compromiso (IoCs)",
            "Atribución por código reutilizado",
            "Lo que el grupo PUEDE hacer",
        ],
        "Análisis de chat logs", [
            "Estructura organizacional real",
            "Procesos internos y workflows",
            "Quién toma decisiones y cómo",
            "Conflictos, motivaciones, cultura",
            "Estimaciones de ingresos y salarios",
            "Lo que el grupo REALMENTE hace",
        ],
    )

    content_slide(prs, "La diferencia que importa", [
        "El malware te dice QUÉ puede hacer el grupo — los chats te dicen CÓMO funciona",
        "Podés tener el mejor análisis técnico de un ransomware y no saber nada del operador",
        "Los chats te dan nombres, roles, rutinas, fricciones internas — inteligencia humana",
        "Para atribución forense: el malware te lleva al código; los chats te llevan a personas",
        ("Este es el primer caso donde podemos aplicar NLP a comunicaciones internas reales", 1),
        ("Y comparar dos generaciones del mismo grupo: Conti y su sucesor BlackBasta", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4: MAPA DEL ANÁLISIS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "04", "Mapa del análisis",
                  "Cinco ejes de investigación en el notebook")

    content_slide(prs, "Lo que vamos a hacer en el notebook", [
        "Eje 1 — Estructura organizacional: identificar roles por patrones de comunicación",
        ("¿Quién reporta a quién? ¿Quiénes son los nodos centrales en el grafo de chat?", 1),
        "Eje 2 — Análisis temporal: actividad por hora, día, estacionalidad",
        ("¿Cuándo trabajan? ¿La invasión de Ucrania cambia los patrones de actividad?", 1),
        "Eje 3 — NLP de roles: clasificar usuarios por tipo de lenguaje usado",
        ("Técnicos vs negociadores vs managers — distintos vocabularios, distintos roles", 1),
        "Eje 4 — NER (Named Entity Recognition): extraer víctimas, montos, fechas",
        "Eje 5 — Comparativa Conti / BlackBasta: ¿la cultura organizacional se hereda?",
    ])

    # ── Transición al notebook ────────────────────────────────────────────────
    demo_slide(prs,
        "Abrimos el notebook",
        [
            "Abrir: notebooks/cases/02_ransomware.ipynb",
            "Sección 1: carga y exploración de los chat logs de Conti",
            "Sección 2: grafo de comunicaciones y estructura organizacional",
            "Sección 3: NLP de roles y análisis temporal",
            "Sección 4: comparativa Conti / BlackBasta",
        ],
        notebook_path="notebooks/cases/02_ransomware.ipynb",
    )


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
