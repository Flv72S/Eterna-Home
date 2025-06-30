import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/system/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "database" in data or data["status"] == "error"
    if data["status"] == "healthy":
        assert data["database"]["status"] == "healthy"
        assert data["redis"]["status"] == "healthy"
        assert data["minio"]["status"] == "healthy"
        assert "system" in data


def test_ready_check():
    response = client.get("/system/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "ready" in data
    assert "timestamp" in data
    if data["ready"]:
        assert data["checks"]["configuration"] is True
        assert data["checks"]["database"] is True
        assert data["checks"]["redis"] is True


def test_metrics_prometheus_format():
    response = client.get("/system/metrics")
    assert response.status_code == 200
    text = response.text
    # Verifica presenza di alcune metriche chiave
    assert "eterna_home_uptime_seconds" in text
    assert "eterna_home_http_requests_total" in text
    assert "eterna_home_cpu_percent" in text
    assert "# TYPE eterna_home_build_info gauge" in text 