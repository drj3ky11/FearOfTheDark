"""
Genera el diagrama de burbujas de temas de LDA (bloque1_bigdata/build_slides.py):
cada burbuja es un tema, cada palabra dentro tiende a aparecer junto con las
demás de su burbuja. Palabras y agrupación inventadas para ilustrar el concepto,
no extraídas de un LDA real.

Nota: esta imagen NO lleva pie de foto propio — build_slides.py ya añade un
caption debajo vía picture_slide(). Antes llevaba un fig.text() con un texto
muy parecido justo pegado al borde inferior, que se leía como un texto
doblado/solapado con el caption del slide; se ha quitado para dejar un único
pie de foto, el del slide.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path(__file__).parent
INK = "#46545D"

topics = [
    {"center": (0.22, 0.6), "radius": 0.22, "color": "#CD2D37",
     "label": "Tema 1", "words": ["dump", "track2", "valid", "cvv"]},
    {"center": (0.55, 0.28), "radius": 0.22, "color": "#2E86AB",
     "label": "Tema 2", "words": ["escrow", "wire", "cashout", "transfer"]},
    {"center": (0.82, 0.65), "radius": 0.22, "color": "#3FA34D",
     "label": "Tema 3", "words": ["welcome", "rules", "forum", "thanks"]},
]

fig, ax = plt.subplots(figsize=(11.0, 4.2), dpi=200)
ax.set_xlim(0, 1.05)
ax.set_ylim(0, 1)
ax.set_axis_off()

for t in topics:
    circle = plt.Circle(t["center"], t["radius"], color=t["color"], alpha=0.18, zorder=1)
    ax.add_patch(circle)
    circle_edge = plt.Circle(t["center"], t["radius"], fill=False, edgecolor=t["color"], linewidth=2, zorder=2)
    ax.add_patch(circle_edge)

    cx, cy = t["center"]
    ax.text(cx, cy + t["radius"] + 0.06, t["label"], ha="center", fontsize=13,
             color=t["color"], fontweight="bold")

    n = len(t["words"])
    for i, w in enumerate(t["words"]):
        # Distribuir las palabras en un pequeño círculo interior para que no se solapen
        angle = 2 * 3.14159 * i / n
        wx = cx + 0.11 * (0.9 ** i) * __import__("math").cos(angle)
        wy = cy + 0.11 * (0.9 ** i) * __import__("math").sin(angle)
        ax.text(wx, wy, w, ha="center", va="center", fontsize=11.5, color=INK)

fig.tight_layout()
fig.savefig(OUT_DIR / "lda_bubbles.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "lda_bubbles.png")
