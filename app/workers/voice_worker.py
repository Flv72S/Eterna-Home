"""
Worker asincrono per elaborazione comandi vocali.
Elabora i messaggi dalla coda RabbitMQ e aggiorna gli AudioLog.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
from sqlmodel import Session, select, create_engine
from app.core.queue import RabbitMQManager
from app.core.config import settings
from app.core.logging import get_logger
from app.models.audio_log import AudioLog
from app.services.audio_log import AudioLogService
from app.services.speech_to_text import SpeechToTextService
from app.services.local_interface import LocalInterfaceService
import re
from app.core.logging_config import log_operation, log_security_event
from app.utils.ai_security import sanitize_prompt

logger = get_logger(__name__)

class VoiceWorker:
    """Worker per elaborazione comandi vocali."""
    
    def __init__(self):
        self.rabbitmq_manager = RabbitMQManager()
        self.engine = create_engine(settings.DATABASE_URL)
        self.minio_client = None
        self.running = False
        
        # Inizializza servizi
        self.speech_service = SpeechToTextService()
        self.local_interface = LocalInterfaceService()
        
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
        """Elabora un messaggio dalla coda con protezione payload e retry."""
        allowed_keys = {"tenant_id", "user_id", "node_id", "audio_url", "transcribed_text", "timestamp"}
        retry_count = message_data.get("_retry_count", 0)
        extra_keys = set(message_data.keys()) - allowed_keys - {"audiolog_id", "command_type", "_retry_count"}
        missing_keys = {"tenant_id", "user_id", "timestamp"} - set(message_data.keys())
        # Filtro chiavi non consentite
        if extra_keys:
            log_security_event(
                event="ai_payload_invalid_keys",
                status="failed",
                user_id=message_data.get("user_id"),
                tenant_id=message_data.get("tenant_id"),
                reason=f"Chiavi non consentite: {extra_keys}",
                metadata={"payload": str(message_data)}
            )
            return
        # Filtro chiavi mancanti
        if missing_keys:
            log_security_event(
                event="ai_payload_missing_keys",
                status="failed",
                user_id=message_data.get("user_id"),
                tenant_id=message_data.get("tenant_id"),
                reason=f"Chiavi mancanti: {missing_keys}",
                metadata={"payload": str(message_data)}
            )
            return
        # Sanitizzazione prompt
        transcribed_text = message_data.get("transcribed_text", "")
        sanitized, reason = sanitize_prompt(transcribed_text)
        if not sanitized:
            log_security_event(
                event="ai_prompt_blocked",
                status="failed",
                user_id=message_data.get("user_id"),
                tenant_id=message_data.get("tenant_id"),
                reason=reason,
                metadata={"input": transcribed_text}
            )
            return
        # Retry logic
        try:
            await self._process_message_safe(message_data)
        except Exception as e:
            if retry_count < 1:
                message_data["_retry_count"] = retry_count + 1
                log_security_event(
                    event="ai_worker_retry",
                    status="failed",
                    user_id=message_data.get("user_id"),
                    tenant_id=message_data.get("tenant_id"),
                    reason=str(e),
                    metadata={"retry": retry_count + 1}
                )
                await self.process_message(message_data)
            else:
                log_security_event(
                    event="ai_worker_failed",
                    status="failed",
                    user_id=message_data.get("user_id"),
                    tenant_id=message_data.get("tenant_id"),
                    reason=str(e),
                    metadata={"payload": str(message_data)}
                )
    
    async def _process_message_safe(self, message_data: Dict[str, Any]):
        """Processa il messaggio dopo i controlli di sicurezza."""
        audiolog_id = message_data.get("audiolog_id")
        command_type = message_data.get("command_type", "text")
        user_id = message_data.get("user_id")
        tenant_id = message_data.get("tenant_id")
        logger.info("Voice command processing started",
                    audiolog_id=audiolog_id,
                    user_id=user_id,
                    command_type=command_type)
        if not audiolog_id:
            logger.error("Messaggio senza audiolog_id")
            return
        with Session(self.engine) as db:
            audio_log = db.get(AudioLog, audiolog_id)
            if not audio_log:
                logger.error("AudioLog not found", audiolog_id=audiolog_id)
                return
            logger.info("Voice command processing",
                        audiolog_id=audio_log.id,
                        user_id=audio_log.user_id,
                        tenant_id=str(audio_log.tenant_id),
                        status=audio_log.processing_status,
                        input_text=audio_log.transcribed_text)
            await self.update_processing_status(db, audio_log, "transcribing")
            try:
                if command_type == "audio":
                    await self.process_audio_message(db, audio_log, message_data)
                else:
                    await self.process_text_message(db, audio_log, message_data)
            except Exception as e:
                logger.error("Voice command processing failed",
                            audiolog_id=audio_log.id,
                            user_id=audio_log.user_id,
                            tenant_id=str(audio_log.tenant_id),
                            error=str(e),
                            exc_info=True)
                await self.update_processing_status(db, audio_log, "failed")
                log_operation(
                    operation="ai_interaction",
                    status="failed",
                    user_id=user_id,
                    tenant_id=tenant_id,
                    resource_type="ai",
                    resource_id=audiolog_id,
                    metadata={"input": message_data.get("transcribed_text", ""), "output": None, "reason": str(e)}
                )
                raise
            # Log di successo
            log_operation(
                operation="ai_interaction",
                status="completed",
                user_id=user_id,
                tenant_id=tenant_id,
                resource_type="ai",
                resource_id=audiolog_id,
                metadata={"input": message_data.get("transcribed_text", ""), "output": getattr(audio_log, "response_text", None)}
            )
    
    async def process_audio_message(self, db: Session, audio_log: AudioLog, message_data: Dict[str, Any]):
        """Elabora un messaggio audio con servizio di trascrizione reale."""
        try:
            logger.info(f"Elaborazione audio per AudioLog {audio_log.id}")
            
            # Usa servizio di trascrizione reale se abilitato
            if settings.USE_REAL_SPEECH_TO_TEXT and audio_log.audio_url:
                transcribed_result = await self.speech_service.transcribe_audio(
                    audio_log.audio_url,
                    settings.GOOGLE_SPEECH_LANGUAGE
                )
                transcribed_text = transcribed_result.get("transcription", "")
                logger.info(f"Trascrizione reale completata: {transcribed_text[:50]}...")
            else:
                # Fallback a simulazione
                transcribed_text = await self.simulate_audio_transcription(message_data)
                logger.info("Usata trascrizione simulata")
            
            # Aggiorna AudioLog con testo trascritto
            audio_log.transcribed_text = transcribed_text
            db.commit()
            
            # Aggiorna stato a "analyzing"
            await self.update_processing_status(db, audio_log, "analyzing")
            
            # Elabora il comando trascritto con interfacce locali
            await self.process_text_message(db, audio_log, message_data)
            
        except Exception as e:
            logger.error(f"Errore elaborazione audio: {e}")
            raise
    
    async def process_text_message(self, db: Session, audio_log: AudioLog, message_data: Dict[str, Any]):
        """Elabora un comando testuale con interfacce locali."""
        try:
            logger.info("Text message processing started",
                        audiolog_id=audio_log.id,
                        user_id=audio_log.user_id,
                        tenant_id=str(audio_log.tenant_id))
            
            # Ottieni il testo da elaborare
            text_to_process = audio_log.transcribed_text or message_data.get("transcribed_text", "")
            
            if not text_to_process:
                logger.warning("No text to process",
                              audiolog_id=audio_log.id,
                              user_id=audio_log.user_id,
                              tenant_id=str(audio_log.tenant_id))
                await self.update_processing_status(db, audio_log, "failed")
                return
            
            # Usa interfacce locali per elaborazione
            if settings.ENABLE_LOCAL_INTERFACES:
                result = await self.local_interface.process_voice_command(audio_log.id)
                response_text = result.get("response", "Elaborazione completata")
                logger.info("Local interface processing completed",
                            audiolog_id=audio_log.id,
                            user_id=audio_log.user_id,
                            tenant_id=str(audio_log.tenant_id),
                            actions_count=len(result.get('actions_executed', [])))
            else:
                # Fallback a elaborazione simulata
                response_text = await self.simulate_nlp_processing(text_to_process, message_data)
                logger.info("Simulated NLP processing completed",
                            audiolog_id=audio_log.id,
                            user_id=audio_log.user_id,
                            tenant_id=str(audio_log.tenant_id))
            
            # Aggiorna AudioLog con risposta
            audio_log.response_text = response_text
            db.commit()
            
            # Aggiorna stato a "completed"
            await self.update_processing_status(db, audio_log, "completed")
            
            # Logging finale dell'interazione AI
            logger.info("Voice command interaction completed",
                        audiolog_id=audio_log.id,
                        user_id=audio_log.user_id,
                        tenant_id=str(audio_log.tenant_id),
                        input_text=text_to_process,
                        response_text=response_text,
                        status="completed")
            
        except Exception as e:
            logger.error("Text message processing failed",
                        audiolog_id=audio_log.id,
                        user_id=audio_log.user_id,
                        tenant_id=str(audio_log.tenant_id),
                        error=str(e),
                        exc_info=True)
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
        """Simula la trascrizione di un file audio (fallback)."""
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
        """Simula l'elaborazione NLP di un comando testuale (fallback)."""
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
    
    async def get_worker_status(self) -> Dict[str, Any]:
        """Restituisce lo stato del worker."""
        return {
            "running": self.running,
            "speech_service_status": self.speech_service.get_service_status(),
            "local_interface_status": await self.local_interface.get_interface_status(),
            "minio_available": self.minio_client is not None,
            "rabbitmq_connected": self.rabbitmq_manager.is_connected if hasattr(self.rabbitmq_manager, 'is_connected') else False
        }

async def main():
    """Funzione principale per avvio worker."""
    worker = VoiceWorker()
    
    try:
        await worker.start()
        
        # Mantieni il worker in esecuzione
        while worker.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interruzione richiesta dall'utente")
    except Exception as e:
        logger.error(f"Errore nel worker: {e}")
    finally:
        await worker.stop()

if __name__ == "__main__":
    asyncio.run(main()) 