from fastapi import FastAPI
import redis
import httpx
import json
import time
import os

app = FastAPI()

# ── Conexión a Redis ──────────────────────────────────────────────────────────
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

# ── URL del generador de respuestas ──────────────────────────────────────────
GENERADOR_URL = "http://generador-respuestas:8001"

import os

# ── TTL por tipo de consulta (segundos) ───────────────────────────────────────
TTL_VALOR = int(os.getenv("TTL", "300"))
TTL_POR_CONSULTA = {
    "q1": TTL_VALOR,
    "q2": TTL_VALOR,
    "q3": TTL_VALOR,
    "q4": TTL_VALOR,
    "q5": TTL_VALOR,
}

# ── Función principal de caché ───────────────────────────────────────────────
async def procesar_consulta(tipo: str, params: dict):
    # Generar cache key
    params_str = ":".join(f"{k}={v}" for k, v in sorted(params.items()))
    cache_key = f"{tipo}:{params_str}"

    inicio = time.time()

    # Buscar en caché
    resultado_cache = redis_client.get(cache_key)

    if resultado_cache:
        # Cache HIT
        latencia = time.time() - inicio
        registrar_metrica("hit", tipo, latencia)
        return {"fuente": "cache", "cache_key": cache_key, "resultado": json.loads(resultado_cache)}

    # Cache MISS — consultar al generador de respuestas
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{GENERADOR_URL}/{tipo}", params=params)
        resultado = response.json()

    # Guardar en caché con TTL
    ttl = TTL_POR_CONSULTA.get(tipo, 300)
    redis_client.setex(cache_key, ttl, json.dumps(resultado))

    latencia = time.time() - inicio
    registrar_metrica("miss", tipo, latencia)

    return {"fuente": "generador", "cache_key": cache_key, "resultado": resultado}

# ── Registro de métricas ──────────────────────────────────────────────────────
def registrar_metrica(tipo_evento: str, consulta: str, latencia: float):
    evento = {
        "tipo": tipo_evento,
        "consulta": consulta,
        "latencia": latencia,
        "timestamp": time.time()
    }
    redis_client.lpush("metricas", json.dumps(evento))

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/q1")
async def q1(zona_id: str, confidence_min: float = 0.0):
    return await procesar_consulta("q1", {"zona_id": zona_id, "confidence_min": confidence_min})

@app.get("/q2")
async def q2(zona_id: str, confidence_min: float = 0.0):
    return await procesar_consulta("q2", {"zona_id": zona_id, "confidence_min": confidence_min})

@app.get("/q3")
async def q3(zona_id: str, confidence_min: float = 0.0):
    return await procesar_consulta("q3", {"zona_id": zona_id, "confidence_min": confidence_min})

@app.get("/q4")
async def q4(zona_a: str, zona_b: str, confidence_min: float = 0.0):
    return await procesar_consulta("q4", {"zona_a": zona_a, "zona_b": zona_b, "confidence_min": confidence_min})

@app.get("/q5")
async def q5(zona_id: str, bins: int = 5):
    return await procesar_consulta("q5", {"zona_id": zona_id, "bins": bins})

@app.get("/health")
def health():
    return {"status": "ok"}