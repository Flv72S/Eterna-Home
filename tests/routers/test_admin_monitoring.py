import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.user_permission import UserPermission
from app.utils.security import create_access_token
from app.database import get_session

# Test database
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

client = TestClient(app)

@pytest.fixture
def test_db():
    """Setup test database"""
    from app.db.base import Base
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def admin_user_with_monitoring_permission(test_db):
    """Crea un utente admin con permesso di monitoraggio"""
    with Session(engine) as session:
        # Crea permesso di monitoraggio
        monitoring_permission = Permission(
            name="view_monitoring",
            description="Visualizza monitoraggio sistema"
        )
        session.add(monitoring_permission)
        session.commit()
        
        # Crea utente admin
        admin_user = User(
            username="admin_monitor",
            email="admin@test.com",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=True
        )
        session.add(admin_user)
        session.commit()
        
        # Assegna permesso direttamente all'utente
        user_permission = UserPermission(
            user_id=admin_user.id,
            permission_id=monitoring_permission.id
        )
        session.add(user_permission)
        session.commit()
        
        return admin_user

@pytest.fixture
def regular_user_without_permission(test_db):
    """Crea un utente normale senza permesso di monitoraggio"""
    with Session(engine) as session:
        user = User(
            username="regular_user",
            email="user@test.com",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False
        )
        session.add(user)
        session.commit()
        return user

@pytest.fixture
def mock_system_endpoints():
    """Mock degli endpoint di sistema"""
    with patch("app.routers.admin.system_monitor.get_system_health") as mock_health, \
         patch("app.routers.admin.system_monitor.get_system_ready") as mock_ready, \
         patch("app.routers.admin.system_monitor.get_system_metrics") as mock_metrics:
        
        # Mock dati di health
        mock_health.return_value = {
            "status": "healthy",
            "database": {"status": "healthy"},
            "minio": {"status": "healthy"},
            "redis": {"status": "healthy"}
        }
        
        # Mock dati di ready
        mock_ready.return_value = {
            "status": "ready",
            "services": ["database", "minio", "redis"]
        }
        
        # Mock dati di metrics
        mock_metrics.return_value = {
            "status": "success",
            "uptime_seconds": 3600,
            "requests_total": 1500,
            "requests_5xx_total": 5,
            "requests_4xx_total": 25,
            "upload_operations_total": 100,
            "active_users": 15,
            "database_connections": 8,
            "redis_connections": 3,
            "minio_operations": 50
        }
        
        yield mock_health, mock_ready, mock_metrics

class TestAdminMonitoringAccess:
    """Test per l'accesso al monitoraggio del sistema"""
    
    def test_admin_monitoring_access_authorized(self, admin_user_with_monitoring_permission, mock_system_endpoints):
        """Test: Utente con permesso view_monitoring vede correttamente la dashboard"""
        # Crea token di accesso
        access_token = create_access_token(
            data={"sub": admin_user_with_monitoring_permission.username}
        )
        
        # Effettua richiesta
        response = client.get(
            "/admin/system/status",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Verifica risposta
        assert response.status_code == 200
        assert "Monitoraggio Sistema" in response.text
        assert "Sistema Operativo" in response.text
        assert "Backend/API" in response.text
        assert "Database PostgreSQL" in response.text
        assert "MinIO Storage" in response.text
        assert "Redis Cache" in response.text
        
        # Verifica che i mock siano stati chiamati
        mock_health, mock_ready, mock_metrics = mock_system_endpoints
        mock_health.assert_called_once()
        mock_ready.assert_called_once()
        mock_metrics.assert_called_once()
    
    def test_admin_monitoring_access_denied(self, regular_user_without_permission):
        """Test: Utente senza permessi riceve 403 Forbidden"""
        # Crea token di accesso per utente senza permessi
        access_token = create_access_token(
            data={"sub": regular_user_without_permission.username}
        )
        
        # Effettua richiesta
        response = client.get(
            "/admin/system/status",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Verifica risposta
        assert response.status_code == 403
        assert "Forbidden" in response.text or "Access denied" in response.text
    
    def test_admin_monitoring_no_token(self):
        """Test: Richiesta senza token riceve 401 Unauthorized"""
        response = client.get("/admin/system/status")
        assert response.status_code == 401

class TestPrometheusMetricsParsing:
    """Test per il parsing delle metriche Prometheus"""
    
    def test_prometheus_metrics_parsing_success(self, admin_user_with_monitoring_permission):
        """Test: Parsing corretto delle metriche Prometheus"""
        from app.routers.admin.system_monitor import parse_prometheus_metrics
        
        # Dati Prometheus di test
        metrics_text = """
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1640995200
# HELP http_requests_total Total number of HTTP requests.
# TYPE http_requests_total counter
http_requests_total{status="200"} 1000
http_requests_total{status="404"} 25
http_requests_total{status="500"} 5
# HELP upload_operations_total Total number of upload operations.
# TYPE upload_operations_total counter
upload_operations_total 100
# HELP active_users Number of active users.
# TYPE active_users gauge
active_users 15
# HELP database_connections Number of database connections.
# TYPE database_connections gauge
database_connections 8
# HELP redis_connections Number of Redis connections.
# TYPE redis_connections gauge
redis_connections 3
# HELP minio_operations Number of MinIO operations.
# TYPE minio_operations counter
minio_operations 50
"""
        
        # Parsing delle metriche
        result = parse_prometheus_metrics(metrics_text)
        
        # Verifica risultati
        assert result["status"] == "success"
        assert result["uptime_seconds"] > 0
        assert result["requests_total"] == 1000
        assert result["requests_4xx_total"] == 25
        assert result["requests_5xx_total"] == 5
        assert result["upload_operations_total"] == 100
        assert result["active_users"] == 15
        assert result["database_connections"] == 8
        assert result["redis_connections"] == 3
        assert result["minio_operations"] == 50
    
    def test_prometheus_metrics_parsing_empty(self, admin_user_with_monitoring_permission):
        """Test: Parsing con metriche vuote"""
        from app.routers.admin.system_monitor import parse_prometheus_metrics
        
        result = parse_prometheus_metrics("")
        
        assert result["status"] == "success"
        assert result["uptime_seconds"] == 0
        assert result["requests_total"] == 0
    
    def test_prometheus_metrics_parsing_error(self, admin_user_with_monitoring_permission):
        """Test: Parsing con errori"""
        from app.routers.admin.system_monitor import parse_prometheus_metrics
        
        # Dati malformati
        metrics_text = "invalid prometheus data\nwith\nmalformed\nlines"
        
        result = parse_prometheus_metrics(metrics_text)
        
        assert result["status"] == "success"  # Non dovrebbe fallire, solo non trovare dati
        assert result["uptime_seconds"] == 0

class TestSystemEndpointsIntegration:
    """Test per l'integrazione con gli endpoint di sistema"""
    
    @patch("httpx.AsyncClient.get")
    def test_system_health_endpoint_success(self, mock_get, admin_user_with_monitoring_permission):
        """Test: Chiamata riuscita all'endpoint health"""
        import asyncio
        from app.routers.admin.system_monitor import get_system_health
        
        # Mock della risposta
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response
        
        # Test della funzione
        result = asyncio.run(get_system_health())
        
        assert result["status"] == "healthy"
        mock_get.assert_called_once()
    
    @patch("httpx.AsyncClient.get")
    def test_system_metrics_endpoint_failure(self, mock_get, admin_user_with_monitoring_permission):
        """Test: Gestione errore endpoint metrics"""
        import asyncio
        from app.routers.admin.system_monitor import get_system_metrics
        
        # Mock dell'errore
        mock_get.side_effect = Exception("Connection timeout")
        
        # Test della funzione
        result = asyncio.run(get_system_metrics())
        
        assert result["status"] == "error"
        assert "Connection timeout" in result["message"]

class TestUptimeFormatting:
    """Test per la formattazione dell'uptime"""
    
    def test_uptime_formatting(self, admin_user_with_monitoring_permission):
        """Test: Formattazione corretta dell'uptime"""
        from app.routers.admin.system_monitor import format_uptime
        
        # Test secondi
        assert format_uptime(30) == "30s"
        
        # Test minuti
        assert format_uptime(90) == "30s"  # 1 minuto e 30 secondi
        
        # Test ore
        assert format_uptime(3661) == "1h 1m"  # 1 ora e 1 minuto
        
        # Test giorni
        assert format_uptime(90000) == "1d 1h"  # 1 giorno e 1 ora 