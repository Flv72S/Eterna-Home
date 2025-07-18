"""
Test per il sistema di logging base.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from app.core.logging_config import get_logger, setup_logging


def test_get_logger():
    """Test che get_logger restituisce un logger valido."""
    logger = get_logger("test_module")
    assert logger is not None
    assert isinstance(logger, logging.Logger)


def test_setup_logging():
    """Test che setup_logging non genera errori."""
    try:
        setup_logging(level="INFO", json_format=False)
        assert True
    except Exception as e:
        pytest.fail(f"setup_logging ha generato un errore: {e}")


def test_logger_info():
    """Test logging di messaggi info."""
    logger = get_logger("test_module")
    
    with patch('sys.stdout') as mock_stdout:
        logger.info("Test message")
        # Verifica che il logger non generi errori
        assert True


def test_logger_error():
    """Test logging di messaggi di errore."""
    logger = get_logger("test_module")
    
    with patch('sys.stdout') as mock_stdout:
        logger.error("Test error message")
        # Verifica che il logger non generi errori
        assert True


def test_logger_warning():
    """Test logging di messaggi di warning."""
    logger = get_logger("test_module")
    
    with patch('sys.stdout') as mock_stdout:
        logger.warning("Test warning message")
        # Verifica che il logger non generi errori
        assert True


def test_logger_debug():
    """Test logging di messaggi debug."""
    logger = get_logger("test_module")
    
    with patch('sys.stdout') as mock_stdout:
        logger.debug("Test debug message")
        # Verifica che il logger non generi errori
        assert True


def test_logger_with_context():
    """Test logging con contesto aggiuntivo."""
    logger = get_logger("test_module")
    
    with patch('sys.stdout') as mock_stdout:
        logger.info("Test message", extra={"user_id": 123, "action": "test"})
        # Verifica che il logger non generi errori
        assert True


def test_logger_exception():
    """Test logging di eccezioni."""
    logger = get_logger("test_module")
    
    with patch('sys.stdout') as mock_stdout:
        try:
            raise ValueError("Test exception")
        except Exception:
            logger.exception("Test exception logging")
        # Verifica che il logger non generi errori
        assert True 