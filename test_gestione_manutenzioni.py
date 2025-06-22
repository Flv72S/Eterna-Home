#!/usr/bin/env python3
"""
Test di funzionalità per la gestione manutenzioni
"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

async def test_gestione_manutenzioni():
    """Test completo delle funzionalità di gestione manutenzioni"""
    
    print("=" * 60)
    print("TEST DI FUNZIONALITÀ - GESTIONE MANUTENZIONI")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        
        # 1. Registrazione utente
        print("\n1. TEST REGISTRAZIONE UTENTE")
        user_data = {
            "email": f"test_maintenance_{datetime.now().timestamp()}@example.com",
            "username": f"testmaintenance_{datetime.now().timestamp()}",
            "password": "TestPassword123!",
            "full_name": "Test Maintenance User"
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=user_data)
        print(f"Registrazione: {response.status_code}")
        assert response.status_code == 201
        
        # 2. Login utente
        print("\n2. TEST LOGIN UTENTE")
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/auth/login", data=login_data)
        print(f"Login: {response.status_code}")
        assert response.status_code == 200
        
        token_data = response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Creazione casa
        print("\n3. TEST CREAZIONE CASA")
        house_data = {
            "name": "Casa Test Manutenzioni",
            "address": "Via Test Manutenzioni 123"
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/houses/", json=house_data, headers=headers)
        print(f"Creazione casa: {response.status_code}")
        assert response.status_code == 201
        
        house = response.json()
        house_id = house["id"]
        
        # 4. Creazione stanza
        print("\n4. TEST CREAZIONE STANZA")
        room_data = {
            "name": "Stanza Test Manutenzioni",
            "description": "Stanza per test manutenzioni",
            "floor": 1,
            "area": 25.5,
            "house_id": house_id
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/rooms/", json=room_data, headers=headers)
        print(f"Creazione stanza: {response.status_code}")
        assert response.status_code == 201
        
        room = response.json()
        room_id = room["id"]
        
        # 5. Creazione nodo IoT
        print("\n5. TEST CREAZIONE NODO IoT")
        node_data = {
            "name": "Nodo Test Manutenzioni",
            "description": "Nodo IoT per test manutenzioni",
            "nfc_id": f"NFC_MAINT_{datetime.now().timestamp()}",
            "house_id": house_id,
            "room_id": room_id
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/nodes/", json=node_data, headers=headers)
        print(f"Creazione nodo: {response.status_code}")
        assert response.status_code == 201
        
        node = response.json()
        node_id = node["id"]
        
        # 6. Creazione record di manutenzione
        print("\n6. TEST CREAZIONE RECORD MANUTENZIONE")
        maintenance_data = {
            "node_id": node_id,
            "timestamp": datetime.now().isoformat(),
            "maintenance_type": "ROUTINE",
            "description": "Test manutenzione routine",
            "status": "PENDING",
            "notes": "Note di test per manutenzione"
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/maintenance/", json=maintenance_data, headers=headers)
        print(f"Creazione manutenzione: {response.status_code}")
        assert response.status_code == 201
        
        maintenance = response.json()
        maintenance_id = maintenance["id"]
        
        # 7. Lettura record di manutenzione
        print("\n7. TEST LETTURA RECORD MANUTENZIONE")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/maintenance/{maintenance_id}", headers=headers)
        print(f"Lettura manutenzione: {response.status_code}")
        assert response.status_code == 200
        
        maintenance_read = response.json()
        assert maintenance_read["id"] == maintenance_id
        assert maintenance_read["description"] == "Test manutenzione routine"
        
        # 8. Aggiornamento record di manutenzione
        print("\n8. TEST AGGIORNAMENTO RECORD MANUTENZIONE")
        update_data = {
            "status": "COMPLETED",
            "notes": "Manutenzione completata con successo"
        }
        
        response = await client.put(f"{BASE_URL}{API_PREFIX}/maintenance/{maintenance_id}", json=update_data, headers=headers)
        print(f"Aggiornamento manutenzione: {response.status_code}")
        assert response.status_code == 200
        
        maintenance_updated = response.json()
        assert maintenance_updated["status"] == "COMPLETED"
        
        # 9. Lista record di manutenzione
        print("\n9. TEST LISTA RECORD MANUTENZIONI")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/maintenance/", headers=headers)
        print(f"Lista manutenzioni: {response.status_code}")
        assert response.status_code == 200
        
        maintenance_list = response.json()
        assert len(maintenance_list) > 0
        
        # 10. Ricerca manutenzioni per nodo
        print("\n10. TEST RICERCA MANUTENZIONI PER NODO")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/maintenance/search?node_id={node_id}", headers=headers)
        print(f"Ricerca per nodo: {response.status_code}")
        assert response.status_code == 200
        
        search_results = response.json()
        assert len(search_results) > 0
        
        # 11. Ricerca manutenzioni per stato
        print("\n11. TEST RICERCA MANUTENZIONI PER STATO")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/maintenance/search?status=COMPLETED", headers=headers)
        print(f"Ricerca per stato: {response.status_code}")
        assert response.status_code == 200
        
        status_results = response.json()
        assert len(status_results) > 0
        
        # 12. Eliminazione record di manutenzione
        print("\n12. TEST ELIMINAZIONE RECORD MANUTENZIONE")
        response = await client.delete(f"{BASE_URL}{API_PREFIX}/maintenance/{maintenance_id}", headers=headers)
        print(f"Eliminazione manutenzione: {response.status_code}")
        assert response.status_code == 200
        
        # 13. Verifica eliminazione
        response = await client.get(f"{BASE_URL}{API_PREFIX}/maintenance/{maintenance_id}", headers=headers)
        print(f"Verifica eliminazione: {response.status_code}")
        assert response.status_code == 404
        
        print("\n" + "=" * 60)
        print("✅ TUTTI I TEST DI GESTIONE MANUTENZIONI SUPERATI!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_gestione_manutenzioni()) 