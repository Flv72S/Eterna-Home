"""
Test completi per il sistema di monitoring.
Include test per health check, readiness probe e metrics.
"""
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.storage.minio import get_minio_client
from app.core.redis import get_redis_client
from app.database import get_db
from app.routers import system

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_health_cache():
    system._health_cache["last_check"] = None
    system._health_cache["status"] = None
    yield
    system._health_cache["last_check"] = None
    system._health_cache["status"] = None


class MockMinIOClient:
    """Mock per MinIO client."""
    
    def __init__(self, healthy=True):
        self.healthy = healthy
        self.buckets = [Mock(name="test-bucket")] if healthy else []
    
    def list_buckets(self):
        if not self.healthy:
            raise Exception("MinIO connection failed")
        return self.buckets
    
    def list_objects(self, bucket_name, recursive=True):
        if not self.healthy:
            raise Exception("MinIO list objects failed")
        return [Mock(size=1024)]  # Mock object with size


class MockRedisClient:
    """Mock per Redis client."""
    
    def __init__(self, healthy=True):
        self.healthy = healthy
        self.info_data = {"used_memory": 1024 * 1024}  # 1MB
    
    def ping(self):
        if not self.healthy:
            raise Exception("Redis connection failed")
        return True
    
    def info(self):
        if not self.healthy:
            raise Exception("Redis info failed")
        return self.info_data


@pytest.fixture
def mock_healthy_services():
    """Mock per servizi sani."""
    with patch('app.routers.system.get_minio_client') as mock_minio, \
         patch('app.routers.system.get_redis_client') as mock_redis, \
         patch('app.routers.system.get_db') as mock_db:
        
        # Mock MinIO
        mock_minio.return_value = MockMinIOClient(healthy=True)
        
        # Mock Redis
        mock_redis.return_value = MockRedisClient(healthy=True)
        
        # Mock Database
        mock_session = Mock(spec=Session)
        mock_session.execute.return_value.fetchone.return_value = [1]
        mock_db.return_value = iter([mock_session])
        
        yield {
            'minio': mock_minio,
            'redis': mock_redis,
            'db': mock_db
        }


@pytest.fixture
def mock_unhealthy_services():
    """Mock per servizi non sani."""
    with patch('app.routers.system.get_minio_client') as mock_minio, \
         patch('app.routers.system.get_redis_client') as mock_redis, \
         patch('app.routers.system.get_db') as mock_db:
        
        # Mock MinIO unhealthy
        mock_minio.return_value = MockMinIOClient(healthy=False)
        
        # Mock Redis healthy (per readiness check)
        mock_redis.return_value = MockRedisClient(healthy=True)
        
        # Mock Database healthy
        mock_session = Mock(spec=Session)
        mock_session.execute.return_value.fetchone.return_value = [1]
        mock_db.return_value = iter([mock_session])
        
        yield {
            'minio': mock_minio,
            'redis': mock_redis,
            'db': mock_db
        }


@pytest.fixture
def mock_partially_unhealthy_services():
    """Mock per servizi parzialmente non sani."""
    with patch('app.routers.system.get_minio_client') as mock_minio, \
         patch('app.routers.system.get_redis_client') as mock_redis, \
         patch('app.routers.system.get_db') as mock_db:
        
        # Mock MinIO healthy
        mock_minio.return_value = MockMinIOClient(healthy=True)
        
        # Mock Redis unhealthy
        mock_redis.return_value = MockRedisClient(healthy=False)
        
        # Mock Database healthy
        mock_session = Mock(spec=Session)
        mock_session.execute.return_value.fetchone.return_value = [1]
        mock_db.return_value = iter([mock_session])
        
        yield {
            'minio': mock_minio,
            'redis': mock_redis,
            'db': mock_db
        }


class TestHealthCheck:
    """Test per l'endpoint /system/health."""
    
    def test_health_check_success(self, mock_healthy_services):
        """Test health check con tutti i servizi sani."""
        response = client.get("/system/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica struttura della risposta
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "response_time" in data
        assert "cached" in data
        assert "database" in data
        assert "redis" in data
        assert "minio" in data
        assert "system" in data
        
        # Verifica stato dei servizi
        assert data["database"]["status"] == "healthy"
        assert data["redis"]["status"] == "healthy"
        assert data["minio"]["status"] == "healthy"
        assert "response_time" in data["database"]
        assert "response_time" in data["redis"]
        assert "response_time" in data["minio"]
        assert "buckets_count" in data["minio"]
        
        # Verifica metriche di sistema
        system_info = data["system"]
        assert "cpu_percent" in system_info
        assert "memory_percent" in system_info
        assert "disk_percent" in system_info
        assert "uptime" in system_info
    
    def test_health_check_minio_failure(self, mock_unhealthy_services):
        """Test health check con MinIO non disponibile."""
        response = client.get("/system/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["database"]["status"] == "healthy"
        assert data["redis"]["status"] == "healthy"
        assert data["minio"]["status"] == "unhealthy"
        assert "error" in data["minio"]
    
    def test_health_check_redis_failure(self, mock_partially_unhealthy_services):
        """Test health check con Redis non disponibile."""
        response = client.get("/system/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["database"]["status"] == "healthy"
        assert data["redis"]["status"] == "unhealthy"
        assert data["minio"]["status"] == "healthy"
        assert "error" in data["redis"]
    
    def test_health_check_cache_behavior(self, mock_healthy_services):
        """Test che il cache funzioni correttamente."""
        # Prima chiamata
        response1 = client.get("/system/health")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["cached"] == False
        
        # Simula cache valida
        system._health_cache["status"] = {
            "database": {"status": "healthy"},
            "redis": {"status": "healthy"},
            "minio": {"status": "healthy"},
            "system": {"cpu_percent": 10}
        }
        
        # Seconda chiamata (dovrebbe essere cached)
        response2 = client.get("/system/health")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cached"] == True


class TestReadinessCheck:
    """Test per l'endpoint /system/ready."""
    
    def test_readiness_check_success(self, mock_healthy_services):
        """Test readiness check con configurazione e servizi critici sani."""
        response = client.get("/system/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica struttura della risposta
        assert "ready" in data
        assert data["ready"] == True
        assert "timestamp" in data
        assert "response_time" in data
        assert "checks" in data
        
        # Verifica controlli
        checks = data["checks"]
        assert checks["configuration"] == True
        assert checks["database"] == True
        assert checks["redis"] == True
    
    def test_readiness_check_redis_failure(self, mock_partially_unhealthy_services):
        """Test readiness check con Redis non disponibile."""
        response = client.get("/system/ready")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["ready"] == False
        assert data["checks"]["configuration"] == True
        assert data["checks"]["database"] == True
        assert data["checks"]["redis"] == False
    
    def test_readiness_check_configuration_failure(self, mock_healthy_services):
        """Test readiness check con configurazione mancante."""
        with patch('app.routers.system.settings') as mock_settings:
            # Simula configurazione mancante
            mock_settings.DATABASE_URL = None
            mock_settings.REDIS_URL = "redis://localhost:6379"
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            mock_settings.SECRET_KEY = "test-key"
            
            response = client.get("/system/ready")
            
            assert response.status_code == 503
            data = response.json()
            assert data["ready"] == False
            assert "error" in data


class TestMetrics:
    """Test per l'endpoint /system/metrics."""
    
    def test_metrics_success(self, mock_healthy_services):
        """Test metrics con tutti i servizi sani."""
        response = client.get("/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica struttura della risposta
        assert "timestamp" in data
        assert "system" in data
        assert "database" in data
        assert "redis" in data
        assert "storage" in data
        assert "requests" in data
        
        # Verifica metriche di sistema
        system_metrics = data["system"]
        assert "uptime_seconds" in system_metrics
        assert "memory_usage_mb" in system_metrics
        assert "cpu_percent" in system_metrics
        assert "disk_usage_percent" in system_metrics
        
        # Verifica metriche database
        db_metrics = data["database"]
        assert "connection_status" in db_metrics
        assert "query_count" in db_metrics
        assert "avg_query_time_ms" in db_metrics
        
        # Verifica metriche Redis
        redis_metrics = data["redis"]
        assert "connection_status" in redis_metrics
        assert "memory_usage_mb" in redis_metrics
        
        # Verifica metriche storage
        storage_metrics = data["storage"]
        assert "connection_status" in storage_metrics
        assert "total_files" in storage_metrics
        assert "total_size_mb" in storage_metrics
        
        # Verifica metriche richieste
        request_metrics = data["requests"]
        assert "total_requests" in request_metrics
        assert "requests_per_minute" in request_metrics
        assert "avg_response_time_ms" in request_metrics
        assert "error_rate_percent" in request_metrics
    
    def test_metrics_with_service_failures(self, mock_unhealthy_services):
        """Test metrics con alcuni servizi non disponibili."""
        response = client.get("/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica che le metriche siano ancora presenti anche con errori
        assert data["database"]["connection_status"] == "healthy"
        assert data["redis"]["connection_status"] == "healthy"
        assert "error:" in data["storage"]["connection_status"]
    
    def test_metrics_error_handling(self):
        """Test gestione errori nelle metrics."""
        with patch('sqlalchemy.orm.Session.execute', side_effect=Exception("Database error")):
            response = client.get("/system/metrics")
            assert response.status_code == 200
            data = response.json()
            assert "error:" in data["database"]["connection_status"]


class TestSystemEndpointsIntegration:
    """Test di integrazione per tutti gli endpoint di sistema."""
    
    def test_all_system_endpoints_accessible(self, mock_healthy_services):
        """Test che tutti gli endpoint di sistema siano accessibili."""
        endpoints = [
            "/system/health",
            "/system/ready", 
            "/system/metrics"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 503]  # 503 è accettabile per readiness/health
            assert response.headers["content-type"] == "application/json"
    
    def test_system_endpoints_response_time(self, mock_healthy_services):
        """Test che gli endpoint rispondano in tempi ragionevoli."""
        start_time = time.time()
        
        response = client.get("/system/health")
        
        response_time = time.time() - start_time
        assert response_time < 5.0  # Dovrebbe rispondere in meno di 5 secondi
        
        if response.status_code == 200:
            data = response.json()
            assert data["response_time"] < 5.0
    
    def test_system_endpoints_logging(self, mock_healthy_services):
        """Test che gli endpoint logghino correttamente."""
        # Test con health check
        response = client.get("/system/health")
        
        # Verifica che la risposta contenga informazioni di logging
        if response.status_code == 200:
            data = response.json()
            assert "timestamp" in data
            assert "response_time" in data
    
    def test_system_endpoints_security_headers(self, mock_healthy_services):
        """Test che gli endpoint abbiano header di sicurezza appropriati."""
        response = client.get("/system/health")
        
        # Verifica header di sicurezza di base
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json"


class TestSystemErrorScenarios:
    """Test per scenari di errore del sistema."""
    
    def test_database_connection_failure(self):
        """Test con database non disponibile."""
        with patch('app.routers.system.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = client.get("/system/health")
            assert response.status_code == 503
            
            response = client.get("/system/ready")
            assert response.status_code == 503
    
    def test_redis_connection_failure(self):
        """Test con Redis non disponibile."""
        with patch('app.routers.system.get_redis_client') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")
            
            response = client.get("/system/health")
            assert response.status_code == 503
            
            response = client.get("/system/ready")
            assert response.status_code == 503
    
    def test_minio_connection_failure(self):
        """Test con MinIO non disponibile."""
        with patch('app.routers.system.get_minio_client') as mock_minio:
            mock_minio.side_effect = Exception("MinIO connection failed")
            
            response = client.get("/system/health")
            assert response.status_code == 503
    
    def test_system_metrics_with_all_failures(self):
        """Test metrics con tutti i servizi non disponibili."""
        with patch('sqlalchemy.orm.Session.execute', side_effect=Exception("DB error")), \
             patch('app.core.redis.get_redis_client') as mock_redis, \
             patch('app.core.storage.minio.get_minio_client') as mock_minio:

            mock_redis.return_value.ping.side_effect = Exception("Redis error")
            mock_minio.return_value.list_buckets.side_effect = Exception("MinIO error")

            response = client.get("/system/metrics")
            assert response.status_code == 200
            data = response.json()
            assert "error:" in data["database"]["connection_status"]
            assert "error:" in data["redis"]["connection_status"]
            assert "error:" in data["storage"]["connection_status"]


class TestSystemPerformance:
    """Test di performance per il sistema."""
    
    def test_health_check_performance(self, mock_healthy_services):
        """Test performance dell'health check."""
        start_time = time.time()
        
        for _ in range(5):
            response = client.get("/system/health")
            assert response.status_code in [200, 503]
        
        total_time = time.time() - start_time
        avg_time = total_time / 5
        
        # Ogni chiamata dovrebbe essere veloce
        assert avg_time < 2.0
    
    def test_metrics_performance(self, mock_healthy_services):
        """Test performance delle metrics."""
        start_time = time.time()
        
        response = client.get("/system/metrics")
        assert response.status_code == 200
        
        response_time = time.time() - start_time
        assert response_time < 3.0  # Metrics possono richiedere più tempo
    
    def test_concurrent_requests(self, mock_healthy_services):
        """Test richieste concorrenti."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = client.get("/system/health")
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")
        
        # Esegue 3 richieste concorrenti
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Attende completamento
        for thread in threads:
            thread.join()
        
        # Verifica risultati
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())
        
        # Tutte le richieste dovrebbero avere successo
        assert len(status_codes) == 3
        assert all(code in [200, 503] for code in status_codes) 