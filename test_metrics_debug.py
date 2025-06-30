"""
Test di debug specifico per l'endpoint metrics.
"""
import sys
import traceback
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Mock di tutte le dipendenze esterne
with patch('app.core.redis.get_redis_client'):
    with patch('app.core.storage.minio.get_minio_client'):
        with patch('app.database.get_db'):
            with patch('app.core.logging_config.get_logger'):
                with patch('app.core.logging_config.log_security_event'):
                    try:
                        from app.routers.system import router
                        print("✅ Router system importato con successo")
                    except Exception as e:
                        print(f"❌ Errore import router: {e}")
                        traceback.print_exc()
                        sys.exit(1)

# Crea un'app di test con solo il router system
app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_metrics_debug():
    """Test di debug per l'endpoint metrics"""
    print("🔍 Test di debug per /system/metrics")
    
    try:
        with patch('app.routers.system.get_system_info') as mock_sys:
            mock_sys.return_value = {
                "cpu_percent": 25.0,
                "memory_percent": 50.0,
                "disk_percent": 30.0,
                "uptime": 3600.0
            }
            
            print("📡 Invio richiesta a /system/metrics...")
            response = client.get("/system/metrics")
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📊 Content-Type: {response.headers.get('content-type')}")
            print(f"📊 Response: {response.text[:500]}...")
            
            if response.status_code == 200:
                print("✅ Endpoint metrics funziona!")
            else:
                print(f"❌ Endpoint metrics restituisce errore: {response.text}")
                
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_metrics_debug() 