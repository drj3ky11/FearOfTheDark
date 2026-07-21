"""
Genera el esquema de la slide 'Qué es un embedding' (bloque3_setup/build_slides.py):
texto de entrada -> vector numérico -> textos similares quedan cerca en el espacio.

Esquemático, sin fórmulas: solo cajas, flechas y puntos en un plano.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUT_DIR = Path(__file__).parent

RED  = "#CD2D37"
GRAY = "#9AA3B5"
INK  = "#46545D"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.0), dpi=200)

# ── Panel izquierdo: texto -> vector ──────────────────────────────────────
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 6)
ax1.axis("off")

box1 = FancyBboxPatch((0.3, 2.3), 3.2, 1.4, boxstyle="round,pad=0.12",
                       linewidth=1.6, edgecolor=INK, facecolor="#F1F2F6")
ax1.add_patch(box1)
ax1.text(1.9, 3.0, '"contraseña\nreutilizada"', ha="center", va="center",
          fontsize=11, color=INK)

arrow = FancyArrowPatch((3.65, 3.0), (5.7, 3.0), arrowstyle="-|>",
                         mutation_scale=22, linewidth=2, color=RED)
ax1.add_patch(arrow)
ax1.text(4.7, 3.5, "embedding", ha="center", fontsize=10, color=RED, fontweight="bold")

box2 = FancyBboxPatch((5.9, 2.1), 3.5, 1.8, boxstyle="round,pad=0.12",
                       linewidth=1.6, edgecolor=RED, facecolor="#FFF5F5")
ax1.add_patch(box2)
ax1.text(7.65, 3.0, "[ 0.12, -0.87,\n  0.43, ... ]", ha="center", va="center",
          fontsize=10.5, color=RED, family="monospace")

ax1.text(5, 5.4, "Texto → vector numérico", ha="center", fontsize=13,
          color=INK, fontweight="bold")

# ── Panel derecho: vectores cercanos = significado parecido ──────────────
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)
ax2.axis("off")
ax2.text(5, 9.4, "Textos parecidos → vectores cercanos", ha="center",
          fontsize=13, color=INK, fontweight="bold")

cluster_a = [(2.3, 6.4), (3.1, 7.0), (2.6, 7.6), (1.9, 6.9)]
cluster_b = [(7.4, 3.0), (8.2, 2.4), (7.6, 1.8), (8.5, 3.3)]
outlier   = (5.0, 5.2)

for (x, y) in cluster_a:
    ax2.scatter(x, y, s=110, color=RED, zorder=3)
ax2.text(2.55, 5.55, "credenciales\nfiltradas", ha="center", fontsize=9, color=INK)

for (x, y) in cluster_b:
    ax2.scatter(x, y, s=110, color=GRAY, zorder=3)
ax2.text(7.95, 0.9, "tutoriales\nde phishing", ha="center", fontsize=9, color=INK)

ax2.scatter(*outlier, s=110, color=INK, zorder=3, marker="x")
ax2.text(5.0, 4.5, "post random", ha="center", fontsize=9, color=INK)

for pts in (cluster_a, cluster_b):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax2.plot(xs + [xs[0]], ys + [ys[0]], color=GRAY, alpha=0)  # sin línea, solo referencia visual

fig.tight_layout()
fig.savefig(OUT_DIR / "embedding_diagram.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "embedding_diagram.png")
