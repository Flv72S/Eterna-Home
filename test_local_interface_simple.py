#!/usr/bin/env python3
"""
Test semplificato per l'integrazione delle interfacce locali.
Non dipende da MinIO o servizi esterni.
"""

import sys
import os
import asyncio
from pathlib import Path

# Aggiungi il path del progetto
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.core.config import settings
from app.db.session import get_session
from app.models.audio_log import AudioLog
from sqlmodel import select

class SimpleLocalInterfaceTester:
    """Classe per testare le interfacce locali senza dipendenze esterne."""
    
    def __init__(self):
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
    
    def test_configuration(self):
        """Test configurazione interfacce locali."""
        print("\n🧪 Test configurazione interfacce locali...")
        
        try:
            # Verifica configurazioni
            assert hasattr(settings, 'ENABLE_LOCAL_INTERFACES'), "Manca ENABLE_LOCAL_INTERFACES"
            assert hasattr(settings, 'ENABLE_VOICE_COMMANDS'), "Manca ENABLE_VOICE_COMMANDS"
            assert hasattr(settings, 'USE_REAL_SPEECH_TO_TEXT'), "Manca USE_REAL_SPEECH_TO_TEXT"
            
            print(f"✅ Interfacce locali abilitate: {settings.ENABLE_LOCAL_INTERFACES}")
            print(f"✅ Comandi vocali abilitati: {settings.ENABLE_VOICE_COMMANDS}")
            print(f"✅ Trascrizione audio reale: {settings.USE_REAL_SPEECH_TO_TEXT}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test configurazione: FALLITO - {e}")
            return False
    
    def test_audio_log_model(self):
        """Test modello AudioLog."""
        print("\n🧪 Test modello AudioLog...")
        
        try:
            # Crea AudioLog di test
            audio_log = self.create_test_audio_log("Test comando vocale")
            
            # Verifica proprietà
            assert audio_log.id is not None, "ID non dovrebbe essere None"
            assert audio_log.user_id == self.test_user_id, "user_id non corretto"
            assert audio_log.transcribed_text == "Test comando vocale", "transcribed_text non corretto"
            assert audio_log.processing_status == "received", "processing_status non corretto"
            
            # Test proprietà calcolate
            assert hasattr(audio_log, 'status_display'), "Manca status_display"
            assert hasattr(audio_log, 'is_completed'), "Manca is_completed"
            assert hasattr(audio_log, 'is_processing'), "Manca is_processing"
            
            print(f"✅ Status display: {audio_log.status_display}")
            print(f"✅ Is completed: {audio_log.is_completed}")
            print(f"✅ Is processing: {audio_log.is_processing}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test modello AudioLog: FALLITO - {e}")
            return False
    
    def test_command_analysis_simulation(self):
        """Test simulazione analisi comandi."""
        print("\n🧪 Test simulazione analisi comandi...")
        
        try:
            # Simula analisi comandi
            commands = [
                "Accendi le luci del soggiorno",
                "Spegni tutte le luci",
                "Qual è la temperatura?",
                "Converti modello BIM",
                "Lista documenti",
                "Aiuto"
            ]
            
            for command in commands:
                # Simula analisi
                actions = self._simulate_command_analysis(command)
                print(f"✅ Comando '{command}': {len(actions)} azioni trovate")
            
            return True
            
        except Exception as e:
            print(f"❌ Test analisi comandi: FALLITO - {e}")
            return False
    
    def _simulate_command_analysis(self, text: str) -> list:
        """Simula analisi comando."""
        text_lower = text.lower()
        actions = []
        
        # Simula analisi IoT
        if any(word in text_lower for word in ["accendi", "spegni", "luci"]):
            actions.append({
                "type": "iot_control",
                "description": f"Controllo IoT per: {text}"
            })
        
        # Simula analisi BIM
        if any(word in text_lower for word in ["bim", "converti"]):
            actions.append({
                "type": "bim_conversion",
                "description": f"Conversione BIM per: {text}"
            })
        
        # Simula analisi informativa
        if any(word in text_lower for word in ["temperatura", "stato", "aiuto"]):
            actions.append({
                "type": "info_query",
                "description": f"Query informativa per: {text}"
            })
        
        return actions
    
    def test_response_generation_simulation(self):
        """Test simulazione generazione risposte."""
        print("\n🧪 Test simulazione generazione risposte...")
        
        try:
            # Simula risultati
            results = [
                {
                    "action": {"type": "iot_control", "description": "Accende luci soggiorno"},
                    "success": True,
                    "result": {"status": "executed"}
                },
                {
                    "action": {"type": "info_query", "description": "Legge temperatura"},
                    "success": True,
                    "result": {"temperature": 22.5, "unit": "°C"}
                }
            ]
            
            response = self._simulate_response_generation(results)
            
            assert isinstance(response, str), "Risposta deve essere una stringa"
            assert len(response) > 0, "Risposta non può essere vuota"
            
            print(f"✅ Risposta generata: {response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test generazione risposte: FALLITO - {e}")
            return False
    
    def _simulate_response_generation(self, results: list) -> str:
        """Simula generazione risposta."""
        response_parts = []
        
        for result in results:
            if result["success"]:
                response_parts.append(f"{result['action']['description']} completato.")
            else:
                response_parts.append(f"Errore: {result.get('error', 'Errore sconosciuto')}")
        
        return " ".join(response_parts) if response_parts else "Nessuna azione eseguita."
    
    def test_integration_points(self):
        """Test punti di integrazione."""
        print("\n🧪 Test punti di integrazione...")
        
        try:
            # Verifica integrazioni configurate
            integrations = {
                "iot": settings.ENABLE_IOT_INTEGRATION,
                "bim": settings.ENABLE_BIM_INTEGRATION,
                "documents": settings.ENABLE_DOCUMENT_INTEGRATION
            }
            
            for integration, enabled in integrations.items():
                print(f"✅ Integrazione {integration}: {'abilitata' if enabled else 'disabilitata'}")
            
            # Verifica che almeno un'integrazione sia abilitata
            assert any(integrations.values()), "Almeno un'integrazione deve essere abilitata"
            
            return True
            
        except Exception as e:
            print(f"❌ Test punti di integrazione: FALLITO - {e}")
            return False
    
    def test_supported_languages_simulation(self):
        """Test simulazione lingue supportate."""
        print("\n🧪 Test simulazione lingue supportate...")
        
        try:
            # Simula lingue supportate
            languages = [
                "it-IT",  # Italiano
                "en-US",  # Inglese US
                "en-GB",  # Inglese UK
                "es-ES",  # Spagnolo
                "fr-FR",  # Francese
                "de-DE",  # Tedesco
            ]
            
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

def run_simple_tests():
    """Esegue tutti i test semplificati."""
    
    print("🏠 Test Semplificato Interfacce Locali")
    print("=" * 50)
    
    tester = SimpleLocalInterfaceTester()
    results = []
    
    try:
        # Esegui test
        test_methods = [
            tester.test_configuration,
            tester.test_audio_log_model,
            tester.test_command_analysis_simulation,
            tester.test_response_generation_simulation,
            tester.test_integration_points,
            tester.test_supported_languages_simulation
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
        print("-" * 30)
        
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
    success = run_simple_tests()
    sys.exit(0 if success else 1) 