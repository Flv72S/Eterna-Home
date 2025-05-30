from fastapi import FastAPI
from api.router import router as api_router

# Inizializzazione dell'applicazione FastAPI.
# Il titolo, la descrizione e la versione verranno visualizzati nella documentazione OpenAPI (Swagger UI).
app = FastAPI(
    title="Eterna Home Backend",
    description="API per la gestione centralizzata della casa digitale.",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api")

@app.get("/", tags=["Root"])
async def read_root():
    """
    Endpoint di benvenuto per testare l'avvio dell'applicazione.
    Restituisce un semplice messaggio "Hello World".
    """
    return {"message": "Hello World"}

# Il blocco if __name__ == "__main__": è utile per l'esecuzione diretta in sviluppo.
# In produzione, Gunicorn (o un altro WSGI server) si occuperà di avviare l'applicazione.
# if __name__ == "__main__":
#     import uvicorn
#     # reload=True abilita il ricaricamento automatico del codice ad ogni modifica,
#     # utile per lo sviluppo.
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
