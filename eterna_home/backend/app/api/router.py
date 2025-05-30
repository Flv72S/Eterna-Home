from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Benvenuto in Eterna Home API"}

