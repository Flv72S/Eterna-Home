import uuid
import logging
import traceback
import sys
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List
from minio.error import S3Error
import io
import os
from datetime import datetime
import shutil
from pathlib import Path

from backend.db.session import get_db
from backend.utils.auth import get_current_user
from backend.config.settings import settings
from backend.utils.minio import get_minio_client, upload_file_to_minio
from backend.models.legacy_documents import LegacyDocument
from backend.models.user import User
from backend.models.node import Node
from backend.models.house import House
from backend.schemas.legacy_documents import LegacyDocumentCreate, LegacyDocument as LegacyDocumentSchema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/legacy-documents", tags=["Legacy Documents"])

@router.post("/", response_model=LegacyDocumentSchema)
async def create_legacy_document(
    house_id: int = Form(...),
    node_id: int = Form(...),
    type: str = Form(...),
    version: str = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.debug(f"Ricevuta richiesta di caricamento documento per house_id={house_id}, node_id={node_id}")
        
        # Verifica che il nodo esista e appartenga a una casa dell'utente
        logger.debug(f"Verifica nodo {node_id} per utente {current_user.id}")
        node = db.query(Node).join(House).filter(
            Node.id == node_id,
            House.owner_id == current_user.id
        ).first()
        if not node:
            logger.warning(f"Nodo {node_id} non trovato o non appartiene all'utente {current_user.id}")
            raise HTTPException(status_code=404, detail="Node not found")

        # Inizializza il client MinIO
        logger.debug("Inizializzazione client MinIO...")
        minio_client = get_minio_client()
        
        # Genera un nome unico per il file
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        logger.debug(f"Nome file generato: {unique_filename}")
        
        # Leggi il contenuto del file
        logger.debug(f"Lettura contenuto file {file.filename}...")
        file_content = await file.read()
        logger.debug(f"File letto, dimensione: {len(file_content)} bytes")
        
        # Carica il file su MinIO
        logger.debug(f"Caricamento file su MinIO (bucket: {settings.MINIO_BUCKET_LEGACY})...")
        file_url = await upload_file_to_minio(
            minio_client,
            settings.MINIO_BUCKET_LEGACY,
            unique_filename,
            file_content,
            file.content_type
        )
        
        # Crea il nuovo documento nel database
        logger.debug("Creazione documento nel database...")
        db_document = LegacyDocument(
            house_id=house_id,
            node_id=node_id,
            type=type,
            version=version,
            file_url=file_url
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        logger.info(f"Documento creato con successo. ID: {db_document.id}")
        return db_document
        
    except S3Error as e:
        error_msg = f"Errore S3 durante il caricamento del documento: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=f"Errore durante il caricamento del file: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_msg = f"Errore durante il caricamento del documento:\nTipo: {exc_type.__name__}\nMessaggio: {str(e)}\nTraceback:\n{''.join(traceback.format_tb(exc_traceback))}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{node_id}", response_model=List[LegacyDocumentSchema])
async def get_legacy_documents(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verifica che il nodo esista e appartenga a una casa dell'utente
        node = db.query(Node).join(House).filter(
            Node.id == node_id,
            House.owner_id == current_user.id
        ).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        documents = db.query(LegacyDocument).filter(LegacyDocument.node_id == node_id).all()
        return documents
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Errore durante il recupero dei documenti: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=str(e)) 