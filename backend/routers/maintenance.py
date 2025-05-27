from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.maintenance import MaintenanceTaskCreate, MaintenanceTask
from backend.db.session import get_db
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])
 
@router.get("/test-maintenance")
async def test_maintenance_protected(current_user: User = Depends(get_current_user)):
    return {"message": f"Maintenance data for user {current_user.email} - router works!"} 