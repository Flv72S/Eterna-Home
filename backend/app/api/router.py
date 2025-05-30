from fastapi import APIRouter
from app.api.v1.api import api_router

router = APIRouter()

# Includi tutti i router delle API v1
router.include_router(api_router)

@router.get("/")
async def root():
    return {"message": "Benvenuto in Eterna Home API"}

