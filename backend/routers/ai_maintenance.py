from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import random
from datetime import datetime
import logging

from backend.db.session import get_db
from backend.schemas.ai_maintenance import AISampleInput
from backend.schemas.maintenance import MaintenanceTaskCreate, MaintenanceTaskResponse
from backend.models.maintenance import MaintenanceTask
from backend.utils.auth import get_current_user
from backend.models.user import User
from backend.services.ai_service import analyze_maintenance_data, generate_maintenance_report
from backend.utils.cache import get_cache, set_cache
from backend.config.settings import settings

router = APIRouter(
    prefix="/ai-maintenance",
    tags=["AI Maintenance"]
)

@router.post("/predict")
async def predict_maintenance(
    input_data: AISampleInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Simula una predizione di manutenzione basata sui dati del nodo.
    In una implementazione reale, qui verrebbe chiamato un modello AI.
    """
    try:
        # Simulazione di una predizione
        risk_levels = ["Low", "Medium", "High"]
        prediction = random.choice(risk_levels)
        confidence = round(random.uniform(0.7, 0.95), 2)
        
        return {
            "prediction": f"{prediction} risk of failure",
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
            "node_id": input_data.node_id,
            "additional_data": input_data.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/", response_model=MaintenanceTaskResponse)
def create_maintenance_task(
    task: MaintenanceTaskCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuovo task di manutenzione"""
    db_task = MaintenanceTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks/", response_model=List[MaintenanceTaskResponse])
def get_maintenance_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Recupera tutti i task di manutenzione"""
    tasks = db.query(MaintenanceTask).offset(skip).limit(limit).all()
    return tasks 