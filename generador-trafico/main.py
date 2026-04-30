import httpx
import numpy as np
import time
import random
import asyncio
import os

# Configuración 
CACHE_URL = "http://cache:8002"
ZONAS = ["Z1", "Z2", "Z3", "Z4", "Z5"]
CONSULTAS = ["q1", "q2", "q3", "q4", "q5"]
TOTAL_CONSULTAS = 1000 #Se dejó en 1000 para que se pueda probar rapidamente, pero en los experimentos realizados...
# ... se utilizaron 15.000 y 50.000 consultas! (descrito en el informe)
INTERVALO = 0.01 

# Distribución Zipf
def get_zona_zipf():
    pesos = [1 / (i + 1) for i in range(len(ZONAS))]
    pesos = [p / sum(pesos) for p in pesos]
    return np.random.choice(ZONAS, p=pesos)

# Distribución Uniforme
def get_zona_uniforme():
    return random.choice(ZONAS)

# Generar parámetros por tipo de consulta
MODO = os.getenv("MODO", "aleatorio")

def generar_params(tipo: str, zona: str):
    if MODO == "fijo":
        confidence_values = [0.0, 0.3, 0.5, 0.7, 0.9]
        bins_values = [5, 10]
    else:
        confidence_values = [round(random.uniform(0.0, 1.0), 2) for _ in range(100)]
        bins_values = list(range(2, 21))

    if tipo == "q1":
        return {"zona_id": zona, "confidence_min": random.choice(confidence_values)}
    elif tipo == "q2":
        return {"zona_id": zona, "confidence_min": random.choice(confidence_values)}
    elif tipo == "q3":
        return {"zona_id": zona, "confidence_min": random.choice(confidence_values)}
    elif tipo == "q4":
        zona_b = random.choice([z for z in ZONAS if z != zona])
        return {"zona_a": zona, "zona_b": zona_b, "confidence_min": random.choice(confidence_values)}
    elif tipo == "q5":
        return {"zona_id": zona, "bins": random.choice(bins_values)}

# Ejecutar consultas
async def ejecutar_consultas(distribucion: str):
    print(f"\n Iniciando {TOTAL_CONSULTAS} consultas con distribución {distribucion}...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(TOTAL_CONSULTAS):
            tipo = random.choice(CONSULTAS)
            zona = get_zona_zipf() if distribucion == "zipf" else get_zona_uniforme()
            params = generar_params(tipo, zona)

            try:
                response = await client.get(f"{CACHE_URL}/{tipo}", params=params)
                fuente = response.json().get("fuente", "?")
                print(f"  [{i+1}/{TOTAL_CONSULTAS}] {tipo} {zona} → {fuente}")
            except Exception as e:
                print(f"  [{i+1}/{TOTAL_CONSULTAS}] Error: {e}")

            await asyncio.sleep(INTERVALO)

    print(f"\n Consultas completadas con distribución {distribucion}")

async def main():
    print("Esperando que los servicios estén listos...")
    await asyncio.sleep(10)

    # Limpiar métricas antes de empezar
    async with httpx.AsyncClient() as client:
        await client.get("http://almacenamiento-metricas:8003/metricas/limpiar")

    # Ronda 1 — Distribución uniforme
    await ejecutar_consultas("uniforme")

    # Guardar métricas de uniforme
    async with httpx.AsyncClient() as client:
        r_uniforme = await client.get("http://almacenamiento-metricas:8003/metricas")
        await client.get("http://almacenamiento-metricas:8003/metricas/limpiar")

    await asyncio.sleep(5)

    # Ronda 2 — Distribución Zipf
    await ejecutar_consultas("zipf")

    # Guardar métricas de Zipf
    async with httpx.AsyncClient() as client:
        r_zipf = await client.get("http://almacenamiento-metricas:8003/metricas")
        r_evictions = await client.get("http://almacenamiento-metricas:8003/metricas/evictions")

    # Mostrar ambas juntas al final
    print("\n" + "="*50)
    print("Resultados Obtenidos")
    print("="*50)
    print(f"Distribucion UNIFORME: {r_uniforme.text}")
    print(f"Distribucion ZIPF:     {r_zipf.text}")
    print(f"Evictions Totales: {r_evictions.text}")
    print("="*50)
    
if __name__ == "__main__":
    asyncio.run(main())