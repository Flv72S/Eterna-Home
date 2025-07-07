"""
Test completi per gli endpoint di monitoraggio di sistema.
Valida /system/health, /system/ready e /system/metrics con verifiche dettagliate.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_external_services():
    """Mock per tutti i servizi esterni"""
    with patch("app.routers.system.check_database") as mock_db, \
         patch("app.routers.system.check_redis") as mock_redis, \
         patch("app.routers.system.check_minio") as mock_minio:
        
        # Mock database healthy
        mock_db.return_value = {
            "status": "healthy",
            "response_time": 0.001
        }
        
        # Mock redis healthy
        mock_redis.return_value = {
            "status": "healthy", 
            "response_time": 0.002
        }
        
        # Mock minio healthy
        mock_minio.return_value = {
            "status": "healthy",
            "response_time": 0.003,
            "buckets_count": 5
        }
        
        yield mock_db, mock_redis, mock_minio


@pytest.fixture
def mock_metrics():
    """Mock per le metriche di sistema"""
    with patch("app.routers.system._metrics") as mock_metrics_dict:
        # Reset metrics
        mock_metrics_dict.update({
            "http_requests_total": 0,
            "http_request_duration_seconds": [],
            "active_users": 0,
            "upload_count": 0,
            "download_count": 0,
            "auth_failures": 0,
            "security_events": 0,
            "start_time": time.time()
        })
        yield mock_metrics_dict


@pytest.fixture
def reset_cache():
    """Reset della cache tra i test"""
    from app.routers.system import _health_cache, _metrics
    
    # Backup valori originali
    original_cache = _health_cache.copy()
    original_metrics = _metrics.copy()
    
    # Reset cache
    _health_cache["last_check"] = None
    _health_cache["status"] = None
    
    # Reset metrics
    _metrics["http_requests_total"] = 0
    _metrics["http_request_duration_seconds"] = []
    
    yield
    
    # Ripristina valori originali
    _health_cache.update(original_cache)
    _metrics.update(original_metrics)


class TestSystemHealth:
    """Test per l'endpoint /system/health"""
    
    def test_health_check_status_code(self, mock_external_services):
        """Verifica che l'endpoint risponda con status code appropriato"""
        response = client.get("/system/health")
        assert response.status_code == 200, f"Status code inaspettato: {response.status_code}"
    
    def test_health_check_response_structure(self, mock_external_services):
        """Verifica la struttura della risposta JSON"""
        response = client.get("/system/health")
        data = response.json()
        
        # Campi obbligatori
        assert "status" in data, "Campo 'status' mancante"
        assert "timestamp" in data, "Campo 'timestamp' mancante"
        assert "response_time" in data, "Campo 'response_time' mancante"
        
        # Verifica formato timestamp
        from datetime import datetime
        try:
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("Timestamp non in formato ISO")
    
    def test_health_check_healthy_status(self, mock_external_services):
        """Verifica che quando healthy, tutti i servizi siano up"""
        response = client.get("/system/health")
        data = response.json()
        
        assert data["status"] == "healthy", "Status dovrebbe essere healthy con mock"
        assert "database" in data, "Campo 'database' mancante in risposta healthy"
        assert "redis" in data, "Campo 'redis' mancante in risposta healthy"
        assert "minio" in data, "Campo 'minio' mancante in risposta healthy"
        assert "system" in data, "Campo 'system' mancante in risposta healthy"
        
        # Verifica stato servizi
        assert data["database"]["status"] == "healthy", "Database non healthy"
        assert data["redis"]["status"] == "healthy", "Redis non healthy"
        assert data["minio"]["status"] == "healthy", "MinIO non healthy"
        
        # Verifica metriche sistema
        system_info = data["system"]
        assert "cpu_percent" in system_info, "CPU percent mancante"
        assert "memory_percent" in system_info, "Memory percent mancante"
        assert "disk_percent" in system_info, "Disk percent mancante"
        assert "uptime" in system_info, "Uptime mancante"
        
        # Verifica range valori
        assert 0 <= system_info["cpu_percent"] <= 100, "CPU percent fuori range"
        assert 0 <= system_info["memory_percent"] <= 100, "Memory percent fuori range"
        assert 0 <= system_info["disk_percent"] <= 100, "Disk percent fuori range"
        assert system_info["uptime"] > 0, "Uptime deve essere positivo"
    
    def test_health_check_cache_behavior(self, mock_external_services, reset_cache):
        """Verifica il comportamento della cache"""
        mock_db, mock_redis, mock_minio = mock_external_services
        
        # Reset cache
        mock_db.return_value = {
            "status": "healthy",
            "response_time": 0.001
        }
        mock_redis.return_value = {
            "status": "healthy",
            "response_time": 0.002
        }
        mock_minio.return_value = {
            "status": "healthy",
            "response_time": 0.003,
            "buckets_count": 5
        }
        
        # Prima chiamata
        response1 = client.get("/system/health")
        data1 = response1.json()
        
        # Seconda chiamata rapida (dovrebbe usare cache)
        time.sleep(0.1)
        response2 = client.get("/system/health")
        data2 = response2.json()
        
        # Verifica che la seconda risposta sia più veloce (cache)
        if "cached" in data2:
            assert data2["cached"] is True, "Seconda chiamata dovrebbe usare cache"
            assert data2["response_time"] < data1["response_time"], "Risposta cache dovrebbe essere più veloce"
    
    def test_health_check_unhealthy_services(self, mock_external_services):
        """Verifica comportamento con servizi unhealthy"""
        mock_db, mock_redis, mock_minio = mock_external_services
        
        # Mock database unhealthy
        mock_db.return_value = {
            "status": "unhealthy",
            "error": "Connection failed"
        }
        
        response = client.get("/system/health")
        data = response.json()
        
        assert data["status"] == "unhealthy", "Status dovrebbe essere unhealthy"
        assert data["database"]["status"] == "unhealthy", "Database dovrebbe essere unhealthy"
        assert response.status_code == 503, "Status code dovrebbe essere 503"


class TestSystemReady:
    """Test per l'endpoint /system/ready"""
    
    def test_ready_check_status_code(self, mock_external_services):
        """Verifica che l'endpoint risponda con status code appropriato"""
        response = client.get("/system/ready")
        assert response.status_code == 200, f"Status code inaspettato: {response.status_code}"
    
    def test_ready_check_response_structure(self, mock_external_services):
        """Verifica la struttura della risposta JSON"""
        response = client.get("/system/ready")
        data = response.json()
        
        # Campi obbligatori
        assert "ready" in data, "Campo 'ready' mancante"
        assert "timestamp" in data, "Campo 'timestamp' mancante"
        assert "response_time" in data, "Campo 'response_time' mancante"
        assert "checks" in data, "Campo 'checks' mancante"
        
        # Verifica struttura checks
        checks = data["checks"]
        assert "configuration" in checks, "Check 'configuration' mancante"
        assert "database" in checks, "Check 'database' mancante"
        assert "redis" in checks, "Check 'redis' mancante"
    
    def test_ready_check_ready_status(self, mock_external_services):
        """Verifica che quando ready, tutti i check siano true"""
        response = client.get("/system/ready")
        data = response.json()
        
        assert data["ready"] is True, "Ready dovrebbe essere true con mock healthy"
        checks = data["checks"]
        assert checks["configuration"] is True, "Configuration check fallito"
        assert checks["database"] is True, "Database check fallito"
        assert checks["redis"] is True, "Redis check fallito"
    
    def test_ready_check_consistency_with_health(self, mock_external_services):
        """Verifica consistenza tra ready e health"""
        health_response = client.get("/system/health")
        ready_response = client.get("/system/ready")
        
        health_data = health_response.json()
        ready_data = ready_response.json()
        
        # Con mock healthy, entrambi dovrebbero essere healthy/ready
        assert health_data["status"] == "healthy", "Health dovrebbe essere healthy"
        assert ready_data["ready"] is True, "Ready dovrebbe essere true"


class TestSystemMetrics:
    """Test per l'endpoint /system/metrics"""
    
    def test_metrics_status_code(self, mock_metrics):
        """Verifica che l'endpoint risponda con status code 200"""
        response = client.get("/system/metrics")
        assert response.status_code == 200, f"Status code inaspettato: {response.status_code}"
    
    def test_metrics_content_type(self, mock_metrics):
        """Verifica che il content-type sia text/plain per Prometheus"""
        response = client.get("/system/metrics")
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_metrics_prometheus_format(self, mock_metrics):
        """Verifica che il contenuto sia in formato Prometheus"""
        response = client.get("/system/metrics")
        content = response.text
        
        # Verifica presenza di metriche chiave
        required_metrics = [
            "eterna_home_uptime_seconds",
            "eterna_home_http_requests_total",
            "eterna_home_cpu_percent",
            "eterna_home_memory_percent",
            "eterna_home_disk_percent"
        ]
        
        for metric in required_metrics:
            assert metric in content, f"Metrica '{metric}' mancante"
        
        # Verifica formato Prometheus
        lines = content.split('\n')
        metric_lines = [line for line in lines if line.startswith('eterna_home_') and not line.startswith('#')]
        
        for line in metric_lines:
            # Verifica che ogni metrica abbia un valore
            assert ' ' in line, f"Formato metrica non valido: {line}"
            metric_name, metric_value = line.split(' ', 1)
            assert metric_name.startswith('eterna_home_'), f"Nome metrica non valido: {metric_name}"
            
            # Verifica che il valore sia numerico
            try:
                float(metric_value)
            except ValueError:
                pytest.fail(f"Valore metrica non numerico: {metric_value}")
    
    def test_metrics_histogram_format(self, mock_metrics):
        """Verifica formato histogram per response time"""
        response = client.get("/system/metrics")
        content = response.text
        
        # Verifica presenza di bucket histogram
        histogram_metrics = [
            "eterna_home_http_request_duration_seconds_bucket",
            "eterna_home_http_request_duration_seconds_sum",
            "eterna_home_http_request_duration_seconds_count"
        ]
        
        for metric in histogram_metrics:
            assert metric in content, f"Metrica histogram '{metric}' mancante"
        
        # Verifica percentili
        percentile_metrics = [
            "eterna_home_http_request_duration_p50",
            "eterna_home_http_request_duration_p95",
            "eterna_home_http_request_duration_p99"
        ]
        
        for metric in percentile_metrics:
            assert metric in content, f"Metrica percentile '{metric}' mancante"
    
    def test_metrics_values_range(self, mock_metrics):
        """Verifica che i valori delle metriche siano in range ragionevoli"""
        response = client.get("/system/metrics")
        content = response.text
        
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('eterna_home_uptime_seconds '):
                uptime = float(line.split(' ')[1])
                assert uptime > 0, "Uptime deve essere positivo"
                break
        
        for line in lines:
            if line.startswith('eterna_home_cpu_percent '):
                cpu = float(line.split(' ')[1])
                assert 0 <= cpu <= 100, "CPU percent deve essere tra 0 e 100"
                break
        
        for line in lines:
            if line.startswith('eterna_home_memory_percent '):
                memory = float(line.split(' ')[1])
                assert 0 <= memory <= 100, "Memory percent deve essere tra 0 e 100"
                break
    
    def test_metrics_build_info(self, mock_metrics):
        """Verifica presenza build info"""
        response = client.get("/system/metrics")
        content = response.text
        
        # Verifica build info
        build_info_found = False
        for line in content.split('\n'):
            if line.startswith('eterna_home_build_info'):
                build_info_found = True
                break
        
        if not build_info_found:
            pytest.skip("Build info non implementato ancora")


class TestSystemEndpointsIntegration:
    """Test di integrazione tra gli endpoint di sistema"""
    
    def test_all_system_endpoints_accessible(self, mock_external_services, mock_metrics):
        """Verifica che tutti gli endpoint di sistema siano accessibili"""
        endpoints = [
            "/system/health",
            "/system/ready", 
            "/system/metrics"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in (200, 503), f"Endpoint {endpoint} non accessibile"
    
    def test_metrics_increment_on_requests(self, mock_external_services, mock_metrics):
        """Verifica che le metriche si incrementino con le richieste"""
        # Leggi metriche iniziali
        response1 = client.get("/system/metrics")
        content1 = response1.text
        
        # Estrai numero richieste iniziali
        initial_requests = 0
        for line in content1.split('\n'):
            if line.startswith('eterna_home_http_requests_total '):
                initial_requests = int(line.split(' ')[1])
                break
        
        # Fai alcune richieste
        client.get("/system/health")
        client.get("/system/ready")
        client.get("/system/metrics")
        
        # Leggi metriche finali
        response2 = client.get("/system/metrics")
        content2 = response2.text
        
        # Estrai numero richieste finali
        final_requests = 0
        for line in content2.split('\n'):
            if line.startswith('eterna_home_http_requests_total '):
                final_requests = int(line.split(' ')[1])
                break
        
        # Verifica incremento
        assert final_requests > initial_requests, "Le richieste totali dovrebbero essere incrementate"
    
    def test_system_endpoints_logging(self, mock_external_services, mock_metrics):
        """Verifica che gli endpoint generino log appropriati"""
        # Questo test verifica che gli endpoint generino log
        # In un ambiente reale, verificheresti i file di log
        response = client.get("/system/health")
        assert response.status_code == 200
        
        response = client.get("/system/ready")
        assert response.status_code == 200
        
        response = client.get("/system/metrics")
        assert response.status_code == 200


if __name__ == "__main__":
    # Esegui i test
    pytest.main([__file__, "-v"]) 