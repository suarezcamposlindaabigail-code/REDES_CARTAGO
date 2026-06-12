# 🚛 CVRP – Provincia de Cartago, Costa Rica

**Bloque 03 · Trabajo Grupal · II-1122**  
Prof. David Benavides · UCR Sede Alajuela · I-2026

---

## Descripción

Aplicación que resuelve el **CVRP (Capacitated Vehicle Routing Problem)** para la
distribución de productos desde el Centro de Distribución (CD) de Cartago hacia los
8 cantones de la provincia, minimizando la distancia total recorrida.

### Modelo — Flujo de Red (MIP)

| Restricción | Ecuación |
|---|---|
| **R1** Camión entra − camión sale = 0 | `Σ x[i,v] − Σ x[v,j] = 0` ∀ v ∈ C |
| **R2** Flujo entra − flujo sale = demanda | `Σ f[i,v] − Σ f[v,j] = q_v` ∀ v ∈ C |
| **R3** Gran-M (acota camiones que salen) | `f[i,j] ≤ Q · x[i,j]` ∀ i,j |
| **R4** Flujo total desde depósito | `Σ f[0,j] = Σ q_v` |
| **R5** Flota mínima | `Σ x[0,j] ≥ ⌈406/24⌉ = 17` |

**Objetivo:** `min Σ d[i,j] · x[i,j]`  
**Óptimo validado:** **437 km** (lower bound ≈ 430 km → solución prácticamente óptima)

---

## Archivos

```
├── app.py              ← Streamlit (Sección 1: fija · Sección 2: personalizada)
├── solver.py           ← Modelo MIP con PuLP/CBC + reconstrucción de rutas
├── map_cartago.py      ← Mapa visual de cantones con rutas superpuestas
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml     ← Tema oscuro
```

## Instalación local

```bash
git clone https://github.com/<usuario>/cvrp-cartago.git
cd cvrp-cartago
pip install -r requirements.txt
streamlit run app.py
```

## Despliegue en Streamlit Cloud

1. Subí los 5 archivos/carpetas a GitHub
2. Ir a [share.streamlit.io](https://share.streamlit.io)
3. Conectar repo → `app.py` → **Deploy**

---

## Datos del problema

| Cantón | Nodo | Demanda (pal/sem) |
|---|---|---|
| Cartago | 1 | 124 |
| Paraíso | 2 | 48 |
| La Unión | 3 | 75 |
| Jiménez | 4 | 15 |
| Turrialba | 5 | 61 |
| Alvarado | 6 | 12 |
| Oreamuno | 7 | 36 |
| El Guarco | 8 | 35 |
| **TOTAL** | | **406** |

*UCR Sede Alajuela · I-2026*
