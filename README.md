# S.D-tarea1 — Plataforma de Análisis de Edificaciones con Caché

Sistema distribuido de 4 servicios para el análisis de datos geoespaciales  de la Región Metropolitana de Santiago, con caché basado en Redis.

## Requisitos

- Docker
- Docker Compose

## Configuración previa

Antes de levantar el sistema se necesita el dataset filtrado (sólo a la región metropolitana)

1. Descargar el archivo `967_buildings.csv` desde Google Open Buildings: (https://sites.research.google/gr/open-buildings/) 
y colocarlo en la carpeta `datos/`.

2. Ejecutar el script de filtrado:

```bash
python3 filtrar_dataset.py
```

Esto genera el archivo `datos/dataset.csv` con las edificaciones de las 5 zonas de Santiago a estudiar.

## Levantar el sistema

```bash
docker compose up
```

Esto levanta los 4 servicios automáticamente:
- **Redis** : en puerto 6379
- **Generador de Respuestas** : en puerto 8001
- **Caché** : en puerto 8002
- **Almacenamiento de Métricas** : en puerto 8003


## Endpoints disponibles
### Caché (puerto 8002)
- `GET /q1?zona_id=Z1` — Conteo de edificios
- `GET /q2?zona_id=Z1` — Área promedio y total
- `GET /q3?zona_id=Z1` — Densidad por km²
- `GET /q4?zona_a=Z1&zona_b=Z2` — Comparación entre zonas
- `GET /q5?zona_id=Z1` — Distribución de confianza

### Métricas (puerto 8003)
- `GET /metricas` — Métricas generales
- `GET /metricas/por-consulta` — Métricas por tipo de consulta
- `GET /metricas/evictions` — Total de evictions
- `GET /metricas/limpiar` — Limpiar métricas y caché

## Zonas disponibles

| ID | Sector |
|----|-----------------|
| Z1 | Providencia |
| Z2 | Las Condes |
| Z3 | Maipú |
| Z4 | Santiago Centro |
| Z5 | Pudahuel |

## Configuración de experimentos

Los parámetros se pueden ajustar en `docker-compose.yml`:

```yaml
command: redis-server --maxmemory 200mb --maxmemory-policy allkeys-lru
```

Políticas disponibles: `allkeys-lru`, `allkeys-lfu`, `allkeys-random`
Tamaños utilizados: 2MB, 50MB, 200MB, 500MB

TTL configurable en la sección `cache`:
```yaml
environment:
  - TTL=300
```