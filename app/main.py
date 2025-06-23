from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
import os
from typing import List

from app.core.config import settings
from app.database import get_db, engine
from app.routers import auth, users, roles, house as house_router, node as node_router, document as document_router, documents as documents_router, bim as bim_router, node_areas, main_areas, area_reports, voice, local_interface, secure_area
from app.core.redis import redis_client
from app.core.limiter import limiter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all models to ensure they are registered
from app.db.base import Base

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Eterna-Home API...")
    
    # Test Redis connection
    try:
        await redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
    
    # Test database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Eterna-Home API...")
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="Eterna-Home API",
    description="API per la gestione di case intelligenti",
    version="1.0.0",
    lifespan=lifespan
)

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

@app.get("/")
async def root():
    return {"message": "Eterna-Home API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Eterna-Home API is operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)