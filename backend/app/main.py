import os
import sys
print(f"[DEBUG] main.py path: {__file__}")
print(f"[DEBUG] Current working directory: {os.getcwd()}")
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.routers.roles import router as roles_router
from app.db.session import get_session
from tests.test_session import get_test_session

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API per la gestione delle prenotazioni di case",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"]
)
app.include_router(
    users_router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["users"]
)
app.include_router(
    roles_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["roles"]
)

@app.on_event("startup")
def print_routes():
    print("\n[ROUTES REGISTRATE]")
    for route in app.routes:
        print(f"{route.path} -> {route.name} [{getattr(route, 'methods', None)}]")
    print("[FINE ROUTES]\n")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Benvenuto nell'API di Eterna Home"}