"""
Genera los dos esquemas de grafo de la slide 'Degree vs. betweenness'
(bloque1_bigdata/build_slides.py): un nodo con degree alto (muchas conexiones
directas) frente a un nodo con betweenness alto (puente entre dos clusters).

Grafos sintéticos construidos a mano para que el contraste sea nítido, no
extraídos de datos reales.
"""
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path(__file__).parent

RED  = "#CD2D37"
GRAY = "#9AA3B5"
EDGE = "#C9CDD6"


def _draw(G, pos, highlight, path, node_size=1400):
    fig, ax = plt.subplots(figsize=(5.4, 4.2), dpi=200)
    colors = [RED if n == highlight else GRAY for n in G.nodes()]
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=EDGE, width=1.8)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colors, node_size=node_size,
                            edgecolors="white", linewidths=1.5)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, transparent=True)
    plt.close(fig)


# ─── Degree alto: nodo central con muchas conexiones directas ────────────────
G1 = nx.star_graph(7)  # nodo 0 = centro, 1..7 = hojas
pos1 = nx.spring_layout(G1, seed=3, k=0.9)
_draw(G1, pos1, highlight=0, path=OUT_DIR / "network_degree.png")

# ─── Betweenness alto: un nodo puente entre dos clusters densos ──────────────
G2 = nx.Graph()
cluster_a = [f"a{i}" for i in range(4)]
cluster_b = [f"b{i}" for i in range(4)]
G2.add_edges_from([(u, v) for i, u in enumerate(cluster_a) for v in cluster_a[i + 1:]])
G2.add_edges_from([(u, v) for i, u in enumerate(cluster_b) for v in cluster_b[i + 1:]])
G2.add_edge("a0", "bridge")
G2.add_edge("bridge", "b0")

pos2 = {}
pos2.update(nx.circular_layout(cluster_a, center=(-1.3, 0), scale=0.55))
pos2.update(nx.circular_layout(cluster_b, center=(1.3, 0), scale=0.55))
pos2["bridge"] = (0, 0)

_draw(G2, pos2, highlight="bridge", path=OUT_DIR / "network_betweenness.png")

print("Guardado:", OUT_DIR / "network_degree.png")
print("Guardado:", OUT_DIR / "network_betweenness.png")
