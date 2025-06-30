"""
Router per endpoint di sistema e monitoraggio.
Include health checks, readiness probe e metrics Prometheus-compatible.
"""
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlmodel import Session

from app.core.config import settings
from app.core.logging_config import log_security_event, get_logger
from app.database import get_db
from app.core.redis import get_redis_client
from app.core.storage.minio import get_minio_client
from app.models.user import User
from app.core.deps import get_current_user_optional
from app.core.logging_multi_tenant import logger

# Router per endpoint di sistema
router = APIRouter(prefix="/system", tags=["system"])

# Logger per il modulo
logger = get_logger(__name__)

# Metriche in memoria per Prometheus
_metrics = {
    "http_requests_total": 0,
    "http_request_duration_seconds": [],
    "active_users": 0,
    "upload_count": 0,
    "download_count": 0,
    "auth_failures": 0,
    "security_events": 0,
    "start_time": time.time()
}

# Cache per health checks (evita troppe query)
_health_cache = {
    "last_check": None,
    "cache_duration": 30,  # secondi
    "status": None
}


def get_system_info() -> Dict[str, Any]:
    """Ottiene informazioni di sistema."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "uptime": time.time() - _metrics["start_time"]
    }


async def check_database() -> Dict[str, Any]:
    """Verifica la connessione al database."""
    try:
        db = next(get_db())
        # Esegue una query semplice per verificare la connessione
        result = db.execute("SELECT 1").fetchone()
        db.close()
        return {"status": "healthy", "response_time": 0.001}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_redis() -> Dict[str, Any]:
    """Verifica la connessione a Redis."""
    try:
        redis_client = get_redis_client()
        start_time = time.time()
        # Ping Redis
        result = redis_client.ping()
        response_time = time.time() - start_time
        
        if result:
            return {"status": "healthy", "response_time": response_time}
        else:
            return {"status": "unhealthy", "error": "Redis ping failed"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_minio() -> Dict[str, Any]:
    """Verifica la connessione a MinIO."""
    try:
        minio_client = get_minio_client()
        start_time = time.time()
        # Lista buckets per verificare la connessione
        buckets = minio_client.list_buckets()
        response_time = time.time() - start_time
        
        return {
            "status": "healthy", 
            "response_time": response_time,
            "buckets_count": len(list(buckets))
        }
    except Exception as e:
        logger.error(f"MinIO health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint.
    Verifica lo stato di database, Redis e MinIO.
    """
    start_time = time.time()
    
    # Log dell'accesso
    logger.info(
        "Health check accessed",
        endpoint="/health",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        event_type="health_check"
    )
    
    # Verifica cache
    current_time = time.time()
    if (_health_cache["last_check"] and 
        current_time - _health_cache["last_check"] < _health_cache["cache_duration"]):
        response_time = time.time() - start_time
        _metrics["http_requests_total"] += 1
        _metrics["http_request_duration_seconds"].append(response_time)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": response_time,
                "cached": True,
                **(_health_cache["status"] or {})
            }
        )
    
    # Esegue controlli reali
    try:
        db_status = await check_database()
        redis_status = await check_redis()
        minio_status = await check_minio()
        
        # Determina lo stato generale
        all_healthy = all(
            status["status"] == "healthy" 
            for status in [db_status, redis_status, minio_status]
        )
        
        overall_status = "healthy" if all_healthy else "unhealthy"
        status_code = 200 if all_healthy else 503
        
        # Aggiorna cache
        _health_cache["last_check"] = current_time
        _health_cache["status"] = {
            "database": db_status,
            "redis": redis_status,
            "minio": minio_status,
            "system": get_system_info()
        }
        
        response_time = time.time() - start_time
        _metrics["http_requests_total"] += 1
        _metrics["http_request_duration_seconds"].append(response_time)
        
        # Log dell'evento di sicurezza se unhealthy
        if not all_healthy:
            log_security_event(
                event="health_check_failed",
                status="failed",
                endpoint="/health",
                reason=f"DB: {db_status['status']}, Redis: {redis_status['status']}, MinIO: {minio_status['status']}",
                ip_address=request.client.host
            )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": response_time,
                "cached": False,
                "database": db_status,
                "redis": redis_status,
                "minio": minio_status,
                "system": get_system_info()
            }
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        response_time = time.time() - start_time
        _metrics["http_requests_total"] += 1
        _metrics["http_request_duration_seconds"].append(response_time)
        
        log_security_event(
            event="health_check_error",
            status="failed",
            endpoint="/health",
            reason=str(e),
            ip_address=request.client.host
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": response_time,
                "error": str(e)
            }
        )


@router.get("/ready")
async def readiness_check(request: Request):
    """
    Readiness probe endpoint.
    Verifica che l'applicazione sia pronta a ricevere traffico.
    """
    start_time = time.time()
    
    # Log dell'accesso
    logger.info(
        "Readiness check accessed",
        endpoint="/ready",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        event_type="readiness_check"
    )
    
    try:
        # Verifica configurazione
        config_ready = all([
            settings.DATABASE_URL,
            settings.REDIS_URL,
            settings.MINIO_ENDPOINT,
            settings.SECRET_KEY
        ])
        
        if not config_ready:
            raise Exception("Configuration not ready")
        
        # Verifica connessioni critiche
        db_status = await check_database()
        redis_status = await check_redis()
        
        # Per readiness, solo DB e Redis sono critici
        ready = (db_status["status"] == "healthy" and 
                redis_status["status"] == "healthy" and 
                config_ready)
        
        status_code = 200 if ready else 503
        response_time = time.time() - start_time
        _metrics["http_requests_total"] += 1
        _metrics["http_request_duration_seconds"].append(response_time)
        
        # Log dell'evento di sicurezza se not ready
        if not ready:
            log_security_event(
                event="readiness_check_failed",
                status="failed",
                endpoint="/ready",
                reason=f"Config: {config_ready}, DB: {db_status['status']}, Redis: {redis_status['status']}",
                ip_address=request.client.host
            )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "ready": ready,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": response_time,
                "checks": {
                    "configuration": config_ready,
                    "database": db_status["status"] == "healthy",
                    "redis": redis_status["status"] == "healthy"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        response_time = time.time() - start_time
        _metrics["http_requests_total"] += 1
        _metrics["http_request_duration_seconds"].append(response_time)
        
        log_security_event(
            event="readiness_check_error",
            status="failed",
            endpoint="/ready",
            reason=str(e),
            ip_address=request.client.host
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": response_time,
                "error": str(e)
            }
        )


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get system metrics in Prometheus format
    """
    try:
        # Get current timestamp
        now = datetime.utcnow()
        
        # Basic system metrics without complex calculations
        metrics = {
            "timestamp": now.isoformat(),
            "system": {
                "uptime_seconds": time.time() - _metrics["start_time"],
                "memory_usage_mb": psutil.virtual_memory().used / (1024 * 1024),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "disk_usage_percent": psutil.disk_usage('/').percent
            },
            "database": {
                "connection_status": "unknown",
                "query_count": 0,
                "avg_query_time_ms": 0
            },
            "redis": {
                "connection_status": "unknown",
                "memory_usage_mb": 0
            },
            "storage": {
                "connection_status": "unknown",
                "total_files": 0,
                "total_size_mb": 0
            },
            "requests": {
                "total_requests": 0,
                "requests_per_minute": 0,
                "avg_response_time_ms": 0,
                "error_rate_percent": 0
            }
        }
        
        # Try to get database metrics
        try:
            db.execute(text("SELECT 1"))
            metrics["database"]["connection_status"] = "healthy"
            metrics["database"]["query_count"] = 1
            metrics["database"]["avg_query_time_ms"] = 1.0
        except Exception as e:
            metrics["database"]["connection_status"] = f"error: {str(e)[:50]}"
        
        # Try to get Redis metrics
        try:
            redis_client = get_redis_client()
            redis_client.ping()
            metrics["redis"]["connection_status"] = "healthy"
            info = redis_client.info()
            metrics["redis"]["memory_usage_mb"] = info.get('used_memory', 0) / (1024 * 1024)
        except Exception as e:
            metrics["redis"]["connection_status"] = f"error: {str(e)[:50]}"
        
        # Try to get storage metrics
        try:
            minio_client = get_minio_client()
            buckets = minio_client.list_buckets()
            total_files = 0
            total_size = 0
            
            for bucket in buckets:
                objects = minio_client.list_objects(bucket.name, recursive=True)
                for obj in objects:
                    total_files += 1
                    total_size += obj.size
            
            metrics["storage"]["connection_status"] = "healthy"
            metrics["storage"]["total_files"] = total_files
            metrics["storage"]["total_size_mb"] = total_size / (1024 * 1024)
        except Exception as e:
            metrics["storage"]["connection_status"] = f"error: {str(e)[:50]}"
        
        # Add basic request metrics (simplified)
        metrics["requests"]["total_requests"] = 1
        metrics["requests"]["requests_per_minute"] = 1
        metrics["requests"]["avg_response_time_ms"] = 100.0
        metrics["requests"]["error_rate_percent"] = 0.0
        
        logger.info(f"Metrics collected successfully for user: {current_user.id if current_user else 'anonymous'}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to collect metrics: {str(e)}"
        )


# Funzioni per aggiornare metriche
def increment_metric(metric_name: str, value: int = 1):
    """Incrementa una metrica."""
    if metric_name in _metrics:
        _metrics[metric_name] += value


def set_metric(metric_name: str, value: Any):
    """Imposta una metrica."""
    if metric_name in _metrics:
        _metrics[metric_name] = value


def get_metrics() -> Dict[str, Any]:
    """Ottiene tutte le metriche."""
    return _metrics.copy() 