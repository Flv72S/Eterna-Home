from fastapi import APIRouter
from app.api.v1.endpoints import users, maintenance, auth

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(maintenance.router, prefix="/maintenance_records", tags=["maintenance"]) 