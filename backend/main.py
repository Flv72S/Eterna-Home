from fastapi import FastAPI, Request
from db.session import engine, Base
from models import user, house, node, document, audio_log
from routers import house as house_router
from routers import node as node_router
from routers import document as document_router
from routers import auth as auth_router
from routers import maintenance as maintenance_router
from routers import legacy_documents as legacy_documents_router
from routers import ai_maintenance as ai_maintenance_router
from routers import bim_files as bim_files_router
from config.logging_config import setup_logging
import logging
from fastapi.middleware.cors import CORSMiddleware

# Configurazione del logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Eterna Home Backend API")

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

app.include_router(auth_router.router)
app.include_router(house_router.router)
app.include_router(node_router.router)
app.include_router(document_router.router)
app.include_router(maintenance_router.router)
app.include_router(legacy_documents_router.router)
app.include_router(ai_maintenance_router.router)
app.include_router(bim_files_router.router)

@app.get("/")
async def root():
    return {"message": "Eterna Home Backend is running!"}

@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/checked successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Applicazione terminata") 