from fastapi import FastAPI
import redis
import json
import time

app = FastAPI()

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

@app.get("/metricas")
def obtener_metricas():
    eventos = redis_client.lrange("metricas", 0, -1)
    eventos = [json.loads(e) for e in eventos]

    if not eventos:
        return {"total": 0, "hits": 0, "misses": 0, "hit_rate": 0}

    hits = [e for e in eventos if e["tipo"] == "hit"]
    misses = [e for e in eventos if e["tipo"] == "miss"]

    total = len(eventos)
    n_hits = len(hits)
    n_misses = len(misses)

    latencias = [e["latencia"] for e in eventos]
    latencias_sorted = sorted(latencias)
    p50 = latencias_sorted[int(len(latencias_sorted) * 0.50)]
    p95 = latencias_sorted[int(len(latencias_sorted) * 0.95)]

    return {
        "total": total,
        "hits": n_hits,
        "misses": n_misses,
        "hit_rate": round(n_hits / total, 4),
        "latencia_p50": round(p50, 4),
        "latencia_p95": round(p95, 4),
    }

@app.get("/metricas/por-consulta")
def metricas_por_consulta():
    eventos = redis_client.lrange("metricas", 0, -1)
    eventos = [json.loads(e) for e in eventos]

    resumen = {}
    for e in eventos:
        consulta = e["consulta"]
        if consulta not in resumen:
            resumen[consulta] = {"hits": 0, "misses": 0, "latencias": []}
        if e["tipo"] == "hit":
            resumen[consulta]["hits"] += 1
        else:
            resumen[consulta]["misses"] += 1
        resumen[consulta]["latencias"].append(e["latencia"])

    resultado = {}
    for consulta, datos in resumen.items():
        total = datos["hits"] + datos["misses"]
        resultado[consulta] = {
            "hits": datos["hits"],
            "misses": datos["misses"],
            "hit_rate": round(datos["hits"] / total, 4) if total > 0 else 0,
            "latencia_promedio": round(sum(datos["latencias"]) / len(datos["latencias"]), 4)
        }

    return resultado

@app.get("/metricas/limpiar")
def limpiar_metricas():
    redis_client.delete("metricas")
    redis_client.flushdb()
    return {"status": "métricas y caché eliminados"}

@app.get("/metricas/evictions")
def obtener_evictions():
    info = redis_client.info("stats")
    evictions = info.get("evicted_keys", 0)
    return {"evictions_total": evictions}

@app.get("/health")
def health():
    return {"status": "ok"}