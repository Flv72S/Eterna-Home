import requests
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Configura il logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurazione
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "integration_test_user@example.com"
TEST_PASSWORD = "securepassword123"
TEST_HOUSE_NAME = "Casa di Test"
TEST_HOUSE_ADDRESS = "Via Roma 123, Milano"

@dataclass
class TestResult:
    """Classe per memorizzare i risultati dei test"""
    name: str
    success: bool
    message: str
    timestamp: datetime = datetime.now()

def get_headers(access_token: Optional[str] = None) -> Dict[str, str]:
    """Ottiene gli header con autorizzazione opzionale"""
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers

def test_signup() -> TestResult:
    """Test di registrazione utente"""
    try:
        logger.info("\nEsecuzione test registrazione...")
        logger.info(f"URL: {BASE_URL}/auth/signup")
        logger.info(f"Dati inviati: email={TEST_EMAIL}, full_name=Test User")
        
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            headers=get_headers()
        )
        
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        logger.info(f"Risposta completa: {response.text}")
        print(f"\nRisposta del server: {response.text}")  # Stampa diretta
        
        if response.status_code in [200, 400]:  # 400 se l'utente esiste già
            return TestResult(
                "Registrazione",
                True,
                "Utente creato" if response.status_code == 200 else "Utente già esistente"
            )
        else:
            return TestResult(
                "Registrazione",
                False,
                f"Codice di stato inatteso: {response.status_code}"
            )
    except Exception as e:
        logger.error(f"Errore durante la registrazione: {str(e)}", exc_info=True)
        return TestResult("Registrazione", False, str(e))

def test_login() -> tuple[TestResult, Optional[str]]:
    """Test di login utente e ottenimento token"""
    try:
        logger.info("\nEsecuzione test login...")
        logger.info(f"URL: {BASE_URL}/auth/login")
        logger.info(f"Dati inviati: username={TEST_EMAIL}")
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        logger.info(f"Risposta completa: {response.text}")
        
        if response.status_code == 200:
            access_token = response.json()["access_token"]
            return TestResult("Login", True, "Token di accesso ottenuto con successo"), access_token
        else:
            return TestResult("Login", False, f"Codice di stato inatteso: {response.status_code}"), None
    except Exception as e:
        logger.error(f"Errore durante il login: {str(e)}", exc_info=True)
        return TestResult("Login", False, str(e)), None

def test_create_house(access_token: str) -> TestResult:
    """Test di creazione casa e restituzione ID"""
    try:
        logger.info("\nEsecuzione test creazione casa...")
        logger.info(f"URL: {BASE_URL}/houses/")
        logger.info(f"Dati inviati: name={TEST_HOUSE_NAME}, address={TEST_HOUSE_ADDRESS}")
        
        response = requests.post(
            f"{BASE_URL}/houses/",
            json={
                "name": TEST_HOUSE_NAME,
                "address": TEST_HOUSE_ADDRESS
            },
            headers=get_headers(access_token)
        )
        
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        logger.info(f"Risposta completa: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            house_id = response_data.get("id")
            
            # Verifica che l'ID non sia vuoto
            if not house_id:
                return TestResult("Creazione Casa", False, "ID casa non presente nella risposta")
            
            # Verifica che i dati restituiti corrispondano a quelli inviati
            if response_data.get("name") != TEST_HOUSE_NAME or response_data.get("address") != TEST_HOUSE_ADDRESS:
                return TestResult("Creazione Casa", False, "Dati casa non corrispondenti")
            
            return TestResult("Creazione Casa", True, f"Casa creata con ID: {house_id}")
        else:
            return TestResult("Creazione Casa", False, f"Codice di stato inatteso: {response.status_code}")
    except Exception as e:
        logger.error(f"Errore durante la creazione della casa: {str(e)}", exc_info=True)
        return TestResult("Creazione Casa", False, str(e))

def main():
    """Funzione principale di esecuzione dei test"""
    logger.info("Avvio Test Creazione Casa...")
    logger.info("=" * 50)
    
    # Test di registrazione
    signup_result = test_signup()
    logger.info(f"\nTest Registrazione: {'SUCCESSO' if signup_result.success else 'FALLITO'}")
    logger.info(f"Messaggio: {signup_result.message}")
    
    if not signup_result.success:
        logger.error("Registrazione fallita, interruzione dei test")
        return
    
    # Test di login
    login_result, access_token = test_login()
    logger.info(f"\nTest Login: {'SUCCESSO' if login_result.success else 'FALLITO'}")
    logger.info(f"Messaggio: {login_result.message}")
    
    if not login_result.success:
        logger.error("Login fallito, interruzione dei test")
        return
    
    # Test di creazione casa
    house_result = test_create_house(access_token)
    logger.info(f"\nTest Creazione Casa: {'SUCCESSO' if house_result.success else 'FALLITO'}")
    logger.info(f"Messaggio: {house_result.message}")
    
    logger.info("\nTest Completati!")
    logger.info("=" * 50)

if __name__ == "__main__":
    main() 