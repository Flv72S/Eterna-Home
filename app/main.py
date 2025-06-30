from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
import os
from typing import List

from app.core.config import settings
from app.core.logging_config import (
    setup_logging, 
    get_logger, 
    set_context, 
    clear_context,
    log_operation
)
from app.core.middleware import LoggingMiddleware, SecurityMiddleware
from app.database import get_db, engine
from app.routers import (
    auth, users, roles, house as house_router, node as node_router, 
    document as document_router, documents as documents_router, 
    bim as bim_router, node_areas, main_areas, area_reports, 
    voice, local_interface, secure_area, ai_assistant, activator,
    user_house, system
)
from app.routers.admin import dashboard as admin_dashboard, roles as admin_roles
from app.core.redis import redis_client
from app.security.limiter import security_limiter, rate_limit_middleware

# Configura il logging strutturato centralizzato
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_format=os.getenv("LOG_FORMAT", "json").lower() == "json",
    log_dir=os.getenv("LOG_DIR", "logs")
)

logger = get_logger(__name__)

# Import all models to ensure they are registered
from app.db.base import Base

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(
        "Starting up Eterna-Home API",
        event_name="application_startup",
        status="started",
        service="eterna-home-api",
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development")
    )
    
    # Test Redis connection
    try:
        if redis_client:
            await redis_client.ping()
            logger.info(
                "Redis connection successful",
                event_name="redis_connection",
                status="success",
                component="redis"
            )
        else:
            logger.warning(
                "Redis connection failed",
                event_name="redis_connection",
                status="failed",
                component="redis",
                error="Redis client not initialized"
            )
    except Exception as e:
        logger.error(
            "Redis connection failed",
            event_name="redis_connection",
            status="failed",
            component="redis",
            error=str(e)
        )
    
    # Test database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(
            "Database connection successful",
            event_name="database_connection",
            status="success",
            component="database"
        )
    except Exception as e:
        logger.error(
            "Database connection failed",
            event_name="database_connection",
            status="failed",
            component="database",
            error=str(e)
        )
    
    yield
    
    # Shutdown
    logger.info(
        "Shutting down Eterna-Home API",
        event_name="application_shutdown",
        status="shutdown",
        service="eterna-home-api"
    )
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="Eterna-Home API",
    description="API per la gestione di case intelligenti",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware per il logging e sicurezza
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityMiddleware)

# CORS middleware - Configurazione sicura dalle variabili d'ambiente
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOWED_METHODS,
    allow_headers=settings.CORS_ALLOWED_HEADERS,
)

# Rate limiting setup - nuovo sistema avanzato
if settings.ENABLE_RATE_LIMITING:
    app.state.limiter = security_limiter.limiter
    app.add_exception_handler(Exception, rate_limit_middleware)
    logger.info(
        "Rate limiting enabled",
        event_name="rate_limiting_setup",
        status="enabled"
    )
else:
    logger.info(
        "Rate limiting disabled",
        event_name="rate_limiting_setup",
        status="disabled"
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(roles.router, prefix="/api/v1", tags=["roles"])
app.include_router(house_router.router, prefix="/api/v1", tags=["houses"])
app.include_router(node_router.router, prefix="/api/v1", tags=["nodes"])
app.include_router(document_router.router, prefix="/api/v1", tags=["documents"])
app.include_router(documents_router.router, prefix="/api/v1", tags=["documents"])
app.include_router(bim_router.router, prefix="/api/v1", tags=["BIM Models"])
app.include_router(node_areas.router, prefix="/api/v1/node-areas", tags=["Node Areas"])
app.include_router(main_areas.router, prefix="/api/v1/main-areas", tags=["Main Areas"])
app.include_router(area_reports.router, prefix="/api/v1/area-reports", tags=["Area Reports"])
app.include_router(voice.router, tags=["Voice Commands"])
app.include_router(local_interface.router, tags=["Local Interface"])
app.include_router(secure_area.router)
app.include_router(ai_assistant.router, prefix="/api/v1", tags=["AI Assistant"])
app.include_router(activator.router, prefix="/api/v1", tags=["Physical Activators"])
app.include_router(user_house.router, tags=["User House Management"])

# Include admin dashboard router
app.include_router(admin_dashboard.router, tags=["admin"])
app.include_router(admin_roles.router, tags=["admin"])

# Include system monitoring router
app.include_router(system.router, tags=["system"])

@app.get("/")
async def root():
    logger.info(
        "Root endpoint accessed",
        event_name="endpoint_access",
        status="success",
        endpoint="/"
    )
    return {"message": "Eterna-Home API is running!"}

@app.get("/health")
async def health_check():
    logger.info(
        "Health check endpoint accessed",
        event_name="health_check",
        status="success",
        endpoint="/health"
    )
    return {"status": "healthy", "message": "Eterna-Home API is operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)