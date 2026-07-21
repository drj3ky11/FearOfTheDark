"""
Genera la gráfica de la slide 'Detectar picos de actividad' (bloque1_bigdata/build_slides.py):
serie temporal semanal con un pico marcado y el umbral µ+2σ de detección por z-score.

Datos sintéticos — ilustran el MÉTODO de detección, no un dataset real. El eje
X sí usa fechas de calendario reales y legibles (p. ej. "abr 2020") en vez de
un índice de semana sin contexto — es más fácil de leer para la audiencia.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from datetime import date, timedelta
from pathlib import Path

OUT_DIR = Path(__file__).parent

RED  = "#CD2D37"
GRAY = "#9AA3B5"
INK  = "#46545D"

MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun",
            "jul", "ago", "sep", "oct", "nov", "dic"]


def _fmt_es(x, _pos=None):
    d = mdates.num2date(x)
    return f"{MESES_ES[d.month - 1]} {d.year}"


rng = np.random.default_rng(11)
n_weeks = 52
start = date(2020, 1, 6)  # primer lunes del año, para fechas "redondas"
dates_list = [start + timedelta(weeks=w) for w in range(n_weeks)]
weeks = np.arange(n_weeks)
baseline = 300 + 15 * np.sin(weeks / 52 * 2 * np.pi * 3)
noise = rng.normal(0, 25, size=len(weeks))
posts = baseline + noise

# Insertamos un pico claro (p. ej. tras una operación policial competidora, un exploit viral...)
spike_week = 33
posts[spike_week] += 260

mu, sigma = posts.mean(), posts.std()
threshold = mu + 2 * sigma
z = (posts - mu) / sigma
is_spike = z > 2

plt.rcParams["font.family"] = "DejaVu Sans"
fig, ax = plt.subplots(figsize=(11.0, 3.9), dpi=200)
ax.plot(dates_list, posts, color=INK, linewidth=1.6, alpha=0.85)
ax.scatter(np.array(dates_list)[~is_spike], posts[~is_spike], color=GRAY, s=18, zorder=3)
ax.scatter(np.array(dates_list)[is_spike], posts[is_spike], color=RED, s=70, zorder=4, label="spike (z > 2)")

ax.axhline(threshold, color=RED, linestyle=":", linewidth=1.4)
ax.text(dates_list[1], threshold + 8, f"umbral µ+2σ = {threshold:.0f}", color=RED, fontsize=10)

for w in weeks[is_spike]:
    ax.annotate(
        f"z = {z[w]:.1f}", xy=(dates_list[w], posts[w]), xytext=(dates_list[w], posts[w] + 45),
        fontsize=10, color=RED, ha="center",
        arrowprops=dict(arrowstyle="->", color=RED, lw=1.2),
    )

ax.set_xlabel("Fecha (semanal)", fontsize=11, color=INK)
ax.set_ylabel("Posts / semana", fontsize=11, color=INK)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax.xaxis.set_major_formatter(mticker.FuncFormatter(_fmt_es))
fig.autofmt_xdate(rotation=30, ha="right")
ax.tick_params(labelsize=9.5, colors=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK)
ax.spines["bottom"].set_color(INK)

fig.tight_layout()
fig.savefig(OUT_DIR / "activity_spike.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "activity_spike.png")
