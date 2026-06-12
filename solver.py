"""
CVRP Cartago – Modelo de Flujo de Red (MIP)
============================================
Variables:
  x[i,j]  ∈ Z+   número de camiones que recorren el arco (i,j)
  f[i,j]  ≥ 0    flujo de pallets en el arco (i,j)

Restricciones:
  R1  Σ x[i,v] − Σ x[v,j] = 0          ∀ v ∈ C   (camión entra − camión sale = 0)
  R2  Σ f[i,v] − Σ f[v,j] = q_v         ∀ v ∈ C   (flujo entra − flujo sale = demanda)
  R3  f[i,j] ≤ Q · x[i,j]               ∀ i,j     (Gran-M: acota camiones que salen)
  R4  Σ f[0,j] = Σ q_v                             (flujo total desde depósito)
  R5  Σ x[0,j] ≥ ⌈Σq/Q⌉                            (flota mínima)

Objetivo: min Σ d[i,j] · x[i,j]
"""

import math
import copy
import pulp

# ─────────────────────────────────────────────
#  DATOS FIJOS DEL EXCEL
# ─────────────────────────────────────────────
CANTONES = {
    0: "CD Cartago",
    1: "Cartago",
    2: "Paraíso",
    3: "La Unión",
    4: "Jiménez",
    5: "Turrialba",
    6: "Alvarado",
    7: "Oreamuno",
    8: "El Guarco",
}

DEMANDA_FIJA = {1: 124, 2: 48, 3: 75, 4: 15, 5: 61, 6: 12, 7: 36, 8: 35}

# Demanda desglosada por producto
DEMANDA_IMPERIAL = {1: 62, 2: 24, 3: 37, 4: 7,  5: 31, 6: 6,  7: 18, 8: 17}
DEMANDA_PILSEN   = {1: 31, 2: 12, 3: 19, 4: 4,  5: 15, 6: 3,  7:  9, 8:  9}
DEMANDA_TROPICAL = {1: 31, 2: 12, 3: 19, 4: 4,  5: 15, 6: 3,  7:  9, 8:  9}

# Matriz de distancias por carretera (km) — 9×9 simétrica
DIST = [
    [0,  0,  9, 10, 34, 34, 20,  6,  6],   # 0 CD Cartago
    [0,  0,  9, 10, 34, 34, 20,  6,  6],   # 1 Cartago
    [9,  9,  0, 19, 26, 28, 13,  7, 12],   # 2 Paraíso
    [10, 10, 19,  0, 45, 43, 29, 14, 11],  # 3 La Unión
    [34, 34, 26, 45,  0, 20, 21, 31, 37],  # 4 Jiménez
    [34, 34, 28, 43, 20,  0, 15, 29, 40],  # 5 Turrialba
    [20, 20, 13, 29, 21, 15,  0, 14, 25],  # 6 Alvarado
    [6,  6,  7, 14, 31, 29, 14,  0, 12],   # 7 Oreamuno
    [6,  6, 12, 11, 37, 40, 25, 12,  0],   # 8 El Guarco
]

Q_DEFAULT = 24
N = list(range(9))   # nodos 0..8
C = list(range(1, 9))  # clientes 1..8


# ─────────────────────────────────────────────
#  SOLVER MIP
# ─────────────────────────────────────────────
def solve_cvrp(demanda: dict, Q: int = Q_DEFAULT, time_limit: int = 120) -> dict:
    """
    Resuelve el CVRP como modelo de flujo de red con PuLP/CBC.

    Parámetros
    ----------
    demanda    : {1..8: pallets/semana}
    Q          : capacidad máxima por camión
    time_limit : segundos máximo para el solver

    Retorna dict con: status, objective, arcos, flujos, routes, K_min, total_dem
    """
    total_dem = sum(demanda.values())
    K_min = math.ceil(total_dem / Q)

    prob = pulp.LpProblem("CVRP_Cartago", pulp.LpMinimize)

    # Variables de decisión
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", lowBound=0, cat="Integer")
         for i in N for j in N if i != j}
    f = {(i, j): pulp.LpVariable(f"f_{i}_{j}", lowBound=0, cat="Continuous")
         for i in N for j in N if i != j}

    # ── Función objetivo ──────────────────────
    prob += pulp.lpSum(DIST[i][j] * x[i, j]
                       for i in N for j in N if i != j), "MinKm"

    # ── R1: Camión entra − Camión sale = 0 ───
    for v in C:
        prob += (
            pulp.lpSum(x[i, v] for i in N if i != v) -
            pulp.lpSum(x[v, j] for j in N if j != v) == 0
        ), f"R1_veh_{v}"

    # ── R2: Flujo entra − Flujo sale = demanda ─
    for v in C:
        prob += (
            pulp.lpSum(f[i, v] for i in N if i != v) -
            pulp.lpSum(f[v, j] for j in N if j != v) == demanda[v]
        ), f"R2_flow_{v}"

    # ── R3: Gran-M — f[i,j] ≤ Q · x[i,j] ───
    for i in N:
        for j in N:
            if i != j:
                prob += f[i, j] <= Q * x[i, j], f"R3_bigM_{i}_{j}"

    # ── R4: Flujo total desde depósito ───────
    prob += (
        pulp.lpSum(f[0, j] for j in C) == total_dem
    ), "R4_depot_flow"

    # ── R5: Flota mínima ──────────────────────
    prob += (
        pulp.lpSum(x[0, j] for j in C) >= K_min
    ), "R5_fleet_min"

    # ── Resolver ─────────────────────────────
    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    obj    = pulp.value(prob.objective) if prob.objective else None

    # Extraer arcos y flujos activos
    arcos = {}
    for (i, j) in x:
        v = pulp.value(x[i, j])
        if v is not None and v > 0.5:
            arcos[(i, j)] = int(round(v))

    flujos = {}
    for (i, j) in f:
        v = pulp.value(f[i, j])
        if v is not None and v > 0.05:
            flujos[(i, j)] = round(v, 2)

    # Reconstruir rutas individuales con pallets exactos
    routes = _reconstruct_routes(arcos, flujos, demanda, Q)

    return {
        "status":    status,
        "objective": obj,
        "arcos":     arcos,
        "flujos":    flujos,
        "routes":    routes,
        "K_min":     K_min,
        "total_dem": total_dem,
        "demanda":   demanda,
    }


# ─────────────────────────────────────────────
#  RECONSTRUCCIÓN DE RUTAS CON PALLETS EXACTOS
# ─────────────────────────────────────────────
def _reconstruct_routes(arcos: dict, flujos: dict,
                        demanda: dict, Q: int) -> list:
    """
    Reconstruye las rutas individuales a partir de los arcos activos.
    Asigna pallets exactos a cada ruta usando los flujos del MIP.

    Retorna lista de dicts:
      id, route (lista nodos), km, pallets_por_canton, total_pallets
    """
    arcos_rem  = copy.deepcopy(arcos)
    flujos_rem = copy.deepcopy(flujos)
    routes_raw = []

    # Contar salidas desde depósito para saber cuántos viajes
    starts = []
    for j in C:
        for _ in range(arcos_rem.get((0, j), 0)):
            starts.append(j)

    for s in starts:
        route = [0, s]
        arcos_rem[(0, s)] = arcos_rem.get((0, s), 0) - 1
        cur = s
        for _ in range(len(C) + 2):
            next_node = None
            for j in C:
                if j != cur and arcos_rem.get((cur, j), 0) > 0:
                    next_node = j
                    break
            if next_node is None:
                break
            route.append(next_node)
            arcos_rem[(cur, next_node)] -= 1
            cur = next_node
        route.append(0)
        routes_raw.append(route)

    # ── Calcular pallets exactos por ruta ────────────────────────────
    # Para cada cantón, distribuir su demanda entre sus visitas.
    # Se usa el flujo del primer arco (0 → primer_nodo) dividido
    # por el número total de viajes a ese primer nodo.
    arc_trip_index = {}   # (i,j) → contador de uso
    routes_info = []

    for idx, route in enumerate(routes_raw):
        km = sum(DIST[route[k]][route[k + 1]]
                 for k in range(len(route) - 1))

        # Pallets: seguimos el flujo arco a arco
        # f_entrada al primer nodo = flujo total en arco (0,s) / x[0,s]
        s = route[1]
        total_x_0s = arcos.get((0, s), 1)
        f_0s       = flujos.get((0, s), 0)
        pallets_entrada = round(f_0s / total_x_0s) if total_x_0s > 0 else 0

        # Seguir el flujo a lo largo de la ruta para saber cuánto
        # se entrega en cada cantón (simplificación proporcional)
        pallets_por_canton: dict[int, int] = {}
        carga_restante = pallets_entrada
        for k in range(1, len(route) - 1):
            nodo = route[k]
            # Cuánto flujo sale de este nodo hacia adelante en la ruta
            nodo_siguiente = route[k + 1] if k + 1 < len(route) - 1 else 0
            f_sal = flujos.get((nodo, nodo_siguiente), 0) if nodo_siguiente != 0 else 0
            entrega = max(0, carga_restante - round(f_sal / max(arcos.get((nodo, nodo_siguiente), 1), 1))
                          ) if nodo_siguiente != 0 else carga_restante
            entrega = min(entrega, demanda[nodo], carga_restante)
            pallets_por_canton[nodo] = entrega
            carga_restante -= entrega

        # Si quedaron pallets sin asignar por redondeos, asignar al último nodo
        if carga_restante > 0 and len(route) > 2:
            last_c = route[-2]
            pallets_por_canton[last_c] = pallets_por_canton.get(last_c, 0) + carga_restante

        total_pal = sum(pallets_por_canton.values())

        routes_info.append({
            "id":                idx + 1,
            "route":             route,
            "km":                km,
            "pallets_por_canton": pallets_por_canton,
            "total_pallets":     total_pal,
        })

    return routes_info
