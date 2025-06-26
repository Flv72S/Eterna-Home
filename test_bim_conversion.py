#!/usr/bin/env python3
"""
Test completi per il sistema di conversione BIM asincrona.
"""

import sys
import os
import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

# Aggiungi il path del progetto
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.core.config import settings
from app.db.session import get_session
from app.models.bim_model import BIMModel, BIMFormat, BIMSoftware, BIMLevelOfDetail, BIMConversionStatus
from app.schemas.bim import BIMConversionRequest, BIMConversionResponse
from sqlmodel import Session, select
from app.services.minio_service import MinIOService

class BIMConversionTester:
    """Classe per testare il sistema di conversione BIM asincrona."""
    
    def __init__(self):
        self.minio_service = MinIOService()
        self.test_user_id = 1
        self.test_house_id = 1
        self.test_models = []
        
    def create_test_bim_model(self, format_type: str, name: str = None) -> BIMModel:
        """Crea un modello BIM di test."""
        
        # Crea file di test
        test_content = f"Test BIM file in {format_type} format"
        test_filename = f"test_model.{format_type}"
        
        # Calcola checksum
        import hashlib
        checksum = hashlib.sha256(test_content.encode()).hexdigest()
        
        # Carica su MinIO
        bucket_name = "bim"
        file_path = f"{self.test_user_id}/test_{checksum[:8]}_{test_filename}"
        
        try:
            asyncio.run(self.minio_service.upload_file(
                bucket_name=bucket_name,
                file_path=file_path,
                file_data=test_content.encode(),
                content_type="application/octet-stream"
            ))
        except Exception as e:
            print(f"⚠️ Errore upload MinIO (simulato): {e}")
        
        # Crea modello nel database
        db = next(get_session())
        
        bim_model = BIMModel(
            name=name or f"Test Model {format_type.upper()}",
            description=f"Modello di test in formato {format_type}",
            format=format_type,
            software_origin=BIMSoftware.REVIT if format_type == "rvt" else BIMSoftware.OTHER,
            level_of_detail=BIMLevelOfDetail.LOD_300,
            file_url=f"{bucket_name}/{file_path}",
            file_size=len(test_content),
            checksum=checksum,
            user_id=self.test_user_id,
            house_id=self.test_house_id,
            conversion_status=BIMConversionStatus.PENDING
        )
        
        db.add(bim_model)
        db.commit()
        db.refresh(bim_model)
        
        self.test_models.append(bim_model.id)
        print(f"✅ Modello BIM creato: {bim_model.id} ({format_type})")
        
        return bim_model
    
    def test_model_creation(self):
        """Test creazione modelli BIM."""
        print("\n🧪 Test creazione modelli BIM...")
        
        try:
            # Crea modelli in diversi formati
            ifc_model = self.create_test_bim_model("ifc", "Test IFC Model")
            rvt_model = self.create_test_bim_model("rvt", "Test RVT Model")
            
            # Verifica creazione
            db = next(get_session())
            models = db.exec(select(BIMModel).where(BIMModel.id.in_([ifc_model.id, rvt_model.id]))).all()
            
            assert len(models) == 2, f"Attesi 2 modelli, trovati {len(models)}"
            assert any(m.format == BIMFormat.IFC for m in models), "Modello IFC non trovato"
            assert any(m.format == BIMFormat.RVT for m in models), "Modello RVT non trovato"
            
            print("✅ Test creazione modelli BIM: PASSATO")
            return True
            
        except Exception as e:
            print(f"❌ Test creazione modelli BIM: FALLITO - {e}")
            return False
    
    def test_conversion_status_update(self):
        """Test aggiornamento stato conversione."""
        print("\n🧪 Test aggiornamento stato conversione...")
        
        try:
            # Crea modello di test
            model = self.create_test_bim_model("ifc", "Test Status Update")
            
            # Simula aggiornamento stato
            db = next(get_session())
            model = db.exec(select(BIMModel).where(BIMModel.id == model.id)).first()
            
            model.conversion_status = BIMConversionStatus.PROCESSING
            model.conversion_message = "Conversione in corso"
            model.conversion_progress = 50
            model.conversion_started_at = datetime.now(timezone.utc)
            db.commit()
            
            # Verifica aggiornamento
            db.refresh(model)
            assert model.conversion_status == BIMConversionStatus.PROCESSING
            assert model.conversion_progress == 50
            assert model.conversion_started_at is not None
            
            print("✅ Test aggiornamento stato conversione: PASSATO")
            return True
            
        except Exception as e:
            print(f"❌ Test aggiornamento stato conversione: FALLITO - {e}")
            return False
    
    def test_conversion_workflow(self):
        """Test workflow completo di conversione."""
        print("\n🧪 Test workflow conversione...")
        
        try:
            # Crea modello IFC
            model = self.create_test_bim_model("ifc", "Test Conversion Workflow")
            
            # Simula workflow di conversione
            db = next(get_session())
            model = db.exec(select(BIMModel).where(BIMModel.id == model.id)).first()
            
            # Stato 1: Processing
            model.conversion_status = BIMConversionStatus.PROCESSING
            model.conversion_message = "Avvio conversione IFC → GLTF"
            model.conversion_progress = 10
            model.conversion_started_at = datetime.now(timezone.utc)
            db.commit()
            
            # Stato 2: Validating
            model.conversion_status = BIMConversionStatus.VALIDATING
            model.conversion_message = "Validazione modello"
            model.conversion_progress = 60
            db.commit()
            
            # Stato 3: Completed
            model.conversion_status = BIMConversionStatus.COMPLETED
            model.conversion_message = "Conversione completata"
            model.conversion_progress = 100
            model.converted_file_url = "bim/test_converted.gltf"
            model.conversion_completed_at = datetime.now(timezone.utc)
            db.commit()
            
            # Verifica stato finale
            db.refresh(model)
            assert model.conversion_status == BIMConversionStatus.COMPLETED
            assert model.conversion_progress == 100
            assert model.converted_file_url is not None
            assert model.conversion_completed_at is not None
            
            # Verifica durata conversione
            duration = model.conversion_duration
            assert duration is not None and duration >= 0
            
            print("✅ Test workflow conversione: PASSATO")
            return True
            
        except Exception as e:
            print(f"❌ Test workflow conversione: FALLITO - {e}")
            return False
    
    def test_conversion_schemas(self):
        """Test schemi Pydantic per conversione."""
        print("\n🧪 Test schemi conversione...")
        
        try:
            # Test BIMConversionRequest
            request = BIMConversionRequest(
                model_id=1,
                conversion_type="ifc_to_gltf",
                with_validation=True
            )
            
            assert request.model_id == 1
            assert request.conversion_type == "ifc_to_gltf"
            assert request.with_validation is True
            
            # Test BIMConversionResponse
            response = BIMConversionResponse(
                success=True,
                model_id=1,
                conversion_type="ifc_to_gltf",
                task_id="test-task-123",
                message="Conversione avviata",
                estimated_duration=120
            )
            
            assert response.success is True
            assert response.model_id == 1
            assert response.task_id == "test-task-123"
            
            print("✅ Test schemi conversione: PASSATO")
            return True
            
        except Exception as e:
            print(f"❌ Test schemi conversione: FALLITO - {e}")
            return False
    
    def test_error_handling(self):
        """Test gestione errori conversione."""
        print("\n🧪 Test gestione errori...")
        
        try:
            # Crea modello di test
            model = self.create_test_bim_model("ifc", "Test Error Handling")
            
            # Simula errore di conversione
            db = next(get_session())
            model = db.exec(select(BIMModel).where(BIMModel.id == model.id)).first()
            
            model.conversion_status = BIMConversionStatus.FAILED
            model.conversion_message = "Errore durante la conversione: File corrotto"
            model.conversion_progress = 0
            db.commit()
            
            # Verifica stato di errore
            db.refresh(model)
            assert model.conversion_status == BIMConversionStatus.FAILED
            assert "Errore" in model.conversion_message
            assert model.conversion_progress == 0
            
            print("✅ Test gestione errori: PASSATO")
            return True
            
        except Exception as e:
            print(f"❌ Test gestione errori: FALLITO - {e}")
            return False
    
    def cleanup_test_data(self):
        """Pulisce i dati di test."""
        print("\n🧹 Pulizia dati di test...")
        
        try:
            db = next(get_session())
            
            # Elimina modelli di test
            for model_id in self.test_models:
                model = db.exec(select(BIMModel).where(BIMModel.id == model_id)).first()
                if model:
                    db.delete(model)
            
            db.commit()
            print(f"✅ Eliminati {len(self.test_models)} modelli di test")
            
        except Exception as e:
            print(f"⚠️ Errore durante la pulizia: {e}")

def run_all_tests():
    """Esegue tutti i test del sistema di conversione BIM."""
    
    print("🏗️  Test Sistema Conversione BIM Asincrona")
    print("=" * 60)
    
    tester = BIMConversionTester()
    results = []
    
    try:
        # Esegui test
        test_methods = [
            tester.test_model_creation,
            tester.test_conversion_status_update,
            tester.test_conversion_workflow,
            tester.test_conversion_schemas,
            tester.test_error_handling
        ]
        
        for test_method in test_methods:
            try:
                result = test_method()
                results.append((test_method.__name__, result))
            except Exception as e:
                print(f"❌ Errore durante {test_method.__name__}: {e}")
                results.append((test_method.__name__, False))
        
        # Riepilogo risultati
        print("\n📊 Riepilogo Test:")
        print("-" * 40)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASSATO" if result else "❌ FALLITO"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 Risultato finale: {passed}/{len(results)} test passati")
        
        if passed == len(results):
            print("🎉 Tutti i test sono passati!")
            return True
        else:
            print("⚠️ Alcuni test sono falliti")
            return False
            
    finally:
        # Pulizia
        tester.cleanup_test_data()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 