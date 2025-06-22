#!/usr/bin/env python3
"""
Test di funzionalità per la gestione documenti (upload/download)
Esegui questo script con MinIO configurato e il backend avviato.
"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

async def test_gestione_documenti():
    print("=" * 60)
    print("TEST DI FUNZIONALITÀ - GESTIONE DOCUMENTI (UPLOAD/DOWNLOAD)")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 1. Registrazione utente
        print("\n1. REGISTRAZIONE UTENTE")
        user_data = {
            "email": f"test_doc_{datetime.now().timestamp()}@example.com",
            "username": f"testdoc_{datetime.now().timestamp()}",
            "password": "TestPassword123!",
            "full_name": "Test Doc User"
        }
        resp = await client.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=user_data)
        assert resp.status_code == 201, resp.text
        print("Registrazione OK")

        # 2. Login
        print("2. LOGIN UTENTE")
        login_data = {"username": user_data["username"], "password": user_data["password"]}
        resp = await client.post(f"{BASE_URL}{API_PREFIX}/auth/token", data=login_data)
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login OK")

        # 3. Creazione casa
        print("3. CREAZIONE CASA")
        house_data = {"name": "Casa Documenti", "address": "Via Documenti 1"}
        resp = await client.post(f"{BASE_URL}{API_PREFIX}/houses/", json=house_data, headers=headers)
        assert resp.status_code == 201, resp.text
        house_id = resp.json()["id"]
        print(f"Casa creata con ID: {house_id}")

        # 4. Creazione documento
        print("4. CREAZIONE DOCUMENTO")
        doc_data = {
            "name": "Documento Test",
            "type": "application/pdf",
            "size": 0,
            "path": "",
            "checksum": "",
            "house_id": house_id
        }
        resp = await client.post(f"{BASE_URL}{API_PREFIX}/documents/", json=doc_data, headers=headers)
        assert resp.status_code == 201, resp.text
        document_id = resp.json()["id"]
        print(f"Documento creato con ID: {document_id}")

        # 5. Upload file
        print("5. UPLOAD FILE")
        file_content = b"Contenuto di test per upload documenti."
        files = {"file": ("test_upload.txt", file_content, "text/plain")}
        resp = await client.post(f"{BASE_URL}{API_PREFIX}/documents/{document_id}/upload", files=files, headers=headers)
        if resp.status_code != 200:
            print("Errore upload:", resp.text)
        assert resp.status_code == 200, resp.text
        print("Upload OK")
        upload_data = resp.json()
        print("Risposta upload:", upload_data)

        # 6. Download file
        print("6. DOWNLOAD FILE")
        resp = await client.get(f"{BASE_URL}{API_PREFIX}/documents/download/{document_id}", headers=headers)
        if resp.status_code != 200:
            print("Errore download:", resp.text)
        assert resp.status_code == 200, resp.text
        download_url = resp.json().get("download_url")
        print("Download URL ottenuto:", download_url)
        assert download_url, "Nessuna download_url nella risposta"

        # 7. Scarica effettivamente il file (se MinIO configurato)
        print("7. SCARICO IL FILE DA MinIO (se configurato)")
        try:
            file_resp = await client.get(download_url)
            if file_resp.status_code == 200:
                print("File scaricato con successo. Lunghezza:", len(file_resp.content))
            else:
                print("Errore scaricamento file da MinIO:", file_resp.status_code)
        except Exception as e:
            print("Download reale non riuscito (MinIO non configurato?)", str(e))

if __name__ == "__main__":
    asyncio.run(test_gestione_documenti()) 