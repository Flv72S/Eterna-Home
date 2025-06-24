from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os
from typing import List

from app.core.config import settings
from app.core.logging import setup_logging, get_logger, set_trace_id, get_trace_id
from app.core.middleware import LoggingMiddleware, ErrorLoggingMiddleware, SecurityLoggingMiddleware
from app.database import get_db, engine
from app.routers import (
    auth, users, roles, house as house_router, node as node_router, 
    document as document_router, documents as documents_router, 
    bim as bim_router, node_areas, main_areas, area_reports, 
    voice, local_interface, secure_area, ai_assistant
)
from app.core.redis import redis_client
from app.core.limiter import limiter

# Configura il logging strutturato
setup_logging(
    level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO",
    json_format=True,
    include_trace_id=True
)

logger = get_logger(__name__)

# Import all models to ensure they are registered
from app.db.base import Base

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Eterna-Home API", 
                service="eterna-home-api",
                version="1.0.0",
                environment=os.getenv("ENVIRONMENT", "development"))
    
    # Test Redis connection
    try:
        await redis_client.ping()
        logger.info("Redis connection successful", 
                    component="redis",
                    status="connected")
    except Exception as e:
        logger.error("Redis connection failed", 
                     component="redis",
                     error=str(e),
                     exc_info=True)
    
    # Test database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection successful", 
                    component="database",
                    status="connected")
    except Exception as e:
        logger.error("Database connection failed", 
                     component="database",
                     error=str(e),
                     exc_info=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Eterna-Home API", 
                service="eterna-home-api",
                trace_id=get_trace_id())
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="Eterna-Home API",
    description="API per la gestione di case intelligenti",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware per il logging
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(SecurityLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting setup - use the correct slowapi syntax
app.state.limiter = limiter

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

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Eterna-Home API is running!"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy", "message": "Eterna-Home API is operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)