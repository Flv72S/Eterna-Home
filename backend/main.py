from fastapi import FastAPI, Request, Depends
from backend.db.session import engine
from sqlmodel import SQLModel
from backend.models import user, house, node, document, audio_log, maintenance
from backend.routers import houses as houses_router
from backend.routers import node as node_router
from backend.routers import document as document_router
from backend.routers import auth as auth_router
from backend.routers import maintenance as maintenance_router
from backend.routers import legacy_documents as legacy_documents_router
from backend.routers import ai_maintenance as ai_maintenance_router
from backend.routers import bim_files as bim_files_router
from backend.routers import voice_interfaces as voice_interfaces_router
from backend.config.logging_config import setup_logging
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
import os
from backend.core.config import settings

# Configurazione del logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware per il logging delle richieste
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Richiesta ricevuta: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.debug(f"Risposta inviata: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione della richiesta: {str(e)}")
        raise

# Includi tutti i router nell'applicazione
app.include_router(auth_router.router)
app.include_router(houses_router.router)
app.include_router(node_router.router)
app.include_router(document_router.router)
app.include_router(maintenance_router.router)
app.include_router(legacy_documents_router.router)
app.include_router(ai_maintenance_router.router)
app.include_router(bim_files_router.router)
app.include_router(voice_interfaces_router.router)

@app.get("/")
async def root():
    return {"message": "Eterna Home Backend is running!"}

@app.on_event("startup")
async def on_startup():
    SQLModel.metadata.create_all(engine)
    try:
        # Inizializza Redis solo se non siamo in modalità sviluppo
        if os.getenv("ENVIRONMENT") != "development":
            try:
                redis_client = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
                await FastAPILimiter.init(redis_client)
                logger.info("Redis initialized successfully.")
            except Exception as e:
                logger.warning(f"Redis initialization failed: {str(e)}")
                logger.warning("Rate limiting will be disabled.")
        else:
            logger.info("Running in development mode - Redis rate limiting disabled.")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Applicazione terminata")

# Esempio di rate limiting su un endpoint
@app.get("/rate-limited", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def rate_limited():
    return {"message": "This endpoint is rate limited to 5 requests per minute."} 