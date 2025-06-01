from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.user import router as user_router

app = FastAPI(
    title="Eterna Home API",
    description="API per la gestione degli utenti e delle loro attività",
    version="1.0.0"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare i domini consentiti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusione dei router
app.include_router(user_router)

@app.get("/")
def read_root():
    return {"message": "Benvenuto nell'API di Eterna Home"} 