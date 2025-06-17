from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.users import router as users_router
from app.core.config import settings
from app.core.limiter import limiter

app = FastAPI(
    title="Eterna Home API",
    description="API for Eterna Home application",
    version="1.0.0",
)

# Aggiungi il limiter allo stato dell'app
app.state.limiter = limiter

# Gestore per le eccezioni di rate limit
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Troppi tentativi di login. Riprova più tardi."},
    )

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includi i router
app.include_router(auth_router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(users_router, prefix=settings.API_V1_STR + "/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to Eterna Home API"}