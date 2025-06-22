#!/usr/bin/env python3
"""
Test di funzionalità per la gestione case e stanze
Verifica le funzionalità principali del sistema di gestione case e stanze
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

async def test_gestione_case_stanze():
    """Test completo delle funzionalità di gestione case e stanze"""
    
    print("=" * 60)
    print("TEST DI FUNZIONALITÀ - GESTIONE CASE E STANZE")
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
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/register", json=user_data)
        print(f"Registrazione utente: {response.status_code}")
        
        if response.status_code == 201:
            user_info = response.json()
            print(f"✅ Utente registrato con ID: {user_info['id']}")
        else:
            print(f"❌ Errore registrazione: {response.text}")
            return
        
        # 2. TEST LOGIN UTENTE
        print("\n2. TEST LOGIN UTENTE")
        print("-" * 30)
        
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/token", data=login_data)
        print(f"Login utente: {response.status_code}")
        
        if response.status_code == 200:
            token_info = response.json()
            access_token = token_info["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            print("✅ Login effettuato con successo")
        else:
            print(f"❌ Errore login: {response.text}")
            return
        
        # 3. TEST CREAZIONE CASA
        print("\n3. TEST CREAZIONE CASA")
        print("-" * 30)
        
        house_data = {
            "name": "Villa Test",
            "address": "Via Roma 123, Milano",
            "description": "Una bellissima villa di test"
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/houses/", json=house_data, headers=headers)
        print(f"Creazione casa: {response.status_code}")
        
        if response.status_code == 201:
            house_info = response.json()
            house_id = house_info["id"]
            print(f"✅ Casa creata con ID: {house_id}")
            print(f"   Nome: {house_info['name']}")
            print(f"   Indirizzo: {house_info['address']}")
        else:
            print(f"❌ Errore creazione casa: {response.text}")
            return
        
        # 4. TEST LETTURA CASA
        print("\n4. TEST LETTURA CASA")
        print("-" * 30)
        
        response = await client.get(f"{BASE_URL}{API_PREFIX}/houses/{house_id}", headers=headers)
        print(f"Lettura casa: {response.status_code}")
        
        if response.status_code == 200:
            house_detail = response.json()
            print(f"✅ Casa letta con successo")
            print(f"   Nome: {house_detail['name']}")
            print(f"   Indirizzo: {house_detail['address']}")
            print(f"   Proprietario: {house_detail['owner_id']}")
        else:
            print(f"❌ Errore lettura casa: {response.text}")
        
        # 5. TEST LISTA CASE
        print("\n5. TEST LISTA CASE")
        print("-" * 30)
        
        response = await client.get(f"{BASE_URL}{API_PREFIX}/houses/", headers=headers)
        print(f"Lista case: {response.status_code}")
        
        if response.status_code == 200:
            houses_list = response.json()
            print(f"✅ Lista case ottenuta con successo")
            print(f"   Numero case: {len(houses_list)}")
            for house in houses_list:
                print(f"   - {house['name']} (ID: {house['id']})")
        else:
            print(f"❌ Errore lista case: {response.text}")
        
        # 6. TEST AGGIORNAMENTO CASA
        print("\n6. TEST AGGIORNAMENTO CASA")
        print("-" * 30)
        
        update_data = {
            "name": "Villa Test Aggiornata",
            "description": "Descrizione aggiornata"
        }
        
        response = await client.put(f"{BASE_URL}{API_PREFIX}/houses/{house_id}", json=update_data, headers=headers)
        print(f"Aggiornamento casa: {response.status_code}")
        
        if response.status_code == 200:
            updated_house = response.json()
            print(f"✅ Casa aggiornata con successo")
            print(f"   Nuovo nome: {updated_house['name']}")
            print(f"   Nuova descrizione: {updated_house.get('description', 'N/A')}")
        else:
            print(f"❌ Errore aggiornamento casa: {response.text}")
        
        # 7. TEST CREAZIONE STANZA
        print("\n7. TEST CREAZIONE STANZA")
        print("-" * 30)
        
        room_data = {
            "name": "Camera da Letto",
            "description": "Camera principale",
            "floor": 1,
            "area": 25.5,
            "house_id": house_id
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/rooms/", json=room_data, headers=headers)
        print(f"Creazione stanza: {response.status_code}")
        
        if response.status_code == 201:
            room_info = response.json()
            room_id = room_info["id"]
            print(f"✅ Stanza creata con ID: {room_id}")
            print(f"   Nome: {room_info['name']}")
            print(f"   Piano: {room_info['floor']}")
            print(f"   Area: {room_info['area']} m²")
        else:
            print(f"❌ Errore creazione stanza: {response.text}")
            room_id = None
        
        # 8. TEST LETTURA STANZA
        if room_id:
            print("\n8. TEST LETTURA STANZA")
            print("-" * 30)
            
            response = await client.get(f"{BASE_URL}{API_PREFIX}/rooms/{room_id}", headers=headers)
            print(f"Lettura stanza: {response.status_code}")
            
            if response.status_code == 200:
                room_detail = response.json()
                print(f"✅ Stanza letta con successo")
                print(f"   Nome: {room_detail['name']}")
                print(f"   Piano: {room_detail['floor']}")
                print(f"   Area: {room_detail['area']} m²")
                print(f"   Casa: {room_detail['house_id']}")
            else:
                print(f"❌ Errore lettura stanza: {response.text}")
        
        # 9. TEST LISTA STANZE
        print("\n9. TEST LISTA STANZE")
        print("-" * 30)
        
        response = await client.get(f"{BASE_URL}{API_PREFIX}/rooms/", headers=headers)
        print(f"Lista stanze: {response.status_code}")
        
        if response.status_code == 200:
            rooms_list = response.json()
            print(f"✅ Lista stanze ottenuta con successo")
            print(f"   Numero stanze: {len(rooms_list)}")
            for room in rooms_list:
                print(f"   - {room['name']} (ID: {room['id']}, Piano: {room['floor']})")
        else:
            print(f"❌ Errore lista stanze: {response.text}")
        
        # 10. TEST FILTRO STANZE PER CASA
        print("\n10. TEST FILTRO STANZE PER CASA")
        print("-" * 30)
        
        response = await client.get(f"{BASE_URL}{API_PREFIX}/rooms/?house_id={house_id}", headers=headers)
        print(f"Filtro stanze per casa: {response.status_code}")
        
        if response.status_code == 200:
            filtered_rooms = response.json()
            print(f"✅ Filtro stanze per casa effettuato con successo")
            print(f"   Numero stanze nella casa: {len(filtered_rooms)}")
            for room in filtered_rooms:
                print(f"   - {room['name']} (Piano: {room['floor']})")
        else:
            print(f"❌ Errore filtro stanze: {response.text}")
        
        # 11. TEST AGGIORNAMENTO STANZA
        if room_id:
            print("\n11. TEST AGGIORNAMENTO STANZA")
            print("-" * 30)
            
            room_update_data = {
                "name": "Camera da Letto Principale",
                "area": 30.0
            }
            
            response = await client.put(f"{BASE_URL}{API_PREFIX}/rooms/{room_id}", json=room_update_data, headers=headers)
            print(f"Aggiornamento stanza: {response.status_code}")
            
            if response.status_code == 200:
                updated_room = response.json()
                print(f"✅ Stanza aggiornata con successo")
                print(f"   Nuovo nome: {updated_room['name']}")
                print(f"   Nuova area: {updated_room['area']} m²")
            else:
                print(f"❌ Errore aggiornamento stanza: {response.text}")
        
        # 12. TEST ELIMINAZIONE STANZA
        if room_id:
            print("\n12. TEST ELIMINAZIONE STANZA")
            print("-" * 30)
            
            response = await client.delete(f"{BASE_URL}{API_PREFIX}/rooms/{room_id}", headers=headers)
            print(f"Eliminazione stanza: {response.status_code}")
            
            if response.status_code == 204:
                print("✅ Stanza eliminata con successo")
            else:
                print(f"❌ Errore eliminazione stanza: {response.text}")
        
        # 13. TEST ELIMINAZIONE CASA
        print("\n13. TEST ELIMINAZIONE CASA")
        print("-" * 30)
        
        response = await client.delete(f"{BASE_URL}{API_PREFIX}/houses/{house_id}", headers=headers)
        print(f"Eliminazione casa: {response.status_code}")
        
        if response.status_code == 204:
            print("✅ Casa eliminata con successo")
        else:
            print(f"❌ Errore eliminazione casa: {response.text}")
        
        # 14. TEST VERIFICA ELIMINAZIONE
        print("\n14. TEST VERIFICA ELIMINAZIONE")
        print("-" * 30)
        
        response = await client.get(f"{BASE_URL}{API_PREFIX}/houses/{house_id}", headers=headers)
        print(f"Verifica eliminazione casa: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Casa eliminata correttamente (404 Not Found)")
        else:
            print(f"⚠️ Casa ancora presente: {response.status_code}")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETATO")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_gestione_case_stanze()) 