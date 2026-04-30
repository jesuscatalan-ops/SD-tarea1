from fastapi import FastAPI
import pandas as pd
import numpy as np
import os

app = FastAPI()

# ── Zonas definidas en el enunciado ──────────────────────────────────────────
ZONAS = {
    "Z1": {"lat_min": -33.445, "lat_max": -33.420, "lon_min": -70.640, "lon_max": -70.600},
    "Z2": {"lat_min": -33.420, "lat_max": -33.390, "lon_min": -70.600, "lon_max": -70.550},
    "Z3": {"lat_min": -33.530, "lat_max": -33.490, "lon_min": -70.790, "lon_max": -70.740},
    "Z4": {"lat_min": -33.460, "lat_max": -33.430, "lon_min": -70.670, "lon_max": -70.630},
    "Z5": {"lat_min": -33.470, "lat_max": -33.430, "lon_min": -70.810, "lon_max": -70.760},
}

# ── Área de cada zona en km² ──────────────────────────────────────────────────
def calcular_area_km2(zona):
    lat_diff = abs(zona["lat_max"] - zona["lat_min"]) * 111
    lon_diff = abs(zona["lon_max"] - zona["lon_min"]) * 111
    return lat_diff * lon_diff

ZONAS_AREA_KM2 = {z: calcular_area_km2(ZONAS[z]) for z in ZONAS}

# ── Carga del dataset ─────────────────────────────────────────────────────────
DATA = {}

def cargar_datos():
    ruta = "/app/datos/dataset.csv"
    if not os.path.exists(ruta):
        print("⚠️  dataset.csv no encontrado, generando datos sintéticos...")
        generar_datos_sinteticos()
        return

    print("📂 Cargando dataset real...")
    df = pd.read_csv(ruta)
    for zona_id, zona in ZONAS.items():
        filtro = (
            (df["latitude"] >= zona["lat_min"]) & (df["latitude"] <= zona["lat_max"]) &
            (df["longitude"] >= zona["lon_min"]) & (df["longitude"] <= zona["lon_max"])
        )
        DATA[zona_id] = df[filtro][["latitude", "longitude", "area_in_meters", "confidence"]].to_dict("records")
        print(f"  {zona_id}: {len(DATA[zona_id])} edificios cargados")

def generar_datos_sinteticos():
    print("🔧 Generando datos sintéticos por zona...")
    for zona_id, zona in ZONAS.items():
        n = np.random.randint(500, 2000)
        DATA[zona_id] = [
            {
                "latitude": np.random.uniform(zona["lat_min"], zona["lat_max"]),
                "longitude": np.random.uniform(zona["lon_min"], zona["lon_max"]),
                "area_in_meters": np.random.uniform(50, 500),
                "confidence": np.random.uniform(0.5, 1.0),
            }
            for _ in range(n)
        ]
        print(f"  {zona_id}: {n} edificios sintéticos generados")

cargar_datos()

# ── Consultas Q1–Q5 ───────────────────────────────────────────────────────────
@app.get("/q1")
def q1_count(zona_id: str, confidence_min: float = 0.0):
    registros = DATA.get(zona_id, [])
    conteo = sum(1 for r in registros if r["confidence"] >= confidence_min)
    return {"zona_id": zona_id, "conteo": conteo, "confidence_min": confidence_min}

@app.get("/q2")
def q2_area(zona_id: str, confidence_min: float = 0.0):
    areas = [r["area_in_meters"] for r in DATA.get(zona_id, []) if r["confidence"] >= confidence_min]
    if not areas:
        return {"zona_id": zona_id, "avg_area": 0, "total_area": 0, "n": 0}
    return {"zona_id": zona_id, "avg_area": np.mean(areas), "total_area": np.sum(areas), "n": len(areas)}

@app.get("/q3")
def q3_densidad(zona_id: str, confidence_min: float = 0.0):
    conteo = q1_count(zona_id, confidence_min)["conteo"]
    area_km2 = ZONAS_AREA_KM2.get(zona_id, 1)
    return {"zona_id": zona_id, "densidad_por_km2": conteo / area_km2, "confidence_min": confidence_min}

@app.get("/q4")
def q4_comparar(zona_a: str, zona_b: str, confidence_min: float = 0.0):
    da = q3_densidad(zona_a, confidence_min)["densidad_por_km2"]
    db = q3_densidad(zona_b, confidence_min)["densidad_por_km2"]
    return {"zona_a": da, "zona_b": db, "ganador": zona_a if da > db else zona_b}

@app.get("/q5")
def q5_confianza(zona_id: str, bins: int = 5):
    scores = [r["confidence"] for r in DATA.get(zona_id, [])]
    conteos, bordes = np.histogram(scores, bins=bins, range=(0, 1))
    return [{"bucket": i, "min": bordes[i], "max": bordes[i+1], "conteo": int(conteos[i])} for i in range(bins)]

@app.get("/health")
def health():
    return {"status": "ok", "zonas": {z: len(DATA.get(z, [])) for z in ZONAS}}