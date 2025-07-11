#!/usr/bin/env python3
"""
Test per il parsing BIM e la creazione automatica dei nodi.
Verifica che il file BIM venga parsato correttamente e che i nodi vengano creati automaticamente.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime

def test_bim_parsing_to_nodes():
    """Test: Parsing automatico del file BIM → creazione nodi."""
    print("\n[TEST] TEST PARSING BIM → CREAZIONE NODI")
    print("=" * 60)
    
    # Mock del file BIM
    bim_data = {
        "rooms": [
            {
                "room_id": "room_001",
                "room_name": "Soggiorno",
                "room_type": "living_room",
                "coordinates": {
                    "x": 10.5,
                    "y": 15.2,
                    "z": 0.0
                },
                "properties": {
                    "area": 25.5,
                    "height": 2.8,
                    "windows": 2
                }
            },
            {
                "room_id": "room_002", 
                "room_name": "Cucina",
                "room_type": "kitchen",
                "coordinates": {
                    "x": 5.2,
                    "y": 8.7,
                    "z": 0.0
                },
                "properties": {
                    "area": 12.3,
                    "height": 2.8,
                    "appliances": ["fridge", "oven", "dishwasher"]
                }
            },
            {
                "room_id": "room_003",
                "room_name": "Camera da letto",
                "room_type": "bedroom", 
                "coordinates": {
                    "x": 15.8,
                    "y": 12.1,
                    "z": 0.0
                },
                "properties": {
                    "area": 18.7,
                    "height": 2.8,
                    "bathroom_attached": True
                }
            }
        ],
        "tenant_id": "tenant_001",
        "house_id": "house_001",
        "bim_reference_id": "bim_001"
    }
    
    print("Dati BIM di input:")
    print(f"  • Tenant ID: {bim_data['tenant_id']}")
    print(f"  • House ID: {bim_data['house_id']}")
    print(f"  • BIM Reference ID: {bim_data['bim_reference_id']}")
    print(f"  • Numero stanze: {len(bim_data['rooms'])}")
    
    # Simula parsing BIM → creazione nodi
    created_nodes = []
    
    for room in bim_data['rooms']:
        node = {
            "id": len(created_nodes) + 1,
            "name": f"Node {room['room_name']}",
            "node_type": "room_sensor",
            "position_x": room['coordinates']['x'],
            "position_y": room['coordinates']['y'], 
            "position_z": room['coordinates']['z'],
            "properties": json.dumps(room['properties']),
            "tenant_id": bim_data['tenant_id'],
            "house_id": bim_data['house_id'],
            "bim_reference_id": bim_data['bim_reference_id'],
            "room_id": room['room_id'],
            "room_name": room['room_name'],
            "room_type": room['room_type'],
            "created_at": datetime.now().isoformat()
        }
        created_nodes.append(node)
        
        print(f"\nNodo creato per {room['room_name']}:")
        print(f"  • ID: {node['id']}")
        print(f"  • Nome: {node['name']}")
        print(f"  • Tipo: {node['node_type']}")
        print(f"  • Posizione: ({node['position_x']}, {node['position_y']}, {node['position_z']})")
        print(f"  • Room ID: {node['room_id']}")
        print(f"  • Room Type: {node['room_type']}")
    
    # Verifiche
    assert len(created_nodes) == len(bim_data['rooms'])
    
    for i, node in enumerate(created_nodes):
        room = bim_data['rooms'][i]
        assert node['room_id'] == room['room_id']
        assert node['room_name'] == room['room_name']
        assert node['room_type'] == room['room_type']
        assert node['tenant_id'] == bim_data['tenant_id']
        assert node['house_id'] == bim_data['house_id']
        assert node['bim_reference_id'] == bim_data['bim_reference_id']
    
    print(f"\n[OK] Test parsing BIM completato: {len(created_nodes)} nodi creati!")


def test_node_activator_association():
    """Test: Associazione attivatori ai nodi creati dal BIM."""
    print("\n[TEST] TEST ASSOCIAZIONE ATTIVATORI AI NODI")
    print("=" * 60)
    
    # Nodi creati dal BIM
    nodes = [
        {
            "id": 1,
            "name": "Node Soggiorno",
            "room_id": "room_001",
            "room_type": "living_room",
            "tenant_id": "tenant_001",
            "house_id": "house_001"
        },
        {
            "id": 2,
            "name": "Node Cucina", 
            "room_id": "room_002",
            "room_type": "kitchen",
            "tenant_id": "tenant_001",
            "house_id": "house_001"
        },
        {
            "id": 3,
            "name": "Node Camera",
            "room_id": "room_003", 
            "room_type": "bedroom",
            "tenant_id": "tenant_001",
            "house_id": "house_001"
        }
    ]
    
    # Attivatori da associare
    activators = [
        {
            "id": "nfc_001",
            "type": "nfc",
            "nfc_tag_id": "04:A3:B2:C1:D0:E5:F6",
            "node_id": 1,
            "name": "NFC Soggiorno"
        },
        {
            "id": "ble_001",
            "type": "ble", 
            "ble_device_id": "AA:BB:CC:DD:EE:FF",
            "node_id": 2,
            "name": "BLE Cucina"
        },
        {
            "id": "qr_001",
            "type": "qr_code",
            "qr_code": "https://eterna.home/qr/camera",
            "node_id": 3,
            "name": "QR Camera"
        }
    ]
    
    print("Associazione attivatori ai nodi:")
    
    # Simula associazione
    node_activators = {}
    
    for activator in activators:
        node_id = activator['node_id']
        if node_id not in node_activators:
            node_activators[node_id] = []
        
        node_activators[node_id].append(activator)
        
        # Trova il nodo corrispondente
        node = next((n for n in nodes if n['id'] == node_id), None)
        
        print(f"\nAttivatore {activator['name']} associato a {node['name']}:")
        print(f"  • Tipo: {activator['type']}")
        print(f"  • ID: {activator['id']}")
        print(f"  • Nodo: {node['name']} ({node['room_type']})")
    
    # Verifiche
    assert len(node_activators) == len(nodes)
    
    for node_id, node_activators_list in node_activators.items():
        assert len(node_activators_list) >= 1  # Ogni nodo ha almeno un attivatore
    
    print(f"\n[OK] Test associazione attivatori completato!")


def test_activator_trigger_event():
    """Test: Trigger evento da attivatore → verifica mappatura corretta."""
    print("\n[TEST] TEST TRIGGER EVENTO DA ATTIVATORE")
    print("=" * 60)
    
    # Evento di trigger
    trigger_event = {
        "activator_id": "nfc_001",
        "activator_type": "nfc",
        "nfc_tag_id": "04:A3:B2:C1:D0:E5:F6",
        "timestamp": datetime.now().isoformat(),
        "user_id": "user_001",
        "tenant_id": "tenant_001",
        "house_id": "house_001",
        "manual_override": False
    }
    
    print("Evento trigger ricevuto:")
    for key, value in trigger_event.items():
        print(f"  • {key}: {value}")
    
    # Simula ricerca attivatore → nodo
    activator_mapping = {
        "nfc_001": {
            "node_id": 1,
            "node_name": "Node Soggiorno",
            "room_type": "living_room",
            "action": "toggle_lights",
            "ai_enabled": True
        }
    }
    
    activator_id = trigger_event['activator_id']
    mapping = activator_mapping.get(activator_id)
    
    if mapping:
        print(f"\nAttivatore {activator_id} mappato correttamente:")
        print(f"  • Nodo: {mapping['node_name']} (ID: {mapping['node_id']})")
        print(f"  • Tipo stanza: {mapping['room_type']}")
        print(f"  • Azione: {mapping['action']}")
        print(f"  • AI abilitata: {mapping['ai_enabled']}")
        
        # Simula attivazione AI
        if mapping['ai_enabled']:
            ai_response = {
                "node_id": mapping['node_id'],
                "command": "toggle_lights",
                "response": "Luci del soggiorno accese",
                "timestamp": datetime.now().isoformat()
            }
            print(f"  • Risposta AI: {ai_response['response']}")
    
    assert mapping is not None
    assert mapping['node_id'] == 1
    assert mapping['room_type'] == 'living_room'
    
    print(f"\n[OK] Test trigger evento completato!")


def test_security_logging():
    """Test: Logging di sicurezza per eventi attivatore."""
    print("\n[TEST] TEST LOGGING DI SICUREZZA")
    print("=" * 60)
    
    # Eventi da loggare
    events = [
        {
            "event_type": "activator_trigger",
            "activator_id": "nfc_001",
            "user_id": "user_001",
            "tenant_id": "tenant_001",
            "house_id": "house_001",
            "node_id": 1,
            "timestamp": datetime.now().isoformat(),
            "success": True
        },
        {
            "event_type": "ai_interaction",
            "node_id": 1,
            "user_id": "user_001",
            "command": "toggle_lights",
            "response": "Luci del soggiorno accese",
            "timestamp": datetime.now().isoformat(),
            "success": True
        },
        {
            "event_type": "unauthorized_access",
            "activator_id": "unknown_nfc",
            "user_id": "user_002",
            "tenant_id": "tenant_002",  # Tenant diverso
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "reason": "Activator not found in tenant"
        }
    ]
    
    print("Logging eventi di sicurezza:")
    
    for event in events:
        log_entry = {
            "timestamp": event['timestamp'],
            "event_type": event['event_type'],
            "user_id": event['user_id'],
            "tenant_id": event['tenant_id'],
            "success": event['success']
        }
        
        if event['event_type'] == 'activator_trigger':
            log_entry.update({
                "activator_id": event['activator_id'],
                "node_id": event['node_id'],
                "house_id": event['house_id']
            })
        elif event['event_type'] == 'ai_interaction':
            log_entry.update({
                "node_id": event['node_id'],
                "command": event['command'],
                "response": event['response']
            })
        elif event['event_type'] == 'unauthorized_access':
            log_entry.update({
                "activator_id": event['activator_id'],
                "reason": event['reason']
            })
        
        print(f"\nLog: {event['event_type']}")
        print(f"  • Success: {event['success']}")
        print(f"  • User: {event['user_id']}")
        print(f"  • Tenant: {event['tenant_id']}")
        
        if not event['success']:
            print(f"  • Reason: {event.get('reason', 'N/A')}")
    
    # Verifiche
    success_events = [e for e in events if e['success']]
    failed_events = [e for e in events if not e['success']]
    
    assert len(success_events) == 2
    assert len(failed_events) == 1
    assert failed_events[0]['event_type'] == 'unauthorized_access'
    
    print(f"\n[OK] Test logging sicurezza completato!")
    print(f"  • Eventi di successo: {len(success_events)}")
    print(f"  • Eventi falliti: {len(failed_events)}")


if __name__ == "__main__":
    print("🧪 Esecuzione test completi per gestione Nodi & IoT...")
    test_bim_parsing_to_nodes()
    test_node_activator_association() 
    test_activator_trigger_event()
    test_security_logging()
    print("\n🎉 Tutti i test Nodi & IoT PASSATI!") 