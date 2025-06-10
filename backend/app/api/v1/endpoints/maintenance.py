from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, status, Query
from sqlmodel import Session, select, and_, or_
from sqlalchemy import func
import pandas as pd
from datetime import datetime
from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.node import Node
from app.db.session import get_db
from app.core.logging import logger
from pydantic import BaseModel
import csv
from io import StringIO
from fastapi.responses import StreamingResponse
from app.schemas.maintenance import MaintenanceExportParams
from dateutil.parser import parse as parse_date
import json
from app.api.deps import get_current_active_superuser
from app.models.user import User

router = APIRouter()

def default_json(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

@router.get("/", response_model=List[MaintenanceRecord])
def read_maintenance_records(db: Session = Depends(get_db)):
    """Lista tutti i record di manutenzione."""
    return db.exec(select(MaintenanceRecord)).all()

@router.get("/search", response_model=List[MaintenanceRecord])
def search_maintenance_records(
    node_id: Optional[int] = Query(None, description="Filter by node ID"),
    status: Optional[str] = Query(None, description="Filter by maintenance status"),
    created_from: Optional[str] = Query(None, description="Filter by creation date from (ISO format)"),
    created_to: Optional[str] = Query(None, description="Filter by creation date to (ISO format)"),
    updated_from: Optional[str] = Query(None, description="Filter by update date from (ISO format)"),
    updated_to: Optional[str] = Query(None, description="Filter by update date to (ISO format)"),
    notes_query: Optional[str] = Query(None, description="Search in notes (case-insensitive)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Ricerca avanzata di record di manutenzione con supporto a filtri e paginazione.
    """
    query = select(MaintenanceRecord)
    filters = []
    if node_id is not None:
        filters.append(MaintenanceRecord.node_id == node_id)
    if status is not None:
        try:
            # Converti lo status in minuscolo per corrispondere ai valori dell'enum
            status_enum = MaintenanceStatus(status.lower())
            filters.append(MaintenanceRecord.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status value. Must be one of: {', '.join(s.value for s in MaintenanceStatus)}"
            )
    if created_from is not None:
        try:
            created_from_dt = datetime.fromisoformat(created_from)
            filters.append(MaintenanceRecord.date >= created_from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid created_from date format. Use ISO format.")
    if created_to is not None:
        try:
            created_to_dt = datetime.fromisoformat(created_to)
            filters.append(MaintenanceRecord.date <= created_to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid created_to date format. Use ISO format.")
    if updated_from is not None:
        try:
            updated_from_dt = datetime.fromisoformat(updated_from)
            filters.append(MaintenanceRecord.updated_at >= updated_from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid updated_from date format. Use ISO format.")
    if updated_to is not None:
        try:
            updated_to_dt = datetime.fromisoformat(updated_to)
            filters.append(MaintenanceRecord.updated_at <= updated_to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid updated_to date format. Use ISO format.")
    if notes_query is not None:
        filters.append(MaintenanceRecord.notes.ilike(f"%{notes_query}%"))
    if filters:
        query = query.where(and_(*filters))
    query = query.order_by(MaintenanceRecord.created_at.desc())
    query = query.offset(skip).limit(limit)
    return db.execute(query).scalars().all()

@router.get("/export")
def export_maintenance_records(
    format: str = Query("csv", description="Formato di export: csv o json"),
    status: Optional[str] = Query(None, description="Stato manutenzione"),
    type: Optional[str] = Query(None, description="Tipo manutenzione"),
    node_id: Optional[int] = Query(None, description="ID nodo"),
    start_date: Optional[str] = Query(None, description="Data inizio intervallo"),
    end_date: Optional[str] = Query(None, description="Data fine intervallo"),
    search: Optional[str] = Query(None, description="Cerca nella descrizione"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Esporta i record di manutenzione in formato CSV o JSON.
    Supporta filtri per stato, tipo, nodo e intervallo di date.
    """
    # Valida il formato
    if format.lower() not in ["csv", "json"]:
        raise HTTPException(status_code=422, detail="Format must be either 'csv' or 'json'")

    query = select(MaintenanceRecord)
    filters = []

    if status is not None:
        try:
            status_enum = MaintenanceStatus(status.lower())
            filters.append(MaintenanceRecord.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status value. Must be one of: {', '.join(s.value for s in MaintenanceStatus)}"
            )

    if type is not None:
        filters.append(MaintenanceRecord.type == type)

    if node_id is not None:
        filters.append(MaintenanceRecord.node_id == node_id)

    if start_date is not None:
        try:
            start_dt = parse_date(start_date)
            filters.append(MaintenanceRecord.date >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date is not None:
        try:
            end_dt = parse_date(end_date)
            filters.append(MaintenanceRecord.date <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    if start_date and end_date:
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
        if end_dt < start_dt:
            raise HTTPException(status_code=422, detail="end_date must be after start_date")

    if search is not None:
        filters.append(MaintenanceRecord.description.ilike(f"%{search}%"))

    if filters:
        query = query.where(and_(*filters))

    records = db.execute(query).scalars().all()

    if format.lower() == "json":
        return StreamingResponse(
            iter([json.dumps([record.model_dump() for record in records], default=default_json)]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=maintenance_records.json"}
        )
    else:
        output = StringIO()
        fieldnames = ["id", "node_id", "date", "type", "description", "status", "notes", "created_at", "updated_at"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            data = record.model_dump()
            writer.writerow(data)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=maintenance_records.csv"}
        )

@router.get("/{id}", response_model=MaintenanceRecord)
def read_maintenance_record(id: int, db: Session = Depends(get_db)):
    """Ottiene il dettaglio di un record di manutenzione."""
    record = db.get(MaintenanceRecord, id)
    if not record:
        raise HTTPException(status_code=404, detail="Record non trovato")
    return record

@router.post("/", response_model=MaintenanceRecord)
def create_maintenance_record(record: MaintenanceRecord, db: Session = Depends(get_db)):
    """Crea un nuovo record di manutenzione."""
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.put("/{id}", response_model=MaintenanceRecord)
def update_maintenance_record(id: int, record: MaintenanceRecord, db: Session = Depends(get_db)):
    """Aggiorna un record di manutenzione esistente."""
    db_record = db.get(MaintenanceRecord, id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Record non trovato")
    for key, value in record.model_dump(exclude_unset=True).items():
        setattr(db_record, key, value)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.delete("/{id}", response_model=MaintenanceRecord)
def delete_maintenance_record(id: int, db: Session = Depends(get_db)):
    """Elimina un record di manutenzione."""
    record = db.get(MaintenanceRecord, id)
    if not record:
        raise HTTPException(status_code=404, detail="Record non trovato")
    db.delete(record)
    db.commit()
    return record

async def process_import_file(file_content: bytes, file_type: str, db: Session):
    """Process the imported file and create maintenance records."""
    try:
        if file_type == "csv":
            df = pd.read_csv(pd.io.common.BytesIO(file_content))
        else:  # json
            df = pd.read_json(pd.io.common.BytesIO(file_content))

        # Convert column names to lowercase
        df.columns = df.columns.str.lower()
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Validate node_id exists
                node = db.get(Node, row['node_id'])
                if not node:
                    logger.warning(f"Node {row['node_id']} not found, skipping record")
                    continue

                # Create maintenance record
                record = MaintenanceRecord(
                    node_id=row['node_id'],
                    date=pd.to_datetime(row['date']).to_pydatetime() if 'date' in row else datetime.utcnow(),
                    type=row.get('type', 'Unknown'),
                    description=row.get('description', ''),
                    status=MaintenanceStatus(row['status']) if 'status' in row else MaintenanceStatus.PENDING,
                    notes=row.get('notes', '')
                )
                db.add(record)
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                continue

        db.commit()
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        db.rollback()

@router.post("/import-historical-data", status_code=status.HTTP_202_ACCEPTED)
async def import_historical_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import historical maintenance records from CSV or JSON file.
    The import process runs in background.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Determine file type
    file_type = file.filename.split('.')[-1].lower()
    if file_type not in ['csv', 'json']:
        raise HTTPException(status_code=400, detail="File must be CSV or JSON")

    # Read file content
    content = await file.read()
    
    # Count rows (approximate)
    if file_type == "csv":
        row_count = len(pd.read_csv(pd.io.common.BytesIO(content)))
    else:
        row_count = len(pd.read_json(pd.io.common.BytesIO(content)))

    # Add background task
    background_tasks.add_task(process_import_file, content, file_type, db)

    return {
        "message": "Import started",
        "file_name": file.filename,
        "rows_accepted": row_count
    } 