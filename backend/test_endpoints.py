import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    # 1. Creare una casa
    print("\n1. Creazione di una casa...")
    house_data = {
        "name": "Test House",
        "owner_id": 1  # Aggiungiamo un owner_id di default
    }
    house_response = requests.post(f"{BASE_URL}/houses/", json=house_data)
    house = house_response.json()
    print(f"Casa creata: {house}")
    house_id = house["id"]

    # 2. Creare un nodo
    print("\n2. Creazione di un nodo...")
    node_data = {
        "house_id": house_id,
        "location": "Living Room",
        "type": "camera"
    }
    node_response = requests.post(f"{BASE_URL}/nodes/", json=node_data)
    node = node_response.json()
    print(f"Nodo creato: {node}")
    node_id = node["id"]

    # 3. Recuperare il nodo
    print("\n3. Recupero del nodo...")
    get_node_response = requests.get(f"{BASE_URL}/nodes/{node_id}")
    retrieved_node = get_node_response.json()
    print(f"Nodo recuperato: {retrieved_node}")

    # 4. Recuperare i documenti del nodo (dovrebbe essere vuoto)
    print("\n4. Recupero dei documenti del nodo...")
    documents_response = requests.get(f"{BASE_URL}/documents/{node_id}")
    documents = documents_response.json()
    print(f"Documenti recuperati: {documents}")

if __name__ == "__main__":
    test_endpoints() 