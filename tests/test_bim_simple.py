"""
Test semplice per verificare che il router BIM sia accessibile.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_bim_router_accessible():
    """Test che il router BIM sia accessibile."""
    # Verifica che l'endpoint esista (dovrebbe restituire 401 o 403 per mancanza di autenticazione)
    response = client.get("/api/v1/bim/")
    
    # Dovrebbe restituire 401 (Unauthorized) o 403 (Forbidden) per mancanza di autenticazione
    assert response.status_code in [401, 403, 422]
    
    print(f"BIM router response: {response.status_code}")
    if response.status_code != 200:
        print(f"Response content: {response.text}")

def test_bim_upload_endpoint_exists():
    """Test che l'endpoint di upload BIM esista."""
    # Verifica che l'endpoint esista (dovrebbe restituire 401 o 403 per mancanza di autenticazione)
    response = client.post("/api/v1/bim/upload")
    
    # Dovrebbe restituire 401 (Unauthorized) o 403 (Forbidden) per mancanza di autenticazione
    assert response.status_code in [401, 403, 422]
    
    print(f"BIM upload endpoint response: {response.status_code}")

def test_bim_convert_endpoint_exists():
    """Test che l'endpoint di conversione BIM esista."""
    # Verifica che l'endpoint esista (dovrebbe restituire 401 o 403 per mancanza di autenticazione)
    response = client.post("/api/v1/bim/convert")
    
    # Dovrebbe restituire 401 (Unauthorized) o 403 (Forbidden) per mancanza di autenticazione
    assert response.status_code in [401, 403, 422]
    
    print(f"BIM convert endpoint response: {response.status_code}")

def test_bim_storage_info_endpoint_exists():
    """Test che l'endpoint di info storage BIM esista."""
    # Verifica che l'endpoint esista (dovrebbe restituire 401 o 403 per mancanza di autenticazione)
    response = client.get("/api/v1/bim/storage/info")
    
    # Dovrebbe restituire 401 (Unauthorized) o 403 (Forbidden) per mancanza di autenticazione
    assert response.status_code in [401, 403, 422]
    
    print(f"BIM storage info endpoint response: {response.status_code}") 