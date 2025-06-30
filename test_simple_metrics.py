"""
Test con versione semplificata dell'endpoint metrics.
"""
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import time

app = FastAPI()

# Metriche semplificate
_metrics = {
    "http_requests_total": 0,
    "http_request_duration_seconds": [],
    "start_time": time.time()
}

@app.get("/metrics")
async def metrics_simple(request: Request):
    """Versione semplificata dell'endpoint metrics"""
    try:
        # Calcola metriche base
        uptime_seconds = time.time() - _metrics["start_time"]
        durations = _metrics["http_request_duration_seconds"]
        
        # Calcola percentili in modo sicuro
        if durations and len(durations) > 0:
            durations.sort()
            p50 = durations[len(durations) // 2]
            p95 = durations[int(len(durations) * 0.95)]
            p99 = durations[int(len(durations) * 0.99)]
        else:
            p50 = p95 = p99 = 0.0
            durations = [0.0]
        
        # Genera formato Prometheus semplificato
        prometheus_metrics = f"""# HELP eterna_home_uptime_seconds Uptime dell'applicazione in secondi
# TYPE eterna_home_uptime_seconds gauge
eterna_home_uptime_seconds {uptime_seconds}

# HELP eterna_home_http_requests_total Numero totale di richieste HTTP
# TYPE eterna_home_http_requests_total counter
eterna_home_http_requests_total {_metrics["http_requests_total"]}

# HELP eterna_home_http_request_duration_p50 Percentile 50 della durata richieste
# TYPE eterna_home_http_request_duration_p50 gauge
eterna_home_http_request_duration_p50 {p50}
"""
        
        response_time = time.time() - time.time()  # Semplificato
        _metrics["http_requests_total"] += 1
        _metrics["http_request_duration_seconds"].append(response_time)
        
        return PlainTextResponse(
            content=prometheus_metrics,
            media_type="text/plain"
        )
        
    except Exception as e:
        print(f"Errore in metrics_simple: {e}")
        import traceback
        traceback.print_exc()
        return PlainTextResponse(
            content=f"Error: {str(e)}",
            media_type="text/plain",
            status_code=500
        )

if __name__ == "__main__":
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    print("🧪 Test endpoint metrics semplificato...")
    response = client.get("/metrics")
    
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Endpoint metrics semplificato funziona!")
    else:
        print(f"❌ Errore: {response.text}") 