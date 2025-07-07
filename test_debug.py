#!/usr/bin/env python3
"""Test di debug per diagnosticare il problema con l'upload documenti."""

import io
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.house import House
from app.core.security import create_access_token
from app.database import get_db
from unittest.mock import patch, MagicMock

def test_debug_upload():
    """Test di debug per l'upload documenti."""
    
    # Crea un client di test
    client = TestClient(app)
    
    # Crea un tenant ID di test
    tenant_id = uuid.uuid4()
    
    # Crea un utente di test
    with next(get_db()) as session:
        user = User(
            email="debug@test.com",
            username="debuguser",
            hashed_password="hashed_password",
            is_active=True,
            tenant_id=tenant_id,
            role="admin"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Crea una casa di test
        house = House(
            name="Debug House",
            address="Via Debug 1",
            tenant_id=tenant_id,
            owner_id=user.id
        )
        session.add(house)
        session.commit()
        session.refresh(house)
        
        # Crea un token di accesso
        token = create_access_token(data={
            "sub": user.email,
            "tenant_id": str(tenant_id)
        })
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Crea contenuto file di test
        file_content = b"Debug test content"
        file_data = io.BytesIO(file_content)
        
        # Mock del servizio MinIO
        with patch('app.services.minio_service.get_minio_service') as mock_minio:
            service = MagicMock()
            service.upload_file.return_value = {
                "storage_path": f"houses/{house.id}/documents/debug.pdf",
                "file_size": len(file_content),
                "content_type": "application/pdf"
            }
            mock_minio.return_value = service
            
            print(f"Mock MinIO service: {service}")
            print(f"Mock upload_file method: {service.upload_file}")
            
            # Prova l'upload
            try:
                response = client.post(
                    "/api/v1/documents/upload",
                    files={"file": ("debug.pdf", file_data, "application/pdf")},
                    data={
                        "title": "Debug Document",
                        "description": "Debug description",
                        "document_type": "general",
                        "house_id": house.id
                    },
                    headers=headers
                )
                
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                if response.status_code != 200:
                    print(f"Response content: {response.text}")
                else:
                    print(f"Response JSON: {response.json()}")
                    
            except Exception as e:
                print(f"Exception during request: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_debug_upload() 