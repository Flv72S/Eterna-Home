#!/usr/bin/env python3
"""
Script di test manuale per la gestione dei nodi IoT
Testa tutte le operazioni CRUD sui nodi IoT tramite chiamate HTTP reali
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

# Configurazione
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

async def test_gestione_nodi_iot():
    """Test completo della gestione nodi IoT"""
    print("=== TEST GESTIONE NODI IoT ===")
    
    async with httpx.AsyncClient() as client:
        # 1. Login come utente
        print("\n1. TEST LOGIN UTENTE")
        login_data = {
            "username": "admin@example.com",
            "password": "admin123"
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/auth/token", data=login_data)
        print(f"Login: {response.status_code}")
        assert response.status_code == 200
        
        token_data = response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Creazione casa
        print("\n2. TEST CREAZIONE CASA")
        house_data = {
            "name": "Casa Test Nodi IoT",
            "address": "Via Test Nodi IoT, 123"
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/houses/", json=house_data, headers=headers)
        print(f"Creazione casa: {response.status_code}")
        assert response.status_code == 201
        
        house = response.json()
        house_id = house["id"]
        
        # 3. Creazione stanza
        print("\n3. TEST CREAZIONE STANZA")
        room_data = {
            "name": "Stanza Test Nodi IoT",
            "description": "Stanza per test nodi IoT",
            "floor": 1,
            "area": 30.0,
            "house_id": house_id
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/rooms/", json=room_data, headers=headers)
        print(f"Creazione stanza: {response.status_code}")
        assert response.status_code == 201
        
        room = response.json()
        room_id = room["id"]
        
        # 4. Creazione nodo IoT
        print("\n4. TEST CREAZIONE NODO IoT")
        node_data = {
            "name": "Nodo IoT Test",
            "description": "Nodo IoT per test funzionalità",
            "nfc_id": f"NFC_IOT_{datetime.now().timestamp()}",
            "house_id": house_id,
            "room_id": room_id
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/nodes/", json=node_data, headers=headers)
        print(f"Creazione nodo: {response.status_code}")
        assert response.status_code == 200
        
        node = response.json()
        node_id = node["id"]
        assert node["name"] == "Nodo IoT Test"
        assert node["nfc_id"] == node_data["nfc_id"]
        
        # 5. Lettura nodo IoT
        print("\n5. TEST LETTURA NODO IoT")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/nodes/{node_id}", headers=headers)
        print(f"Lettura nodo: {response.status_code}")
        assert response.status_code == 200
        
        node_read = response.json()
        assert node_read["id"] == node_id
        assert node_read["name"] == "Nodo IoT Test"
        
        # 6. Aggiornamento nodo IoT
        print("\n6. TEST AGGIORNAMENTO NODO IoT")
        update_data = {
            "name": "Nodo IoT Aggiornato",
            "description": "Nodo IoT aggiornato per test"
        }
        
        response = await client.put(f"{BASE_URL}{API_PREFIX}/nodes/{node_id}", json=update_data, headers=headers)
        print(f"Aggiornamento nodo: {response.status_code}")
        assert response.status_code == 200
        
        node_updated = response.json()
        assert node_updated["name"] == "Nodo IoT Aggiornato"
        
        # 7. Lista nodi IoT
        print("\n7. TEST LISTA NODI IoT")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/nodes/", headers=headers)
        print(f"Lista nodi: {response.status_code}")
        assert response.status_code == 200
        
        nodes_list = response.json()
        assert len(nodes_list) > 0
        
        # 8. Filtro nodi per casa
        print("\n8. TEST FILTRO NODI PER CASA")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/nodes/?house_id={house_id}", headers=headers)
        print(f"Filtro per casa: {response.status_code}")
        assert response.status_code == 200
        
        filtered_nodes = response.json()
        assert len(filtered_nodes) > 0
        assert all(node["house_id"] == house_id for node in filtered_nodes)
        
        # 9. Creazione secondo nodo IoT
        print("\n9. TEST CREAZIONE SECONDO NODO IoT")
        node2_data = {
            "name": "Nodo IoT Secondo",
            "description": "Secondo nodo IoT per test",
            "nfc_id": f"NFC_IOT_2_{datetime.now().timestamp()}",
            "house_id": house_id,
            "room_id": room_id
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/nodes/", json=node2_data, headers=headers)
        print(f"Creazione secondo nodo: {response.status_code}")
        assert response.status_code == 200
        
        node2 = response.json()
        node2_id = node2["id"]
        
        # 10. Test duplicato NFC ID
        print("\n10. TEST DUPLICATO NFC ID")
        duplicate_data = {
            "name": "Nodo Duplicato",
            "description": "Test duplicato NFC ID",
            "nfc_id": node_data["nfc_id"],  # Stesso NFC ID del primo nodo
            "house_id": house_id,
            "room_id": room_id
        }
        
        response = await client.post(f"{BASE_URL}{API_PREFIX}/nodes/", json=duplicate_data, headers=headers)
        print(f"Test duplicato NFC ID: {response.status_code}")
        assert response.status_code == 400  # Dovrebbe fallire
        
        # 11. Eliminazione nodi IoT
        print("\n11. TEST ELIMINAZIONE NODI IoT")
        
        # Elimina il secondo nodo
        response = await client.delete(f"{BASE_URL}{API_PREFIX}/nodes/{node2_id}", headers=headers)
        print(f"Eliminazione secondo nodo: {response.status_code}")
        assert response.status_code == 200
        
        # Verifica che sia stato eliminato
        response = await client.get(f"{BASE_URL}{API_PREFIX}/nodes/{node2_id}", headers=headers)
        print(f"Verifica eliminazione: {response.status_code}")
        assert response.status_code == 404
        
        # Elimina il primo nodo
        response = await client.delete(f"{BASE_URL}{API_PREFIX}/nodes/{node_id}", headers=headers)
        print(f"Eliminazione primo nodo: {response.status_code}")
        assert response.status_code == 200
        
        # 12. Test accesso non autenticato
        print("\n12. TEST ACCESSO NON AUTENTICATO")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/nodes/")
        print(f"Accesso non autenticato: {response.status_code}")
        assert response.status_code == 401
        
        print("\n=== TUTTI I TEST NODI IoT COMPLETATI CON SUCCESSO ===")

if __name__ == "__main__":
    asyncio.run(test_gestione_nodi_iot()) 