from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.logging import logger

# Inizializzazione dell'applicazione FastAPI.
# Il titolo, la descrizione e la versione verranno visualizzati nella documentazione OpenAPI (Swagger UI).
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Eterna Home API"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Eterna Home API")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Eterna Home API")

# Il blocco if __name__ == "__main__": è utile per l'esecuzione diretta in sviluppo.
# In produzione, Gunicorn (o un altro WSGI server) si occuperà di avviare l'applicazione.
# if __name__ == "__main__":
#     import uvicorn
#     # reload=True abilita il ricaricamento automatico del codice ad ogni modifica,
#     # utile per lo sviluppo.
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
