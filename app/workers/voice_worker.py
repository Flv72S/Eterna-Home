"""
Worker asincrono per elaborazione comandi vocali.
Elabora i messaggi dalla coda RabbitMQ e aggiorna gli AudioLog.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
from sqlmodel import Session, create_engine
from app.core.queue import RabbitMQManager
from app.core.config import settings
from app.models.audio_log import AudioLog
from app.services.audio_log import AudioLogService

logger = logging.getLogger(__name__)

class VoiceWorker:
    """Worker per elaborazione comandi vocali."""
    
    def __init__(self):
        self.rabbitmq_manager = RabbitMQManager()
        self.engine = create_engine(settings.DATABASE_URL)
        self.minio_client = None
        self.running = False
        
        # Inizializza MinIO client solo se necessario
        try:
            from app.core.storage.minio import get_minio_client
            self.minio_client = get_minio_client()
            logger.info("MinIO client inizializzato")
        except Exception as e:
            logger.warning(f"MinIO non disponibile: {e}")
            logger.info("Worker funzionerà senza MinIO")
        
    async def start(self):
        """Avvia il worker."""
        try:
            logger.info("Avvio Voice Worker...")
            
            # Connessione a RabbitMQ
            await self.rabbitmq_manager.connect()
            
            # Connessione al database
            logger.info("Connessione al database stabilita")
            
            self.running = True
            logger.info("Voice Worker avviato con successo")
            
            # Inizia a consumare messaggi
            await self.rabbitmq_manager.consume_messages(self.process_message)
            
        except Exception as e:
            logger.error(f"Errore avvio Voice Worker: {e}")
            raise
    
    async def stop(self):
        """Ferma il worker."""
        logger.info("Arresto Voice Worker...")
        self.running = False
        await self.rabbitmq_manager.disconnect()
        logger.info("Voice Worker arrestato")
    
    async def process_message(self, message_data: Dict[str, Any]):
        """Elabora un messaggio dalla coda."""
        try:
            logger.info(f"Elaborazione messaggio: {message_data}")
            
            audiolog_id = message_data.get("audiolog_id")
            command_type = message_data.get("command_type", "text")
            
            if not audiolog_id:
                logger.error("Messaggio senza audiolog_id")
                return
            
            # Crea sessione database
            with Session(self.engine) as db:
                # Recupera AudioLog
                audio_log = db.get(AudioLog, audiolog_id)
                if not audio_log:
                    logger.error(f"AudioLog {audiolog_id} non trovato")
                    return
                
                # Aggiorna stato a "transcribing"
                await self.update_processing_status(db, audio_log, "transcribing")
                
                try:
                    if command_type == "audio":
                        # Elabora file audio
                        await self.process_audio_message(db, audio_log, message_data)
                    else:
                        # Elabora comando testuale
                        await self.process_text_message(db, audio_log, message_data)
                        
                except Exception as e:
                    logger.error(f"Errore elaborazione messaggio: {e}")
                    await self.update_processing_status(db, audio_log, "failed")
                    
        except Exception as e:
            logger.error(f"Errore processamento messaggio: {e}")
    
    async def process_audio_message(self, db: Session, audio_log: AudioLog, message_data: Dict[str, Any]):
        """Elabora un messaggio audio."""
        try:
            logger.info(f"Elaborazione audio per AudioLog {audio_log.id}")
            
            # Simula trascrizione audio (TODO: integrare servizio di trascrizione)
            transcribed_text = await self.simulate_audio_transcription(message_data)
            
            # Aggiorna AudioLog con testo trascritto
            audio_log.transcribed_text = transcribed_text
            db.commit()
            
            # Aggiorna stato a "analyzing"
            await self.update_processing_status(db, audio_log, "analyzing")
            
            # Elabora il comando trascritto
            await self.process_text_message(db, audio_log, message_data)
            
        except Exception as e:
            logger.error(f"Errore elaborazione audio: {e}")
            raise
    
    async def process_text_message(self, db: Session, audio_log: AudioLog, message_data: Dict[str, Any]):
        """Elabora un comando testuale."""
        try:
            logger.info(f"Elaborazione testo per AudioLog {audio_log.id}")
            
            # Ottieni il testo da elaborare
            text_to_process = audio_log.transcribed_text or message_data.get("transcribed_text", "")
            
            if not text_to_process:
                logger.warning(f"Nessun testo da elaborare per AudioLog {audio_log.id}")
                await self.update_processing_status(db, audio_log, "failed")
                return
            
            # Simula elaborazione NLP (TODO: integrare servizio NLP/LLM)
            response_text = await self.simulate_nlp_processing(text_to_process, message_data)
            
            # Aggiorna AudioLog con risposta
            audio_log.response_text = response_text
            db.commit()
            
            # Aggiorna stato a "completed"
            await self.update_processing_status(db, audio_log, "completed")
            
            logger.info(f"Elaborazione completata per AudioLog {audio_log.id}")
            
        except Exception as e:
            logger.error(f"Errore elaborazione testo: {e}")
            raise
    
    async def update_processing_status(self, db: Session, audio_log: AudioLog, status: str):
        """Aggiorna lo stato di elaborazione di un AudioLog."""
        try:
            audio_log.processing_status = status
            db.commit()
            logger.info(f"AudioLog {audio_log.id} aggiornato a stato: {status}")
        except Exception as e:
            logger.error(f"Errore aggiornamento stato AudioLog {audio_log.id}: {e}")
            db.rollback()
    
    async def simulate_audio_transcription(self, message_data: Dict[str, Any]) -> str:
        """Simula la trascrizione di un file audio."""
        # TODO: Integrare servizio di trascrizione (Google Speech-to-Text, Azure Speech, etc.)
        logger.info("Simulazione trascrizione audio...")
        
        # Simula delay di elaborazione
        await asyncio.sleep(2)
        
        # Restituisce testo simulato basato sul tipo di comando
        audio_url = message_data.get("audio_url", "")
        if "voice-commands" in audio_url:
            return "Accendi le luci del soggiorno"
        else:
            return "Comando audio ricevuto e trascritto"
    
    async def simulate_nlp_processing(self, text: str, message_data: Dict[str, Any]) -> str:
        """Simula l'elaborazione NLP di un comando testuale."""
        # TODO: Integrare servizio NLP/LLM (OpenAI, Azure Cognitive Services, etc.)
        logger.info(f"Simulazione elaborazione NLP per: '{text}'")
        
        # Simula delay di elaborazione
        await asyncio.sleep(1)
        
        # Logica di risposta simulata
        text_lower = text.lower()
        
        if "accendi" in text_lower and "luci" in text_lower:
            return "Luci accese con successo"
        elif "spegni" in text_lower and "luci" in text_lower:
            return "Luci spente con successo"
        elif "temperatura" in text_lower:
            return "Temperatura attuale: 22°C"
        elif "stato" in text_lower or "status" in text_lower:
            return "Tutti i sistemi funzionano correttamente"
        elif "aiuto" in text_lower or "help" in text_lower:
            return "Comandi disponibili: accendi/spegni luci, temperatura, stato sistema"
        else:
            return f"Comando ricevuto: '{text}'. Elaborazione completata."

async def main():
    """Funzione principale per avvio del worker."""
    worker = VoiceWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Interruzione ricevuta, arresto worker...")
    except Exception as e:
        logger.error(f"Errore worker: {e}")
    finally:
        await worker.stop()

if __name__ == "__main__":
    # Configurazione logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Avvia worker
    asyncio.run(main()) 