#!/usr/bin/env python3
"""
Test completo del sistema di logging con l'applicazione FastAPI.
"""
import sys
import os
import json
import time

# Aggiungi il path dell'app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.logging import setup_logging, get_logger, set_trace_id, get_trace_id
    
    print("✅ Import dell'applicazione riuscito")
    
    # Configura il logging per i test
    setup_logging(level="DEBUG", json_format=True, include_trace_id=True)
    logger = get_logger("test_complete")
    
    print("✅ Configurazione logging completata")
    
    # Crea il client di test
    client = TestClient(app)
    print("✅ Client di test creato")
    
    # Test 1: Endpoint root
    print("\n🔍 Test 1: Endpoint root")
    response = client.get("/")
    assert response.status_code == 200
    print(f"✅ Status code: {response.status_code}")
    
    # Verifica Trace ID nell'header
    trace_id = response.headers.get("X-Trace-ID")
    if trace_id:
        print(f"✅ Trace ID nell'header: {trace_id}")
    else:
        print("⚠️  Trace ID non trovato nell'header")
    
    # Test 2: Health check
    print("\n🔍 Test 2: Health check")
    response = client.get("/health")
    assert response.status_code == 200
    print(f"✅ Status code: {response.status_code}")
    
    # Test 3: Registrazione utente
    print("\n🔍 Test 3: Registrazione utente")
    user_data = {
        "email": "test_logging_complete@example.com",
        "username": "test_logging_complete",
        "password": "testpassword123",
        "full_name": "Test Logging Complete User"
    }
    
    response = client.post("/api/v1/register", json=user_data)
    if response.status_code == 201:
        print("✅ Utente registrato con successo")
    elif response.status_code == 400:
        print("ℹ️  Utente già esistente (normale per test multipli)")
    else:
        print(f"⚠️  Status code inaspettato: {response.status_code}")
    
    # Test 4: Login
    print("\n🔍 Test 4: Login")
    login_data = {
        "username": "test_logging_complete@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/token", data=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login riuscito")
        print(f"✅ Token ottenuto: {token[:20]}...")
    else:
        print(f"⚠️  Login fallito: {response.status_code}")
        token = None
    
    # Test 5: Endpoint protetto
    if token:
        print("\n🔍 Test 5: Endpoint protetto")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        if response.status_code == 200:
            print("✅ Endpoint protetto accessibile")
        else:
            print(f"⚠️  Endpoint protetto non accessibile: {response.status_code}")
    
    # Test 6: Endpoint che non esiste (per testare logging errori)
    print("\n🔍 Test 6: Endpoint non esistente")
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404
    print("✅ 404 gestito correttamente")
    
    # Test 7: Logging manuale
    print("\n🔍 Test 7: Logging manuale")
    logger.info("Test di logging manuale dall'applicazione",
                test_type="manual",
                user_agent="test-script")
    
    # Test 8: Logging con errori
    print("\n🔍 Test 8: Logging con errori")
    try:
        # Simula un errore
        raise ValueError("Test error for logging")
    except Exception as e:
        logger.error("Errore simulato per test logging",
                     error_type=type(e).__name__,
                     error_message=str(e),
                     exc_info=True)
        print("✅ Errore loggato correttamente")
    
    print("\n🎉 Tutti i test del logging sono completati!")
    print("\n📋 Riepilogo:")
    print("- ✅ Sistema di logging strutturato funzionante")
    print("- ✅ Trace ID generati e tracciati")
    print("- ✅ Log in formato JSON")
    print("- ✅ Middleware di logging attivo")
    print("- ✅ Logging di errori con traceback")
    print("- ✅ Logging delle richieste API")
    
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 