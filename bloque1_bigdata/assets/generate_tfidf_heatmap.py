"""
Genera el mapa de calor de TF-IDF (bloque1_bigdata/build_slides.py): qué tan
característica es una palabra de una comunidad (detectada por Leiden en la
Sección 2), sin fórmulas — solo intensidad de color. Datos inventados a
propósito para que el contraste sea obvio; ya no se agrupa por subforo,
porque este bloque usa un único foro de muestra (Carder.pro_2013.04).
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

OUT_DIR = Path(__file__).parent
INK = "#46545D"

communities = ["Comunidad 1 (dumps)", "Comunidad 2 (escrow/cashout)", "Comunidad 3 (novatos)", "Comunidad 4 (general)"]
words       = ["gracias", "dump", "escrow", "welcome"]

# Fila = comunidad de Leiden, columna = palabra. Valores altos = palabra muy
# característica de ESA comunidad. "gracias" es baja y pareja en todas
# (palabra común); las otras tres son altas solo en su comunidad
# correspondiente (palabras discriminantes).
scores = np.array([
    [0.05, 0.90, 0.05, 0.05],   # Comunidad 1 (dumps)
    [0.05, 0.05, 0.90, 0.05],   # Comunidad 2 (escrow/cashout)
    [0.05, 0.05, 0.05, 0.90],   # Comunidad 3 (novatos)
    [0.05, 0.05, 0.05, 0.05],   # Comunidad 4 (general)
])

cmap = LinearSegmentedColormap.from_list("brand_reds", ["#FFFFFF", "#CD2D37"])

plt.rcParams["font.family"] = "DejaVu Sans"
fig, ax = plt.subplots(figsize=(7.4, 4.2), dpi=200)
im = ax.imshow(scores, cmap=cmap, vmin=0, vmax=1, aspect="auto")

ax.set_xticks(range(len(words)))
ax.set_xticklabels(words, fontsize=12, color=INK)
ax.set_yticks(range(len(communities)))
ax.set_yticklabels(communities, fontsize=11, color=INK)
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_visible(False)

# Cuadrícula sutil entre celdas
ax.set_xticks(np.arange(-0.5, len(words), 1), minor=True)
ax.set_yticks(np.arange(-0.5, len(communities), 1), minor=True)
ax.grid(which="minor", color="white", linewidth=3)
ax.tick_params(which="minor", length=0)

fig.text(0.5, 0.02, "más rojo = palabra más característica de esa comunidad",
          ha="center", fontsize=10.5, color=INK)

fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(OUT_DIR / "tfidf_heatmap.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "tfidf_heatmap.png")
