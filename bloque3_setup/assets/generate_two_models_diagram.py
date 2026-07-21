"""
Genera el esquema de la slide 'Nuestros dos modelos' (bloque3_setup/build_slides.py):
contraste visual entre un modelo de embeddings (mide parecido) y uno generativo
(escribe texto nuevo) — mismo par de conceptos que la slide de embeddings/generativo,
pero aquí aplicado a los dos modelos concretos del curso.
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

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 3.0), dpi=200)

for ax, color, title, in_box, out_box, arrow_label in [
    (ax1, RED,  "qwen3-embedding — MIDE parecido",
     '"contraseña\nreutilizada"', "[ 0.12, -0.87, ... ]", "embedding"),
    (ax2, BLUE, "qwen2.5:14b — GENERA texto",
     '"post en ruso\nsin traducir"', '"post en\ninglés"', "genera"),
]:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.text(5, 4.6, title, ha="center", fontsize=12.5, color=INK, fontweight="bold")

    box1 = FancyBboxPatch((0.3, 1.3), 3.4, 1.6, boxstyle="round,pad=0.12",
                           linewidth=1.6, edgecolor=INK, facecolor="#F1F2F6")
    ax.add_patch(box1)
    ax.text(2.0, 2.1, in_box, ha="center", va="center", fontsize=10, color=INK)

    arrow = FancyArrowPatch((3.9, 2.1), (5.9, 2.1), arrowstyle="-|>",
                             mutation_scale=22, linewidth=2, color=color)
    ax.add_patch(arrow)
    ax.text(4.9, 2.6, arrow_label, ha="center", fontsize=9.5, color=color, fontweight="bold")

    box2 = FancyBboxPatch((6.1, 1.1), 3.6, 2.0, boxstyle="round,pad=0.12",
                           linewidth=1.6, edgecolor=color, facecolor="#FFF5F5" if color == RED else "#EAF4F9")
    ax.add_patch(box2)
    ax.text(7.9, 2.1, out_box, ha="center", va="center", fontsize=10,
            color=color, family="monospace" if color == RED else None)

fig.tight_layout()
fig.savefig(OUT_DIR / "two_models_diagram.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "two_models_diagram.png")
