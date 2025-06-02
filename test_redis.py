import redis
from app.core.redis import get_redis_client

def test_redis_connection():
    try:
        # Test di connessione
        redis_client = get_redis_client()
        
        # Test di scrittura
        redis_client.set("test_key", "test_value")
        
        # Test di lettura
        value = redis_client.get("test_key")
        
        print("✅ Test Redis completato con successo!")
        print(f"Valore letto: {value}")
        
        # Pulizia
        redis_client.delete("test_key")
        
    except Exception as e:
        print(f"❌ Errore durante il test Redis: {str(e)}")

if __name__ == "__main__":
    test_redis_connection() 