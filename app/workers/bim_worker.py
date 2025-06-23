import os
import tempfile
import logging
from typing import Dict, Any, Optional
from celery import current_task
from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.minio_service import MinioService
from app.db.session import get_db
from app.models.bim_model import BIMModel, BIMFormat
from sqlmodel import Session, select
import hashlib
import json
from datetime import datetime, timezone

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BIMConversionWorker:
    """Worker per la conversione di modelli BIM."""
    
    def __init__(self):
        self.minio_service = MinioService()
        self.temp_dir = tempfile.mkdtemp()
    
    def update_model_status(self, model_id: int, status: str, message: str = None, progress: int = 0):
        """Aggiorna lo stato del modello BIM nel database."""
        try:
            db = next(get_db())
            model = db.exec(select(BIMModel).where(BIMModel.id == model_id)).first()
            if model:
                model.conversion_status = status
                model.conversion_message = message
                model.conversion_progress = progress
                model.updated_at = datetime.now(timezone.utc)
                db.commit()
                logger.info(f"Modello {model_id} aggiornato: {status} - {message}")
        except Exception as e:
            logger.error(f"Errore aggiornamento stato modello {model_id}: {e}")
    
    def download_file(self, file_url: str) -> str:
        """Scarica il file da MinIO."""
        try:
            bucket_name, file_path = file_url.split("/", 1)
            local_path = os.path.join(self.temp_dir, os.path.basename(file_path))
            
            # Scarica file da MinIO
            file_data = self.minio_service.download_file(bucket_name, file_path)
            with open(local_path, "wb") as f:
                f.write(file_data)
            
            logger.info(f"File scaricato: {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Errore download file {file_url}: {e}")
            raise
    
    async def upload_converted_file(self, local_path: str, original_url: str, format_suffix: str) -> str:
        """Carica un file convertito su MinIO."""
        try:
            # Estrai bucket e path dal URL originale
            bucket_name, file_path = original_url.split("/", 1)
            
            # Crea nuovo path per il file convertito
            base_name = file_path.rsplit(".", 1)[0]
            new_file_path = f"{base_name}_converted.{format_suffix}"
            
            with open(local_path, "rb") as f:
                file_data = f.read()
            
            await self.minio_service.upload_file(
                bucket_name=bucket_name,
                file_path=new_file_path,
                file_data=file_data,
                content_type="application/octet-stream"
            )
            
            logger.info(f"File convertito caricato: {new_file_path}")
            return f"{bucket_name}/{new_file_path}"
        except Exception as e:
            logger.error(f"Errore upload file convertito: {e}")
            raise

@celery_app.task(bind=True, name="convert_ifc_to_gltf")
async def convert_ifc_to_gltf(self, model_id: int) -> Dict[str, Any]:
    """Converte un file IFC in formato GLTF per visualizzazione web."""
    worker = BIMConversionWorker()
    
    try:
        # Aggiorna stato iniziale
        worker.update_model_status(model_id, "processing", "Avvio conversione IFC → GLTF", 10)
        
        # Ottieni modello dal database
        db = next(get_db())
        model = db.exec(select(BIMModel).where(BIMModel.id == model_id)).first()
        if not model:
            raise Exception(f"Modello BIM {model_id} non trovato")
        
        if model.format != BIMFormat.IFC:
            raise Exception(f"Formato non supportato per conversione GLTF: {model.format}")
        
        # Scarica file
        worker.update_model_status(model_id, "processing", "Download file IFC", 20)
        local_path = worker.download_file(model.file_url)
        
        # Simula conversione IFC → GLTF (in produzione usare IfcOpenShell)
        worker.update_model_status(model_id, "processing", "Conversione in corso", 50)
        
        # Simula elaborazione
        import time
        time.sleep(5)  # Simula tempo di conversione
        
        # Crea file GLTF simulato
        gltf_path = local_path.replace(".ifc", ".gltf")
        with open(gltf_path, "w") as f:
            f.write('{"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": []}')
        
        # Carica file convertito
        worker.update_model_status(model_id, "processing", "Upload file convertito", 80)
        converted_url = await worker.upload_converted_file(gltf_path, model.file_url, "gltf")
        
        # Aggiorna modello con URL del file convertito
        model.converted_file_url = converted_url
        model.conversion_status = "completed"
        model.conversion_message = "Conversione completata con successo"
        model.conversion_progress = 100
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        # Pulisci file temporanei
        os.remove(local_path)
        os.remove(gltf_path)
        
        logger.info(f"Conversione IFC → GLTF completata per modello {model_id}")
        
        return {
            "success": True,
            "model_id": model_id,
            "converted_url": converted_url,
            "message": "Conversione completata con successo"
        }
        
    except Exception as e:
        worker.update_model_status(model_id, "failed", f"Errore conversione: {str(e)}", 0)
        logger.error(f"Errore conversione IFC → GLTF per modello {model_id}: {e}")
        raise

@celery_app.task(bind=True, name="convert_rvt_to_ifc")
async def convert_rvt_to_ifc(self, model_id: int) -> Dict[str, Any]:
    """Converte un file RVT (Revit) in formato IFC."""
    worker = BIMConversionWorker()
    
    try:
        # Aggiorna stato iniziale
        worker.update_model_status(model_id, "processing", "Avvio conversione RVT → IFC", 10)
        
        # Ottieni modello dal database
        db = next(get_db())
        model = db.exec(select(BIMModel).where(BIMModel.id == model_id)).first()
        if not model:
            raise Exception(f"Modello BIM {model_id} non trovato")
        
        if model.format != BIMFormat.RVT:
            raise Exception(f"Formato non supportato per conversione IFC: {model.format}")
        
        # Scarica file
        worker.update_model_status(model_id, "processing", "Download file RVT", 20)
        local_path = worker.download_file(model.file_url)
        
        # Simula conversione RVT → IFC (in produzione usare Revit API o Forge)
        worker.update_model_status(model_id, "processing", "Conversione in corso", 50)
        
        # Simula elaborazione
        import time
        time.sleep(10)  # Simula tempo di conversione più lungo per RVT
        
        # Crea file IFC simulato
        ifc_path = local_path.replace(".rvt", ".ifc")
        with open(ifc_path, "w") as f:
            f.write("# IFC file converted from RVT\nISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;")
        
        # Carica file convertito
        worker.update_model_status(model_id, "processing", "Upload file convertito", 80)
        converted_url = await worker.upload_converted_file(ifc_path, model.file_url, "ifc")
        
        # Aggiorna modello con URL del file convertito
        model.converted_file_url = converted_url
        model.conversion_status = "completed"
        model.conversion_message = "Conversione RVT → IFC completata"
        model.conversion_progress = 100
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        # Pulisci file temporanei
        os.remove(local_path)
        os.remove(ifc_path)
        
        logger.info(f"Conversione RVT → IFC completata per modello {model_id}")
        
        return {
            "success": True,
            "model_id": model_id,
            "converted_url": converted_url,
            "message": "Conversione RVT → IFC completata"
        }
        
    except Exception as e:
        worker.update_model_status(model_id, "failed", f"Errore conversione: {str(e)}", 0)
        logger.error(f"Errore conversione RVT → IFC per modello {model_id}: {e}")
        raise

@celery_app.task(bind=True, name="validate_bim_model")
async def validate_bim_model(self, model_id: int) -> Dict[str, Any]:
    """Valida un modello BIM e genera report di validazione."""
    worker = BIMConversionWorker()
    
    try:
        # Aggiorna stato iniziale
        worker.update_model_status(model_id, "validating", "Avvio validazione modello", 10)
        
        # Ottieni modello dal database
        db = next(get_db())
        model = db.exec(select(BIMModel).where(BIMModel.id == model_id)).first()
        if not model:
            raise Exception(f"Modello BIM {model_id} non trovato")
        
        # Scarica file
        worker.update_model_status(model_id, "validating", "Download file per validazione", 30)
        local_path = worker.download_file(model.file_url)
        
        # Simula validazione
        worker.update_model_status(model_id, "validating", "Validazione in corso", 60)
        
        import time
        time.sleep(3)  # Simula tempo di validazione
        
        # Genera report di validazione simulato
        validation_report = {
            "model_id": model_id,
            "validation_date": datetime.now(timezone.utc).isoformat(),
            "file_size": model.file_size,
            "format": model.format,
            "checksum_valid": True,
            "structure_valid": True,
            "elements_count": 1250,
            "warnings": [
                "Elemento WALL_001 ha geometria non valida",
                "Materiale MAT_002 non definito"
            ],
            "errors": [],
            "compliance_level": "LOD_300"
        }
        
        # Salva report su MinIO
        report_path = f"validation_reports/{model_id}_validation.json"
        await worker.minio_service.upload_file(
            bucket_name="bim",
            file_path=report_path,
            file_data=json.dumps(validation_report, indent=2).encode(),
            content_type="application/json"
        )
        
        # Aggiorna modello
        model.validation_report_url = f"bim/{report_path}"
        model.conversion_status = "validated"
        model.conversion_message = "Validazione completata"
        model.conversion_progress = 100
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        # Pulisci file temporanei
        os.remove(local_path)
        
        logger.info(f"Validazione completata per modello {model_id}")
        
        return {
            "success": True,
            "model_id": model_id,
            "validation_report": validation_report,
            "message": "Validazione completata con successo"
        }
        
    except Exception as e:
        worker.update_model_status(model_id, "failed", f"Errore validazione: {str(e)}", 0)
        logger.error(f"Errore validazione per modello {model_id}: {e}")
        raise 