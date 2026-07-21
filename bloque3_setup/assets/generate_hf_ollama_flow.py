"""
Genera el esquema de flujo de la slide 'De Hugging Face a Ollama'
(bloque3_setup/build_slides.py): tres pasos, buscar -> descargar -> correr en local.
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

# Proporción ancho:alto <= ~2.3 a propósito: picture_slide escala la imagen
# por altura, y si el título de la diapositiva cabe en una sola línea el hueco
# vertical disponible crece (menos "push" bajo el título) — con una proporción
# más panorámica (como el 3.2:1 original) la imagen se ensancha más de lo que
# caben las 11in de columna y se corta por el borde derecho.
fig, ax = plt.subplots(figsize=(9.0, 3.9), dpi=200)
ax.set_xlim(0, 9)
ax.set_ylim(0, 4)
ax.axis("off")

steps = [
    (1.4, "Hugging Face", "Buscar modelo\n(filtro: GGUF)", GRAY),
    (4.5, "ollama pull", "hf.co/usuario/modelo", RED),
    (7.6, "ollama run", "Corriendo en local,\nsin salir de tu máquina", INK),
]

for i, (x, title, sub, color) in enumerate(steps):
    box = FancyBboxPatch((x - 1.1, 1.1), 2.2, 1.9, boxstyle="round,pad=0.11",
                          linewidth=2, edgecolor=color, facecolor="#FFFFFF" if i != 1 else "#FFF5F5")
    ax.add_patch(box)
    ax.text(x, 2.55, title, ha="center", va="center", fontsize=11, color=color, fontweight="bold")
    ax.text(x, 1.75, sub, ha="center", va="center", fontsize=9, color=INK, family="monospace" if i else None)

    if i < len(steps) - 1:
        arrow = FancyArrowPatch((x + 1.15, 2.0), (steps[i + 1][0] - 1.15, 2.0),
                                 arrowstyle="-|>", mutation_scale=20, linewidth=2.2, color=RED)
        ax.add_patch(arrow)

fig.tight_layout()
fig.savefig(OUT_DIR / "hf_ollama_flow.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "hf_ollama_flow.png")
