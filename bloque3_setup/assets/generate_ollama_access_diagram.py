"""
Genera el esquema de la slide 'Cómo se usa desde Python y desde terminal'
(bloque3_setup/build_slides.py): un único servidor Ollama, tres formas
distintas de hablar con él — para aclarar la confusión de si Ollama "es un
paquete" (no lo es) frente a sus dos clientes, que sí lo son.

Figura deliberadamente compacta (ancha, poco alta): esta slide ya tiene 4
bullets encima, así que el diagrama tiene que caber en un hueco pequeño.
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
BLUE = "#2E86AB"

fig, ax = plt.subplots(figsize=(11.5, 2.0), dpi=200)
ax.set_xlim(0, 12)
ax.set_ylim(0, 3.4)
ax.axis("off")

# Servidor Ollama (izquierda) — NO es un paquete de Python
server = FancyBboxPatch((0.3, 0.5), 2.9, 2.4, boxstyle="round,pad=0.1",
                         linewidth=2, edgecolor=RED, facecolor="#FFF5F5")
ax.add_patch(server)
ax.text(1.75, 2.35, "Servidor Ollama", ha="center", fontsize=11.5, color=RED, fontweight="bold")
ax.text(1.75, 1.85, "aplicación aparte\n(no es pip install)", ha="center", va="center", fontsize=8.5, color=INK)
ax.text(1.75, 0.85, "localhost:11434", ha="center", fontsize=8, color=GRAY, family="monospace")

clients = [
    ("CLI propia de Ollama", "ollama run / ollama pull", INK, "incluida al instalar"),
    ("Librería ollama (Python)", "ollama.chat(...) / ollama.embed(...)", BLUE, "paquete pip/uv"),
    ("CLI llm + plugin", 'llm -m ollama/modelo "..."', GRAY, "paquete pip aparte"),
]
ys = [2.6, 1.7, 0.8]
for (title, code, color, tag), y in zip(clients, ys):
    box = FancyBboxPatch((3.7, y - 0.42), 7.9, 0.84, boxstyle="round,pad=0.08",
                          linewidth=1.4, edgecolor=color, facecolor="#F7F8FA")
    ax.add_patch(box)
    ax.text(3.95, y + 0.16, title, fontsize=9.5, color=color, fontweight="bold", va="center")
    ax.text(3.95, y - 0.16, code, fontsize=8, color=INK, family="monospace", va="center")
    ax.text(11.4, y, tag, fontsize=7.5, color=color, ha="right", va="center", style="italic")

    arrow = FancyArrowPatch((3.25, 1.7), (3.65, y), arrowstyle="-|>",
                             mutation_scale=13, linewidth=1.3, color=color,
                             connectionstyle="arc3,rad=0.15")
    ax.add_patch(arrow)

fig.tight_layout()
fig.savefig(OUT_DIR / "ollama_access_diagram.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "ollama_access_diagram.png")
