#!/usr/bin/env python3
"""
Test per il sistema asincrono di elaborazione comandi vocali.
Verifica l'integrazione tra API, coda RabbitMQ e worker.
"""
import asyncio
import json
import time
import requests
import logging
from datetime import datetime
from typing import Dict, Any

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione test
API_BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

class VoiceWorkerTester:
    """Tester per il sistema di elaborazione comandi vocali."""
    
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        
    def setup_auth(self):
        """Configura l'autenticazione per i test."""
        try:
            # Login per ottenere token
            login_data = {
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/auth/login",
                data=login_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                logger.info("Autenticazione configurata con successo")
                return True
            else:
                logger.error(f"Errore login: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Errore setup autenticazione: {e}")
            return False
    
    def test_voice_command_text(self) -> Dict[str, Any]:
        """Test invio comando vocale testuale."""
        try:
            logger.info("Test comando vocale testuale...")
            
            command_data = {
                "transcribed_text": "Accendi le luci del soggiorno",
                "node_id": 1,
                "house_id": 1
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/voice/commands",
                json=command_data
            )
            
            if response.status_code == 202:
                result = response.json()
                logger.info(f"Comando testuale inviato: {result}")
                return result
            else:
                logger.error(f"Errore invio comando testuale: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Errore test comando testuale: {e}")
            return None
    
    def test_voice_command_audio(self) -> Dict[str, Any]:
        """Test invio comando vocale audio (simulato)."""
        try:
            logger.info("Test comando vocale audio...")
            
            # Simula file audio (in un test reale si userebbe un file vero)
            audio_data = b"fake_audio_data"
            
            files = {
                "audio_file": ("test_audio.wav", audio_data, "audio/wav")
            }
            
            data = {
                "node_id": 1,
                "house_id": 1
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/voice/commands/audio",
                files=files,
                data=data
            )
            
            if response.status_code == 202:
                result = response.json()
                logger.info(f"Comando audio inviato: {result}")
                return result
            else:
                logger.error(f"Errore invio comando audio: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Errore test comando audio: {e}")
            return None
    
    def get_audio_logs(self) -> Dict[str, Any]:
        """Ottiene la lista degli AudioLog."""
        try:
            response = self.session.get(f"{API_BASE_URL}/api/v1/voice/logs")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"AudioLog ottenuti: {len(result.get('items', []))} record")
                return result
            else:
                logger.error(f"Errore ottenimento AudioLog: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Errore ottenimento AudioLog: {e}")
            return None
    
    def get_audio_log(self, log_id: int) -> Dict[str, Any]:
        """Ottiene un AudioLog specifico."""
        try:
            response = self.session.get(f"{API_BASE_URL}/api/v1/voice/logs/{log_id}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"AudioLog {log_id}: {result}")
                return result
            else:
                logger.error(f"Errore ottenimento AudioLog {log_id}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Errore ottenimento AudioLog {log_id}: {e}")
            return None
    
    def monitor_processing_status(self, log_id: int, max_wait: int = 30) -> bool:
        """Monitora lo stato di elaborazione di un AudioLog."""
        logger.info(f"Monitoraggio stato elaborazione AudioLog {log_id}...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            audio_log = self.get_audio_log(log_id)
            if audio_log:
                status = audio_log.get("processing_status")
                logger.info(f"Stato AudioLog {log_id}: {status}")
                
                if status in ["completed", "failed"]:
                    logger.info(f"Elaborazione AudioLog {log_id} completata con stato: {status}")
                    return True
                elif status in ["transcribing", "analyzing"]:
                    logger.info(f"AudioLog {log_id} in elaborazione...")
                else:
                    logger.info(f"AudioLog {log_id} in attesa...")
            
            time.sleep(2)
        
        logger.warning(f"Timeout monitoraggio AudioLog {log_id}")
        return False
    
    def run_complete_test(self):
        """Esegue un test completo del sistema."""
        logger.info("=== TEST SISTEMA ELABORAZIONE COMANDI VOCALI ===")
        
        # Setup autenticazione
        if not self.setup_auth():
            logger.error("Impossibile configurare autenticazione")
            return False
        
        # Test comando testuale
        text_result = self.test_voice_command_text()
        if not text_result:
            logger.error("Test comando testuale fallito")
            return False
        
        # Estrai ID AudioLog dal risultato
        request_id = text_result.get("request_id", "")
        text_log_id = int(request_id.split("-")[-1]) if "-" in request_id else None
        
        if text_log_id:
            logger.info(f"Monitoraggio elaborazione AudioLog testuale {text_log_id}")
            self.monitor_processing_status(text_log_id)
        
        # Test comando audio (simulato)
        audio_result = self.test_voice_command_audio()
        if audio_result:
            request_id = audio_result.get("request_id", "")
            audio_log_id = int(request_id.split("-")[-1]) if "-" in request_id else None
            
            if audio_log_id:
                logger.info(f"Monitoraggio elaborazione AudioLog audio {audio_log_id}")
                self.monitor_processing_status(audio_log_id)
        
        # Ottieni tutti gli AudioLog
        logs = self.get_audio_logs()
        if logs:
            logger.info("=== RIEPILOGO AUDIOLOG ===")
            for item in logs.get("items", []):
                logger.info(f"ID: {item.get('id')}, Stato: {item.get('processing_status')}, "
                          f"Testo: {item.get('transcribed_text')}, "
                          f"Risposta: {item.get('response_text')}")
        
        logger.info("=== TEST COMPLETATO ===")
        return True

def main():
    """Funzione principale per eseguire i test."""
    tester = VoiceWorkerTester()
    
    try:
        success = tester.run_complete_test()
        if success:
            logger.info("✅ Tutti i test completati con successo")
        else:
            logger.error("❌ Alcuni test sono falliti")
            return 1
    except Exception as e:
        logger.error(f"Errore durante i test: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 