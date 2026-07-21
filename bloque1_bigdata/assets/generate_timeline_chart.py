"""
Genera la gráfica de la slide 'La forma del foro en el tiempo'
(bloque1_bigdata/build_slides.py): posts por mes sobre datos REALES de
results/01_posts_clean.parquet (CardingForums) — el mismo dataset que el
resto de gráficos de la franja "El problema de escala" (slides 3-8).

A propósito NO se marcan "eventos" ni se hace lectura interpretativa de
fechas — en esta fase (estadística descriptiva / validación) los datos de
fecha solo sirven para comprobar que el parseo fue correcto: ¿hay huecos
raros?, ¿el rango tiene sentido?, ¿hay fechas en blanco o corruptas? La
lectura interpretativa de picos y eventos externos se reserva para la
Sección 3 (análisis temporal), donde se trata en profundidad.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pathlib import Path

OUT_DIR = Path(__file__).parent
RESULTS_DIR = Path(__file__).parent.parent.parent / "results"

RED  = "#CD2D37"
GRAY = "#9AA3B5"
INK  = "#46545D"

posts = pd.read_parquet(RESULTS_DIR / "01_posts_clean.parquet", columns=["forum", "dateline", "dateline_valid"])
# Un único leak, igual que el resto de gráficos de esta franja y que el notebook:
# el parquet mezcla 5 foros distintos, y mezclarlos aquí generaría un hueco falso
# (frontera entre dumps, no un cierre real de foro) — ver demo_bigdata.ipynb.
posts = posts.loc[(posts["dateline_valid"]) & (posts["forum"] == "Carder.pro_2013.04")]

monthly = posts["dateline"].dt.tz_localize(None).dt.to_period("M").value_counts().sort_index()
monthly.index = monthly.index.to_timestamp()

plt.rcParams["font.family"] = "DejaVu Sans"
fig, ax = plt.subplots(figsize=(11.0, 3.9), dpi=200)
ax.plot(monthly.index, monthly.values, color=RED, linewidth=2.0)
ax.fill_between(monthly.index, monthly.values, color=RED, alpha=0.08)

ax.set_ylabel("Posts / mes", fontsize=11, color=INK)
ax.set_xlabel("Validar: ¿el rango tiene sentido? ¿hay huecos sin explicación?", fontsize=10, color=GRAY)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.tick_params(labelsize=10, colors=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK)
ax.spines["bottom"].set_color(INK)
ax.set_ylim(0, monthly.values.max() * 1.15)

fig.tight_layout()
fig.savefig(OUT_DIR / "forum_timeline.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "forum_timeline.png")
print("Rango:", monthly.index.min(), "→", monthly.index.max())
