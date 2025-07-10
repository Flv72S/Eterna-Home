"""
Test per il micro-step di import BIM da repository pubbliche.
Testa download, validazione MIME, sicurezza e logging per fonti esterne.
"""

import pytest
import uuid
import aiohttp
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime

from app.main import app
from app.models.user import User
from app.models.bim_model import BIMModel
from app.models.house import House
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_tenant_role import UserTenantRole
from app.models.role_permission import RolePermission
from app.services.bim_public_import import BIMPublicImportService
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
        resource="bim_model",
        action="upload",
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
    """Assegna un ruolo a un utente in un tenant."""
    role = session.exec(select(Role).where(Role.name == role_name)).first()
    if not role:
        role = create_test_role(session, role_name, f"{role_name} role")
    
    # Verifica se l'assegnazione esiste già
    existing = session.exec(
        select(UserTenantRole).where(
            UserTenantRole.user_id == user_id,
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.role_id == role.id
        )
    ).first()
    
    if not existing:
        user_tenant_role = UserTenantRole(
            user_id=user_id,
            tenant_id=tenant_id,
            role_id=role.id
        )
        session.add(user_tenant_role)
        session.commit()

@pytest.fixture
def test_user_with_bim_public_permissions(session):
    """Crea un utente di test con permessi per import BIM pubblico."""
    # Crea utente e tenant
    user, tenant_id = create_test_user_with_tenant(session)
    
    # Crea ruolo admin con permessi BIM
    admin_role = create_test_role(session, "admin", "Admin role with BIM permissions")
    
    # Crea permessi BIM
    permissions = [
        "upload_bim",
        "manage_bim_sources",
        "read_bim_models", 
        "write_bim_models"
    ]
    
    for perm_name in permissions:
        permission = create_test_permission(session, perm_name, f"Permission to {perm_name}")
        # Assegna il permesso al ruolo admin
        existing = session.exec(
            select(RolePermission).where(
                RolePermission.role_id == admin_role.id,
                RolePermission.permission_id == permission.id
            )
        ).first()
        if not existing:
            role_permission = RolePermission(
                role_id=admin_role.id,
                permission_id=permission.id
            )
            session.add(role_permission)
    
    # Assegna il ruolo admin all'utente nel tenant
    assign_role_to_user_in_tenant(session, user.id, tenant_id, "admin")
    
    session.commit()
    return user, tenant_id, session

@pytest.fixture
def test_house(session, test_user_with_bim_public_permissions):
    """Crea una casa di test."""
    user, tenant_id, session = test_user_with_bim_public_permissions
    
    house = House(
        name="Test House",
        address="Via Test 123",
        city="Test City",
        postal_code="12345",
        country="Italy",
        tenant_id=tenant_id,
        owner_id=user.id
    )
    session.add(house)
    session.commit()
    session.refresh(house)
    return house

class TestBIMPublicImportService:
    """Test per il servizio di import BIM pubblico."""
    
    def test_validate_url_valid(self):
        """Test validazione URL valido."""
        service = BIMPublicImportService()
        url = "https://geoportale.regione.lazio.it/bim/modelo.ifc"
        
        # Dovrebbe passare senza eccezioni
        assert service._validate_url(url) == True
    
    def test_validate_url_invalid_protocol(self):
        """Test validazione URL con protocollo non valido."""
        service = BIMPublicImportService()
        url = "ftp://example.com/file.ifc"
        
        with pytest.raises(Exception):
            service._validate_url(url)
    
    def test_validate_url_unauthorized_domain(self):
        """Test validazione URL con dominio non autorizzato."""
        service = BIMPublicImportService()
        url = "https://malicious-site.com/file.ifc"
        
        with pytest.raises(Exception):
            service._validate_url(url)
    
    def test_validate_url_suspicious_pattern(self):
        """Test validazione URL con pattern sospetto."""
        service = BIMPublicImportService()
        url = "https://example.com/../../../file.ifc"
        
        with pytest.raises(Exception):
            service._validate_url(url)
    
    def test_validate_file_extension_valid(self):
        """Test validazione estensione file valida."""
        service = BIMPublicImportService()
        
        assert service._validate_file_extension("model.ifc") == True
        assert service._validate_file_extension("drawing.dxf") == True
        assert service._validate_file_extension("document.pdf") == True
    
    def test_validate_file_extension_invalid(self):
        """Test validazione estensione file non valida."""
        service = BIMPublicImportService()
        
        assert service._validate_file_extension("model.exe") == False
        assert service._validate_file_extension("drawing.jpg") == False
        assert service._validate_file_extension("") == False
    
    def test_validate_mime_type_valid(self):
        """Test validazione tipo MIME valido."""
        service = BIMPublicImportService()
        
        assert service._validate_mime_type("application/octet-stream") == True
        assert service._validate_mime_type("model/ifc") == True
        assert service._validate_mime_type("application/pdf") == True
    
    def test_validate_mime_type_invalid(self):
        """Test validazione tipo MIME non valido."""
        service = BIMPublicImportService()
        
        assert service._validate_mime_type("image/jpeg") == False
        assert service._validate_mime_type("text/html") == False
        assert service._validate_mime_type("") == False
    
    def test_validate_file_size_valid(self):
        """Test validazione dimensione file valida."""
        service = BIMPublicImportService()
        
        assert service._validate_file_size(100 * 1024 * 1024) == True  # 100MB
        assert service._validate_file_size(500 * 1024 * 1024) == True  # 500MB (limite)
    
    def test_validate_file_size_invalid(self):
        """Test validazione dimensione file troppo grande."""
        service = BIMPublicImportService()
        
        assert service._validate_file_size(501 * 1024 * 1024) == False  # 501MB
        assert service._validate_file_size(1024 * 1024 * 1024) == False  # 1GB
    
    @pytest.mark.asyncio
    async def test_download_and_validate_file_success(self):
        """Test download e validazione file con successo."""
        service = BIMPublicImportService()
        
        # Mock della risposta HTTP
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {
            'content-type': 'application/octet-stream',
            'content-length': '1024'
        }
        mock_response.read = AsyncMock(return_value=b"fake_bim_content")
        
        # Mock della sessione HTTP
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(service, '_get_session', return_value=mock_session):
            result = await service.download_and_validate_file(
                url="https://geoportale.regione.lazio.it/bim/modelo.ifc",
                tenant_id=uuid.uuid4(),
                house_id=1
            )
        
        assert result["content"] == b"fake_bim_content"
        assert result["file_size"] == 1024
        assert result["content_type"] == "application/octet-stream"
    
    @pytest.mark.asyncio
    async def test_download_and_validate_file_http_error(self):
        """Test download con errore HTTP."""
        service = BIMPublicImportService()
        
        # Mock della risposta HTTP con errore
        mock_response = MagicMock()
        mock_response.status = 404
        
        # Mock della sessione HTTP
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(service, '_get_session', return_value=mock_session):
            with pytest.raises(Exception):
                await service.download_and_validate_file(
                    url="https://geoportale.regione.lazio.it/bim/modelo.ifc",
                    tenant_id=uuid.uuid4()
                )

class TestBIMPublicImportAPI:
    """Test per gli endpoint API di import BIM pubblico."""
    
    def test_download_bim_from_public_repository_success(self, test_user_with_bim_public_permissions, test_house):
        """Test download BIM da repository pubblico con successo."""
        user, tenant_id, session = test_user_with_bim_public_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Mock del servizio di import
        with patch('app.routers.bim_public.BIMPublicImportService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Mock del download
            mock_service.download_and_validate_file = AsyncMock(return_value={
                "content": b"fake_bim_content",
                "filename": "test_model.ifc",
                "content_type": "application/octet-stream",
                "file_size": 1024
            })
            
            # Mock del servizio MinIO
            with patch('app.routers.bim_public.get_minio_service') as mock_minio:
                mock_minio.return_value.client = None  # Modalità sviluppo
                
                # Mock del parser BIM
                with patch('app.routers.bim_public.bim_parser') as mock_parser:
                    mock_parser.parse_bim_file = AsyncMock(return_value={
                        "parsing_success": True,
                        "total_area": 100.0,
                        "total_volume": 500.0
                    })
                    
                    # Test della richiesta
                    response = client.post(
                        "/api/v1/bim/public/download",
                        headers=headers,
                        data={
                            "url": "https://geoportale.regione.lazio.it/bim/modelo.ifc",
                            "name": "Test BIM Model",
                            "description": "Test model from public repository",
                            "house_id": test_house.id,
                            "source_repository": "geoportale_regionale"
                        }
                    )
        
        assert response.status_code == 201
        result = response.json()
        
        assert result["name"] == "Test BIM Model"
        assert result["format"] == "ifc"
        assert result["house_id"] == test_house.id
        assert result["tenant_id"] == str(tenant_id)
        
        # Verifica che il modello sia stato salvato nel database
        db_model = session.get(BIMModel, result["id"])
        assert db_model is not None
        assert db_model.project_author == "Repository: geoportale_regionale"
        assert db_model.project_phase == "imported"
        
        # Verifica che sia stata creata una versione
        # versions = session.exec(
        #     select(BIMModelVersion).where(BIMModelVersion.bim_model_id == db_model.id)
        # ).all()
        # assert len(versions) == 1
        # assert versions[0].change_description == "Importazione da geoportale_regionale"
    
    def test_download_bim_from_public_repository_invalid_url(self, test_user_with_bim_public_permissions):
        """Test download BIM con URL non valido."""
        user, tenant_id, session = test_user_with_bim_public_permissions
        headers = get_auth_headers(user, tenant_id)
        
        response = client.post(
            "/api/v1/bim/public/download",
            headers=headers,
            data={
                "url": "",  # URL vuoto
                "source_repository": "geoportale_regionale"
            }
        )
        
        assert response.status_code == 400
        assert "URL non può essere vuoto" in response.json()["detail"]
    
    def test_download_bim_from_public_repository_unauthorized_domain(self, test_user_with_bim_public_permissions):
        """Test download BIM da dominio non autorizzato."""
        user, tenant_id, session = test_user_with_bim_public_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Mock del servizio di import per simulare dominio non autorizzato
        with patch('app.routers.bim_public.BIMPublicImportService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Mock del download che solleva eccezione per dominio non autorizzato
            mock_service.download_and_validate_file = AsyncMock(side_effect=Exception("Dominio non autorizzato"))
            
            response = client.post(
                "/api/v1/bim/public/download",
                headers=headers,
                data={
                    "url": "https://malicious-site.com/file.ifc",
                    "source_repository": "custom"
                }
            )
        
        assert response.status_code == 500
    
    def test_download_bim_from_public_repository_house_not_found(self, test_user_with_bim_public_permissions):
        """Test download BIM con casa non trovata."""
        user, tenant_id, session = test_user_with_bim_public_permissions
        headers = get_auth_headers(user, tenant_id)
        
        response = client.post(
            "/api/v1/bim/public/download",
            headers=headers,
            data={
                "url": "https://geoportale.regione.lazio.it/bim/modelo.ifc",
                "house_id": 99999,  # Casa inesistente
                "source_repository": "geoportale_regionale"
            }
        )
        
        assert response.status_code == 404
        assert "Casa non trovata" in response.json()["detail"]
    
    def test_get_public_bim_sources(self, test_user_with_bim_public_permissions):
        """Test ottenimento lista fonti pubbliche."""
        user, tenant_id, session = test_user_with_bim_public_permissions
        headers = get_auth_headers(user, tenant_id)
        
        response = client.get("/api/v1/bim/public/sources", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "sources" in result
        assert "supported_formats" in result
        assert "max_file_size_mb" in result
        
        # Verifica che le fonti siano presenti
        sources = result["sources"]
        source_ids = [s["id"] for s in sources]
        assert "geoportale_regionale" in source_ids
        assert "catasto" in source_ids
        assert "comune" in source_ids
        assert "custom" in source_ids
        
        # Verifica formati supportati
        assert "ifc" in result["supported_formats"]
        assert "dxf" in result["supported_formats"]
        assert "pdf" in result["supported_formats"]
        
        # Verifica dimensione massima
        assert result["max_file_size_mb"] == 500

class TestBIMPublicImportSecurity:
    """Test per la sicurezza dell'import BIM pubblico."""
    
    def test_log_security_event_on_success(self, test_user_with_bim_public_permissions, test_house):
        """Test che l'evento di sicurezza sia loggato su successo."""
        user, tenant_id, session = test_user_with_bim_public_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Mock del servizio di import
        with patch('app.routers.bim_public.BIMPublicImportService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            mock_service.download_and_validate_file = AsyncMock(return_value={
                "content": b"fake_bim_content",
                "filename": "test_model.ifc",
                "content_type": "application/octet-stream",
                "file_size": 1024
            })
            
            # Mock del servizio MinIO
            with patch('app.routers.bim_public.get_minio_service') as mock_minio:
                mock_minio.return_value.client = None
                
                # Mock del parser BIM
                with patch('app.routers.bim_public.bim_parser') as mock_parser:
                    mock_parser.parse_bim_file = AsyncMock(return_value={
                        "parsing_success": True
                    })
                    
                    # Mock del logging di sicurezza
                    with patch('app.routers.bim_public.log_security_event') as mock_log:
                        response = client.post(
                            "/api/v1/bim/public/download",
                            headers=headers,
                            data={
                                "url": "https://geoportale.regione.lazio.it/bim/modelo.ifc",
                                "house_id": test_house.id,
                                "source_repository": "geoportale_regionale"
                            }
                        )
                        
                        # Verifica che l'evento sia stato loggato
                        mock_log.assert_called_once()
                        call_args = mock_log.call_args
                        assert call_args[1]["event_type"] == "bim_public_import"
                        assert call_args[1]["user_id"] == user.id
                        assert call_args[1]["tenant_id"] == tenant_id
                        assert call_args[1]["details"]["import_success"] == True
    
    def test_log_security_event_on_failure(self, test_user_with_bim_public_permissions):
        """Test che l'evento di sicurezza sia loggato su fallimento."""
        user, tenant_id, session = test_user_with_bim_public_permissions
        headers = get_auth_headers(user, tenant_id)
        
        # Mock del servizio di import che fallisce
        with patch('app.routers.bim_public.BIMPublicImportService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            mock_service.download_and_validate_file = AsyncMock(side_effect=Exception("Download failed"))
            
            # Mock del logging di sicurezza
            with patch('app.routers.bim_public.log_security_event') as mock_log:
                try:
                    response = client.post(
                        "/api/v1/bim/public/download",
                        headers=headers,
                        data={
                            "url": "https://geoportale.regione.lazio.it/bim/modelo.ifc",
                            "source_repository": "geoportale_regionale"
                        }
                    )
                except:
                    pass
                
                # Verifica che l'evento di fallimento sia stato loggato
                mock_log.assert_called_once()
                call_args = mock_log.call_args
                assert call_args[1]["event_type"] == "bim_public_import_failed"
                assert call_args[1]["details"]["import_success"] == False

class TestBIMPublicImportPermissions:
    """Test per i permessi di import BIM pubblico."""
    
    def test_download_bim_requires_upload_bim_permission(self, session):
        """Test che il download richieda il permesso upload_bim."""
        # Crea utente senza permessi BIM
        user, tenant_id = create_test_user_with_tenant(session)
        headers = get_auth_headers(user, tenant_id)
        
        response = client.post(
            "/api/v1/bim/public/download",
            headers=headers,
            data={
                "url": "https://geoportale.regione.lazio.it/bim/modelo.ifc",
                "source_repository": "geoportale_regionale"
            }
        )
        
        # Dovrebbe restituire 403 Forbidden
        assert response.status_code == 403
    
    def test_get_sources_requires_read_bim_models_permission(self, session):
        """Test che l'ottenimento delle fonti richieda il permesso read_bim_models."""
        # Crea utente senza permessi BIM
        user, tenant_id = create_test_user_with_tenant(session)
        headers = get_auth_headers(user, tenant_id)
        
        response = client.get("/api/v1/bim/public/sources", headers=headers)
        
        # Dovrebbe restituire 403 Forbidden
        assert response.status_code == 403

if __name__ == "__main__":
    pytest.main([__file__]) 