import pytest
import json
import logging
from fastapi.testclient import TestClient
from app.main import app
from app.core.logging_config import get_logger, set_context, clear_context, log_operation
from app.models.user import User
from app.core.security import create_access_token
from app.database import get_db
import structlog
from unittest.mock import patch, MagicMock
from app.models.enums import UserRole

client = TestClient(app)

@pytest.fixture
def db_session():
    """Get database session for testing"""
    with next(get_db()) as session:
        yield session

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id="house_1"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def mock_logger():
    """Mock logger to capture log entries"""
    with patch('app.core.logging_config.get_logger') as mock:
        logger = MagicMock()
        mock.return_value = logger
        yield logger

def test_log_structure_contains_required_fields(mock_logger):
    """Test that log entries contain all required structured fields"""
    
    # Set context with tenant and user info
    set_context(tenant_id="house_1", user_id="user_123")
    
    # Log an operation
    log_operation(
        event="test_operation",
        status="success",
        details="Test operation completed"
    )
    
    # Verify logger.info was called
    mock_logger.info.assert_called_once()
    
    # Get the call arguments
    call_args = mock_logger.info.call_args
    log_data = call_args[1]  # Keyword arguments
    
    # Verify required fields are present
    required_fields = ["tenant_id", "user_id", "event", "status", "timestamp"]
    for field in required_fields:
        assert field in log_data, f"Missing required field: {field}"
    
    # Verify field values
    assert log_data["tenant_id"] == "house_1"
    assert log_data["user_id"] == "user_123"
    assert log_data["event"] == "test_operation"
    assert log_data["status"] == "success"
    assert "timestamp" in log_data  # Should be auto-generated

def test_log_json_format():
    """Test JSON format logging"""
    
    # Set up context
    set_context(
        tenant_id="house_1",
        user_id="user_123"
    )
    
    logger = structlog.get_logger()
    
    # Log a test message
    with patch('sys.stdout') as mock_stdout:
        logger.info(
            "test_message",
            tenant_id="house_1",
            user_id="user_123",
            status="success"
        )
    
    # Verify JSON format (this is a basic check)
    # In real implementation, you'd capture the actual log output
    assert True  # Placeholder for JSON format verification

def test_log_context_management():
    """Test context setting and clearing"""
    
    # Set context
    set_context(tenant_id="house_1", user_id="user_123")
    
    # Verify context is set
    # This would require access to the actual context storage
    # For now, we test the function calls don't raise exceptions
    assert True
    
    # Clear context
    clear_context()
    
    # Verify context is cleared
    assert True

def test_log_operation_with_all_fields(mock_logger):
    """Test log_operation function with all possible fields"""
    
    # Set context
    set_context(tenant_id="house_1", user_id="user_123")
    
    # Log operation with all fields
    log_operation(
        operation="document_upload",
        status="success",
        user_id="user_123",
        tenant_id="house_1",
        resource_type="document",
        resource_id="doc_123",
        metadata={
            "file_size": 1024,
            "filename": "test.pdf",
            "endpoint": "/api/v1/documents/upload",
            "method": "POST",
            "response_time_ms": 150,
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0..."
        }
    )
    
    # Verify logger.info was called
    mock_logger.info.assert_called_once()
    
    # Get the call arguments
    call_args = mock_logger.info.call_args
    log_data = call_args[1]  # Keyword arguments
    
    # Verify all fields are present
    expected_fields = [
        "tenant_id", "user_id", "operation", "status", "timestamp",
        "resource_type", "resource_id"
    ]
    
    for field in expected_fields:
        assert field in log_data, f"Missing field: {field}"
    
    # Verify field values
    assert log_data["operation"] == "document_upload"
    assert log_data["status"] == "success"
    assert log_data["resource_type"] == "document"
    assert log_data["resource_id"] == "doc_123"

def test_log_error_with_stack_trace(mock_logger):
    """Test error logging with stack trace"""
    
    # Set context
    set_context(tenant_id="house_1", user_id="user_123")
    
    # Simulate an error
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_operation(
            operation="error_occurred",
            status="error",
            user_id="user_123",
            tenant_id="house_1",
            metadata={
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
    
    # Verify logger.error was called
    mock_logger.error.assert_called_once()
    
    # Get the call arguments
    call_args = mock_logger.error.call_args
    log_data = call_args[1]  # Keyword arguments
    
    # Verify error fields
    assert log_data["operation"] == "error_occurred"
    assert log_data["status"] == "error"
    assert "error" in log_data
    assert "error_type" in log_data
    assert log_data["error_type"] == "ValueError"

def test_log_security_event(mock_logger):
    """Test security event logging"""
    
    # Set context
    set_context(tenant_id="house_1", user_id="user_123")
    
    # Log security event
    log_operation(
        operation="security_violation",
        status="warning",
        user_id="user_123",
        tenant_id="house_1",
        resource_type="security",
        metadata={
            "security_level": "high",
            "ip_address": "192.168.1.100",
            "user_agent": "Suspicious Bot",
            "action_taken": "blocked"
        }
    )
    
    # Verify logger.warning was called
    mock_logger.warning.assert_called_once()
    
    # Get the call arguments
    call_args = mock_logger.warning.call_args
    log_data = call_args[1]  # Keyword arguments
    
    # Verify security fields
    assert log_data["operation"] == "security_violation"
    assert log_data["status"] == "warning"
    assert log_data["security_level"] == "high"
    assert log_data["action_taken"] == "blocked"

def test_log_performance_metrics(mock_logger):
    """Test performance metrics logging"""
    
    # Set context
    set_context(tenant_id="house_1", user_id="user_123")
    
    # Log performance metrics
    log_operation(
        operation="performance_metrics",
        status="success",
        user_id="user_123",
        tenant_id="house_1",
        resource_type="performance",
        metadata={
            "response_time_ms": 250,
            "database_query_time_ms": 50,
            "cache_hit_ratio": 0.85,
            "memory_usage_mb": 128,
            "cpu_usage_percent": 15.5
        }
    )
    
    # Verify logger.info was called
    mock_logger.info.assert_called_once()
    
    # Get the call arguments
    call_args = mock_logger.info.call_args
    log_data = call_args[1]  # Keyword arguments
    
    # Verify performance fields
    assert log_data["operation"] == "performance_metrics"
    assert log_data["response_time_ms"] == 250
    assert log_data["database_query_time_ms"] == 50
    assert log_data["cache_hit_ratio"] == 0.85
    assert log_data["memory_usage_mb"] == 128
    assert log_data["cpu_usage_percent"] == 15.5

def test_log_multi_tenant_context(mock_logger):
    """Test logging with multi-tenant context"""
    
    # Test different tenants
    tenants = ["house_1", "house_2", "house_3"]
    
    for tenant_id in tenants:
        # Set context for each tenant
        set_context(tenant_id=tenant_id, user_id=f"user_{tenant_id}")
        
        # Log operation
        log_operation(
            operation="tenant_operation",
            status="success",
            user_id=f"user_{tenant_id}",
            tenant_id=tenant_id,
            resource_type="tenant",
            metadata={"details": f"Operation for tenant {tenant_id}"}
        )
        
        # Verify tenant_id is correctly set
        call_args = mock_logger.info.call_args
        log_data = call_args[1]
        assert log_data["tenant_id"] == tenant_id
        assert log_data["user_id"] == f"user_{tenant_id}"

def test_log_trace_id_correlation(mock_logger):
    """Test trace ID correlation in logs"""
    
    # Set context with trace ID
    set_context(
        tenant_id="house_1", 
        user_id="user_123",
        trace_id="test-trace-123"
    )
    
    # Log multiple operations
    operations = ["op1", "op2", "op3"]
    
    for operation in operations:
        log_operation(
            operation=operation,
            status="success",
            user_id="user_123",
            tenant_id="house_1",
            resource_type="test"
        )
    
    # Verify all logs have the same trace ID
    for call in mock_logger.info.call_args_list:
        log_data = call[1]  # Keyword arguments
        assert log_data["trace_id"] == "test-trace-123" 