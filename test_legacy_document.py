import requests
import logging
import os
from datetime import datetime

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "integration_test_user@example.com"
TEST_FILE_PATH = "test_document.txt"

def create_test_file():
    """Crea un file di test per l'upload"""
    with open(TEST_FILE_PATH, "w") as f:
        f.write("Questo è un documento di test per l'upload")
    return TEST_FILE_PATH

def cleanup_test_file():
    """Rimuove il file di test dopo l'uso"""
    if os.path.exists(TEST_FILE_PATH):
        os.remove(TEST_FILE_PATH)

def test_upload_legacy_document():
    """Test per l'upload di un documento legacy"""
    logger.info("Avvio Test Upload Documento Legacy...")
    logger.info("=" * 50)

    try:
        # 1. Registrazione utente (se non esiste)
        logger.info("\nEsecuzione registrazione...")
        signup_data = {
            "email": TEST_USER_EMAIL,
            "full_name": "Test User",
            "password": "password123"
        }
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        logger.info(f"Risposta completa: {response.text}")
        
        # 2. Login per ottenere il token
        logger.info("\nEsecuzione login...")
        login_data = {
            "username": TEST_USER_EMAIL,
            "password": "password123"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data, headers=headers)
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Login fallito: {response.text}")
            return False
        
        token = response.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 3. Creazione casa di test
        logger.info("\nCreazione casa di test...")
        house_data = {
            "name": "Casa Test",
            "address": "Via Test 123"
        }
        response = requests.post(f"{BASE_URL}/houses/", json=house_data, headers=headers)
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        logger.info(f"Risposta completa: {response.text}")
        
        if response.status_code != 200:
            logger.error("Creazione casa fallita")
            return False
        
        house_id = response.json()["id"]
        
        # 4. Creazione nodo di test
        logger.info("\nCreazione nodo di test...")
        node_data = {
            "name": "Nodo Test",
            "type": "sensor",
            "status": "active",
            "house_id": house_id
        }
        response = requests.post(f"{BASE_URL}/nodes/", json=node_data, headers=headers)
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        logger.info(f"Risposta completa: {response.text}")
        
        if response.status_code != 200:
            logger.error("Creazione nodo fallita")
            return False
        
        node_id = response.json()["id"]
        
        # 5. Creazione file di test
        test_file_path = create_test_file()
        
        # 6. Preparazione dati per l'upload
        with open(test_file_path, 'rb') as f:
            files = {
                'file': ('test_document.txt', f, 'text/plain')
            }
            data = {
                'description': 'Documento di test per l\'integrazione',
                'node_id': node_id,
                'house_id': house_id,
                'type': 'manual'
            }
            
            # 7. Esecuzione upload
            logger.info("\nEsecuzione upload documento...")
            logger.info(f"URL: {BASE_URL}/legacy-documents/")
            logger.info(f"Dati inviati: description={data['description']}, node_id={data['node_id']}, house_id={data['house_id']}, type={data['type']}")
            
            response = requests.post(
                f"{BASE_URL}/legacy-documents/",
                files=files,
                data=data,
                headers=headers
            )
        
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        logger.info(f"Risposta completa: {response.text}")
        
        # 8. Verifica risultati
        if response.status_code == 200:
            response_data = response.json()
            
            # Verifica campi obbligatori
            required_fields = ['id', 'filename', 'file_path', 'description', 'node_id', 'created_at']
            for field in required_fields:
                if field not in response_data:
                    logger.error(f"Campo mancante nella risposta: {field}")
                    return False
                if not response_data[field]:
                    logger.error(f"Campo vuoto nella risposta: {field}")
                    return False
            
            # Verifica corrispondenza dati
            if response_data['description'] != data['description']:
                logger.error("La descrizione non corrisponde")
                return False
            
            if response_data['node_id'] != data['node_id']:
                logger.error("L'ID del nodo non corrisponde")
                return False
            
            logger.info("\nTest Upload Documento Legacy: SUCCESSO")
            logger.info("Messaggio: Documento caricato correttamente")
            return True
            
        else:
            logger.error("\nTest Upload Documento Legacy: FALLITO")
            logger.error(f"Messaggio: Codice di stato inatteso: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Errore durante il test: {str(e)}")
        return False
    finally:
        cleanup_test_file()

def test_get_legacy_documents():
    """Test per il recupero dei documenti legacy"""
    logger.info("Avvio Test Recupero Documenti Legacy...")
    logger.info("=" * 50)

    try:
        # Login per ottenere il token
        login_data = {
            "username": TEST_USER_EMAIL,
            "password": "password123"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data, headers=headers)
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Login fallito: {response.text}")
            return False
        token = response.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}"
        }

        # Recupero documenti legacy
        logger.info("\nRecupero lista documenti legacy...")
        response = requests.get(f"{BASE_URL}/legacy-documents/", headers=headers)
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        logger.info(f"Risposta completa: {response.text}")

        if response.status_code != 200:
            logger.error("Recupero documenti legacy fallito")
            return False

        documents = response.json()
        if not isinstance(documents, list):
            logger.error("La risposta non è una lista")
            return False
        if len(documents) == 0:
            logger.error("Nessun documento trovato nella lista")
            return False

        # Cerca il documento caricato in precedenza
        found = None
        for doc in documents:
            if doc.get("description") == "Documento di test per l'integrazione":
                found = doc
                break
        if not found:
            logger.error("Documento di test non trovato nella lista")
            return False

        # Verifica campi necessari
        required_fields = ['id', 'filename', 'file_path', 'description', 'node_id', 'created_at']
        for field in required_fields:
            if field not in found:
                logger.error(f"Campo mancante nel documento trovato: {field}")
                return False
            if not found[field]:
                logger.error(f"Campo vuoto nel documento trovato: {field}")
                return False

        logger.info("\nTest Recupero Documenti Legacy: SUCCESSO")
        logger.info("Messaggio: Documento trovato e valido nella lista")
        return True

    except Exception as e:
        logger.error(f"Errore durante il test: {str(e)}")
        return False

if __name__ == "__main__":
    test_upload_legacy_document()
    test_get_legacy_documents() 