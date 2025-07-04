#!/usr/bin/env python3
"""
Script di test per le funzionalità di prenotazione di Eterna-Home.
Testa la creazione, gestione e operazioni sulle prenotazioni.
"""

import requests
import json
from datetime import datetime, timedelta

# Configurazione
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Credenziali di test
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class BookingAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_user_id = None
        self.test_house_id = None
        self.test_room_id = None
        self.test_booking_id = None
    
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
        """Ottiene dati di test (utente, casa, stanza) per i test."""
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
        
        # Ottieni stanze della casa
        if self.test_house_id:
            response = self.session.get(f"{API_BASE}/rooms/?house_id={self.test_house_id}")
            if response.status_code == 200:
                rooms = response.json()["items"]
                if rooms:
                    self.test_room_id = rooms[0]["id"]
                    print(f"✅ Stanza di test: {rooms[0]['name']} (ID: {self.test_room_id})")
    
    def test_create_booking(self):
        """Test: Creazione prenotazione."""
        print("\n🧪 Test: Creazione prenotazione")
        
        if not self.test_room_id:
            print("⚠️  Nessuna stanza disponibile per il test")
            return False
        
        # Date di test (prossima settimana)
        start_date = datetime.now() + timedelta(days=7)
        end_date = start_date + timedelta(days=3)
        
        booking_data = {
            "title": "Test Prenotazione",
            "description": "Prenotazione di test per Eterna-Home",
            "room_id": self.test_room_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": "confirmed"
        }
        
        response = self.session.post(f"{API_BASE}/bookings/", json=booking_data)
        
        if response.status_code == 201:
            data = response.json()
            self.test_booking_id = data["id"]
            print(f"✅ Prenotazione creata: ID {data['id']}")
            print(f"   Titolo: {data['title']}")
            print(f"   Stanza: {data['room_id']}")
            print(f"   Data inizio: {data['start_date']}")
            print(f"   Data fine: {data['end_date']}")
            print(f"   Stato: {data['status']}")
            return True
        else:
            print(f"❌ Errore creazione: {response.status_code} - {response.text}")
            return False
    
    def test_get_bookings(self):
        """Test: Lista prenotazioni."""
        print("\n🧪 Test: Lista prenotazioni")
        
        response = self.session.get(f"{API_BASE}/bookings/")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Prenotazioni trovate: {data['total']}")
            print(f"   Pagina: {data['page']}/{data['pages']}")
            print(f"   Elementi per pagina: {data['size']}")
            
            if data["items"]:
                booking = data["items"][0]
                print(f"   Prima prenotazione: {booking['title']} ({booking['status']})")
            
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_get_booking_by_id(self):
        """Test: Prenotazione specifica."""
        print("\n🧪 Test: Prenotazione specifica")
        
        if not self.test_booking_id:
            print("⚠️  Nessuna prenotazione disponibile per il test")
            return False
        
        response = self.session.get(f"{API_BASE}/bookings/{self.test_booking_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Prenotazione trovata: ID {data['id']}")
            print(f"   Titolo: {data['title']}")
            print(f"   Descrizione: {data['description']}")
            print(f"   Stato: {data['status']}")
            print(f"   Data inizio: {data['start_date']}")
            print(f"   Data fine: {data['end_date']}")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_update_booking(self):
        """Test: Aggiornamento prenotazione."""
        print("\n🧪 Test: Aggiornamento prenotazione")
        
        if not self.test_booking_id:
            print("⚠️  Nessuna prenotazione disponibile per il test")
            return False
        
        update_data = {
            "title": "Test Prenotazione Aggiornata",
            "description": "Prenotazione aggiornata per Eterna-Home",
            "status": "confirmed"
        }
        
        response = self.session.put(f"{API_BASE}/bookings/{self.test_booking_id}", json=update_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Prenotazione aggiornata: ID {data['id']}")
            print(f"   Nuovo titolo: {data['title']}")
            print(f"   Nuova descrizione: {data['description']}")
            print(f"   Stato: {data['status']}")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    
    def test_booking_validation(self):
        """Test: Validazioni prenotazione."""
        print("\n🧪 Test: Validazioni prenotazione")
        
        if not self.test_room_id:
            print("⚠️  Nessuna stanza disponibile per il test")
            return False
        
        # Test: data fine precedente a data inizio
        start_date = datetime.now() + timedelta(days=7)
        end_date = start_date - timedelta(days=1)  # Data fine precedente
        
        invalid_booking = {
            "title": "Test Prenotazione Invalida",
            "room_id": self.test_room_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        response = self.session.post(f"{API_BASE}/bookings/", json=invalid_booking)
        
        if response.status_code == 400:
            print("✅ Validazione date: rifiutata correttamente")
            return True
        else:
            print(f"❌ Validazione date: accettata erroneamente ({response.status_code})")
            return False
    
    def test_booking_conflicts(self):
        """Test: Conflitti prenotazione."""
        print("\n🧪 Test: Conflitti prenotazione")
        
        if not self.test_room_id:
            print("⚠️  Nessuna stanza disponibile per il test")
            return False
        
        # Crea prima prenotazione
        start_date1 = datetime.now() + timedelta(days=10)
        end_date1 = start_date1 + timedelta(days=5)
        
        booking1 = {
            "title": "Prenotazione 1",
            "room_id": self.test_room_id,
            "start_date": start_date1.isoformat(),
            "end_date": end_date1.isoformat()
        }
        
        response1 = self.session.post(f"{API_BASE}/bookings/", json=booking1)
        
        if response1.status_code != 201:
            print("❌ Errore creazione prima prenotazione")
            return False
        
        # Crea seconda prenotazione sovrapposta
        start_date2 = start_date1 + timedelta(days=2)  # Sovrapposta
        end_date2 = end_date1 + timedelta(days=2)
        
        booking2 = {
            "title": "Prenotazione 2 (Conflitto)",
            "room_id": self.test_room_id,
            "start_date": start_date2.isoformat(),
            "end_date": end_date2.isoformat()
        }
        
        response2 = self.session.post(f"{API_BASE}/bookings/", json=booking2)
        
        if response2.status_code == 400:
            print("✅ Conflitto prenotazione: rilevato correttamente")
            return True
        else:
            print(f"❌ Conflitto prenotazione: non rilevato ({response2.status_code})")
            return False
    
    def test_booking_filters(self):
        """Test: Filtri prenotazione."""
        print("\n🧪 Test: Filtri prenotazione")
        
        # Test filtro per stanza
        if self.test_room_id:
            response = self.session.get(f"{API_BASE}/bookings/?room_id={self.test_room_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Filtro per stanza: {data['total']} prenotazioni")
        
        # Test filtro per stato
        response = self.session.get(f"{API_BASE}/bookings/?status=confirmed")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtro per stato 'confirmed': {data['total']} prenotazioni")
        
        # Test paginazione
        response = self.session.get(f"{API_BASE}/bookings/?page=1&size=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Paginazione: pagina {data['page']}, {len(data['items'])} elementi")
        
        return True
    
    def run_all_tests(self):
        """Esegue tutti i test di prenotazione."""
        print("🚀 Avvio test API Prenotazioni per Eterna-Home")
        print("=" * 50)
        
        # Login
        if not self.login():
            return False
        
        # Ottieni dati di test
        self.get_test_data()
        
        # Esegui test
        tests = [
            ("Creazione prenotazione", self.test_create_booking),
            ("Lista prenotazioni", self.test_get_bookings),
            ("Prenotazione specifica", self.test_get_booking_by_id),
            ("Aggiornamento prenotazione", self.test_update_booking),
            ("Validazioni prenotazione", self.test_booking_validation),
            ("Conflitti prenotazione", self.test_booking_conflicts),
            ("Filtri prenotazione", self.test_booking_filters),
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
        print("\n" + "=" * 50)
        print(f"📊 RISULTATI TEST: {passed}/{total} test passati")
        
        if passed == total:
            print("🎉 Tutti i test di prenotazione sono passati!")
        else:
            print(f"⚠️  {total - passed} test falliti")
        
        return passed == total

if __name__ == "__main__":
    tester = BookingAPITester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n💡 Suggerimenti:")
        print("1. Assicurati che il server sia in esecuzione su localhost:8000")
        print("2. Verifica che le credenziali di test siano corrette")
        print("3. Controlla che ci siano case e stanze nel database")
        print("4. Verifica che le validazioni delle date funzionino correttamente")
    
    exit(0 if success else 1) 