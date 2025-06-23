#!/usr/bin/env python3
"""
Script di test per le API vocali di Eterna-Home.
Testa tutti gli endpoint per la gestione dei comandi vocali.
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Credenziali di test (sostituisci con credenziali reali)
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class VoiceAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_user_id = None
        self.test_house_id = None
        self.test_node_id = None
        self.test_audio_log_id = None
    
    def login(self):
        """Effettua il login e ottiene il token di accesso."""
        print("🔐 Effettuando login...")
        
        login_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            print("✅ Login effettuato con successo")
            return True
        else:
            print(f"❌ Login fallito: {response.status_code} - {response.text}")
            return False
    
    def get_test_data(self):
        """Ottiene dati di test (utente, casa, nodo) per i test."""
        print("📋 Ottenendo dati di test...")
        
        # Ottieni utente corrente
        response = self.session.get(f"{API_BASE}/users/me")
        if response.status_code == 200:
            user_data = response.json()
            self.test_user_id = user_data["id"]
            print(f"✅ Utente di test: {user_data['username']} (ID: {self.test_user_id})")
        
        # Ottieni case dell'utente
        response = self.session.get(f"{API_BASE}/houses/")
        if response.status_code == 200:
            houses = response.json()["items"]
            if houses:
                self.test_house_id = houses[0]["id"]
                print(f"✅ Casa di test: {houses[0]['name']} (ID: {self.test_house_id})")
        
        # Ottieni nodi della casa
        if self.test_house_id:
            response = self.session.get(f"{API_BASE}/nodes/?house_id={self.test_house_id}")
            if response.status_code == 200:
                nodes = response.json()["items"]
                if nodes:
                    self.test_node_id = nodes[0]["id"]
                    print(f"✅ Nodo di test: {nodes[0]['name']} (ID: {self.test_node_id})")
    
    def test_create_voice_command_text(self):
        """Test 3.3.2.1: POST /voice/commands - Success con testo."""
        print("\n🧪 Test 3.3.2.1: Creazione comando vocale (testo)")
        
        command_data = {
            "transcribed_text": "Accendi la luce in cucina",
            "node_id": self.test_node_id,
            "house_id": self.test_house_id
        }
        
        response = self.session.post(f"{API_BASE}/voice/commands", json=command_data)
        
        if response.status_code == 202:
            data = response.json()
            self.test_audio_log_id = data["request_id"].split("-")[1]
            print(f"✅ Comando vocale creato: {data['request_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Messaggio: {data['message']}")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_create_voice_command_unauthorized(self):
        """Test 3.3.2.2: POST /voice/commands - Unauthorized."""
        print("\n🧪 Test 3.3.2.2: Creazione comando vocale (non autorizzato)")
        
        # Rimuovi il token di autorizzazione
        original_headers = self.session.headers.copy()
        self.session.headers.pop("Authorization", None)
        
        command_data = {
            "transcribed_text": "Accendi la luce",
            "house_id": self.test_house_id
        }
        
        response = self.session.post(f"{API_BASE}/voice/commands", json=command_data)
        
        # Ripristina il token
        self.session.headers.update(original_headers)
        
        if response.status_code == 401:
            print("✅ Accesso negato correttamente (401 Unauthorized)")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_get_audio_logs(self):
        """Test: GET /voice/logs - Lista AudioLog."""
        print("\n🧪 Test: Ottieni lista AudioLog")
        
        response = self.session.get(f"{API_BASE}/voice/logs")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AudioLog trovati: {data['total']}")
            print(f"   Pagina: {data['page']}/{data['pages']}")
            print(f"   Elementi per pagina: {data['size']}")
            
            if data["items"]:
                log = data["items"][0]
                print(f"   Primo log: ID {log['id']}, Status: {log['processing_status']}")
            
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_get_audio_log_by_id(self):
        """Test: GET /voice/logs/{id} - AudioLog specifico."""
        print("\n🧪 Test: Ottieni AudioLog specifico")
        
        if not self.test_audio_log_id:
            print("⚠️  Nessun AudioLog ID disponibile per il test")
            return False
        
        response = self.session.get(f"{API_BASE}/voice/logs/{self.test_audio_log_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AudioLog trovato: ID {data['id']}")
            print(f"   Testo: {data['transcribed_text']}")
            print(f"   Status: {data['processing_status']}")
            print(f"   Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_update_audio_log(self):
        """Test: PUT /voice/logs/{id} - Aggiorna AudioLog."""
        print("\n🧪 Test: Aggiorna AudioLog")
        
        if not self.test_audio_log_id:
            print("⚠️  Nessun AudioLog ID disponibile per il test")
            return False
        
        update_data = {
            "response_text": "Luce in cucina accesa con successo",
            "processing_status": "completed"
        }
        
        response = self.session.put(f"{API_BASE}/voice/logs/{self.test_audio_log_id}", json=update_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AudioLog aggiornato: ID {data['id']}")
            print(f"   Nuovo status: {data['processing_status']}")
            print(f"   Risposta: {data['response_text']}")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_get_processing_statuses(self):
        """Test: GET /voice/statuses - Stati di elaborazione."""
        print("\n🧪 Test: Ottieni stati di elaborazione")
        
        response = self.session.get(f"{API_BASE}/voice/statuses")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stati disponibili: {len(data['statuses'])}")
            for status in data["statuses"]:
                desc = data["descriptions"].get(status, "N/A")
                print(f"   - {status}: {desc}")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_get_voice_stats(self):
        """Test: GET /voice/stats - Statistiche vocali."""
        print("\n🧪 Test: Ottieni statistiche vocali")
        
        response = self.session.get(f"{API_BASE}/voice/stats")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statistiche ottenute:")
            print(f"   Comandi totali: {data['total_commands']}")
            print(f"   Breakdown per stato: {data['status_breakdown']}")
            if data['house_breakdown']:
                print(f"   Breakdown per casa: {data['house_breakdown']}")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_filters(self):
        """Test: Filtri per AudioLog."""
        print("\n🧪 Test: Filtri AudioLog")
        
        # Test filtro per casa
        if self.test_house_id:
            response = self.session.get(f"{API_BASE}/voice/logs?house_id={self.test_house_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Filtro per casa: {data['total']} log trovati")
        
        # Test filtro per stato
        response = self.session.get(f"{API_BASE}/voice/logs?status=completed")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtro per stato 'completed': {data['total']} log trovati")
        
        # Test paginazione
        response = self.session.get(f"{API_BASE}/voice/logs?page=1&size=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Paginazione: pagina {data['page']}, {len(data['items'])} elementi")
        
        return True
    
    def run_all_tests(self):
        """Esegue tutti i test."""
        print("🚀 Avvio test API vocali per Eterna-Home")
        print("=" * 60)
        
        # Login
        if not self.login():
            return False
        
        # Ottieni dati di test
        self.get_test_data()
        
        # Esegui test
        tests = [
            ("Creazione comando vocale (testo)", self.test_create_voice_command_text),
            ("Creazione comando vocale (non autorizzato)", self.test_create_voice_command_unauthorized),
            ("Lista AudioLog", self.test_get_audio_logs),
            ("AudioLog specifico", self.test_get_audio_log_by_id),
            ("Aggiorna AudioLog", self.test_update_audio_log),
            ("Stati di elaborazione", self.test_get_processing_statuses),
            ("Statistiche vocali", self.test_get_voice_stats),
            ("Filtri AudioLog", self.test_filters),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    print(f"❌ Test '{test_name}' fallito")
            except Exception as e:
                print(f"❌ Test '{test_name}' fallito con errore: {e}")
        
        # Risultati
        print("\n" + "=" * 60)
        print(f"📊 RISULTATI TEST: {passed}/{total} test passati")
        
        if passed == total:
            print("🎉 Tutti i test sono passati!")
        else:
            print(f"⚠️  {total - passed} test falliti")
        
        return passed == total

if __name__ == "__main__":
    tester = VoiceAPITester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n💡 Suggerimenti:")
        print("1. Assicurati che il server sia in esecuzione su localhost:8000")
        print("2. Verifica che le credenziali di test siano corrette")
        print("3. Controlla che la tabella audio_logs sia stata creata")
        print("4. Verifica che ci siano utenti, case e nodi nel database")
    
    exit(0 if success else 1) 