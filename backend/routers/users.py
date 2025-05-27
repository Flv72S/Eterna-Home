from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.models.user import User
from backend.utils.auth import get_current_user, role_required

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/admin-only")
async def admin_only(current_user: User = Depends(role_required(["admin"]))):
    return {"message": "This endpoint is only accessible to admins."} 