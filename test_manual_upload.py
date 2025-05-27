import requests
import os
import io

def main():
    BASE_URL = "http://localhost:8000"
    EMAIL = "integration_test_user@example.com"
    PASSWORD = "securepassword123"
    HOUSE_NAME = "Casa di Test Manuale"
    HOUSE_ADDRESS = "Via Roma 123, Milano"
    NODE_NAME = "Nodo Manuale"
    NODE_TYPE = "Tipo Manuale"
    NODE_LOCATION = "Posizione Manuale"
    FILE_CONTENT = "Contenuto di test per upload manuale."
    FILE_NAME = "manual_test.txt"
    
    # 1. Login
    print("[1] Login...")
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": EMAIL, "password": PASSWORD}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if resp.status_code != 200:
        print("Login fallito:", resp.text)
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login OK.")

    # 2. Crea casa
    print("[2] Creazione casa...")
    resp = requests.post(f"{BASE_URL}/houses/", json={"name": HOUSE_NAME, "address": HOUSE_ADDRESS}, headers=headers)
    if resp.status_code != 200:
        print("Creazione casa fallita:", resp.text)
        return
    house_id = resp.json()["id"]
    print(f"Casa creata con ID: {house_id}")

    # 3. Crea nodo
    print("[3] Creazione nodo...")
    node_data = {"name": NODE_NAME, "house_id": house_id, "location": NODE_LOCATION, "type": NODE_TYPE}
    resp = requests.post(f"{BASE_URL}/nodes/", json=node_data, headers=headers)
    if resp.status_code != 200:
        print("Creazione nodo fallita:", resp.text)
        return
    node_id = resp.json()["id"]
    print(f"Nodo creato con ID: {node_id}")

    # 4. Upload documento legacy
    print("[4] Upload documento legacy...")
    print(f"Tipo di FILE_CONTENT: {type(FILE_CONTENT)}")
    file_content = FILE_CONTENT.encode('utf-8')
    print(f"Tipo di file_content: {type(file_content)}")
    file_obj = io.BytesIO(file_content)
    print(f"Tipo di file_obj: {type(file_obj)}")
    print(f"file_obj ha 'read': {hasattr(file_obj, 'read')}")
    files = {
        "file": (FILE_NAME, file_obj, "text/plain")
    }
    print(f"Tipo di files['file']: {type(files['file'])}")
    print(f"Tipo di files['file'][1]: {type(files['file'][1])}")
    print(f"files['file'][1] ha 'read': {hasattr(files['file'][1], 'read')}")
    data = {
        "house_id": str(house_id),
        "node_id": str(node_id),
        "type": "TXT",
        "version": "1.0"
    }
    
    # Invia la richiesta
    print("Invio richiesta di upload...")
    resp = requests.post(f"{BASE_URL}/legacy-documents/", headers=headers, files=files, data=data)
    print(f"Status code: {resp.status_code}")
    print("Risposta:", resp.text)

if __name__ == "__main__":
    main() 