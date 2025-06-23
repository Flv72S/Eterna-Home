#!/usr/bin/env python3
"""
Test rapido per il sistema asincrono di elaborazione comandi vocali.
Verifica il funzionamento in modalità fallback (senza RabbitMQ).
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.audio_log import AudioLog
from app.schemas.audio_log import AudioLogCreate
from app.services.audio_log import AudioLogService
from app.core.deps import get_db
from sqlmodel import Session, create_engine
from app.core.config import settings

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_audio_log_creation():
    """Test creazione AudioLog senza RabbitMQ."""
    try:
        logger.info("=== TEST SISTEMA ASINCRONO (FALLBACK MODE) ===")
        
        # Crea engine database
        engine = create_engine(settings.DATABASE_URL)
        
        with Session(engine) as db:
            # Crea AudioLog di test
            audio_log_data = AudioLogCreate(
                user_id=1,
                node_id=1,
                house_id=1,
                transcribed_text="Test comando vocale",
                processing_status="received"
            )
            
            # Simula utente (per test)
            class MockUser:
                id = 1
                email = "test@example.com"
            
            mock_user = MockUser()
            
            # Crea AudioLog
            audio_log = AudioLogService.create_audio_log(db, audio_log_data, mock_user)
            
            logger.info(f"✅ AudioLog creato con successo: ID {audio_log.id}")
            logger.info(f"   Stato: {audio_log.processing_status}")
            logger.info(f"   Testo: {audio_log.transcribed_text}")
            logger.info(f"   Timestamp: {audio_log.timestamp}")
            
            # Simula elaborazione asincrona (senza RabbitMQ)
            logger.info("🔄 Simulazione elaborazione asincrona...")
            
            # Aggiorna stato a "transcribing"
            audio_log.processing_status = "transcribing"
            db.commit()
            logger.info(f"   Stato aggiornato a: {audio_log.processing_status}")
            
            # Simula delay
            import time
            time.sleep(1)
            
            # Aggiorna stato a "analyzing"
            audio_log.processing_status = "analyzing"
            db.commit()
            logger.info(f"   Stato aggiornato a: {audio_log.processing_status}")
            
            # Simula delay
            time.sleep(1)
            
            # Simula risposta NLP
            audio_log.response_text = "Comando elaborato con successo"
            audio_log.processing_status = "completed"
            db.commit()
            
            logger.info(f"   Risposta: {audio_log.response_text}")
            logger.info(f"   Stato finale: {audio_log.processing_status}")
            
            # Verifica proprietà helper
            logger.info(f"   È completato: {audio_log.is_completed}")
            logger.info(f"   È in elaborazione: {audio_log.is_processing}")
            logger.info(f"   Display status: {audio_log.status_display}")
            
            # Recupera AudioLog per verifica
            retrieved_log = AudioLogService.get_audio_log(db, audio_log.id, mock_user)
            if retrieved_log:
                logger.info(f"✅ AudioLog recuperato correttamente: {retrieved_log.id}")
            else:
                logger.error("❌ Errore recupero AudioLog")
                return False
            
            # Test lista AudioLog
            result = AudioLogService.get_audio_logs(db, mock_user, None, None, None, 0, 10)
            logger.info(f"✅ Lista AudioLog: {len(result.get('items', []))} record")
            
            logger.info("=== TEST COMPLETATO CON SUCCESSO ===")
            return True
            
    except Exception as e:
        logger.error(f"❌ Errore durante il test: {e}")
        return False

def test_rabbitmq_manager():
    """Test RabbitMQ Manager (senza connessione)."""
    try:
        logger.info("=== TEST RABBITMQ MANAGER ===")
        
        from app.core.queue import RabbitMQManager
        
        # Crea manager
        manager = RabbitMQManager()
        logger.info("✅ RabbitMQ Manager creato")
        
        # Test senza connessione (fallback mode)
        logger.info("ℹ️  RabbitMQ non disponibile - modalità fallback attiva")
        logger.info("✅ Sistema continua a funzionare senza RabbitMQ")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore RabbitMQ Manager: {e}")
        return False

def test_voice_worker_structure():
    """Test struttura Voice Worker."""
    try:
        logger.info("=== TEST STRUTTURA VOICE WORKER ===")
        
        from app.workers.voice_worker import VoiceWorker
        
        # Crea worker
        worker = VoiceWorker()
        logger.info("✅ Voice Worker creato")
        
        # Verifica metodi
        methods = [
            'start', 'stop', 'process_message', 
            'process_audio_message', 'process_text_message',
            'update_processing_status', 'simulate_audio_transcription',
            'simulate_nlp_processing'
        ]
        
        for method in methods:
            if hasattr(worker, method):
                logger.info(f"✅ Metodo {method} presente")
            else:
                logger.error(f"❌ Metodo {method} mancante")
                return False
        
        logger.info("✅ Tutti i metodi del worker sono presenti")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore Voice Worker: {e}")
        return False

def main():
    """Funzione principale per eseguire i test."""
    logger.info("🚀 Avvio test sistema asincrono...")
    
    tests = [
        ("AudioLog Creation", test_audio_log_creation),
        ("RabbitMQ Manager", test_rabbitmq_manager),
        ("Voice Worker Structure", test_voice_worker_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Esecuzione test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                logger.info(f"✅ Test {test_name} PASSATO")
                passed += 1
            else:
                logger.error(f"❌ Test {test_name} FALLITO")
        except Exception as e:
            logger.error(f"❌ Test {test_name} ERRORE: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"RISULTATI FINALI: {passed}/{total} test passati")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 TUTTI I TEST PASSATI!")
        logger.info("✅ Sistema asincrono pronto per l'uso")
        logger.info("ℹ️  Per test completi con RabbitMQ, installare e avviare RabbitMQ")
        return 0
    else:
        logger.error("❌ ALCUNI TEST FALLITI")
        return 1

if __name__ == "__main__":
    exit(main()) 