import requests
import json

def test_signup():
    print("Iniziando il test di registrazione...")
    url = "http://localhost:8000/auth/signup"
    data = {
        "email": "integration_test@example.com",
        "password": "testpassword"
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"Invio richiesta POST a {url}")
    print(f"Dati inviati: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code >= 400:
            print("\nDettagli errore:")
            try:
                error_details = response.json()
                print(json.dumps(error_details, indent=2))
            except:
                print("Risposta non in formato JSON:")
                print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la richiesta HTTP: {str(e)}")
    except Exception as e:
        print(f"Errore inaspettato: {str(e)}")
        print(f"Tipo di errore: {type(e)}")

if __name__ == "__main__":
    print("Avvio test...")
    test_signup()
    print("Test completato.") 