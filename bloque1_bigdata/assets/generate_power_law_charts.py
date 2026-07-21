"""
Genera las gráficas de power-law para bloque1_bigdata/build_slides.py.

power_law_linear.png / power_law_loglog.png: distribución de actividad por
usuario en escala lineal y log-log. Datos sintéticos (y = k / rank**alpha con
ruido) — ilustran la FORMA de la curva, no un dataset real. Ya no se usan en
la slide actual (ver power_law_binned.png más abajo) pero se conservan por si
hacen falta en otro sitio.

power_law_binned.png: histograma de usuarios agrupados por rango de nº de
posts, en bins finos (~20 columnas de 10 en 10 hasta 200, + una columna final
"200+" para la cola de hiperactivos) y en escala LINEAL (sin logaritmo, a
petición del profesor: quiere ver la forma real de la caída, no una recta
log-log). Sobre datos REALES de results/01_posts_clean.parquet, filtrado a
un único foro/leak — Carder.pro_2013.04 — porque el resto del bloque ya usa
ese foro como muestra única (ver demo_bigdata.ipynb). Es la que usa
actualmente la slide 'La forma de un foro: la curva power-law'.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path(__file__).parent

RED   = "#CD2D37"  # C_ACCENT — mismo rojo de marca que el tema de las slides
GRAY  = "#9AA3B5"  # C_MUTED_D-ish — resto de usuarios
INK   = "#46545D"  # texto/ejes

rng = np.random.default_rng(42)

N = 200
rank = np.arange(1, N + 1)
alpha = 1.15
noise = rng.normal(1.0, 0.06, size=N).clip(0.85, 1.15)
posts = (2000 / rank**alpha) * noise
posts = np.maximum(posts, 1)

top_pct_n = max(1, N // 100)  # el "1%" superior
colors = [RED if r <= top_pct_n else GRAY for r in rank]

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = INK
plt.rcParams["text.color"] = INK
plt.rcParams["axes.labelcolor"] = INK
plt.rcParams["xtick.color"] = INK
plt.rcParams["ytick.color"] = INK


def _clean_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(labelsize=10)


# ─── Gráfica 1: escala lineal ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(5.4, 4.2), dpi=200)
show_n = 60  # mostramos solo los primeros 60 para que las barras se vean
ax.bar(rank[:show_n], posts[:show_n], color=colors[:show_n], width=0.9)
ax.set_xlabel("Usuarios (ordenados por actividad)", fontsize=11)
ax.set_ylabel("Nº de posts", fontsize=11)
ax.annotate(
    f"Top 1% de usuarios ({top_pct_n} de {N})",
    xy=(top_pct_n, posts[top_pct_n - 1]),
    xytext=(show_n * 0.35, posts[0] * 0.75),
    fontsize=10, color=RED,
    arrowprops=dict(arrowstyle="->", color=RED, lw=1.3),
)
_clean_axes(ax)
fig.tight_layout()
fig.savefig(OUT_DIR / "power_law_linear.png", transparent=True)
plt.close(fig)

# ─── Gráfica 2: escala log-log ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(5.4, 4.2), dpi=200)
ax.scatter(rank, posts, color=colors, s=14)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Rank de usuario (escala log)", fontsize=11)
ax.set_ylabel("Nº de posts (escala log)", fontsize=11)
ax.text(
    0.97, 0.93, "línea recta en log-log\n⇒ es una power law",
    transform=ax.transAxes, ha="right", va="top",
    fontsize=10, color=RED,
)
_clean_axes(ax)
ax.grid(True, which="both", linestyle=":", linewidth=0.5, color=GRAY, alpha=0.4)
fig.tight_layout()
fig.savefig(OUT_DIR / "power_law_loglog.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "power_law_linear.png")
print("Guardado:", OUT_DIR / "power_law_loglog.png")

# ─── Gráfica 3: histograma binned sobre datos REALES (slide "La forma de un
# foro: la curva power-law") ───────────────────────────────────────────────
# A petición del profesor: nada de escala logarítmica (se ve la caída real,
# no una recta artificial) y bins más finos — ~20 columnas en vez de 5.
# Usa SOLO Carder.pro_2013.04 (el foro de muestra de todo este bloque), no
# el dataset mezclado de 5 foros/leaks.
import pandas as pd

RESULTS_DIR = Path(__file__).parent.parent.parent / "results"
posts = pd.read_parquet(RESULTS_DIR / "01_posts_clean.parquet", columns=["forum", "userid"])
posts = posts[posts["forum"] == "Carder.pro_2013.04"]

posts_per_user = posts.groupby("userid").size()

# Bins finos de 10 en 10 hasta 200 posts (cubren ~93% de los usuarios) + una
# última columna "200+" que agrupa la cola de hiperactivos (~3% de usuarios
# que sin embargo concentran una parte desproporcionada de los posts).
step = 10
cap = 200
edges = list(range(0, cap + step, step))
labels = [f"{a}-{a + step}" for a in edges[:-1]] + [f"{cap}+"]
bins = edges + [float("inf")]
binned = pd.cut(posts_per_user, bins=bins, labels=labels, right=True)
counts = binned.value_counts().reindex(labels)

bar_colors = [GRAY] * (len(labels) - 1) + [RED]  # solo el último rango (hiperactivos) resaltado

fig, ax = plt.subplots(figsize=(11.5, 4.8), dpi=200)
bars = ax.bar(labels, counts.values, color=bar_colors, width=0.75)
for bar, count in zip(bars, counts.values):
    ax.annotate(
        f"{count:,}".replace(",", "."),
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 3), textcoords="offset points",
        ha="center", fontsize=8, color=INK, rotation=90, va="bottom",
    )
ax.annotate(
    "Pocos usuarios,\nmuchísimos posts",
    xy=(len(labels) - 1, counts.values[-1]),
    xytext=(len(labels) - 5.5, counts.values[0] * 0.65),
    fontsize=11, color=RED, fontweight="bold", ha="center",
    arrowprops=dict(arrowstyle="->", color=RED, lw=1.4),
)
ax.set_xlabel("Posts por usuario (Carder.pro_2013.04)", fontsize=12)
ax.set_ylabel("Nº de usuarios", fontsize=12)
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8.5)
# Sin escala logarítmica, a petición del profesor: se ve la caída real.
_clean_axes(ax)
fig.tight_layout()
fig.savefig(OUT_DIR / "power_law_binned.png", transparent=True)
plt.close(fig)

print("Guardado:", OUT_DIR / "power_law_binned.png")
print(counts)
