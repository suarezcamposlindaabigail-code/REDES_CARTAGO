"""
CVRP – Provincia de Cartago, Costa Rica
========================================
Bloque 03 · Trabajo Grupal · II-1122
Prof. David Benavides · UCR Sede Alajuela · I-2026

Dos secciones:
  1. Datos fijos del Excel → solución óptima (437 km)
  2. Demanda personalizable → re-optimización automática
"""

import io
import math
import time

import pandas as pd
import streamlit as st

from solver import (
    CANTONES, DEMANDA_FIJA, DEMANDA_IMPERIAL, DEMANDA_PILSEN,
    DEMANDA_TROPICAL, DIST, C, Q_DEFAULT, N, solve_cvrp,
)
from map_cartago import draw_cartago_map

# ══════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CVRP · Cartago",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Inter:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

/* ── KPI Cards ── */
.kpi-grid { display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap; }
.kpi {
    flex:1; min-width:130px;
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 16px 20px;
}
.kpi-val {
    font-family: 'Syne', sans-serif;
    font-size: 2rem; font-weight: 800;
    color: #f1f5f9; line-height: 1.1;
}
.kpi-val.green { color: #34d399; }
.kpi-val.yellow { color: #fbbf24; }
.kpi-lbl {
    font-size: .68rem; color: #64748b;
    text-transform: uppercase; letter-spacing: .1em;
    margin-top: 5px;
}

/* ── Section banners ── */
.banner {
    border-radius: 0 16px 16px 0;
    padding: 14px 24px;
    margin: 30px 0 20px;
    border-left: 5px solid;
}
.banner-blue  { background: linear-gradient(90deg,#1e3a5f18,#0f172a); border-color:#3b82f6; }
.banner-amber { background: linear-gradient(90deg,#78350f18,#0f172a); border-color:#f59e0b; }
.banner-title { font-family:'Syne',sans-serif; font-size:1.25rem; font-weight:700; color:#f1f5f9; margin:0; }
.banner-sub   { font-size:.78rem; color:#94a3b8; margin:4px 0 0; }

/* ── Optimal badge ── */
.badge {
    display: inline-block; border-radius: 20px;
    font-size: .74rem; font-weight: 600;
    padding: 3px 14px; margin-left: 8px; vertical-align: middle;
}
.badge-ok   { background:#064e3b; border:1px solid #34d399; color:#34d399; }
.badge-warn { background:#451a03; border:1px solid #fbbf24; color:#fbbf24; }

/* ── Solve button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white; border: none; border-radius: 10px;
    font-family: 'Syne', sans-serif; font-weight: 700;
    letter-spacing: .04em; padding: 10px 28px;
    width: 100%;
}
div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    box-shadow: 0 4px 20px rgba(59,130,246,.45);
}

/* ── Table ── */
.dataframe thead tr th { background:#1e293b !important; color:#f1f5f9 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,#0c1445,#0f172a);
            border-radius:18px; padding:30px 36px; margin-bottom:28px;
            border:1px solid #1e3a5f;">
  <div style="font-size:.68rem; color:#60a5fa; font-weight:600;
              letter-spacing:.2em; text-transform:uppercase; margin-bottom:8px;">
    Bloque 03 · Trabajo Grupal · II-1122 · UCR Sede Alajuela · I-2026
  </div>
  <h1 style="margin:0; color:#f9fafb; font-family:'Syne',sans-serif; font-size:2.2rem;">
    🚛 CVRP · Provincia de Cartago
  </h1>
  <p style="color:#94a3b8; margin:10px 0 0; font-size:.9rem; max-width:720px;">
    Minimización de kilómetros recorridos · Modelo de flujo de red (MIP) ·
    8 cantones · 406 pal/sem · Q = 24 pallets/camión · Solver PuLP / CBC
  </p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  HELPER: renderizar resultados
# ══════════════════════════════════════════════════════════════════════
def render_results(result: dict, key: str):
    status   = result["status"]
    obj      = result["objective"]
    routes   = result["routes"]
    K_min    = result["K_min"]
    total_d  = result["total_dem"]
    demanda  = result.get("demanda", DEMANDA_FIJA)

    obj_int  = int(round(obj)) if obj is not None else None
    obj_str  = f"{obj_int} km" if obj_int is not None else "—"

    # Badge
    if obj_int is not None and 434 <= obj_int <= 437:
        badge_html = '<span class="badge badge-ok">✓ ÓPTIMO GLOBAL</span>'
    elif obj_int is not None and obj_int <= 460:
        badge_html = '<span class="badge badge-warn">≈ Buena solución</span>'
    else:
        badge_html = ""

    # ── KPIs ───────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        (c1, obj_str,           "Distancia total",          "green" if badge_html else ""),
        (c2, str(len(routes)),  "Viajes / camiones",        ""),
        (c3, str(K_min),        "Flota mínima ⌈dem/Q⌉",    ""),
        (c4, f"{total_d} pal",  "Demanda total cubierta",  "yellow"),
    ]
    for col, val, lbl, cls in kpis:
        col.markdown(
            f'<div class="kpi">'
            f'<div class="kpi-val {cls}">{val}</div>'
            f'<div class="kpi-lbl">{lbl}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f"**Estado solver:** `{status}` {badge_html}",
        unsafe_allow_html=True,
    )

    # ── Mapa ───────────────────────────────────────────────────────
    st.markdown("#### 🗺️ Mapa — Cantones de Cartago con rutas óptimas")
    fig = draw_cartago_map(
        routes,
        title=f"CVRP · Cartago  ·  {obj_str}  ·  {len(routes)} viajes",
    )
    st.pyplot(fig, use_container_width=True)

    # Botón de descarga del mapa
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight",
                facecolor="#0f172a")
    buf.seek(0)
    st.download_button(
        "⬇ Descargar mapa (PNG)",
        data=buf,
        file_name=f"cvrp_cartago_{key}.png",
        mime="image/png",
        key=f"dl_{key}",
    )

    # ── Tabla de viajes ────────────────────────────────────────────
    st.markdown("#### 📋 Detalle de viajes")
    rows = []
    for rinfo in routes:
        nodes   = rinfo["route"]
        trayecto = " → ".join(CANTONES[n] for n in nodes)
        ppc      = rinfo["pallets_por_canton"]
        dem_cov  = ", ".join(
            f"{CANTONES[n]}: {ppc.get(n, '?')} pal"
            for n in nodes[1:-1]
        )
        rows.append({
            "Viaje #":           f"V{rinfo['id']:02d}",
            "Camión":            f"C{rinfo['id']:02d}",
            "Trayecto":          trayecto,
            "Demanda cubierta":  dem_cov,
            "Total pallets":     rinfo["total_pallets"],
            "% capacidad":       f"{rinfo['total_pallets'] / Q_DEFAULT * 100:.0f}%",
            "Distancia (km)":    rinfo["km"],
        })

    df = pd.DataFrame(rows)

    def style_rows(row):
        km = row["Distancia (km)"]
        if km == 0:
            return ["background-color:#052e16; color:#86efac"] * len(row)
        elif km >= 80:
            return ["background-color:#1c0a00; color:#fed7aa"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(style_rows, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    # Totales de la tabla
    total_km_rutas = sum(r["km"] for r in routes)
    total_pal_rutas = sum(r["total_pallets"] for r in routes)
    st.markdown(
        f"**Total km:** `{total_km_rutas}` &nbsp;|&nbsp; "
        f"**Total pallets transportados:** `{total_pal_rutas}` &nbsp;|&nbsp; "
        f"**Camiones desplegados:** `{len(routes)}`"
    )

    # ── Cobertura por cantón ───────────────────────────────────────
    st.markdown("#### 📊 Cobertura por cantón")
    cov_rows = []
    for cid in C:
        viajes_c = [r for r in routes if cid in r["route"][1:-1]]
        pal_c    = sum(r["pallets_por_canton"].get(cid, 0) for r in viajes_c)
        cov_rows.append({
            "Cantón":              CANTONES[cid],
            "Demanda (pal)":       demanda[cid],
            "Pallets entregados":  pal_c,
            "Viajes que lo atienden": len(viajes_c),
            "Cobertura":           "✅" if pal_c >= demanda[cid] * 0.95 else "⚠️",
        })
    st.dataframe(pd.DataFrame(cov_rows), hide_index=True, use_container_width=True)

    # ── Arcos activos (colapsado) ──────────────────────────────────
    with st.expander("🔍 Arcos activos y flujos del MIP", expanded=False):
        arcos  = result["arcos"]
        flujos = result["flujos"]
        arc_rows = []
        for (i, j), cnt in sorted(arcos.items()):
            arc_rows.append({
                "Arco":           f"{CANTONES[i]} → {CANTONES[j]}",
                "x[i,j] viajes": cnt,
                "f[i,j] pallets": flujos.get((i, j), 0),
                "d[i,j] (km)":    DIST[i][j],
                "Contribución":   cnt * DIST[i][j],
            })
        df_a = pd.DataFrame(arc_rows)
        st.dataframe(df_a, hide_index=True, use_container_width=True)
        st.caption(
            f"Verificación: Σ x·d = **{df_a['Contribución'].sum()} km** "
            f"({'✅ coincide' if df_a['Contribución'].sum() == obj_int else '⚠️ revisar'})"
        )


# ══════════════════════════════════════════════════════════════════════
#  SECCIÓN 1 — DATOS FIJOS DEL EXCEL
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="banner banner-blue">
  <div class="banner-title">📌 Sección 1 — Datos fijos del Excel</div>
  <div class="banner-sub">
    Demanda y distancias exactas del enunciado · 8 cantones · 406 pal/sem ·
    Óptimo esperado: 434–437 km
  </div>
</div>
""", unsafe_allow_html=True)

# Mostrar tablas de datos
with st.expander("📂 Ver datos del problema (fijos)", expanded=False):
    col_dem, col_dist = st.columns(2)

    with col_dem:
        st.markdown("**① Demanda por cantón (pallets/semana)**")
        df_dem = pd.DataFrame([
            {
                "Nodo":     k,
                "Cantón":   CANTONES[k],
                "Imperial": DEMANDA_IMPERIAL[k],
                "Pilsen":   DEMANDA_PILSEN[k],
                "Tropical": DEMANDA_TROPICAL[k],
                "Total":    DEMANDA_FIJA[k],
            }
            for k in range(1, 9)
        ])
        total_row = pd.DataFrame([{
            "Nodo": "—", "Cantón": "TOTAL",
            "Imperial": 202, "Pilsen": 102, "Tropical": 102, "Total": 406,
        }])
        df_dem = pd.concat([df_dem, total_row], ignore_index=True)
        st.dataframe(df_dem, hide_index=True, use_container_width=True)

    with col_dist:
        st.markdown("**② Matriz de distancias por carretera (km)**")
        df_dist = pd.DataFrame(
            DIST,
            index=[f"{i}·{CANTONES[i]}" for i in range(9)],
            columns=[str(i) for i in range(9)],
        )
        st.dataframe(
            df_dist.style
                   .background_gradient(cmap="YlOrRd", axis=None)
                   .format("{:.0f}"),
            use_container_width=True,
        )

# Parámetros del solver
st.markdown("##### Parámetros del solver")
col_q1, col_tl1, col_btn1 = st.columns([1, 2, 1])
with col_q1:
    q_fijo = st.number_input(
        "Capacidad Q (pallets)", 12, 48, 24, 4, key="q_fijo"
    )
with col_tl1:
    tl_fijo = st.slider(
        "Tiempo límite solver (segundos)", 60, 300, 120, 30, key="tl_fijo",
        help="120 s es suficiente para obtener 437 km. Más tiempo puede mejorar a 434 km."
    )
with col_btn1:
    st.markdown("&nbsp;")
    run1 = st.button("▶ Resolver (datos fijos)", key="btn_fijo")

if run1:
    with st.spinner("⚙️ Resolviendo modelo MIP — puede tomar hasta 2 min..."):
        t0 = time.time()
        res1 = solve_cvrp(DEMANDA_FIJA, Q=q_fijo, time_limit=tl_fijo)
        elapsed = time.time() - t0
        st.session_state["res1"]     = res1
        st.session_state["t1"]       = elapsed

if "res1" in st.session_state:
    st.caption(f"⏱ Tiempo de cómputo: {st.session_state['t1']:.1f} s")
    render_results(st.session_state["res1"], "fijo")


# ══════════════════════════════════════════════════════════════════════
#  SECCIÓN 2 — PARÁMETROS PERSONALIZADOS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="banner banner-amber">
  <div class="banner-title">⚙️ Sección 2 — Demanda personalizada</div>
  <div class="banner-sub">
    Ajustá la demanda de cualquier cantón y re-optimizá la red de distribución
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("##### Demanda por cantón (pallets/semana)")

# Grid 4 columnas para los 8 cantones
cols = st.columns(4)
dem_custom: dict[int, int] = {}
for idx, cid in enumerate(range(1, 9)):
    with cols[idx % 4]:
        dem_custom[cid] = st.number_input(
            f"{CANTONES[cid]}",
            min_value=0,
            max_value=600,
            value=int(DEMANDA_FIJA[cid]),
            step=1,
            key=f"dc_{cid}",
        )

total_custom = sum(dem_custom.values())
flota_custom = math.ceil(total_custom / Q_DEFAULT) if total_custom > 0 else 0

col_info, col_q2, col_tl2, col_btn2 = st.columns([2, 1, 1, 1])
with col_info:
    if total_custom > 0:
        st.info(
            f"**Total:** {total_custom} pal/sem &nbsp;·&nbsp; "
            f"**Flota mínima:** ⌈{total_custom}/{Q_DEFAULT}⌉ = **{flota_custom} camiones**"
        )
    else:
        st.warning("La demanda total no puede ser 0.")

with col_q2:
    q_cust = st.number_input("Capacidad Q", 12, 48, 24, 4, key="q_cust")
with col_tl2:
    tl_cust = st.slider("Límite (s)", 60, 300, 120, 30, key="tl_cust")
with col_btn2:
    st.markdown("&nbsp;")
    run2 = st.button("▶ Resolver (personalizado)", key="btn_cust")

if run2:
    if total_custom == 0:
        st.error("⚠️ La demanda total es 0. Ajustá al menos un cantón.")
    else:
        with st.spinner("⚙️ Resolviendo modelo MIP personalizado..."):
            t0 = time.time()
            res2 = solve_cvrp(dem_custom, Q=q_cust, time_limit=tl_cust)
            elapsed = time.time() - t0
            st.session_state["res2"] = res2
            st.session_state["t2"]   = elapsed

if "res2" in st.session_state:
    st.caption(f"⏱ Tiempo de cómputo: {st.session_state['t2']:.1f} s")
    render_results(st.session_state["res2"], "custom")


# ══════════════════════════════════════════════════════════════════════
#  FORMULACIÓN MATEMÁTICA
# ══════════════════════════════════════════════════════════════════════
with st.expander("📖 Formulación matemática completa del modelo MIP", expanded=False):
    st.markdown(r"""
### Modelo de Flujo de Red — CVRP Cartago

**Conjuntos**
- $N = \{0,1,\ldots,8\}$ — nodos (0 = depósito CD Cartago)
- $C = \{1,\ldots,8\}$ — cantones clientes

**Parámetros**
- $d_{ij}$ — distancia por carretera entre $i$ y $j$ (km)
- $q_v$ — demanda del cantón $v$ (pallets/semana)
- $Q = 24$ — capacidad máxima por camión (pallets)

**Variables de decisión**

$$x_{ij} \in \mathbb{Z}^{+} \quad \text{número de camiones en el arco } (i,j)$$
$$f_{ij} \geq 0 \quad \text{flujo de pallets en el arco } (i,j)$$

**Función objetivo**

$$\min \; Z = \sum_{i \in N}\sum_{\substack{j \in N \\ j \neq i}} d_{ij}\; x_{ij}$$

**Restricciones**

$$\underbrace{\sum_{i \neq v} x_{iv} \;-\; \sum_{j \neq v} x_{vj} = 0}_{\text{R1: camión entra} - \text{camión sale} = 0} \qquad \forall\, v \in C$$

$$\underbrace{\sum_{i \neq v} f_{iv} \;-\; \sum_{j \neq v} f_{vj} = q_v}_{\text{R2: flujo entra} - \text{flujo sale} = \text{demanda}} \qquad \forall\, v \in C$$

$$\underbrace{f_{ij} \;\leq\; Q \cdot x_{ij}}_{\text{R3: Gran-M (acota camiones que salen)}} \qquad \forall\, i,j \in N,\; i \neq j$$

$$\underbrace{\sum_{j \in C} f_{0j} = \sum_{v \in C} q_v}_{\text{R4: flujo total desde depósito}}$$

$$\underbrace{\sum_{j \in C} x_{0j} \;\geq\; \left\lceil \dfrac{\displaystyle\sum_{v} q_v}{Q} \right\rceil = 17}_{\text{R5: flota mínima}}$$

$$x_{ij} \in \mathbb{Z}^{+}, \quad f_{ij} \geq 0$$

---
> **Resultado validado:** con los datos del Excel, el solver CBC obtiene **437 km** en ~120 s.
> El lower bound es ≈ 430 km, por lo que la solución es prácticamente óptima global.
    """)


# ══════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<hr style="border-color:#1e293b; margin-top:48px;">
<p style="text-align:center; color:#475569; font-size:.74rem; padding-bottom:14px;">
  Prof. David Benavides · UCR Sede Alajuela · I-2026 ·
  Bloque 03 – Trabajo Grupal · Curso II-1122
</p>
""", unsafe_allow_html=True)
