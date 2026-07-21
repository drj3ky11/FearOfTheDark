"""
Genera la secuencia "paso a paso" de Leiden (bloque1_bigdata/build_slides.py):
el mismo grafo con 3 comunidades, en 4 momentos sucesivos del algoritmo, para
una explicación muy visual y sin fórmulas (la audiencia no es técnica en
matemáticas). Grafo sintético construido a mano para que el contraste sea
nítido, no extraído de datos reales.

Los 4 pasos, pensados para leerse en fila de izquierda a derecha:
  1. leiden_step1_before.png    — grafo sin colorear, comunidades no evidentes
  2. leiden_step2_singleton.png — cada nodo es su propia comunidad (arranque)
  3. leiden_step3_merging.png   — fusiones locales a medio camino
  4. leiden_step4_after.png     — resultado final: 3 comunidades separadas

leiden_before.png / leiden_after.png se conservan con los mismos nombres de
siempre (idénticos a los pasos 1 y 4) por si algo más los referencia.
"""
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path(__file__).parent

GRAY  = "#9AA3B5"
EDGE  = "#C9CDD6"
COMMUNITY_COLORS = ["#CD2D37", "#2E86AB", "#3FA34D"]
# Paleta de "cada nodo su propia comunidad" para el paso 2 — muchos colores
# distintos, deliberadamente ruidosa, para transmitir "todavía no hay orden".
SINGLETON_COLORS = [
    "#CD2D37", "#2E86AB", "#3FA34D", "#E07B39", "#8E44AD",
    "#D4AC0D", "#16A085", "#C0392B", "#2874A6", "#229954",
    "#B9770E", "#7D3C98", "#117864", "#A93226", "#1F618D",
]

# 3 clusters densos + pocas aristas entre clusters (para que Leiden los separe con claridad)
G = nx.Graph()
clusters = [[f"{c}{i}" for i in range(5)] for c in "abc"]
for cluster in clusters:
    for i, u in enumerate(cluster):
        for v in cluster[i + 1:]:
            G.add_edge(u, v)
# Puentes débiles entre comunidades
G.add_edge("a0", "b0")
G.add_edge("b1", "c0")
G.add_edge("c1", "a1")

pos = nx.spring_layout(G, seed=7, k=0.6)
cluster_of = {n: i for i, cluster in enumerate(clusters) for n in cluster}


def _draw(color_fn, path, highlight_edges=None):
    fig, ax = plt.subplots(figsize=(5.4, 4.2), dpi=200)
    edge_colors = [
        (COMMUNITY_COLORS[0] if highlight_edges and e in highlight_edges else EDGE)
        for e in G.edges()
    ]
    edge_widths = [
        (2.6 if highlight_edges and e in highlight_edges else 1.5)
        for e in G.edges()
    ]
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors, width=edge_widths)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=[color_fn(n) for n in G.nodes()],
                            node_size=420, edgecolors="white", linewidths=1.2)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, transparent=True)
    plt.close(fig)


# ─── Paso 1: grafo sin colorear — las comunidades no son evidentes a simple vista
_draw(lambda n: GRAY, OUT_DIR / "leiden_step1_before.png")
_draw(lambda n: GRAY, OUT_DIR / "leiden_before.png")  # alias histórico

# ─── Paso 2: cada usuario arranca como su propia comunidad de una sola persona
node_list = list(G.nodes())
_draw(lambda n: SINGLETON_COLORS[node_list.index(n) % len(SINGLETON_COLORS)],
      OUT_DIR / "leiden_step2_singleton.png")

# ─── Paso 3: fusiones locales a medio camino — el cluster "a" ya se fusionó
# (una comunidad reconocible), "b" y "c" siguen sin resolver (colores sueltos)
half_colors = {}
for n in G.nodes():
    if cluster_of[n] == 0:  # cluster "a" ya fusionado
        half_colors[n] = COMMUNITY_COLORS[0]
    else:
        half_colors[n] = SINGLETON_COLORS[node_list.index(n) % len(SINGLETON_COLORS)]
merged_edges = {(u, v) for u in clusters[0] for v in clusters[0]} | {(v, u) for u in clusters[0] for v in clusters[0]}
_draw(lambda n: half_colors[n], OUT_DIR / "leiden_step3_merging.png",
      highlight_edges=merged_edges)

# ─── Paso 4: resultado final — Leiden separa las 3 comunidades densas
_draw(lambda n: COMMUNITY_COLORS[cluster_of[n]], OUT_DIR / "leiden_step4_after.png")
_draw(lambda n: COMMUNITY_COLORS[cluster_of[n]], OUT_DIR / "leiden_after.png")  # alias histórico

# ─── Zoom de decisión: por qué se fusiona un nodo concreto (a0) con su clúster
# y no con el resto. Cuenta real de aristas, sin fórmulas: a0 tiene 4 conexiones
# con su propio clúster (a1-a4) y solo 1 conexión "puente" hacia fuera (b0).
# Este es el criterio que Leiden evalúa nodo a nodo: ¿dónde tengo más conexiones,
# dentro o fuera? Si dentro gana, me fusiono ahí.
FOCUS_NODE = "a0"
neighbors = list(G.neighbors(FOCUS_NODE))
internal_neighbors = {v for v in neighbors if cluster_of[v] == cluster_of[FOCUS_NODE]}
external_neighbors = {v for v in neighbors if cluster_of[v] != cluster_of[FOCUS_NODE]}

fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=200)
edge_colors, edge_widths = [], []
for u, v in G.edges():
    other = v if u == FOCUS_NODE else (u if v == FOCUS_NODE else None)
    if other in internal_neighbors:
        edge_colors.append("#3FA34D")
        edge_widths.append(3.0)
    elif other in external_neighbors:
        edge_colors.append("#CD2D37")
        edge_widths.append(3.0)
    else:
        edge_colors.append(EDGE)
        edge_widths.append(1.0)
nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors, width=edge_widths)
node_colors = ["#F2C230" if n == FOCUS_NODE else GRAY for n in G.nodes()]
node_sizes = [620 if n == FOCUS_NODE else 380 for n in G.nodes()]
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes,
                        edgecolors="white", linewidths=1.2)
ax.set_axis_off()
ax.text(0.02, 0.06, f"{len(internal_neighbors)} conexiones dentro del clúster",
        transform=ax.transAxes, fontsize=11, color="#3FA34D", fontweight="bold")
ax.text(0.02, 0.00, f"{len(external_neighbors)} conexión puente hacia fuera",
        transform=ax.transAxes, fontsize=11, color="#CD2D37", fontweight="bold")
fig.tight_layout()
fig.savefig(OUT_DIR / "leiden_decision_zoom.png", transparent=True)
plt.close(fig)

for name in ("leiden_step1_before.png", "leiden_step2_singleton.png",
             "leiden_step3_merging.png", "leiden_step4_after.png",
             "leiden_before.png", "leiden_after.png", "leiden_decision_zoom.png"):
    print("Guardado:", OUT_DIR / name)
