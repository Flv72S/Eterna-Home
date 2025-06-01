from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import user, auth
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema di Gestione Centralizzata della Casa Digitale",
    version="1.0.0"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurazione rate limiting
limiter = Limiter(key_func=lambda: "global")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Inclusione dei router
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(auth.router, tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Benvenuto in Eterna Home API"} 