#!/usr/bin/env python3
"""
Test per l'integrazione delle interfacce locali e servizi di trascrizione audio.
"""

import sys
import os
import asyncio
from pathlib import Path

# Aggiungi il path del progetto
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.core.config import settings
from app.services.local_interface import LocalInterfaceService
from app.services.speech_to_text import SpeechToTextService
from app.db.session import get_session
from app.models.audio_log import AudioLog
from sqlmodel import select

class LocalInterfaceTester:
    """Classe per testare le interfacce locali."""
    
    def __init__(self):
        self.local_interface = LocalInterfaceService()
        self.speech_service = SpeechToTextService()
        self.test_user_id = 1
        self.test_house_id = 1
        self.test_audio_logs = []
    
    def create_test_audio_log(self, transcribed_text: str) -> AudioLog:
        """Crea un AudioLog di test."""
        db = next(get_session())
        
        audio_log = AudioLog(
            user_id=self.test_user_id,
            house_id=self.test_house_id,
            transcribed_text=transcribed_text,
            processing_status="received"
        )
        
        db.add(audio_log)
        db.commit()
        db.refresh(audio_log)
        
        self.test_audio_logs.append(audio_log.id)
        print(f"✅ AudioLog creato: {audio_log.id} - '{transcribed_text}'")
        
        return audio_log
    
    def test_speech_service_status(self):
        """Test stato servizio di trascrizione audio."""
        print("\n🧪 Test stato servizio trascrizione audio...")
        
        try:
            status = self.speech_service.get_service_status()
            
            assert isinstance(status, dict), "Status deve essere un dizionario"
            assert "google_speech_available" in status, "Manca google_speech_available"
            assert "azure_speech_available" in status, "Manca azure_speech_available"
            assert "supported_languages" in status, "Manca supported_languages"
            
            print(f"✅ Google Speech disponibile: {status['google_speech_available']}")
            print(f"✅ Azure Speech disponibile: {status['azure_speech_available']}")
            print(f"✅ Lingue supportate: {len(status['supported_languages'])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test stato servizio trascrizione: FALLITO - {e}")
            return False
    
    def test_local_interface_status(self):
        """Test stato interfacce locali."""
        print("\n🧪 Test stato interfacce locali...")
        
        try:
            status = asyncio.run(self.local_interface.get_interface_status())
            
            assert isinstance(status, dict), "Status deve essere un dizionario"
            assert "local_interfaces_enabled" in status, "Manca local_interfaces_enabled"
            assert "voice_commands_enabled" in status, "Manca voice_commands_enabled"
            assert "integrations" in status, "Manca integrations"
            
            print(f"✅ Interfacce locali abilitate: {status['local_interfaces_enabled']}")
            print(f"✅ Comandi vocali abilitati: {status['voice_commands_enabled']}")
            print(f"✅ Integrazioni: {status['integrations']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test stato interfacce locali: FALLITO - {e}")
            return False
    
    def test_voice_command_processing(self):
        """Test elaborazione comandi vocali."""
        print("\n🧪 Test elaborazione comandi vocali...")
        
        try:
            # Crea AudioLog di test
            audio_log = self.create_test_audio_log("Accendi le luci del soggiorno")
            
            # Processa comando
            result = asyncio.run(self.local_interface.process_voice_command(audio_log.id))
            
            assert result["success"] is True, "Elaborazione deve avere successo"
            assert "actions_executed" in result, "Manca actions_executed"
            assert "response" in result, "Manca response"
            
            print(f"✅ Azioni eseguite: {result['actions_executed']}")
            print(f"✅ Risposta: {result['response']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test elaborazione comandi vocali: FALLITO - {e}")
            return False
    
    def test_iot_command_analysis(self):
        """Test analisi comandi IoT."""
        print("\n🧪 Test analisi comandi IoT...")
        
        try:
            # Crea AudioLog con comando IoT
            audio_log = self.create_test_audio_log("Spegni tutte le luci")
            
            # Analizza comando
            actions = asyncio.run(self.local_interface._analyze_command(
                audio_log.transcribed_text, audio_log, next(get_session())
            ))
            
            assert len(actions) > 0, "Dovrebbero essere trovate azioni IoT"
            
            iot_actions = [a for a in actions if a["type"] == "iot_control"]
            assert len(iot_actions) > 0, "Dovrebbero essere trovate azioni di controllo IoT"
            
            print(f"✅ Azioni IoT trovate: {len(iot_actions)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test analisi comandi IoT: FALLITO - {e}")
            return False
    
    def test_bim_command_analysis(self):
        """Test analisi comandi BIM."""
        print("\n🧪 Test analisi comandi BIM...")
        
        try:
            # Crea AudioLog con comando BIM
            audio_log = self.create_test_audio_log("Converti tutti i modelli BIM")
            
            # Analizza comando
            actions = asyncio.run(self.local_interface._analyze_command(
                audio_log.transcribed_text, audio_log, next(get_session())
            ))
            
            bim_actions = [a for a in actions if a["type"] == "bim_conversion"]
            print(f"✅ Azioni BIM trovate: {len(bim_actions)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test analisi comandi BIM: FALLITO - {e}")
            return False
    
    def test_info_command_analysis(self):
        """Test analisi comandi informativi."""
        print("\n🧪 Test analisi comandi informativi...")
        
        try:
            # Crea AudioLog con comando informativo
            audio_log = self.create_test_audio_log("Qual è la temperatura attuale?")
            
            # Analizza comando
            actions = asyncio.run(self.local_interface._analyze_command(
                audio_log.transcribed_text, audio_log, next(get_session())
            ))
            
            info_actions = [a for a in actions if a["type"] == "sensor_read"]
            assert len(info_actions) > 0, "Dovrebbero essere trovate azioni informative"
            
            print(f"✅ Azioni informative trovate: {len(info_actions)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test analisi comandi informativi: FALLITO - {e}")
            return False
    
    def test_response_generation(self):
        """Test generazione risposte."""
        print("\n🧪 Test generazione risposte...")
        
        try:
            # Simula risultati di azioni
            results = [
                {
                    "action": {"type": "iot_control", "description": "Accende luci soggiorno"},
                    "success": True,
                    "result": {"status": "executed"}
                },
                {
                    "action": {"type": "sensor_read", "description": "Legge temperatura"},
                    "success": True,
                    "result": {"temperature": 22.5, "unit": "°C"}
                }
            ]
            
            response = self.local_interface._generate_response(results)
            
            assert isinstance(response, str), "Risposta deve essere una stringa"
            assert len(response) > 0, "Risposta non può essere vuota"
            
            print(f"✅ Risposta generata: {response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test generazione risposte: FALLITO - {e}")
            return False
    
    def test_supported_languages(self):
        """Test lingue supportate."""
        print("\n🧪 Test lingue supportate...")
        
        try:
            languages = self.speech_service.get_supported_languages()
            
            assert isinstance(languages, list), "Lingue deve essere una lista"
            assert len(languages) > 0, "Deve supportare almeno una lingua"
            assert "it-IT" in languages, "Deve supportare italiano"
            assert "en-US" in languages, "Deve supportare inglese"
            
            print(f"✅ Lingue supportate: {len(languages)}")
            print(f"✅ Italiano supportato: {'it-IT' in languages}")
            print(f"✅ Inglese supportato: {'en-US' in languages}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test lingue supportate: FALLITO - {e}")
            return False
    
    def cleanup_test_data(self):
        """Pulisce i dati di test."""
        print("\n🧹 Pulizia dati di test...")
        
        try:
            db = next(get_session())
            
            # Elimina AudioLog di test
            for audio_log_id in self.test_audio_logs:
                audio_log = db.get(AudioLog, audio_log_id)
                if audio_log:
                    db.delete(audio_log)
            
            db.commit()
            print(f"✅ Eliminati {len(self.test_audio_logs)} AudioLog di test")
            
        except Exception as e:
            print(f"⚠️ Errore durante la pulizia: {e}")

def run_all_tests():
    """Esegue tutti i test delle interfacce locali."""
    
    print("🏠 Test Interfacce Locali e Servizi Trascrizione Audio")
    print("=" * 60)
    
    tester = LocalInterfaceTester()
    results = []
    
    try:
        # Esegui test
        test_methods = [
            tester.test_speech_service_status,
            tester.test_local_interface_status,
            tester.test_voice_command_processing,
            tester.test_iot_command_analysis,
            tester.test_bim_command_analysis,
            tester.test_info_command_analysis,
            tester.test_response_generation,
            tester.test_supported_languages
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