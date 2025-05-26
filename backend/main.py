from fastapi import FastAPI
from db.session import engine, Base
from models import user, house, node, document, audio_log
from routers import house as house_router
from routers import node as node_router
from routers import document as document_router
from routers import auth as auth_router
from routers import maintenance as maintenance_router
from routers import legacy_documents as legacy_documents_router
from config.logging_config import setup_logging
import logging

# Configurazione del logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Eterna Home Backend API")

app.include_router(auth_router.router)
app.include_router(house_router.router)
app.include_router(node_router.router)
app.include_router(document_router.router)
app.include_router(maintenance_router.router)
app.include_router(legacy_documents_router.router)

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