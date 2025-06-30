import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.redis import redis_client
from app.database import get_db
from unittest.mock import patch, MagicMock
import json

client = TestClient(app)

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('app.core.redis.redis_client') as mock:
        mock.ping.return_value = True
        yield mock

@pytest.fixture
def mock_db():
    """Mock database connection"""
    with patch('app.database.get_db') as mock:
        mock.return_value = MagicMock()
        yield mock

def test_health_endpoint():
    """Test /health endpoint"""
    
    response = client.get("/health")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "status" in data
    assert "message" in data
    assert data["status"] == "healthy"
    assert "Eterna-Home API is operational" in data["message"]

def test_ready_endpoint(mock_redis, mock_db):
    """Test /ready endpoint"""
    
    response = client.get("/ready")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "timestamp" in data
    
    # Verify status
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert data["redis"] == "connected"

def test_metrics_endpoint():
    """Test /metrics endpoint"""
    
    response = client.get("/metrics")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "uptime" in data
    assert "requests_total" in data
    assert "requests_per_minute" in data
    assert "error_rate" in data
    assert "response_time_avg" in data
    assert "memory_usage" in data
    assert "cpu_usage" in data
    assert "active_connections" in data
    assert "timestamp" in data
    
    # Verify data types
    assert isinstance(data["uptime"], (int, float))
    assert isinstance(data["requests_total"], int)
    assert isinstance(data["requests_per_minute"], (int, float))
    assert isinstance(data["error_rate"], (int, float))
    assert isinstance(data["response_time_avg"], (int, float))
    assert isinstance(data["memory_usage"], (int, float))
    assert isinstance(data["cpu_usage"], (int, float))
    assert isinstance(data["active_connections"], int)

def test_system_info_endpoint():
    """Test /system/info endpoint"""
    
    response = client.get("/system/info")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "version" in data
    assert "environment" in data
    assert "startup_time" in data
    assert "services" in data
    assert "configuration" in data
    
    # Verify service information
    services = data["services"]
    assert "database" in services
    assert "redis" in services
    assert "minio" in services
    assert "celery" in services

def test_system_status_endpoint(mock_redis, mock_db):
    """Test /system/status endpoint"""
    
    response = client.get("/system/status")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "overall_status" in data
    assert "services" in data
    assert "alerts" in data
    assert "last_check" in data
    
    # Verify overall status
    assert data["overall_status"] in ["healthy", "degraded", "unhealthy"]
    
    # Verify services status
    services = data["services"]
    for service_name, service_status in services.items():
        assert "status" in service_status
        assert "last_check" in service_status
        assert service_status["status"] in ["healthy", "degraded", "unhealthy"]

def test_system_logs_endpoint():
    """Test /system/logs endpoint"""
    
    response = client.get("/system/logs")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "logs" in data
    assert "total_count" in data
    assert "page" in data
    assert "per_page" in data
    
    # Verify logs structure
    logs = data["logs"]
    if logs:  # If there are logs
        for log in logs:
            assert "timestamp" in log
            assert "level" in log
            assert "message" in log
            assert "service" in log

def test_system_alerts_endpoint():
    """Test /system/alerts endpoint"""
    
    response = client.get("/system/alerts")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "alerts" in data
    assert "total_count" in data
    assert "active_alerts" in data
    
    # Verify alerts structure
    alerts = data["alerts"]
    if alerts:  # If there are alerts
        for alert in alerts:
            assert "id" in alert
            assert "severity" in alert
            assert "message" in alert
            assert "timestamp" in alert
            assert "status" in alert

def test_system_performance_endpoint():
    """Test /system/performance endpoint"""
    
    response = client.get("/system/performance")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "network" in data
    assert "database" in data
    assert "timestamp" in data
    
    # Verify CPU metrics
    cpu = data["cpu"]
    assert "usage_percent" in cpu
    assert "load_average" in cpu
    
    # Verify memory metrics
    memory = data["memory"]
    assert "total_mb" in memory
    assert "used_mb" in memory
    assert "free_mb" in memory
    assert "usage_percent" in memory

def test_system_security_endpoint():
    """Test /system/security endpoint"""
    
    response = client.get("/system/security")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "security_status" in data
    assert "threats" in data
    assert "vulnerabilities" in data
    assert "last_scan" in data
    assert "recommendations" in data
    
    # Verify security status
    assert data["security_status"] in ["secure", "warning", "critical"]
    
    # Verify threats and vulnerabilities are lists
    assert isinstance(data["threats"], list)
    assert isinstance(data["vulnerabilities"], list)
    assert isinstance(data["recommendations"], list)

def test_system_backup_endpoint():
    """Test /system/backup endpoint"""
    
    response = client.get("/system/backup")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "backups" in data
    assert "last_backup" in data
    assert "backup_status" in data
    assert "storage_used" in data
    
    # Verify backups structure
    backups = data["backups"]
    if backups:  # If there are backups
        for backup in backups:
            assert "id" in backup
            assert "timestamp" in backup
            assert "size_mb" in backup
            assert "status" in backup
            assert "type" in backup

def test_system_maintenance_endpoint():
    """Test /system/maintenance endpoint"""
    
    response = client.get("/system/maintenance")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "maintenance_mode" in data
    assert "scheduled_maintenance" in data
    assert "last_maintenance" in data
    assert "next_maintenance" in data
    
    # Verify maintenance mode is boolean
    assert isinstance(data["maintenance_mode"], bool)

def test_system_health_detailed_endpoint(mock_redis, mock_db):
    """Test /system/health/detailed endpoint"""
    
    response = client.get("/system/health/detailed")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "overall_health" in data
    assert "components" in data
    assert "dependencies" in data
    assert "performance" in data
    assert "security" in data
    
    # Verify components health
    components = data["components"]
    for component_name, component_health in components.items():
        assert "status" in component_health
        assert "last_check" in component_health
        assert "response_time" in component_health
        assert component_health["status"] in ["healthy", "degraded", "unhealthy"]

def test_system_metrics_prometheus():
    """Test /metrics/prometheus endpoint for Prometheus format"""
    
    response = client.get("/metrics/prometheus")
    
    # Verify response
    assert response.status_code == 200
    content = response.text
    
    # Verify Prometheus format
    assert "# HELP" in content
    assert "# TYPE" in content
    assert "eterna_home_" in content
    
    # Verify specific metrics
    assert "eterna_home_requests_total" in content
    assert "eterna_home_response_time_seconds" in content
    assert "eterna_home_error_rate" in content

def test_system_uptime_endpoint():
    """Test /system/uptime endpoint"""
    
    response = client.get("/system/uptime")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "uptime_seconds" in data
    assert "uptime_formatted" in data
    assert "startup_time" in data
    assert "last_restart" in data
    
    # Verify uptime is positive
    assert data["uptime_seconds"] > 0
    
    # Verify formatted uptime
    assert "days" in data["uptime_formatted"] or "hours" in data["uptime_formatted"]

def test_system_version_endpoint():
    """Test /system/version endpoint"""
    
    response = client.get("/system/version")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "version" in data
    assert "build_date" in data
    assert "git_commit" in data
    assert "environment" in data
    
    # Verify version format
    assert "." in data["version"]  # Should contain version numbers

def test_system_config_endpoint():
    """Test /system/config endpoint"""
    
    response = client.get("/system/config")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "database" in data
    assert "redis" in data
    assert "minio" in data
    assert "security" in data
    assert "logging" in data
    
    # Verify configuration structure
    assert "url" in data["database"]
    assert "host" in data["redis"]
    assert "endpoint" in data["minio"] 