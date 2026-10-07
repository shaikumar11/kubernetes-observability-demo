import os
import random
import time

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(title="Demo Service", version="1.0.0")

REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds", "Request latency in seconds", ["path"]
)

_memory_visits = 0
_redis_client = None


def get_redis():
    """Return a Redis client when REDIS_HOST is set, otherwise None."""
    global _redis_client
    host = os.getenv("REDIS_HOST")
    if not host:
        return None
    if _redis_client is None:
        import redis

        _redis_client = redis.Redis(host=host, port=6379, socket_timeout=2)
    return _redis_client


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        path = request.url.path
        LATENCY.labels(path=path).observe(time.perf_counter() - start)
        REQUESTS.labels(method=request.method, path=path, status=str(status)).inc()


@app.get("/health")
def health():
    """Liveness probe: the process is running."""
    return {"status": "alive"}


@app.get("/ready")
def ready():
    """Readiness probe: the service can take traffic."""
    if os.getenv("FORCE_NOT_READY") == "true":
        raise HTTPException(status_code=503, detail="not ready")
    return {"status": "ready"}


@app.get("/work")
def work(fail_rate: float = 0.0, delay_ms: int = 0):
    """Simulate work with optional delay and random failures for monitoring demos."""
    if delay_ms > 0:
        time.sleep(min(delay_ms, 2000) / 1000)
    if random.random() < fail_rate:
        raise HTTPException(status_code=500, detail="simulated failure")
    return {"result": "done"}


@app.get("/visits")
def visits():
    """Count visits in Redis when available, so state survives pod restarts."""
    global _memory_visits
    client = get_redis()
    if client is not None:
        try:
            return {"visits": int(client.incr("visits")), "store": "redis"}
        except Exception:
            raise HTTPException(status_code=503, detail="redis unavailable")
    _memory_visits += 1
    return {"visits": _memory_visits, "store": "memory"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
