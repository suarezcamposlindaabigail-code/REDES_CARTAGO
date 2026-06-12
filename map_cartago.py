"""
Mapa de los Cantones de la Provincia de Cartago, Costa Rica
===========================================================
Polígonos y centroides trazados sobre la geografía real de la provincia.
Canvas normalizado 0–100 (x=este, y=norte).
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon
import numpy as np

# ─── Centroides geográficos (canvas 0-100) ─────────────────────────────
# Basados en la posición relativa real de cada cantón en Cartago
CENTROIDS = {
    0: (27.0, 47.0),   # CD Cartago (depósito – cantón central)
    1: (28.5, 48.0),   # Cartago
    2: (43.0, 59.0),   # Paraíso
    3: (13.0, 47.0),   # La Unión
    4: (64.0, 54.0),   # Jiménez
    5: (80.0, 43.0),   # Turrialba
    6: (51.0, 34.0),   # Alvarado
    7: (36.0, 25.0),   # Oreamuno
    8: (24.0, 64.0),   # El Guarco
}

# ─── Polígonos de cantones (coordenadas x,y) ────────────────────────────
# Trazados para reflejar la forma aproximada real de cada cantón
CANTON_POLYS = {
    # Cartago – cantón central compacto
    1: [(18,39),(29,36),(38,39),(41,49),(36,57),(26,57),(20,52),(17,46)],
    # Paraíso – al este de Cartago, largo norte-sur
    2: [(36,57),(41,49),(55,53),(58,68),(52,74),(38,71),(33,63)],
    # La Unión – al oeste, compacto
    3: [(4,39),(18,39),(17,46),(20,52),(14,57),(7,55),(3,48)],
    # Jiménez – al este, tamaño mediano
    4: [(55,43),(68,41),(72,60),(64,68),(55,63),(52,53)],
    # Turrialba – el más grande, al este
    5: [(68,21),(97,18),(98,65),(78,68),(68,65),(64,46),(68,41)],
    # Alvarado – norte, volcánico
    6: [(38,21),(58,18),(68,21),(68,41),(55,43),(52,53),(44,35),(38,27)],
    # Oreamuno – norte de Cartago
    7: [(17,19),(38,16),(38,21),(38,27),(29,36),(18,39),(14,29)],
    # El Guarco – sur de Cartago
    8: [(14,57),(26,57),(33,63),(38,71),(28,77),(18,78),(9,68),(7,55)],
}

# ─── Colores suaves por cantón ──────────────────────────────────────────
CANTON_COLORS = {
    1: "#5b9bd5",   # Cartago       – azul
    2: "#70ad47",   # Paraíso       – verde
    3: "#ed7d31",   # La Unión      – naranja
    4: "#ffc000",   # Jiménez       – amarillo
    5: "#4bacc6",   # Turrialba     – celeste
    6: "#9dc3e6",   # Alvarado      – azul claro
    7: "#a9d18e",   # Oreamuno      – verde claro
    8: "#c5a3d0",   # El Guarco     – lila
}

# Colores para las rutas (hasta 21 viajes)
ROUTE_COLORS = [
    "#ff4757", "#2ed573", "#ffa502", "#1e90ff", "#ff6b81",
    "#7bed9f", "#eccc68", "#70a1ff", "#ff6348", "#2ed573",
    "#a29bfe", "#fd79a8", "#00cec9", "#fdcb6e", "#e17055",
    "#74b9ff", "#55efc4", "#fab1a0", "#81ecec", "#dfe6e9",
    "#b2bec3",
]

# Etiquetas para el mapa
LABEL = {
    0: "CD\nCartago",
    1: "Cartago",
    2: "Paraíso",
    3: "La\nUnión",
    4: "Jiménez",
    5: "Turrialba",
    6: "Alvarado",
    7: "Oreamuno",
    8: "El\nGuarco",
}

# Offsets de texto para evitar solapamiento
LABEL_OFFSET = {
    0: (0,   -4.5),
    1: (2.5, -4),
    2: (3,   -4),
    3: (-2,  -4),
    4: (3,   -3.5),
    5: (3,   -3.5),
    6: (3.5, -3.5),
    7: (0,   -4),
    8: (0,    4),
}


# ─────────────────────────────────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────
def draw_cartago_map(routes_info: list,
                     title: str = "CVRP · Cartago",
                     figsize: tuple = (14, 10.5)) -> plt.Figure:
    """
    Dibuja el mapa de Cartago con las rutas CVRP superpuestas.

    routes_info : lista de dicts {id, route, km, total_pallets}
    """
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")
    ax.set_xlim(0, 102)
    ax.set_ylim(10, 92)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── 1. Polígonos de cantones ──────────────────────────────────────
    for cid, poly_pts in CANTON_POLYS.items():
        arr = np.array(poly_pts)
        patch = MplPolygon(arr, closed=True,
                           facecolor=CANTON_COLORS[cid],
                           edgecolor="#0f172a",
                           linewidth=2.0,
                           alpha=0.30,
                           zorder=1)
        ax.add_patch(patch)
        # Borde visible
        patch2 = MplPolygon(arr, closed=True,
                            facecolor="none",
                            edgecolor=CANTON_COLORS[cid],
                            linewidth=1.4,
                            alpha=0.70,
                            zorder=2)
        ax.add_patch(patch2)

    # ── 2. Rutas: flechas con offset para rutas paralelas ─────────────
    # Agrupar arcos y cuántas veces se usa cada uno
    arc_drawn_count = {}

    for idx, rinfo in enumerate(routes_info):
        color = ROUTE_COLORS[idx % len(ROUTE_COLORS)]
        route = rinfo["route"]

        for k in range(len(route) - 1):
            i, j = route[k], route[k + 1]
            arc_key = (i, j)
            arc_drawn_count[arc_key] = arc_drawn_count.get(arc_key, 0) + 1
            pass_num = arc_drawn_count[arc_key]

            xi, yi = CENTROIDS[i]
            xj, yj = CENTROIDS[j]

            # Radio de curvatura: aumenta con cada paso adicional
            rad = (pass_num - 1) * 0.22
            # Alternar sentido de curvatura para separar mejor
            if pass_num % 2 == 0:
                rad = -rad

            ax.annotate(
                "",
                xy=(xj, yj),
                xytext=(xi, yi),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=color,
                    lw=1.8,
                    mutation_scale=11,
                    connectionstyle=f"arc3,rad={rad:.2f}",
                    alpha=0.85,
                ),
                zorder=4,
            )

    # ── 3. Nodos ──────────────────────────────────────────────────────
    for nid, (xc, yc) in CENTROIDS.items():
        is_depot = nid == 0
        color    = "#ffd700" if is_depot else "#f1f5f9"
        size     = 230 if is_depot else 120
        zw       = 8 if is_depot else 6

        ax.scatter(xc, yc, s=size, color=color, zorder=zw,
                   edgecolors="#0f172a", linewidths=1.8)

        dx, dy = LABEL_OFFSET.get(nid, (3, -4))
        txt = ax.text(
            xc + dx, yc + dy,
            LABEL[nid],
            fontsize=8.5 if not is_depot else 9,
            color="#ffd700" if is_depot else "#e2e8f0",
            fontweight="bold",
            ha="center", va="center",
            zorder=9,
        )
        txt.set_path_effects([
            pe.withStroke(linewidth=3, foreground="#0f172a")
        ])

    # ── 4. Leyenda de rutas ───────────────────────────────────────────
    total_km = sum(r["km"] for r in routes_info)
    handles = []
    for rinfo in routes_info:
        stops_mid = [rinfo["route"][k] for k in range(1, len(rinfo["route"]) - 1)]
        stops_str = "→".join(str(n) for n in stops_mid)
        label = (f"V{rinfo['id']:02d}: 0→{stops_str}→0  "
                 f"[{rinfo['total_pallets']} pal · {rinfo['km']} km]")
        handles.append(mpatches.Patch(
            color=ROUTE_COLORS[(rinfo["id"] - 1) % len(ROUTE_COLORS)],
            label=label,
        ))

    leg = ax.legend(
        handles=handles,
        loc="lower right",
        fontsize=6.0,
        facecolor="#1e293b",
        labelcolor="#e2e8f0",
        edgecolor="#334155",
        framealpha=0.96,
        ncol=2,
        title=f"  {len(routes_info)} viajes · {int(total_km)} km totales  ",
        title_fontsize=7.5,
        borderpad=0.8,
        labelspacing=0.4,
    )
    leg.get_title().set_color("#fbbf24")

    # ── 5. Título y anotaciones ───────────────────────────────────────
    ax.set_title(
        title,
        color="#f1f5f9",
        fontsize=14,
        fontweight="bold",
        pad=14,
        loc="left",
    )

    # Escudo/logo UCR pequeño como texto
    ax.text(
        99, 88,
        "UCR · II-1122",
        color="#64748b", fontsize=7.5,
        ha="right", va="top", style="italic",
        zorder=10,
    )

    # Brújula
    ax.text(3, 88, "N", color="#94a3b8", fontsize=11,
            fontweight="bold", ha="center", zorder=10)
    ax.annotate("", xy=(3, 86), xytext=(3, 83),
                arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.5),
                zorder=10)

    plt.tight_layout(pad=0.8)
    return fig
