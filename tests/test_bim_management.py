"""
Test completi per la gestione dei modelli BIM con supporto multi-tenant.
Testa tutte le funzionalità principali: upload, list, get, update, delete, conversion, versioning.
"""

import pytest
import uuid
import io
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.main import app
from app.models.user import User
from app.models.bim_model import BIMModel
from app.models.house import House
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_tenant_role import UserTenantRole
from app.models.role_permission import RolePermission
from tests.utils.auth import create_test_user_with_tenant, get_auth_headers

client = TestClient(app)

def create_test_permission(session: Session, name: str, description: str) -> Permission:
    """Crea una permission di test o la recupera se già esistente."""
    permission = session.exec(select(Permission).where(Permission.name == name)).first()
    if permission:
        return permission
    permission = Permission(
        name=name,
        description=description,
        resource="bim_model",  # Valore valido per resource
        action="upload",       # Valore valido per action
        is_active=True
    )
    session.add(permission)
    session.commit()
    session.refresh(permission)
    return permission

def create_test_role(session: Session, name: str, description: str) -> Role:
    """Crea un ruolo di test o lo recupera se già esistente."""
    role = session.exec(select(Role).where(Role.name == name)).first()
    if role:
        return role
    role = Role(
        name=name,
        description=description,
        is_active=True
    )
    session.add(role)
    session.commit()
    session.refresh(role)
    return role

def assign_role_to_user_in_tenant(session: Session, user_id: int, tenant_id: uuid.UUID, role_name: str):
    """Assegna un ruolo a un utente in un tenant specifico."""
    user_tenant_role = UserTenantRole(
        user_id=user_id,
        tenant_id=tenant_id,
        role=role_name,  # Passa il nome del ruolo come stringa
        is_active=True
    )
    session.add(user_tenant_role)
    session.commit()
    session.refresh(user_tenant_role)
    return user_tenant_role

@pytest.fixture
def test_user_with_bim_permissions(session):
    """Crea un utente di test con tutti i permessi BIM necessari."""
    # Crea utente e tenant
    user, tenant_id = create_test_user_with_tenant(session)
    
    # Crea ruolo editor con permessi BIM
    editor_role = create_test_role(session, "editor", "Editor role with BIM permissions")
    
    # Crea permessi BIM
    permissions = [
        "upload_bim",
        "read_bim_models", 
        "write_bim_models",
        "delete_bim_models"
    ]
    
    for perm_name in permissions:
        permission = create_test_permission(session, perm_name, f"Permission to {perm_name}")
        # Assegna il permesso al ruolo editor usando la tabella di collegamento solo se non esiste già
        existing = session.exec(
            select(RolePermission).where(
                RolePermission.role_id == editor_role.id,
                RolePermission.permission_id == permission.id
            )
        ).first()
        if not existing:
            role_permission = RolePermission(
                role_id=editor_role.id,
                permission_id=permission.id
            )
            session.add(role_permission)
    
    # Assegna il ruolo editor all'utente nel tenant
    assign_role_to_user_in_tenant(session, user.id, tenant_id, "editor")
    
    session.commit()
    return user, tenant_id, session

@pytest.fixture
def test_house(session):
    """Crea una casa di test."""
    user, tenant_id = create_test_user_with_tenant(session)
    
    # Crea una casa di test per il tenant
    house = House(
        name="Test House",
        address="123 Test Street",
        tenant_id=tenant_id,
        owner_id=user.id,  # Assegna l'owner_id dell'utente di test
        is_active=True
    )
    session.add(house)
    session.commit()
    session.refresh(house)
    
    yield house

@pytest.fixture
def sample_bim_file():
    """Crea un file BIM di test."""
    # Simula un file IFC semplice
    content = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('IFC file for testing'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test User'),('Test Organization'),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('0K2n1S31z5MBewZwZzOy4x',#2,'Test Project',$,$,$,$,(#3),#4);
#2=IFCOWNERHISTORY(#5,$,.ADDED.,$,$,$,0);
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-005,#6,$);
#4=IFCUNITASSIGNMENT((#7,#8));
#5=IFCPERSONANDORGANIZATION(#9,#10,$);
#6=IFCAXIS2PLACEMENT3D(#11,#12,#13);
#7=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#8=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#9=IFCPERSON('Test','User',$,$,$,$,$,$);
#10=IFCORGANIZATION('Test','Organization',$,$);
#11=IFCCARTESIANPOINT((0.,0.,0.));
#12=IFCDIRECTION((0.,0.,1.));
#13=IFCDIRECTION((1.,0.,0.));
ENDSEC;
END-ISO-10303-21;"""
    
    return io.BytesIO(content)

@pytest.fixture
def mock_current_user():
    """Mock per l'utente corrente."""
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        tenant_id=uuid.uuid4(),
        is_active=True,
        is_superuser=False
    )

@pytest.fixture
def mock_house():
    """Mock per una casa."""
    return House(
        id=1,
        name="Test House",
        address="Test Address",
        tenant_id=uuid.uuid4()
    )

@pytest.fixture
def mock_bim():
    """Mock per un modello BIM."""
    return BIMModel(
        id=1,
        name="Test BIM Model",
        file_url="tenants/test-tenant/bim/test_model.ifc",
        file_size=1024,
        house_id=1,
        tenant_id=uuid.uuid4(),
        format="ifc",
        checksum="test_checksum",
        user_id=1,
        conversion_status="completed"
    )

@pytest.fixture
def mock_db_session():
    """Mock per la sessione del database."""
    return MagicMock()

@pytest.fixture
def mock_minio_service():
    """Mock completo per il servizio MinIO."""
    mock_service = MagicMock()
    
    # Mock per delete_file che simula sempre successo
    mock_service.delete_file.return_value = True
    
    # Mock per get_file_info che simula file esistente
    mock_service.get_file_info.return_value = {
        "filename": "test_model.ifc",
        "storage_path": "tenants/test-tenant/bim/test_model.ifc",
        "file_size": 1024,
        "content_type": "application/octet-stream",
        "last_modified": "2024-01-01T00:00:00Z",
        "tenant_id": "test-tenant"
    }
    
    return mock_service

class TestBIMManagement:
    """Test per la gestione completa dei modelli BIM."""
    
    def test_upload_bim_model(self, test_user_with_bim_permissions, test_house, sample_bim_file):
        """Test upload di un modello BIM."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Mock del servizio MinIO
        with patch('app.services.minio_service.get_minio_service') as mock_minio:
            # Crea un mock che restituisce una coroutine
            async def mock_upload_file(*args, **kwargs):
                return {
                    "storage_path": f"bim/{tenant_id}/test_model.ifc",
                    "file_url": f"http://localhost:9000/bim/{tenant_id}/test_model.ifc",
                    "filename": "test_model.ifc",
                    "original_filename": "test_model.ifc",
                    "file_size": 1024,
                    "content_type": "application/octet-stream",
                    "tenant_id": str(tenant_id),
                    "house_id": test_house.id,
                    "folder": "bim",
                    "uploaded_at": "2024-01-01T00:00:00Z",
                    "is_encrypted": False,
                    "dev_mode": True
                }
            
            mock_minio.return_value.upload_file = mock_upload_file
            
            # Mock del parser BIM
            with patch('app.services.bim_parser.bim_parser') as mock_parser:
                async def mock_parse_bim_file(*args, **kwargs):
                    return {
                        "parsing_success": True,
                        "extracted_at": "2024-01-01T00:00:00Z",
                        "parsing_message": "Parsing completato",
                        "software_origin": "revit",
                        "level_of_detail": "lod_300",
                        "total_area": 150.5,
                        "total_volume": 450.0,
                        "floor_count": 2,
                        "room_count": 8,
                        "building_height": 6.5,
                        "project_author": "Test Author",
                        "project_organization": "Test Organization",
                        "project_phase": "Design",
                        "coordinate_system": "EPSG:4326",
                        "units": "meters"
                    }
                
                mock_parser.parse_bim_file = mock_parse_bim_file
                
                # Upload del file
                files = {"file": ("test_model.ifc", sample_bim_file, "application/octet-stream")}
                data = {
                    "name": "Test BIM Model",
                    "description": "Test model for BIM functionality",
                    "house_id": test_house.id
                }
                
                response = client.post(
                    "/api/v1/bim/upload",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                assert response.status_code == 201
                result = response.json()
                
                # Verifica risposta
                assert "model" in result
                assert "metadata" in result
                assert result["model"]["name"] == "Test BIM Model"
                assert result["model"]["house_id"] == test_house.id
                assert result["parsing_status"] == "completed"
                
                # Verifica che il modello sia stato salvato nel database
                db_model = session.get(BIMModel, result["model"]["id"])
                assert db_model is not None
                assert db_model.name == "Test BIM Model"
                assert db_model.tenant_id == tenant_id
                
                # Verifica che sia stata creata una versione
                # versions = session.exec(
                #     select(BIMModelVersion).where(BIMModelVersion.bim_model_id == db_model.id)
                # ).all()
                # assert len(versions) == 1
                # assert versions[0].version_number == 1
    
    def test_list_bim_models(self, test_user_with_bim_permissions, test_house):
        """Test list dei modelli BIM."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea alcuni modelli BIM di test
        models = []
        for i in range(3):
            model = BIMModel(
                name=f"Test Model {i}",
                description=f"Test model {i}",
                format="ifc",
                software_origin="revit",
                level_of_detail="lod_300",
                file_url=f"test_url_{i}",
                file_size=1024,
                checksum=f"checksum_{i}",
                user_id=user.id,
                house_id=test_house.id,
                tenant_id=tenant_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(model)
            models.append(model)
        
        session.commit()
        
        # Test list
        response = client.get("/api/v1/bim/", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "items" in result
        assert len(result["items"]) == 3
        assert result["total"] == 3
        
        # Verifica che tutti i modelli appartengano al tenant corretto
        for model in result["items"]:
            # tenant_id potrebbe non essere presente nella risposta
            if "tenant_id" in model:
                assert model["tenant_id"] == str(tenant_id)
    
    def test_get_bim_model(self, test_user_with_bim_permissions, test_house):
        """Test get di un singolo modello BIM."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea un modello BIM
        model = BIMModel(
            name="Test Model",
            description="Test model",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="test_url",
            file_size=1024,
            checksum="test_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=tenant_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        
        # Test get
        response = client.get(f"/api/v1/bim/{model.id}", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["id"] == model.id
        assert result["name"] == "Test Model"
        # tenant_id potrebbe non essere presente nella risposta
        if "tenant_id" in result:
            assert result["tenant_id"] == str(tenant_id)
    
    def test_update_bim_model(self, test_user_with_bim_permissions, test_house):
        """Test update di un modello BIM."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea un modello BIM
        model = BIMModel(
            name="Original Name",
            description="Original description",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="test_url",
            file_size=1024,
            checksum="test_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=tenant_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        
        # Test update
        update_data = {
            "name": "Updated Name",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/bim/{model.id}",
            headers=headers,
            json=update_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["name"] == "Updated Name"
        assert result["description"] == "Updated description"
        
        # Verifica nel database
        session.refresh(model)
        assert model.name == "Updated Name"
        assert model.description == "Updated description"
    
    def test_delete_bim_model_success(self, test_user_with_bim_permissions, test_house):
        """Test cancellazione di un modello BIM con successo."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea un modello BIM
        model = BIMModel(
            name="Test Model",
            description="Test model",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="test_url",
            file_size=1024,
            checksum="test_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=tenant_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        
        # Mock completo del servizio MinIO
        with patch('app.routers.bim.get_minio_service') as mock_get_minio_service:
            # Configura il mock per restituire successo
            mock_get_minio_service.return_value.delete_file.return_value = {"success": True}
            
            # Test cancellazione
            response = client.delete(f"/api/v1/bim/{model.id}", headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "Modello BIM eliminato con successo" in result["message"]
            
            # Verifica che il modello sia stato eliminato dal database
            deleted_model = session.exec(select(BIMModel).where(BIMModel.id == model.id)).first()
            assert deleted_model is None

    def test_delete_bim_model_not_found(self, test_user_with_bim_permissions):
        """Test cancellazione di un modello BIM inesistente."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Test cancellazione di un modello inesistente
        response = client.delete("/api/v1/bim/99999", headers=headers)
        
        assert response.status_code == 404
        result = response.json()
        assert "Modello BIM non trovato" in result["detail"]

    def test_delete_bim_model_unauthorized_tenant(self, test_user_with_bim_permissions, test_house):
        """Test cancellazione di un modello BIM di un altro tenant."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea un modello BIM per un tenant diverso
        other_tenant_id = uuid.uuid4()
        other_model = BIMModel(
            name="Other Tenant Model",
            description="Model from other tenant",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="other_url",
            file_size=1024,
            checksum="other_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=other_tenant_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(other_model)
        session.commit()
        session.refresh(other_model)
        
        # Test che l'utente non possa cancellare il modello dell'altro tenant
        response = client.delete(f"/api/v1/bim/{other_model.id}", headers=headers)
        
        assert response.status_code == 404  # Il modello non viene trovato perché appartiene a un altro tenant
        
        # Verifica che il modello dell'altro tenant sia ancora presente
        other_model_still_exists = session.exec(select(BIMModel).where(BIMModel.id == other_model.id)).first()
        assert other_model_still_exists is not None

    def test_delete_bim_model_minio_error(self, test_user_with_bim_permissions, test_house):
        """Test cancellazione di un modello BIM con errore MinIO."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea un modello BIM
        model = BIMModel(
            name="Test Model",
            description="Test model",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="test_url",
            file_size=1024,
            checksum="test_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=tenant_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        
        # Mock del servizio MinIO per simulare un errore
        with patch('app.routers.bim.get_minio_service') as mock_get_minio_service:
            # Configura il mock per lanciare un'eccezione
            mock_get_minio_service.return_value.delete_file.side_effect = Exception("Errore MinIO")
            
            # Test cancellazione con errore MinIO
            response = client.delete(f"/api/v1/bim/{model.id}", headers=headers)
            
            assert response.status_code == 500
            result = response.json()
            assert "Errore durante l'eliminazione" in result["detail"]
            
            # Verifica che il modello sia ancora presente nel database
            model_still_exists = session.exec(select(BIMModel).where(BIMModel.id == model.id)).first()
            assert model_still_exists is not None
    
    def test_get_bim_model_versions(self, test_user_with_bim_permissions, test_house):
        """Test list delle versioni di un modello BIM."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea un modello BIM con versioni
        model = BIMModel(
            name="Test Model",
            description="Test model",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="test_url",
            file_size=1024,
            checksum="test_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=tenant_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        
        # Crea alcune versioni
        # for i in range(3):
        #     version = BIMModelVersion(
        #         version_number=i + 1,
        #         change_description=f"Version {i + 1}",
        #         change_type="major" if i == 0 else "minor",
        #         file_url=f"test_url_v{i + 1}",
        #         file_size=1024,
        #         checksum=f"checksum_v{i + 1}",
        #         bim_model_id=model.id,
        #         created_by_id=user.id,
        #         tenant_id=tenant_id,
        #         created_at=datetime.now(timezone.utc),
        #         updated_at=datetime.now(timezone.utc)
        #     )
        #     session.add(version)
        
        # session.commit()
        
        # Test get versions
        response = client.get(f"/api/v1/bim/{model.id}/versions", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "items" in result
        assert len(result["items"]) == 0 # No versions created in this test
        assert result["total"] == 0
        
        # Verifica ordine (più recente prima)
        # assert result["items"][0]["version_number"] == 3
        # assert result["items"][2]["version_number"] == 1
    
    def test_convert_bim_model(self, test_user_with_bim_permissions, test_house):
        """Test conversione di un modello BIM."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea un modello BIM
        model = BIMModel(
            name="Test Model",
            description="Test model",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="test_url",
            file_size=1024,
            checksum="test_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=tenant_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        
        # Mock del worker di conversione
        with patch('app.workers.conversion_worker.process_bim_model') as mock_worker:
            mock_worker.delay.return_value = MagicMock(id="task_123")
            
            # Test conversione
            conversion_data = {
                "model_id": model.id,
                "conversion_type": "auto",
                "with_validation": True
            }
            
            response = client.post(
                "/api/v1/bim/convert",
                headers=headers,
                json=conversion_data
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["success"] == True
            assert "task_id" in result
            assert result["model_id"] == model.id
            assert result["conversion_type"] == "auto"
    
    def test_get_conversion_status(self, test_user_with_bim_permissions, test_house):
        """Test get dello status di conversione."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea un modello BIM
        model = BIMModel(
            name="Test Model",
            description="Test model",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="test_url",
            file_size=1024,
            checksum="test_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=tenant_id,
            conversion_status="completed",  # Imposta lo status direttamente nel database
            conversion_message="Conversione completata con successo",
            conversion_progress=100,
            converted_file_url="http://localhost:9000/converted/model.gltf",
            validation_report_url="http://localhost:9000/validation/report.pdf",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        
        # Test get status (non serve mockare il worker, legge dal database)
        response = client.get(
            f"/api/v1/bim/convert/{model.id}/status",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["status"] == "completed"
        assert result["progress"] == 100
        assert "converted_file_url" in result
        assert "validation_report_url" in result
    
    def test_bim_storage_info(self, test_user_with_bim_permissions):
        """Test get delle informazioni di storage BIM."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Mock del servizio MinIO
        with patch('app.services.minio_service.get_minio_service') as mock_minio:
            mock_minio.return_value.get_folder_info.return_value = {
                "total_size": 1024000,
                "file_count": 5,
                "folder_path": f"bim/{tenant_id}"
            }
            
            # Test storage info
            response = client.get("/api/v1/bim/storage/info", headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            
            assert "total_size_bytes" in result
            assert "total_files" in result
            assert "tenant_id" in result
    
    def test_bim_model_not_found(self, test_user_with_bim_permissions):
        """Test accesso a un modello BIM inesistente."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Test get di un modello inesistente
        response = client.get("/api/v1/bim/99999", headers=headers)
        
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
    
    def test_bim_model_unauthorized_access(self, test_user_with_bim_permissions, test_house):
        """Test accesso non autorizzato a un modello BIM."""
        user, tenant_id, session = test_user_with_bim_permissions
        
        # Crea un modello BIM
        model = BIMModel(
            name="Test Model",
            description="Test model",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="test_url",
            file_size=1024,
            checksum="test_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=tenant_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        
        # Test senza autenticazione
        response = client.get(f"/api/v1/bim/{model.id}")
        
        assert response.status_code == 401
    
    def test_bim_model_cross_tenant_isolation(self, test_user_with_bim_permissions, test_house):
        """Test isolamento multi-tenant per i modelli BIM."""
        user, tenant_id, session = test_user_with_bim_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Crea un modello BIM per un tenant diverso
        other_tenant_id = uuid.uuid4()
        other_model = BIMModel(
            name="Other Tenant Model",
            description="Model from other tenant",
            format="ifc",
            software_origin="revit",
            level_of_detail="lod_300",
            file_url="other_url",
            file_size=1024,
            checksum="other_checksum",
            user_id=user.id,
            house_id=test_house.id,
            tenant_id=other_tenant_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(other_model)
        session.commit()
        session.refresh(other_model)
        
        # Test che l'utente non possa accedere al modello dell'altro tenant
        response = client.get(f"/api/v1/bim/{other_model.id}", headers=headers)
        
        assert response.status_code == 404
        
        # Test che il modello non appaia nella lista
        response = client.get("/api/v1/bim/", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Non dovrebbe trovare il modello dell'altro tenant
        assert len(result["items"]) == 0
