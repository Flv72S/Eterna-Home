from fastapi import APIRouter, Depends
from utils.auth import get_current_user

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])
 
@router.get("/test-maintenance")
async def test_maintenance_protected(current_user: dict = Depends(get_current_user)):
    return {"message": f"Maintenance data for user {current_user['email']} - router works!"} 