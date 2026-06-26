#!/usr/bin/env python3
"""
Build PPTX para "Caso 3 — Radicalización y Red Social" — Intro Caso 3 (10 min).

Ejecutar con:
    uv run python talks/05_caso3_ironmarch/build_slides.py
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
    table_slide, demo_slide, two_col_slide,
)


def build(prs: Presentation) -> None:

    # ── Portada ───────────────────────────────────────────────────────────────
    title_slide(prs,
        "Caso 3 — Radicalización y Red Social",
        "IronMarch: el foro que conectó el extremismo antes de los ataques",
        "CSBC26  ·  Bloque 4  ·  10 min intro + notebook",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: QUÉ FUE IRONMARCH
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "01", "IronMarch",
                  "El principal foro de neonazis aceleracionistas en inglés (2011–2017)")

    content_slide(prs, "IronMarch — contexto y relevancia", [
        "Foro activo entre 2011 y 2017 — fundado por el ruso Alexander Slavros (Alisher Mukhitdinov)",
        "Ideología: neonazismo aceleracionista — acelerar el colapso del sistema para reconstruirlo",
        "Idioma dominante: inglés — audiencia global, no solo angloparlante",
        "Desmantelado en noviembre 2017 — el fundador cerró el foro abruptamente",
        ("2.000+ miembros registrados, ~150k posts a lo largo de 6 años de actividad", 1),
        ("No era el foro más grande — era el más ideológicamente cohesionado y radicalizado", 1),
    ])

    content_slide(prs, "Por qué IronMarch importa más que otros foros", [
        "La mayoría de los foros extremistas tienen discusión — IronMarch tenía reclutamiento activo",
        "Documentado como punto de contacto entre miembros que luego formaron Atomwaffen Division",
        "Atomwaffen: grupo terrorista responsable de al menos 5 asesinatos en EEUU (2017–2019)",
        "El ataque de Christchurch (2019): el perpetrador mencionó a figuras conocidas del foro",
        ("Esto convierte IronMarch en uno de los pocos casos donde podemos validar el análisis", 1),
        ("Tenemos ground truth: sabemos quiénes son algunos miembros clave. Podemos verificar.", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: EL DATASET
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "02", "El dataset",
                  "Filtrado en 2019 — 6 años de actividad expuestos")

    content_slide(prs, "El leak de noviembre 2019", [
        "Dos años después del cierre del foro, un hacker filtró la base de datos completa",
        "El dump incluye: usuarios, posts, mensajes privados, perfiles, fechas de registro",
        "Publicado en formato SQL — vBulletin con estructura estándar",
        "Cobertura temporal: desde la fundación (2011) hasta el cierre (2017)",
        ("Los mensajes privados son particularmente valiosos: comunicación sin audiencia", 1),
        ("Los MPs revelan coordinación, planificación y relaciones entre miembros", 1),
    ])

    table_slide(prs, "El dataset — contenido",
        ["Tabla", "Registros aprox.", "Valor para análisis"],
        [
            ["Usuarios", "~2.100", "Perfiles, fechas de registro, actividad"],
            ["Posts públicos", "~148k", "Contenido, fechas, relaciones respuesta-usuario"],
            ["Mensajes privados", "~55k", "Coordinación privada entre miembros"],
            ["Threads", "~7.500", "Estructura temática, secciones del foro"],
        ],
        note="Los MPs son inusuales en leaks de foros — la mayoría solo filtra posts públicos"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: GROUND TRUTH
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "03", "Ground truth",
                  "Lo que hace este dataset único para validar el análisis")

    content_slide(prs, "Por qué ground truth es tan valioso", [
        "En la mayoría de los casos forenses: no sabemos quiénes son los usuarios realmente",
        "En IronMarch: periodistas, investigadores y fiscales identificaron públicamente a varios",
        "Esto nos permite comparar: ¿el análisis computacional llega a los mismos nodos centrales?",
        "Si el algoritmo de centralidad pone en el top 5 a alguien que sabemos fue fundador de Atomwaffen — funciona",
        ("Si no: tenemos un problema en el modelo, en los datos, o en nuestra hipótesis", 1),
        ("Ground truth no es trampa — es validación científica. La diferencia importa.", 1),
    ])

    two_col_slide(prs, "Miembros identificados públicamente — ejemplos",
        "Vinculados a Atomwaffen Division", [
            "Fundadores del grupo identificados en reportes de ProPublica y Vice",
            "Miembros arrestados cuyos perfiles en IronMarch fueron correlacionados",
            "Comunicaciones de planificación halladas en los MPs del dump",
            "Nota: usamos solo información de fuentes públicas verificadas",
        ],
        "Metodología de validación", [
            "Los nombres reales NO se muestran en el notebook — solo IDs internos",
            "La validación se hace contra listas de IDs pre-procesadas",
            "El objetivo es verificar el algoritmo, no exponer a personas",
            "Toda la investigación sigue principios de minimización de daño",
        ],
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4: QUÉ VAMOS A DEMOSTRAR
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "04", "Qué vamos a demostrar",
                  "El mapa del análisis en el notebook")

    content_slide(prs, "El mapa del análisis — cinco dimensiones", [
        "Dimensión 1 — Grafo de interacciones: nodos de mayor influencia en la red",
        ("¿Los miembros conocidos como líderes aparecen como hubs en el grafo? Validación.", 1),
        "Dimensión 2 — Evolución temporal: crecimiento, picos de actividad, correlaciones externas",
        ("¿Qué eventos externos correlacionan con picos de reclutamiento?", 1),
        "Dimensión 3 — NER: personas, organizaciones y eventos mencionados",
        ("Cruzado con información pública para mapear el ecosistema de referencias del foro", 1),
        "Dimensión 4 — Clustering: subgrupos ideológicos dentro del foro",
        ("¿IronMarch era homogéneo o había facciones con diferencias detectables?", 1),
        "Dimensión 5 — Estilometría: atribución de posts anónimos a usuarios conocidos",
        ("Algunos posts sin firma — ¿el estilo coincide con algún usuario registrado?", 1),
    ])

    content_slide(prs, "La conclusión que buscamos demostrar", [
        "La red de radicalización de IronMarch no era homogénea",
        "Existían brokers de radicalización — nodos que conectaban a nuevos miembros con el núcleo",
        "Esos brokers son identificables computacionalmente con betweenness centrality",
        "Identificar brokers es más valioso que identificar el miembro más activo",
        ("El actor con 10k posts visibles importa menos que el que conecta a 50 personas nuevas", 1),
        ("Eso es contraintuitivo — y es exactamente lo que el análisis de red demuestra", 1),
    ])

    # ── Transición al notebook ────────────────────────────────────────────────
    demo_slide(prs,
        "Abrimos el notebook",
        [
            "Abrir: notebooks/05_caso3_ironmarch.ipynb",
            "Sección 1: carga del dump, exploración temporal y estadística descriptiva",
            "Sección 2: grafo de interacciones y métricas de centralidad",
            "Sección 3: NER, clustering por embeddings y estilometría",
        ],
        notebook_path="notebooks/05_caso3_ironmarch.ipynb",
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

    out = Path(__file__).parent / "csbc26_caso3_ironmarch.pptx"
    prs.save(str(out))
    print(f"Saved: {out}  ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
