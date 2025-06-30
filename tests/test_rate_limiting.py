import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.core.security import create_access_token
from app.database import get_db
from app.core.redis import redis_client
from unittest.mock import patch, MagicMock
import time

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
def mock_redis():
    """Mock Redis client for rate limiting"""
    with patch('app.core.redis.redis_client') as mock:
        mock.incr.return_value = 1
        mock.expire.return_value = True
        mock.get.return_value = None
        yield mock

def test_rate_limiting_login_attempts(mock_redis):
    """Test rate limiting on login attempts"""
    
    # Simulate multiple login attempts
    for i in range(10):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        # First 9 attempts should be allowed (even if wrong password)
        if i < 9:
            assert response.status_code in [401, 422]  # Unauthorized or validation error
        else:
            # 10th attempt should trigger rate limiting
            assert response.status_code == 429  # Too Many Requests

def test_rate_limiting_reset_after_timeout(mock_redis):
    """Test rate limiting resets after timeout"""
    
    # Mock Redis to simulate rate limit being active
    mock_redis.get.return_value = "10"  # 10 attempts already made
    
    # Try to login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    
    # Should be rate limited
    assert response.status_code == 429
    
    # Mock Redis to simulate timeout (no rate limit)
    mock_redis.get.return_value = None
    
    # Try to login again
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    
    # Should be allowed again
    assert response.status_code in [401, 422]  # Not rate limited

def test_rate_limiting_different_endpoints(mock_redis):
    """Test rate limiting on different endpoints"""
    
    # Test rate limiting on document upload
    for i in range(10):
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", b"test content", "application/pdf")},
            data={"house_id": "1"}
        )
        
        if i < 9:
            assert response.status_code in [401, 422]  # Unauthorized or validation error
        else:
            assert response.status_code == 429  # Too Many Requests

def test_rate_limiting_ip_based(mock_redis):
    """Test rate limiting is IP-based"""
    
    # Mock different IP addresses
    with patch('app.core.limiter.get_client_ip') as mock_ip:
        # First IP
        mock_ip.return_value = "192.168.1.100"
        
        for i in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )
            
            if i < 9:
                assert response.status_code in [401, 422]
            else:
                assert response.status_code == 429
        
        # Different IP should not be rate limited
        mock_ip.return_value = "192.168.1.101"
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code in [401, 422]  # Not rate limited

def test_rate_limiting_user_based(mock_redis):
    """Test rate limiting is user-based for authenticated requests"""
    
    # Create access token
    token = create_access_token(data={
        "sub": "test@example.com",
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test rate limiting on authenticated endpoint
    for i in range(10):
        response = client.get(
            "/api/v1/users/me",
            headers=headers
        )
        
        if i < 9:
            assert response.status_code == 200  # Success
        else:
            assert response.status_code == 429  # Too Many Requests

def test_rate_limiting_configuration():
    """Test rate limiting configuration"""
    
    from app.core.config import settings
    
    # Verify rate limiting is enabled
    assert settings.ENABLE_RATE_LIMITING == True
    
    # Verify rate limit requests per minute
    assert settings.RATE_LIMIT_REQUESTS == 100

def test_rate_limiting_headers(mock_redis):
    """Test rate limiting response headers"""
    
    # Trigger rate limiting
    for i in range(10):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        if i == 9:  # 10th attempt
            assert response.status_code == 429
            
            # Verify rate limiting headers
            headers = response.headers
            assert "X-RateLimit-Limit" in headers
            assert "X-RateLimit-Remaining" in headers
            assert "X-RateLimit-Reset" in headers
            assert "Retry-After" in headers

def test_rate_limiting_whitelist():
    """Test rate limiting whitelist for certain endpoints"""
    
    # Health check should not be rate limited
    for i in range(20):  # More than rate limit
        response = client.get("/health")
        assert response.status_code == 200  # Always allowed

def test_rate_limiting_redis_connection_error():
    """Test rate limiting behavior when Redis is unavailable"""
    
    # Mock Redis connection error
    with patch('app.core.redis.redis_client') as mock_redis:
        mock_redis.incr.side_effect = Exception("Redis connection error")
        
        # Should still work (fallback behavior)
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        # Should not crash, should return appropriate error
        assert response.status_code in [401, 422, 500]

def test_rate_limiting_burst_protection(mock_redis):
    """Test rate limiting burst protection"""
    
    # Simulate burst of requests
    responses = []
    for i in range(15):  # More than rate limit
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        responses.append(response.status_code)
    
    # Count rate limited responses
    rate_limited = responses.count(429)
    assert rate_limited > 0  # Should have some rate limited

def test_rate_limiting_sliding_window(mock_redis):
    """Test rate limiting sliding window behavior"""
    
    # Mock Redis to simulate sliding window
    mock_redis.incr.return_value = 5  # 5 requests in current window
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    
    # Should still be allowed (under limit)
    assert response.status_code in [401, 422]

def test_rate_limiting_logging(mock_redis):
    """Test rate limiting logging"""
    
    with patch('app.core.logging_config.get_logger') as mock_logger:
        logger = MagicMock()
        mock_logger.return_value = logger
        
        # Trigger rate limiting
        for i in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )
        
        # Verify logging was called for rate limiting
        logger.warning.assert_called()
        
        # Verify log contains rate limiting info
        log_calls = logger.warning.call_args_list
        rate_limit_logs = [call for call in log_calls if "rate_limit" in str(call)]
        assert len(rate_limit_logs) > 0

def test_rate_limiting_different_limits():
    """Test different rate limits for different endpoints"""
    
    # Test stricter rate limit for sensitive endpoints
    # This would require configuration of different limits per endpoint
    
    # Login endpoint should have stricter limit
    for i in range(10):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        if i == 9:
            assert response.status_code == 429
    
    # Regular API endpoint might have higher limit
    # This depends on implementation

def test_rate_limiting_cleanup():
    """Test rate limiting cleanup after timeout"""
    
    # Mock Redis to simulate cleanup
    with patch('app.core.redis.redis_client') as mock_redis:
        mock_redis.expire.return_value = True
        
        # Make some requests
        for i in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )
        
        # Verify expire was called (cleanup)
        assert mock_redis.expire.called

def test_rate_limiting_metrics():
    """Test rate limiting metrics collection"""
    
    with patch('app.core.logging_config.get_logger') as mock_logger:
        logger = MagicMock()
        mock_logger.return_value = logger
        
        # Trigger rate limiting
        for i in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )
        
        # Verify metrics logging
        logger.info.assert_called()
        
        # Check for rate limiting metrics
        log_calls = logger.info.call_args_list
        metrics_logs = [call for call in log_calls if "rate_limit" in str(call)]
        assert len(metrics_logs) > 0 