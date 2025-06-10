from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.maintenance import MaintenanceRecord
from app.models.node import Node
from app.models.user import User
from .user import create_random_user

def create_random_maintenance_record(
    db: Session,
    *,
    node: Optional[Node] = None,
    user: Optional[User] = None,
    description: Optional[str] = None,
    maintenance_date: Optional[datetime] = None,
) -> MaintenanceRecord:
    if description is None:
        description = f"Test maintenance {datetime.utcnow()}"
    if maintenance_date is None:
        maintenance_date = datetime.utcnow()
    
    maintenance = MaintenanceRecord(
        node_id=node.id if node else None,
        user=user,
        description=description,
        date=maintenance_date,
        type="ROUTINE",
        status="COMPLETED",
        notes="Test notes"
    )
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    return maintenance 