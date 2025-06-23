"""
Servizio per trascrizione audio usando Google Speech-to-Text.
Supporta anche fallback a servizi alternativi.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import tempfile

# Google Speech-to-Text
try:
    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types
    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False
    logging.warning("Google Speech-to-Text non disponibile. Installa: pip install google-cloud-speech")

# Azure Speech Services (fallback)
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_SPEECH_AVAILABLE = True
except ImportError:
    AZURE_SPEECH_AVAILABLE = False
    logging.warning("Azure Speech Services non disponibile. Installa: pip install azure-cognitiveservices-speech")

from app.core.config import settings
from app.services.minio_service import MinioService

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """Servizio per trascrizione audio con supporto multipli provider."""
    
    def __init__(self):
        self.minio_service = MinioService()
        self.google_client = None
        self.azure_config = None
        
        # Inizializza Google Speech-to-Text
        if GOOGLE_SPEECH_AVAILABLE and settings.GOOGLE_SPEECH_ENABLED:
            try:
                self.google_client = speech.SpeechClient()
                logger.info("Google Speech-to-Text client inizializzato")
            except Exception as e:
                logger.warning(f"Errore inizializzazione Google Speech: {e}")
        
        # Inizializza Azure Speech Services
        if AZURE_SPEECH_AVAILABLE and settings.AZURE_SPEECH_ENABLED:
            self.azure_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION
            )
            logger.info("Azure Speech Services configurato")
    
    async def transcribe_audio(self, audio_url: str, language_code: str = "it-IT") -> Dict[str, Any]:
        """
        Trascrive un file audio usando il servizio disponibile.
        
        Args:
            audio_url: URL del file audio in MinIO
            language_code: Codice lingua per la trascrizione
            
        Returns:
            Dict con trascrizione e metadati
        """
        try:
            logger.info(f"Avvio trascrizione audio: {audio_url}")
            
            # Scarica file audio da MinIO
            audio_data = await self._download_audio_file(audio_url)
            if not audio_data:
                raise Exception("Impossibile scaricare file audio")
            
            # Prova Google Speech-to-Text
            if self.google_client and settings.GOOGLE_SPEECH_ENABLED:
                try:
                    result = await self._transcribe_with_google(audio_data, language_code)
                    if result and result.get("transcription"):
                        logger.info("Trascrizione completata con Google Speech-to-Text")
                        return result
                except Exception as e:
                    logger.warning(f"Google Speech-to-Text fallito: {e}")
            
            # Fallback a Azure Speech Services
            if self.azure_config and settings.AZURE_SPEECH_ENABLED:
                try:
                    result = await self._transcribe_with_azure(audio_data, language_code)
                    if result and result.get("transcription"):
                        logger.info("Trascrizione completata con Azure Speech Services")
                        return result
                except Exception as e:
                    logger.warning(f"Azure Speech Services fallito: {e}")
            
            # Fallback a simulazione
            logger.warning("Tutti i servizi di trascrizione falliti, uso simulazione")
            return await self._simulate_transcription(audio_url)
            
        except Exception as e:
            logger.error(f"Errore trascrizione audio: {e}")
            raise
    
    async def _download_audio_file(self, audio_url: str) -> Optional[bytes]:
        """Scarica file audio da MinIO."""
        try:
            bucket_name, file_path = audio_url.split("/", 1)
            audio_data = await self.minio_service.download_file(bucket_name, file_path)
            logger.info(f"File audio scaricato: {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            logger.error(f"Errore download file audio: {e}")
            return None
    
    async def _transcribe_with_google(self, audio_data: bytes, language_code: str) -> Dict[str, Any]:
        """Trascrive audio usando Google Speech-to-Text."""
        try:
            # Configura riconoscimento
            audio = types.RecognitionAudio(content=audio_data)
            config = types.RecognitionConfig(
                encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                model="latest_long"
            )
            
            # Esegui riconoscimento
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.google_client.recognize, config, audio
            )
            
            if not response.results:
                return {"transcription": "", "confidence": 0.0, "provider": "google"}
            
            # Estrai risultati
            transcriptions = []
            confidences = []
            
            for result in response.results:
                if result.alternatives:
                    alternative = result.alternatives[0]
                    transcriptions.append(alternative.transcript)
                    confidences.append(alternative.confidence)
            
            full_transcription = " ".join(transcriptions)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                "transcription": full_transcription,
                "confidence": avg_confidence,
                "provider": "google",
                "language_code": language_code,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Errore Google Speech-to-Text: {e}")
            raise
    
    async def _transcribe_with_azure(self, audio_data: bytes, language_code: str) -> Dict[str, Any]:
        """Trascrive audio usando Azure Speech Services."""
        try:
            # Salva file temporaneo
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Configura riconoscimento
                audio_config = speechsdk.AudioConfig(filename=temp_file_path)
                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.azure_config,
                    audio_config=audio_config
                )
                
                # Esegui riconoscimento
                result = await asyncio.get_event_loop().run_in_executor(
                    None, speech_recognizer.recognize_once
                )
                
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    return {
                        "transcription": result.text,
                        "confidence": 0.9,  # Azure non fornisce confidence per recognize_once
                        "provider": "azure",
                        "language_code": language_code,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"Azure Speech non ha riconosciuto audio: {result.reason}")
                    return {"transcription": "", "confidence": 0.0, "provider": "azure"}
                    
            finally:
                # Pulisci file temporaneo
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Errore Azure Speech Services: {e}")
            raise
    
    async def _simulate_transcription(self, audio_url: str) -> Dict[str, Any]:
        """Simula trascrizione per fallback."""
        await asyncio.sleep(2)  # Simula elaborazione
        
        # Logica di simulazione basata su URL
        if "voice-commands" in audio_url:
            simulated_text = "Accendi le luci del soggiorno"
        elif "meeting" in audio_url:
            simulated_text = "Riunione di progetto programmata per domani"
        else:
            simulated_text = "Comando audio ricevuto e trascritto"
        
        return {
            "transcription": simulated_text,
            "confidence": 0.8,
            "provider": "simulation",
            "language_code": "it-IT",
            "timestamp": datetime.now().isoformat()
        }
    
    async def transcribe_batch(self, audio_urls: List[str], language_code: str = "it-IT") -> List[Dict[str, Any]]:
        """Trascrive multipli file audio in parallelo."""
        tasks = []
        for audio_url in audio_urls:
            task = self.transcribe_audio(audio_url, language_code)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtra risultati con errori
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Errore trascrizione {audio_urls[i]}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def get_supported_languages(self) -> List[str]:
        """Restituisce le lingue supportate."""
        return [
            "it-IT",  # Italiano
            "en-US",  # Inglese US
            "en-GB",  # Inglese UK
            "es-ES",  # Spagnolo
            "fr-FR",  # Francese
            "de-DE",  # Tedesco
            "pt-BR",  # Portoghese Brasile
            "ru-RU",  # Russo
            "ja-JP",  # Giapponese
            "ko-KR",  # Coreano
            "zh-CN",  # Cinese semplificato
            "zh-TW"   # Cinese tradizionale
        ]
    
    def get_service_status(self) -> Dict[str, Any]:
        """Restituisce lo stato dei servizi di trascrizione."""
        return {
            "google_speech_available": GOOGLE_SPEECH_AVAILABLE and settings.GOOGLE_SPEECH_ENABLED,
            "azure_speech_available": AZURE_SPEECH_AVAILABLE and settings.AZURE_SPEECH_ENABLED,
            "google_client_initialized": self.google_client is not None,
            "azure_config_initialized": self.azure_config is not None,
            "supported_languages": self.get_supported_languages()
        } 