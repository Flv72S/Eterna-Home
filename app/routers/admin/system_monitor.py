from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.utils.security import get_current_user
from app.core.auth.rbac import require_permission_in_tenant
from app.core.logging_config import log_security_event
from app.database import get_session
from app.models.user import User
from app.models.permission import Permission
from app.core.config import settings

router = APIRouter(prefix="/admin/system", tags=["admin-monitoring"])

def require_monitoring_permission():
    """Dependency per verificare il permesso di monitoraggio del sistema"""
    def permission_checker(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
    ) -> User:
        # Verifica se l'utente è superuser
        if current_user.is_superuser:
            return current_user
        
        # Verifica se l'utente ha il permesso view_monitoring
        # Cerca il permesso direttamente associato all'utente
        from app.models.user_permission import UserPermission
        
        permission = session.exec(
            select(Permission)
            .join(UserPermission, Permission.id == UserPermission.permission_id)
            .where(
                UserPermission.user_id == current_user.id,
                Permission.name == "view_monitoring"
            )
        ).first()
        
        if permission:
            return current_user
        
        # Se non ha il permesso diretto, nega l'accesso
        raise HTTPException(
            status_code=403,
            detail="Access denied. Required permission 'view_monitoring'"
        )
    
    return permission_checker

async def get_system_health() -> Dict[str, Any]:
    """Ottiene lo stato di salute del sistema tramite endpoint interno"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.BASE_URL}/system/health", timeout=5.0)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"Health check failed: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Health check error: {str(e)}"}

async def get_system_ready() -> Dict[str, Any]:
    """Ottiene lo stato di readiness del sistema"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.BASE_URL}/system/ready", timeout=5.0)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"Ready check failed: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Ready check error: {str(e)}"}

async def get_system_metrics() -> Dict[str, Any]:
    """Ottiene le metriche Prometheus del sistema"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.BASE_URL}/system/metrics", timeout=5.0)
            if response.status_code == 200:
                return parse_prometheus_metrics(response.text)
            else:
                return {"status": "error", "message": f"Metrics check failed: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Metrics check error: {str(e)}"}

def parse_prometheus_metrics(metrics_text: str) -> Dict[str, Any]:
    """Parsing delle metriche Prometheus in formato leggibile"""
    metrics = {
        "status": "success",
        "uptime_seconds": 0,
        "requests_total": 0,
        "requests_5xx_total": 0,
        "requests_4xx_total": 0,
        "upload_operations_total": 0,
        "active_users": 0,
        "database_connections": 0,
        "redis_connections": 0,
        "minio_operations": 0
    }
    
    try:
        lines = metrics_text.strip().split('\n')
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
                
            if 'process_start_time_seconds' in line:
                # Calcola uptime
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        start_time = float(parts[1])
                        uptime = datetime.now().timestamp() - start_time
                        metrics["uptime_seconds"] = int(uptime)
                    except ValueError:
                        pass
                        
            elif 'http_requests_total' in line and 'status=' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[1])
                        if 'status="5' in line:
                            metrics["requests_5xx_total"] = int(value)
                        elif 'status="4' in line:
                            metrics["requests_4xx_total"] = int(value)
                        else:
                            metrics["requests_total"] = int(value)
                    except ValueError:
                        pass
                        
            elif 'upload_operations_total' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        metrics["upload_operations_total"] = int(float(parts[1]))
                    except ValueError:
                        pass
                        
            elif 'active_users' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        metrics["active_users"] = int(float(parts[1]))
                    except ValueError:
                        pass
                        
            elif 'database_connections' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        metrics["database_connections"] = int(float(parts[1]))
                    except ValueError:
                        pass
                        
            elif 'redis_connections' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        metrics["redis_connections"] = int(float(parts[1]))
                    except ValueError:
                        pass
                        
            elif 'minio_operations' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        metrics["minio_operations"] = int(float(parts[1]))
                    except ValueError:
                        pass
                        
    except Exception as e:
        metrics["status"] = "error"
        metrics["message"] = f"Parsing error: {str(e)}"
        
    return metrics

@router.get("/status", response_class=HTMLResponse)
async def admin_system_status(
    request: Request,
    current_user: User = Depends(require_monitoring_permission()),
    session: Session = Depends(get_session)
):
    """Dashboard di monitoraggio del sistema - Richiede permesso view_monitoring"""
    
    # Log dell'accesso per sicurezza
    await log_security_event(
        "monitor_access",
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        details={"endpoint": "/admin/system/status"}
    )
    
    # Raccolta dati di sistema in parallelo
    health_task = get_system_health()
    ready_task = get_system_ready()
    metrics_task = get_system_metrics()
    
    health_data, ready_data, metrics_data = await asyncio.gather(
        health_task, ready_task, metrics_task, return_exceptions=True
    )
    
    # Gestione eccezioni
    if isinstance(health_data, Exception):
        health_data = {"status": "error", "message": str(health_data)}
    if isinstance(ready_data, Exception):
        ready_data = {"status": "error", "message": str(ready_data)}
    if isinstance(metrics_data, Exception):
        metrics_data = {"status": "error", "message": str(metrics_data)}
    
    # Calcolo stato generale
    overall_status = "healthy"
    if (health_data.get("status") == "error" or 
        ready_data.get("status") == "error" or 
        metrics_data.get("status") == "error"):
        overall_status = "unhealthy"
    
    # Preparazione dati per il template
    context = {
        "user": current_user,
        "overall_status": overall_status,
        "health_data": health_data,
        "ready_data": ready_data,
        "metrics_data": metrics_data,
        "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_formatted": format_uptime(metrics_data.get("uptime_seconds", 0))
    }
    
    return templates.TemplateResponse("admin/system/monitor.html", {"request": request, **context})

def format_uptime(seconds: int) -> str:
    """Formatta l'uptime in formato leggibile"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"

# Import dei template alla fine per evitare import circolari
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="app/templates") 