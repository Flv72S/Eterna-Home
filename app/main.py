from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from app.database import get_session
from sqlmodel import Session
import sqlalchemy

# from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.users import router as users_router
from app.routers.auth import router as auth_router_v2
from app.core.config import settings
from app.core.limiter import limiter
from app.routers.house import router as house_router
from app.routers.document import router as document_router

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
# app.include_router(auth_router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(users_router, prefix=settings.API_V1_STR + "/users", tags=["users"])
app.include_router(auth_router_v2, prefix=settings.API_V1_STR + "/auth", tags=["auth-v2"])
app.include_router(house_router, prefix="/api/v1/houses", tags=["houses"])
app.include_router(document_router, tags=["documents"])

@app.get("/")
async def root():
    return {"message": "Welcome to Eterna Home API"}

@app.get("/debug-db")
def debug_db(session: Session = Depends(get_session)):
    url = str(session.get_bind().url)
    insp = sqlalchemy.inspect(session.get_bind())
    tables = insp.get_table_names()
    with session.connection() as conn:
        current_schema = conn.execute(sqlalchemy.text("SELECT current_schema()")).scalar()
        search_path = conn.execute(sqlalchemy.text("SHOW search_path")).scalar()
    return JSONResponse({
        "db_url": url,
        "tables": tables,
        "current_schema": current_schema,
        "search_path": search_path
    })