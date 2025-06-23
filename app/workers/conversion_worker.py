"""
Worker per la conversione asincrona di modelli BIM
"""
try:
    from celery import current_task, chain, group
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Mock per quando Celery non è disponibile
    def current_task():
        return None
    def chain(*args):
        return None
    def group(*args):
        return None

from datetime import datetime, timezone
from typing import Dict, Any, List
import logging
from sqlmodel import select

try:
    from app.core.celery_app import celery_app
    CELERY_APP_AVAILABLE = True
except ImportError:
    CELERY_APP_AVAILABLE = False
    # Mock per quando Celery non è disponibile
    class MockCeleryApp:
        def task(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    celery_app = MockCeleryApp()

from app.database import get_db
from app.models.bim_model import BIMModel, BIMFormat

try:
    from app.workers.bim_worker import convert_ifc_to_gltf, convert_rvt_to_ifc, validate_bim_model
    BIM_WORKER_AVAILABLE = True
except ImportError:
    BIM_WORKER_AVAILABLE = False
    # Mock per quando bim_worker non è disponibile
    def convert_ifc_to_gltf(*args, **kwargs):
        return None
    def convert_rvt_to_ifc(*args, **kwargs):
        return None
    def validate_bim_model(*args, **kwargs):
        return None

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verifica che Celery sia disponibile
if not CELERY_AVAILABLE or not CELERY_APP_AVAILABLE:
    logger.warning("Celery non disponibile - funzionalità di conversione BIM asincrona disabilitata")

@celery_app.task(bind=True, name="process_bim_model")
def process_bim_model(self, model_id: int, conversion_type: str = "auto") -> Dict[str, Any]:
    """Processa un modello BIM con conversione automatica basata sul formato."""
    try:
        # Ottieni modello dal database
        db = next(get_db())
        model = db.exec(select(BIMModel).where(BIMModel.id == model_id)).first()
        if not model:
            raise Exception(f"Modello BIM {model_id} non trovato")
        
        logger.info(f"Avvio processamento modello {model_id} ({model.format})")
        
        # Determina tipo di conversione basato sul formato
        if conversion_type == "auto":
            if model.format == BIMFormat.IFC:
                conversion_type = "ifc_to_gltf"
            elif model.format == BIMFormat.RVT:
                conversion_type = "rvt_to_ifc"
            else:
                conversion_type = "validate_only"
        
        # Esegui conversione appropriata
        if conversion_type == "ifc_to_gltf":
            result = convert_ifc_to_gltf.delay(model_id)
            return {
                "success": True,
                "model_id": model_id,
                "conversion_type": conversion_type,
                "task_id": result.id,
                "message": "Conversione IFC → GLTF avviata"
            }
            
        elif conversion_type == "rvt_to_ifc":
            result = convert_rvt_to_ifc.delay(model_id)
            return {
                "success": True,
                "model_id": model_id,
                "conversion_type": conversion_type,
                "task_id": result.id,
                "message": "Conversione RVT → IFC avviata"
            }
            
        elif conversion_type == "validate_only":
            result = validate_bim_model.delay(model_id)
            return {
                "success": True,
                "model_id": model_id,
                "conversion_type": conversion_type,
                "task_id": result.id,
                "message": "Validazione modello avviata"
            }
            
        else:
            raise Exception(f"Tipo di conversione non supportato: {conversion_type}")
            
    except Exception as e:
        logger.error(f"Errore processamento modello {model_id}: {e}")
        raise

@celery_app.task(bind=True, name="batch_convert_models")
def batch_convert_models(self, model_ids: List[int], conversion_type: str = "auto") -> Dict[str, Any]:
    """Converte un batch di modelli BIM in parallelo."""
    try:
        logger.info(f"Avvio conversione batch per {len(model_ids)} modelli")
        
        # Crea task per ogni modello
        tasks = []
        for model_id in model_ids:
            task = process_bim_model.delay(model_id, conversion_type)
            tasks.append(task)
        
        # Attendi completamento di tutti i task
        results = []
        for task in tasks:
            try:
                result = task.get(timeout=1800)  # 30 minuti timeout
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e)
                })
        
        # Calcola statistiche
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        
        logger.info(f"Conversione batch completata: {successful} successi, {failed} fallimenti")
        
        return {
            "success": True,
            "total_models": len(model_ids),
            "successful": successful,
            "failed": failed,
            "results": results,
            "message": f"Batch conversion completed: {successful}/{len(model_ids)} successful"
        }
        
    except Exception as e:
        logger.error(f"Errore conversione batch: {e}")
        raise

@celery_app.task(bind=True, name="convert_with_validation")
def convert_with_validation(self, model_id: int, conversion_type: str = "auto") -> Dict[str, Any]:
    """Converte un modello BIM con validazione pre e post conversione."""
    try:
        logger.info(f"Avvio conversione con validazione per modello {model_id}")
        
        # Crea catena di task: validazione → conversione → validazione finale
        if conversion_type == "ifc_to_gltf":
            workflow = chain(
                validate_bim_model.s(model_id),
                convert_ifc_to_gltf.s(model_id),
                validate_bim_model.s(model_id)
            )
        elif conversion_type == "rvt_to_ifc":
            workflow = chain(
                validate_bim_model.s(model_id),
                convert_rvt_to_ifc.s(model_id),
                validate_bim_model.s(model_id)
            )
        else:
            workflow = validate_bim_model.s(model_id)
        
        result = workflow.delay()
        
        return {
            "success": True,
            "model_id": model_id,
            "conversion_type": conversion_type,
            "task_id": result.id,
            "message": "Conversione con validazione avviata"
        }
        
    except Exception as e:
        logger.error(f"Errore conversione con validazione per modello {model_id}: {e}")
        raise

@celery_app.task(bind=True, name="cleanup_conversion_files")
async def cleanup_conversion_files(self, model_id: int) -> Dict[str, Any]:
    """Pulisce i file temporanei di conversione per un modello."""
    try:
        from app.services.minio_service import MinioService
        import os
        
        minio_service = MinioService()
        
        # Ottieni modello dal database
        db = next(get_db())
        model = db.exec(select(BIMModel).where(BIMModel.id == model_id)).first()
        if not model:
            raise Exception(f"Modello BIM {model_id} non trovato")
        
        # Lista file da pulire
        files_to_cleanup = []
        
        # Aggiungi file convertiti se esistono
        if hasattr(model, 'converted_file_url') and model.converted_file_url:
            files_to_cleanup.append(model.converted_file_url)
        
        # Aggiungi report di validazione se esistono
        if hasattr(model, 'validation_report_url') and model.validation_report_url:
            files_to_cleanup.append(model.validation_report_url)
        
        # Elimina file da MinIO
        deleted_count = 0
        for file_url in files_to_cleanup:
            try:
                bucket_name, file_path = file_url.split("/", 1)
                await minio_service.delete_file(bucket_name, file_path)
                deleted_count += 1
                logger.info(f"File eliminato: {file_url}")
            except Exception as e:
                logger.warning(f"Impossibile eliminare file {file_url}: {e}")
        
        # Aggiorna modello
        model.converted_file_url = None
        model.validation_report_url = None
        model.conversion_status = "cleaned"
        model.conversion_message = f"Pulizia completata: {deleted_count} file eliminati"
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"Pulizia completata per modello {model_id}: {deleted_count} file eliminati")
        
        return {
            "success": True,
            "model_id": model_id,
            "deleted_files": deleted_count,
            "message": f"Cleanup completed: {deleted_count} files deleted"
        }
        
    except Exception as e:
        logger.error(f"Errore pulizia file per modello {model_id}: {e}")
        raise

@celery_app.task(bind=True, name="get_conversion_status")
def get_conversion_status(self, model_id: int) -> Dict[str, Any]:
    """Ottiene lo stato di conversione di un modello BIM."""
    try:
        # Ottieni modello dal database
        db = next(get_db())
        model = db.exec(select(BIMModel).where(BIMModel.id == model_id)).first()
        if not model:
            raise Exception(f"Modello BIM {model_id} non trovato")
        
        return {
            "success": True,
            "model_id": model_id,
            "status": getattr(model, 'conversion_status', 'not_started'),
            "message": getattr(model, 'conversion_message', ''),
            "progress": getattr(model, 'conversion_progress', 0),
            "converted_file_url": getattr(model, 'converted_file_url', None),
            "validation_report_url": getattr(model, 'validation_report_url', None),
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"Errore ottenimento stato conversione per modello {model_id}: {e}")
        raise 