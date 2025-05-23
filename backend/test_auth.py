import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    print("\nTest del flusso di autenticazione:")
    print("----------------------------------------\n")

    # 1. Test di registrazione utente
    print("1. Test di registrazione utente...")
    signup_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    signup_response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    if signup_response.status_code == 200:
        print("✓ Registrazione utente completata con successo")
    else:
        print(f"✗ Errore nella registrazione: {signup_response.text}")
        return

    # 2. Test di login
    print("\n2. Test di login...")
    login_data = {
        "username": "test@example.com",
        "password": "testpassword123"
    }
    login_response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        print("✓ Login completato con successo")
    else:
        print(f"✗ Errore nel login: {login_response.text}")
        return

    # 3. Test di accesso a endpoint protetto
    print("\n3. Test di accesso a endpoint protetto...")
    headers = {"Authorization": f"Bearer {token}"}
    protected_response = requests.get(f"{BASE_URL}/houses/", headers=headers)
    if protected_response.status_code == 200:
        print("✓ Accesso a endpoint protetto completato con successo")
    else:
        print(f"✗ Errore nell'accesso all'endpoint protetto: {protected_response.text}")
        return

    # 4. Test di accesso senza token
    print("\n4. Test di accesso senza token...")
    no_token_response = requests.get(f"{BASE_URL}/houses/")
    if no_token_response.status_code == 401:
        print("✓ Accesso senza token correttamente rifiutato")
    else:
        print(f"✗ Errore nel test di accesso senza token: {no_token_response.text}")
        return

    # 5. Test di accesso con token invalido
    print("\n5. Test di accesso con token invalido...")
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    invalid_token_response = requests.get(f"{BASE_URL}/houses/", headers=invalid_headers)
    if invalid_token_response.status_code == 401:
        print("✓ Accesso con token invalido correttamente rifiutato")
    else:
        print(f"✗ Errore nel test di accesso con token invalido: {invalid_token_response.text}")
        return

    print("\n✓ Tutti i test completati con successo!")

if __name__ == "__main__":
    test_auth_flow() 