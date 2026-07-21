"""
Genera el gráfico de barras de la slide 'Cuantización' (bloque3_setup/build_slides.py):
tamaño en disco de un mismo modelo (qwen2.5:14b) en distintas precisiones.

Sin fórmulas: solo barras de tamaño en GB, antes/después de cuantizar.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path(__file__).parent

RED  = "#CD2D37"
GRAY = "#9AA3B5"
INK  = "#46545D"

labels = ["FP16\n(precisión completa)", "Q8\n(cuantizado)", "Q4\n(cuantizado, el que usamos)"]
sizes_gb = [29.5, 15.7, 8.9]
colors = [GRAY, "#E8878D", RED]

fig, ax = plt.subplots(figsize=(9.5, 4.2), dpi=200)
bars = ax.bar(labels, sizes_gb, color=colors, width=0.55, zorder=3)

for bar, size in zip(bars, sizes_gb):
    ax.text(bar.get_x() + bar.get_width() / 2, size + 0.6, f"{size:.1f} GB",
             ha="center", fontsize=13, color=INK, fontweight="bold")

ax.set_ylabel("Tamaño en disco (GB)", fontsize=11, color=INK)
ax.set_ylim(0, 34)
ax.set_title("qwen2.5:14b — mismo modelo, distinta precisión", fontsize=13, color=INK, pad=14)
ax.tick_params(labelsize=10.5, colors=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK)
ax.spines["bottom"].set_color(INK)
ax.grid(axis="y", color=GRAY, alpha=0.25, zorder=0)

fig.tight_layout()
fig.savefig(OUT_DIR / "quantization_bars.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "quantization_bars.png")
