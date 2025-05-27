from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.db.session import get_db
from backend.schemas.bim import BIMCreate, BIM as BIMSchema
from backend.models.bim import BIM as BIMModel
from backend.models.user import User
from backend.utils.auth import get_current_user
from backend.config.cloud_config import settings
from backend.utils.minio import get_minio_client, upload_file_to_minio
from datetime import datetime
import io

router = APIRouter(
    prefix="/bim-files",
    tags=["BIM Files"]
)

@router.post("/upload", response_model=BIMSchema)
async def upload_bim_file(
    house_id: int = Form(...),
    node_id: Optional[int] = Form(None),
    version: str = Form(...),
    format: str = Form(...),
    description: Optional[str] = Form(None),
    bim_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        content = await bim_file.read()
        size_mb = round(len(content) / (1024 * 1024), 2)
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{bim_file.filename}"
        minio_client = get_minio_client()
        file_url = await upload_file_to_minio(
            minio_client,
            settings.MINIO_BUCKET_BIM,
            filename,
            content,
            bim_file.content_type or "application/octet-stream"
        )
        bim_obj = BIMModel(
            house_id=house_id,
            node_id=node_id,
            bim_file_url=file_url,
            version=version,
            format=format,
            size_mb=size_mb,
            description=description
        )
        db.add(bim_obj)
        db.commit()
        db.refresh(bim_obj)
        return bim_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{house_id}", response_model=List[BIMSchema])
async def list_bim_files(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bims = db.query(BIMModel).filter(BIMModel.house_id == house_id).all()
    return bims 