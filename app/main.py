from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlmodel import Session
from typing import Optional
import uuid
from datetime import datetime

from app.routers import users, house, auth, node, document
from app.core.config import settings
from app.db.session import get_session
from app.services.minio_service import MinioService
from app.models.document import Document

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema di Gestione Centralizzata della Casa Digitale",
    version="1.0.0"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurazione rate limiting
limiter = Limiter(key_func=lambda: "global")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Dependency per il servizio MinIO
def get_minio_service():
    return MinioService()

# Inclusione dei router
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(house.router, prefix="/api/v1/houses", tags=["houses"])
app.include_router(node.router, prefix="/api/v1/nodes", tags=["nodes"])
app.include_router(document.router)  # Il prefisso è già incluso nel router

@app.get("/")
async def root():
    return {"message": "Benvenuto in Eterna Home API"}

@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    minio_service: MinioService = Depends(get_minio_service)
):
    # Verifica tipo file
    if not file.content_type.startswith(('image/', 'application/pdf')):
        raise HTTPException(status_code=400, detail="File type not supported")

    try:
        # Leggi il contenuto del file
        content = await file.read()
        
        # Genera un nome univoco per il file
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Se il file è troppo grande, genera un pre-signed URL
        if len(content) > settings.MAX_DIRECT_UPLOAD_SIZE:
            presigned_url = minio_service.get_presigned_put_url(
                unique_filename,
                file.content_type
            )
            return {
                "upload_url": presigned_url,
                "filename": unique_filename,
                "content_type": file.content_type,
                "document_id": None  # Non abbiamo ancora un document_id per i file grandi
            }
        
        # Upload diretto per file piccoli
        minio_path = minio_service.upload_file(
            content,
            unique_filename,
            file.content_type
        )
        
        # Salva i metadati nel DB
        document = Document(
            name=file.filename,
            type=file.content_type,
            size=len(content),
            path=minio_path,
            checksum=minio_service.get_file_checksum(content),
            house_id=None,  # TODO: Aggiungere house_id quando necessario
            author_id=None  # TODO: Aggiungere author_id quando necessario
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "document_id": document.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 