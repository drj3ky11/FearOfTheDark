"""
Genera el diagrama de la slide 'Cómo genera texto un modelo, paso a paso'
(bloque3_setup/build_slides.py): el bucle autorregresivo de generación —
una pasada completa por el modelo (sus parámetros, todos a la vez) produce
UNA palabra nueva, que se agrega a la entrada para la siguiente pasada.

Este es el diagrama que corrige la confusión "parámetros = pasos": los
parámetros son fijos (los pesos aprendidos), lo que avanza paso a paso es
la cantidad de palabras generadas, no la cantidad de parámetros.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUT_DIR = Path(__file__).parent

RED  = "#CD2D37"
BLUE = "#2E86AB"
GRAY = "#9AA3B5"
INK  = "#46545D"

pasos = [
    ('"El mar es"', "vasto"),
    ('"El mar es vasto"', "y"),
    ('"El mar es vasto y"', "profundo"),
]

fig, axes = plt.subplots(3, 1, figsize=(11.5, 6.6), dpi=200)

for i, (ax, (entrada, salida)) in enumerate(zip(axes, pasos)):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.2)
    ax.axis("off")

    ax.text(0.0, 1.9, f"Pasada {i + 1}", fontsize=11, color=GRAY, fontweight="bold")

    box_in = FancyBboxPatch((0.0, 0.3), 3.0, 1.3, boxstyle="round,pad=0.1",
                             linewidth=1.4, edgecolor=INK, facecolor="#F1F2F6")
    ax.add_patch(box_in)
    ax.text(1.5, 0.95, entrada, ha="center", va="center", fontsize=10, color=INK)

    arrow1 = FancyArrowPatch((3.1, 0.95), (4.3, 0.95), arrowstyle="-|>",
                              mutation_scale=20, linewidth=2, color=GRAY)
    ax.add_patch(arrow1)

    box_model = FancyBboxPatch((4.4, 0.1), 2.6, 1.7, boxstyle="round,pad=0.1",
                                linewidth=1.8, edgecolor=BLUE, facecolor="#EAF4F9")
    ax.add_patch(box_model)
    ax.text(5.7, 1.15, "MODELO", ha="center", va="center", fontsize=10.5,
            color=BLUE, fontweight="bold")
    ax.text(5.7, 0.68, "48 capas\n14.8B parámetros\n(fijos, todos a la vez)",
            ha="center", va="center", fontsize=7.8, color=INK)

    arrow2 = FancyArrowPatch((7.1, 0.95), (8.1, 0.95), arrowstyle="-|>",
                              mutation_scale=20, linewidth=2, color=RED)
    ax.add_patch(arrow2)
    ax.text(7.6, 1.35, "1 palabra", ha="center", fontsize=8.5, color=RED, fontweight="bold")

    box_out = FancyBboxPatch((8.2, 0.3), 1.7, 1.3, boxstyle="round,pad=0.1",
                              linewidth=1.6, edgecolor=RED, facecolor="#FFF5F5")
    ax.add_patch(box_out)
    ax.text(9.05, 0.95, f'"{salida}"', ha="center", va="center", fontsize=10.5,
            color=RED, fontweight="bold")

    if i < len(pasos) - 1:
        loop = FancyArrowPatch((9.05, 0.25), (1.5, 0.25), connectionstyle="arc3,rad=-0.35",
                                arrowstyle="-|>", mutation_scale=16, linewidth=1.4,
                                color=GRAY, linestyle="--")
        ax.add_patch(loop)
        ax.text(5.0, -0.15, "la palabra nueva se agrega a la entrada de la siguiente pasada",
                ha="center", fontsize=8, color=GRAY, style="italic")

fig.tight_layout()
fig.savefig(OUT_DIR / "generation_loop_diagram.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "generation_loop_diagram.png")
