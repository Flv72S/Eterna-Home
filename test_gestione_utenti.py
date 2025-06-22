#!/usr/bin/env python3
"""
Test di funzionalità per la gestione utenti
Verifica le funzionalità principali del sistema di gestione utenti
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

async def test_gestione_utenti():
    """Test completo delle funzionalità di gestione utenti"""
    
    print("=" * 60)
    print("TEST DI FUNZIONALITÀ - GESTIONE UTENTI")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        
        # 1. TEST REGISTRAZIONE UTENTE
        print("\n1. TEST REGISTRAZIONE UTENTE")
        print("-" * 30)
        
        user_data = {
            "email": f"test_user_{datetime.now().timestamp()}@example.com",
            "username": f"testuser_{datetime.now().timestamp()}",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
        
        try:
            response = await client.post(f"{BASE_URL}{API_PREFIX}/register", json=user_data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 201:
                print("✅ Registrazione utente: SUCCESSO")
                user_id = response.json().get("id")
            else:
                print("❌ Registrazione utente: FALLITO")
                return
                
        except Exception as e:
            print(f"❌ Errore durante la registrazione: {e}")
            return
        
        # 2. TEST LOGIN UTENTE
        print("\n2. TEST LOGIN UTENTE")
        print("-" * 30)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        try:
            response = await client.post(f"{BASE_URL}{API_PREFIX}/token", data=login_data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                print("✅ Login utente: SUCCESSO")
                print(f"Token ottenuto: {access_token[:20]}...")
            else:
                print(f"❌ Login utente: FALLITO - {response.json()}")
                return
                
        except Exception as e:
            print(f"❌ Errore durante il login: {e}")
            return
        
        # 3. TEST ACCESSO A RISORSE PROTETTE
        print("\n3. TEST ACCESSO A RISORSE PROTETTE")
        print("-" * 30)
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Test accesso alle case dell'utente
        try:
            response = await client.get(f"{BASE_URL}{API_PREFIX}/houses/", headers=headers)
            print(f"Status case: {response.status_code}")
            
            if response.status_code == 200:
                houses = response.json()
                print(f"✅ Accesso case: SUCCESSO - {len(houses)} case trovate")
            else:
                print(f"❌ Accesso case: FALLITO - {response.json()}")
                
        except Exception as e:
            print(f"❌ Errore accesso case: {e}")
        
        # Test accesso ai documenti dell'utente
        try:
            response = await client.get(f"{BASE_URL}{API_PREFIX}/documents/", headers=headers)
            print(f"Status documenti: {response.status_code}")
            
            if response.status_code == 200:
                documents = response.json()
                print(f"✅ Accesso documenti: SUCCESSO - {len(documents)} documenti trovati")
            else:
                print(f"❌ Accesso documenti: FALLITO - {response.json()}")
                
        except Exception as e:
            print(f"❌ Errore accesso documenti: {e}")
        
        # 4. TEST CREAZIONE RISORSE
        print("\n4. TEST CREAZIONE RISORSE")
        print("-" * 30)
        
        # Creazione di una casa
        house_data = {
            "name": "Casa Test",
            "address": "Via Test 123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}{API_PREFIX}/houses/", 
                                       json=house_data, headers=headers)
            print(f"Status creazione casa: {response.status_code}")
            
            if response.status_code == 201:
                house = response.json()
                house_id = house.get("id")
                print(f"✅ Creazione casa: SUCCESSO - ID: {house_id}")
            else:
                print(f"❌ Creazione casa: FALLITO - {response.json()}")
                house_id = None
                
        except Exception as e:
            print(f"❌ Errore creazione casa: {e}")
            house_id = None
        
        # 5. TEST ACCESSO SENZA TOKEN
        print("\n5. TEST ACCESSO SENZA TOKEN")
        print("-" * 30)
        
        try:
            response = await client.get(f"{BASE_URL}{API_PREFIX}/houses/")
            print(f"Status accesso senza token: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ Protezione endpoint: SUCCESSO - Accesso negato senza token")
            else:
                print(f"❌ Protezione endpoint: FALLITO - Status inaspettato: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Errore test protezione: {e}")
        
        # 6. TEST TOKEN INVALIDO
        print("\n6. TEST TOKEN INVALIDO")
        print("-" * 30)
        
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        try:
            response = await client.get(f"{BASE_URL}{API_PREFIX}/houses/", headers=invalid_headers)
            print(f"Status token invalido: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ Validazione token: SUCCESSO - Token invalido rifiutato")
            else:
                print(f"❌ Validazione token: FALLITO - Status inaspettato: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Errore test token invalido: {e}")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETATO")
        print("=" * 60)

if __name__ == "__main__":
    print("Avvio test di funzionalità per la gestione utenti...")
    print("Assicurati che il server sia in esecuzione su http://localhost:8000")
    
    try:
        asyncio.run(test_gestione_utenti())
    except KeyboardInterrupt:
        print("\nTest interrotto dall'utente")
    except Exception as e:
        print(f"Errore durante l'esecuzione del test: {e}") 