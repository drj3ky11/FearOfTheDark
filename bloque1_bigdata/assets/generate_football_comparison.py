"""
Genera la ilustración de la slide 'Por qué la forma del dataset importa'
(bloque1_bigdata/build_slides.py): la metáfora "1 post crítico vale más que
100 posts genéricos", con selecciones nacionales (España vs Francia) en vez
de clubes, para no señalar a un equipo concreto.

Decisión de diseño deliberada: NO se usan fotos reales de futbolistas (sin
derechos de imagen sobre personas identificables) ni logos de clubes. En su
lugar, siluetas genéricas de camiseta (formas geométricas, no una prenda con
marca) coloreadas con los colores de dos selecciones nacionales — España
(rojo/amarillo) vs Francia (azul) — nunca clubes (Madrid/Barça), para que no
se lea como que "va por ese lado". Es una gráfica ilustrativa propia, no una
imagen de prensa ni un meme con caras reales.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
from pathlib import Path

OUT_DIR = Path(__file__).parent
INK = "#46545D"
RED = "#CD2D37"


def _jersey_path(cx, cy, scale=1.0):
    """Silueta genérica de camiseta (cuerpo + dos mangas + escote), no una
    prenda de marca ni de club — solo la forma reconocible de 'camiseta'."""
    verts = [
        (-0.30, 0.42), (-0.55, 0.30), (-0.50, 0.05), (-0.30, 0.14),
        (-0.30, -0.45), (0.30, -0.45), (0.30, 0.14),
        (0.50, 0.05), (0.55, 0.30), (0.30, 0.42),
        (0.14, 0.42), (0.0, 0.30), (-0.14, 0.42), (-0.30, 0.42),
    ]
    verts = [(cx + vx * scale, cy + vy * scale) for vx, vy in verts]
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(verts) - 1) + [MplPath.CLOSEPOLY]
    verts.append(verts[0])
    return MplPath(verts, codes)


def _draw_jersey(ax, cx, cy, scale, primary, secondary):
    patch = PathPatch(_jersey_path(cx, cy, scale), facecolor=primary,
                       edgecolor=secondary, linewidth=max(0.6, scale * 1.2), zorder=2)
    ax.add_patch(patch)


fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), dpi=200)

# ── Izquierda: 1 camiseta grande, España (rojo/amarillo) ──────────────────
ax = axes[0]
ax.set_xlim(-1.2, 1.2)
ax.set_ylim(-1.3, 1.3)
ax.set_axis_off()
_draw_jersey(ax, 0, 0.05, 1.9, primary="#C60B1E", secondary="#FFC400")
ax.text(0, -1.15, "1 post crítico", ha="center", fontsize=15, color=INK, fontweight="bold")
ax.text(0, 1.2, "España — 1 titular decisivo", ha="center", fontsize=12, color=INK)

# ── Derecha: 100 camisetas pequeñas, Francia (azul) ───────────────────────
ax = axes[1]
ax.set_xlim(-0.5, 10.5)
ax.set_ylim(-1.3, 10.5)
ax.set_axis_off()
n_side = 10
for row in range(n_side):
    for col in range(n_side):
        _draw_jersey(ax, col, row, 0.42, primary="#0055A4", secondary="#FFFFFF")
ax.text(n_side / 2 - 0.5, -1.15, "100 posts genéricos", ha="center", fontsize=15,
        color=INK, fontweight="bold")
ax.text(n_side / 2 - 0.5, 10.15, "Francia — 100 suplentes de relleno", ha="center",
        fontsize=12, color=INK)

fig.suptitle("Volumen ≠ relevancia: 1 post bueno pesa más que 100 mediocres",
             fontsize=15, color=RED, fontweight="bold", y=1.01)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(OUT_DIR / "football_comparison.png", transparent=True, bbox_inches="tight")
plt.close(fig)

print("Guardado:", OUT_DIR / "football_comparison.png")
