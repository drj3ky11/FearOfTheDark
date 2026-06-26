#!/usr/bin/env python3
"""
Build PPTX para "Caso 1 — Identidad y Tiempo" — Intro Caso 1 (10 min).

Ejecutar con:
    uv run python talks/04_caso1_hacking/build_slides.py
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
    table_slide, demo_slide,
)


def build(prs: Presentation) -> None:

    # ── Portada ───────────────────────────────────────────────────────────────
    title_slide(prs,
        "Caso 1 — Identidad y Tiempo",
        "Cómo una identidad underground sobrevive a múltiples brechas",
        "CSBC26  ·  Bloque 4  ·  10 min intro + notebook",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: LOS DATASETS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "01", "Los datasets",
                  "RaidForums, BreachForums, OGUsers — cuatro snapshots en tres años")

    content_slide(prs, "El ecosistema de hacking forums", [
        "RaidForums (2020) — foro de redistribución de leaks y servicios underground",
        "Cerrado por el DOJ en abril 2022 — el admin arrestado en UK",
        "BreachForums (2022, 2023) — sucesor directo; brecheado y relanzado múltiples veces",
        "OGUsers (2019, 2020, 2021, 2022) — comunidad de robo y venta de handles 'OG'",
        ("OGUsers es el centro del análisis: cuatro snapshots de la misma comunidad", 1),
        ("Cuatro brechas, tres años, misma red — serie temporal única en este dominio", 1),
    ])

    table_slide(prs, "Los datasets — resumen",
        ["Foro", "Año(s)", "Registros aprox.", "Relevancia"],
        [
            ["RaidForums", "2020", "~550k usuarios", "Hub de redistribución de leaks"],
            ["BreachForums", "2022", "~320k usuarios", "Sucesor post-cierre de RaidForums"],
            ["BreachForums", "2023", "~210k usuarios", "Snapshot post-arresto del admin"],
            ["OGUsers", "2019–2022", "~4 snapshots", "Serie temporal: misma comunidad, cuatro brechas"],
        ],
        note="OGUsers es el único foro con serie temporal de 4 años — eso es lo que lo hace único"
    )

    content_slide(prs, "OGUsers: qué era y por qué importa", [
        "Comunidad especializada en robo y venta de 'OG usernames' — handles cortos y valiosos",
        "Ejemplo de operación: SIM swapping para tomar control de @nombre en Instagram o Twitter",
        "Brecheado cuatro veces entre 2019 y 2022 — cada vez, datos de usuarios expuestos",
        "Después de cada brecha: algunos usuarios desaparecen, otros migran, otros se quedan",
        ("Esto nos da algo que casi nunca existe: la evolución de una comunidad criminal en tiempo real", 1),
        ("No es un snapshot — es una película. Podemos ver quién huye y a dónde va.", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: LA HIPÓTESIS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "02", "La hipótesis",
                  "Las identidades underground no mueren con una brecha — migran")

    content_slide(prs, "La hipótesis central del caso", [
        "Intuición: cuando un foro es brecheado, los usuarios activos no desaparecen",
        "Migran a otro foro — a veces con el mismo handle, a veces con uno nuevo",
        "Si migran con el mismo handle: detección trivial. Si cambian: necesitamos estilometría.",
        "La hipótesis es cuantificable: ¿qué porcentaje de usuarios de OGUsers 2019 aparece en RaidForums?",
        ("Y más fino: ¿los que cambian de handle mantienen el mismo estilo de escritura?", 1),
        ("Si la respuesta es sí, la identidad underground es más persistente de lo que parece", 1),
    ])

    content_slide(prs, "Por qué esto importa para investigación forense", [
        "Un arresto no elimina a un actor — lo desplaza temporalmente",
        "Si podés rastrear la identidad a través del desplazamiento, podés construir un historial",
        "Historial = actividad antes y después de cada brecha, con evidencia computacional",
        "Esto es lo que hacen los investigadores manualmente — nosotros lo escalamos",
        ("La diferencia entre 'este usuario existe en este foro' y 'esta persona operó durante 3 años'", 1),
        ("Esa diferencia vale mucho en contexto legal y en inteligencia de amenazas", 1),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: QUÉ VAMOS A DEMOSTRAR
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, "03", "Qué vamos a demostrar",
                  "El mapa del análisis en el notebook")

    content_slide(prs, "El mapa del análisis — cuatro pasos", [
        "Paso 1 — Estadística comparada: evolución de OGUsers entre los cuatro snapshots",
        ("Quién desaparece, quién permanece, cómo cambia la distribución de actividad", 1),
        "Paso 2 — Pivoting cross-foro: usuarios de OGUsers que aparecen en RaidForums/BreachForums",
        ("Match exacto por username primero; luego por email donde está disponible", 1),
        "Paso 3 — Grafo de evolución temporal: cómo cambia la red tras cada brecha",
        ("Los brokers centrales, ¿siguen siendo los mismos? ¿O hay rotación de liderazgo?", 1),
        "Paso 4 — Estilometría: confirmar identidades cruzadas cuando el username cambió",
        ("Embeddings del estilo de escritura — ¿el vector es similar aunque el nombre sea distinto?", 1),
    ])

    content_slide(prs, "Lo que esperamos encontrar", [
        "Entre el 30% y 60% de usuarios activos de OGUsers 2019 reaparecen en RaidForums",
        "La tasa de migración sube después de cada brecha — cada exposición acelera el movimiento",
        "Los usuarios de mayor actividad (top 5%) tienen mayor tasa de re-aparición",
        "La estilometría confirma al menos una identidad cruzada con username distinto",
        ("Si alguna de estas hipótesis falla, el notebook nos va a decir exactamente por qué", 1),
        ("Los resultados reales siempre son más interesantes que la hipótesis inicial", 1),
    ])

    # ── Transición al notebook ────────────────────────────────────────────────
    demo_slide(prs,
        "Abrimos el notebook",
        [
            "Abrir: notebooks/04_caso1_hacking_forums.ipynb",
            "Sección 1: carga y exploración de los cuatro snapshots de OGUsers",
            "Sección 2: pivoting cross-foro hacia RaidForums y BreachForums",
            "Sección 3: grafo de evolución y estilometría",
        ],
        notebook_path="notebooks/04_caso1_hacking_forums.ipynb",
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

    out = Path(__file__).parent / "csbc26_caso1_hacking.pptx"
    prs.save(str(out))
    print(f"Saved: {out}  ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
