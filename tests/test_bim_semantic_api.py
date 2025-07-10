import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool
import uuid
import json

from app.main import app
from app.models.bim_fragment import BIMFragment
from app.models.bim_model import BIMModel
from app.models.node import Node
from app.models.user import User
from app.utils.security import create_access_token
from app.core.logging_config import get_logger

logger = get_logger(__name__)

@pytest.fixture
def test_engine():
    """Crea un engine di test per il database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    from app.models.bim_fragment import BIMFragment
    from app.models.bim_model import BIMModel
    from app.models.node import Node
    from app.models.user import User
    
    # Crea le tabelle
    BIMFragment.metadata.create_all(engine)
    BIMModel.metadata.create_all(engine)
    Node.metadata.create_all(engine)
    User.metadata.create_all(engine)
    
    return engine

@pytest.fixture
def test_session(test_engine):
    """Crea una sessione di test per il database."""
    with Session(test_engine) as session:
        yield session

@pytest.fixture
def test_client(test_engine):
    """Crea un client di test per l'API."""
    def override_get_session():
        with Session(test_engine) as session:
            yield session
    
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(test_session):
    """Crea un utente di test."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
        tenant_id=uuid.uuid4()
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user

@pytest.fixture
def test_user_token(test_user):
    """Crea un token di accesso per l'utente di test."""
    return create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_user.tenant_id)
    })

@pytest.fixture
def mock_ifc_file():
    """Crea un file IFC di test."""
    ifc_content = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test User'),('Test Organization'),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('2O2Fr$t4X7Zf8NOew3FNrX',$,'Test Project',$,$,$,$,(#2),#3);
#2=IFCOWNERHISTORY(#4,$,.ADDED.,$,$,$,0);
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#5,$);
#4=IFCPERSONANDORGANIZATION(#6,#7,$);
#5=IFCAXIS2PLACEMENT3D(#8,$,$);
#6=IFCPERSON($,$,'Test User',$,$,$);
#7=IFCORGANIZATION($,'Test Organization',$,$,$);
#8=IFCCARTESIANPOINT((0.,0.,0.));
#9=IFCDIRECTION((0.,0.,1.));
#10=IFCDIRECTION((1.,0.,0.));
#11=IFCAXIS2PLACEMENT3D(#8,#9,#10);
#12=IFCLOCALPLACEMENT($,#11);
#13=IFCBUILDING('2O2Fr$t4X7Zf8NOew3FNrX',$,'Test Building',$,$,#12,$,$,.ELEMENT.,$,$,$);
#14=IFCBUILDINGSTOREY('2O2Fr$t4X7Zf8NOew3FNrX',$,'Piano Terra',$,0.,#12,$,$,.ELEMENT.,$);
#15=IFCSPACE('2O2Fr$t4X7Zf8NOew3FNrX',$,'Soggiorno',$,$,#12,$,$,.ELEMENT.,$,$,$);
#16=IFCWALL('2O2Fr$t4X7Zf8NOew3FNrX',$,'Muro Esterno',$,$,#12,$,$,.ELEMENT.,$);
#17=IFCAIRTERMINAL('2O2Fr$t4X7Zf8NOew3FNrX',$,'Terminale Aria',$,$,#12,$,$,.ELEMENT.,$);
ENDSEC;
END-ISO-10303-21;"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        f.write(ifc_content)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestBIMSemanticAPI:
    """Test per l'API BIM semantico."""
    
    @patch('app.services.bim_parser.ifcopenshell')
    def test_upload_bim_semantic_success(self, mock_ifcopenshell, test_client, test_user, test_user_token, mock_ifc_file):
        """Test che l'upload di un file BIM semantico funziona correttamente."""
        # Mock ifcopenshell
        mock_ifc_file_obj = Mock()
        mock_ifcopenshell.open.return_value = mock_ifc_file_obj
        
        # Mock entità IFC
        mock_space = Mock()
        mock_space.GlobalId = "2O2Fr$t4X7Zf8NOew3FNrX"
        mock_space.Name = "Soggiorno"
        mock_space.is_a.return_value = "IFCSPACE"
        mock_space.id.return_value = 15
        
        mock_wall = Mock()
        mock_wall.GlobalId = "2O2Fr$t4X7Zf8NOew3FNrX"
        mock_wall.Name = "Muro Esterno"
        mock_wall.is_a.return_value = "IFCWALL"
        mock_wall.id.return_value = 16
        
        # Mock metodi by_type
        mock_ifc_file_obj.by_type.side_effect = lambda entity_type: {
            'IFCSPACE': [mock_space],
            'IFCWALL': [mock_wall],
            'IFCBUILDINGSTOREY': [],
            'IFCAIRTERMINAL': []
        }.get(entity_type, [])
        
        # Mock ifcopenshell.util.element.get_psets
        with patch('app.services.bim_parser.ifcopenshell.util.element.get_psets') as mock_get_psets:
            mock_get_psets.return_value = {
                'Pset_SpaceCommon': {
                    'Area': 25.5,
                    'Volume': 76.5
                }
            }
            
            # Mock ifcopenshell.util.shape.get_shape
            with patch('app.services.bim_parser.ifcopenshell.util.shape.get_shape') as mock_get_shape:
                mock_shape = Mock()
                mock_shape.bbox.return_value = [0.0, 0.0, 0.0, 5.0, 5.0, 3.0]
                mock_get_shape.return_value = mock_shape
                
                # Mock get_current_user
                with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
                    mock_get_current_user.return_value = test_user
                    
                    # Esegui upload
                    with open(mock_ifc_file, 'rb') as f:
                        response = test_client.post(
                            "/api/v1/bim/semantic-upload",
                            files={"file": ("test.ifc", f, "application/octet-stream")},
                            headers={"Authorization": f"Bearer {test_user_token}"}
                        )
                    
                    # Verifica risposta
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert "bim_model_id" in data
                    assert "fragments_count" in data
                    assert "nodes_created" in data
                    assert "processing_time" in data
                    assert "message" in data
                    
                    assert data["fragments_count"] > 0
                    assert data["nodes_created"] > 0
                    assert data["processing_time"] > 0
    
    def test_upload_bim_unsupported_format(self, test_client, test_user_token):
        """Test che i formati non supportati vengono rifiutati."""
        # Mock get_current_user
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            # Crea un file di test con formato non supportato
            test_content = b"This is not a BIM file"
            
            response = test_client.post(
                "/api/v1/bim/semantic-upload",
                files={"file": ("test.txt", test_content, "text/plain")},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Formato file non supportato" in data["detail"]
    
    def test_upload_bim_unauthorized(self, test_client):
        """Test che l'upload senza autenticazione viene rifiutato."""
        test_content = b"This is a test file"
        
        response = test_client.post(
            "/api/v1/bim/semantic-upload",
            files={"file": ("test.ifc", test_content, "application/octet-stream")}
        )
        
        assert response.status_code == 401
    
    def test_get_bim_fragments_success(self, test_client, test_user, test_user_token, test_session):
        """Test che il recupero dei frammenti BIM funziona correttamente."""
        # Crea frammenti di test
        fragment1 = BIMFragment(
            tenant_id=test_user.tenant_id,
            house_id=1,
            bim_model_id=1,
            entity_type='room',
            entity_name='Soggiorno',
            area=25.5,
            volume=76.5,
            level=1
        )
        
        fragment2 = BIMFragment(
            tenant_id=test_user.tenant_id,
            house_id=1,
            bim_model_id=1,
            entity_type='wall',
            entity_name='Muro Esterno',
            level=1
        )
        
        test_session.add(fragment1)
        test_session.add(fragment2)
        test_session.commit()
        
        # Mock get_current_user
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            response = test_client.get(
                "/api/v1/bim/fragments/1",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "fragments" in data
            assert "total" in data
            assert "page" in data
            assert "size" in data
            
            assert data["total"] == 2
            assert len(data["fragments"]) == 2
            
            # Verifica che i frammenti contengano i dati corretti
            fragment_names = [f["entity_name"] for f in data["fragments"]]
            assert "Soggiorno" in fragment_names
            assert "Muro Esterno" in fragment_names
    
    def test_get_bim_fragments_with_filters(self, test_client, test_user, test_user_token, test_session):
        """Test che i filtri sui frammenti BIM funzionano correttamente."""
        # Crea frammenti di test con diversi tipi
        fragment1 = BIMFragment(
            tenant_id=test_user.tenant_id,
            house_id=1,
            bim_model_id=1,
            entity_type='room',
            entity_name='Soggiorno',
            area=25.5,
            level=1
        )
        
        fragment2 = BIMFragment(
            tenant_id=test_user.tenant_id,
            house_id=1,
            bim_model_id=1,
            entity_type='hvac',
            entity_name='Terminale Aria',
            level=1
        )
        
        fragment3 = BIMFragment(
            tenant_id=test_user.tenant_id,
            house_id=1,
            bim_model_id=1,
            entity_type='room',
            entity_name='Camera da Letto',
            area=15.0,
            level=2
        )
        
        test_session.add_all([fragment1, fragment2, fragment3])
        test_session.commit()
        
        # Mock get_current_user
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            # Test filtro per tipo
            response = test_client.get(
                "/api/v1/bim/fragments/1?entity_type=room",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert all(f["entity_type"] == "room" for f in data["fragments"])
            
            # Test filtro per livello
            response = test_client.get(
                "/api/v1/bim/fragments/1?level=1",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert all(f["level"] == 1 for f in data["fragments"])
            
            # Test filtro per area minima
            response = test_client.get(
                "/api/v1/bim/fragments/1?min_area=20.0",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["fragments"][0]["entity_name"] == "Soggiorno"
            
            # Test ricerca nel nome
            response = test_client.get(
                "/api/v1/bim/fragments/1?search=Soggiorno",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["fragments"][0]["entity_name"] == "Soggiorno"
    
    def test_get_bim_fragments_pagination(self, test_client, test_user, test_user_token, test_session):
        """Test che la paginazione dei frammenti BIM funziona correttamente."""
        # Crea molti frammenti di test
        fragments = []
        for i in range(25):
            fragment = BIMFragment(
                tenant_id=test_user.tenant_id,
                house_id=1,
                bim_model_id=1,
                entity_type='room',
                entity_name=f'Stanza {i}',
                area=20.0,
                level=1
            )
            fragments.append(fragment)
        
        test_session.add_all(fragments)
        test_session.commit()
        
        # Mock get_current_user
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            # Test prima pagina
            response = test_client.get(
                "/api/v1/bim/fragments/1?page=1&size=10",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 25
            assert data["page"] == 1
            assert data["size"] == 10
            assert len(data["fragments"]) == 10
            
            # Test seconda pagina
            response = test_client.get(
                "/api/v1/bim/fragments/1?page=2&size=10",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2
            assert len(data["fragments"]) == 10
    
    def test_get_bim_fragments_stats(self, test_client, test_user, test_user_token, test_session):
        """Test che le statistiche dei frammenti BIM funzionano correttamente."""
        # Crea frammenti di test con diversi tipi e livelli
        fragments = [
            BIMFragment(
                tenant_id=test_user.tenant_id,
                house_id=1,
                bim_model_id=1,
                entity_type='room',
                entity_name='Soggiorno',
                area=25.5,
                volume=76.5,
                level=1
            ),
            BIMFragment(
                tenant_id=test_user.tenant_id,
                house_id=1,
                bim_model_id=1,
                entity_type='room',
                entity_name='Camera da Letto',
                area=15.0,
                volume=45.0,
                level=1
            ),
            BIMFragment(
                tenant_id=test_user.tenant_id,
                house_id=1,
                bim_model_id=1,
                entity_type='hvac',
                entity_name='Terminale Aria',
                level=1
            ),
            BIMFragment(
                tenant_id=test_user.tenant_id,
                house_id=1,
                bim_model_id=1,
                entity_type='room',
                entity_name='Bagno',
                area=8.0,
                volume=24.0,
                level=2
            )
        ]
        
        test_session.add_all(fragments)
        test_session.commit()
        
        # Mock get_current_user
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            response = test_client.get(
                "/api/v1/bim/fragments/1/stats",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "total_fragments" in data
            assert "fragments_by_type" in data
            assert "total_area" in data
            assert "total_volume" in data
            assert "levels" in data
            
            assert data["total_fragments"] == 4
            assert data["fragments_by_type"]["room"] == 3
            assert data["fragments_by_type"]["hvac"] == 1
            assert data["total_area"] == 48.5  # 25.5 + 15.0 + 8.0
            assert data["total_volume"] == 145.5  # 76.5 + 45.0 + 24.0
            assert set(data["levels"]) == {1, 2}
    
    def test_get_bim_fragment_by_id(self, test_client, test_user, test_user_token, test_session):
        """Test che il recupero di un singolo frammento BIM funziona correttamente."""
        # Crea un frammento di test
        fragment = BIMFragment(
            tenant_id=test_user.tenant_id,
            house_id=1,
            bim_model_id=1,
            entity_type='room',
            entity_name='Soggiorno',
            area=25.5,
            volume=76.5,
            level=1,
            ifc_guid='2O2Fr$t4X7Zf8NOew3FNrX',
            bounding_box={
                'x_min': 0.0, 'y_min': 0.0, 'z_min': 0.0,
                'x_max': 5.0, 'y_max': 5.0, 'z_max': 3.0
            },
            metadata={'usage': 'living', 'occupancy': 4}
        )
        
        test_session.add(fragment)
        test_session.commit()
        
        # Mock get_current_user
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            response = test_client.get(
                f"/api/v1/bim/fragments/1/{fragment.id}",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == fragment.id
            assert data["entity_type"] == "room"
            assert data["entity_name"] == "Soggiorno"
            assert data["area"] == 25.5
            assert data["volume"] == 76.5
            assert data["level"] == 1
            assert data["ifc_guid"] == "2O2Fr$t4X7Zf8NOew3FNrX"
            assert data["bounding_box"] is not None
            assert data["metadata"] is not None
            assert data["display_name"] == "Soggiorno (room)"
            assert data["has_geometry"] == True
            assert data["dimensions"] is not None
    
    def test_get_bim_fragment_not_found(self, test_client, test_user, test_user_token):
        """Test che un frammento BIM inesistente restituisce 404."""
        # Mock get_current_user
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            response = test_client.get(
                "/api/v1/bim/fragments/1/999",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "Frammento BIM non trovato" in data["detail"]
    
    def test_delete_bim_fragment_success(self, test_client, test_user, test_user_token, test_session):
        """Test che l'eliminazione di un frammento BIM funziona correttamente."""
        # Crea un frammento di test
        fragment = BIMFragment(
            tenant_id=test_user.tenant_id,
            house_id=1,
            bim_model_id=1,
            entity_type='room',
            entity_name='Soggiorno',
            area=25.5,
            level=1
        )
        
        test_session.add(fragment)
        test_session.commit()
        fragment_id = fragment.id
        
        # Mock get_current_user
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            response = test_client.delete(
                f"/api/v1/bim/fragments/1/{fragment_id}",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "Frammento BIM eliminato con successo" in data["message"]
            
            # Verifica che il frammento sia stato eliminato
            deleted_fragment = test_session.get(BIMFragment, fragment_id)
            assert deleted_fragment is None
    
    def test_delete_bim_fragment_not_found(self, test_client, test_user, test_user_token):
        """Test che l'eliminazione di un frammento BIM inesistente restituisce 404."""
        # Mock get_current_user
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = test_user
            
            response = test_client.delete(
                "/api/v1/bim/fragments/1/999",
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "Frammento BIM non trovato" in data["detail"]
    
    def test_multi_tenant_isolation(self, test_client, test_session):
        """Test che l'isolamento multi-tenant funziona correttamente."""
        # Crea due utenti con tenant diversi
        tenant1_id = uuid.uuid4()
        tenant2_id = uuid.uuid4()
        
        user1 = User(
            email="user1@example.com",
            hashed_password="hashed_password",
            full_name="User 1",
            is_active=True,
            tenant_id=tenant1_id
        )
        
        user2 = User(
            email="user2@example.com",
            hashed_password="hashed_password",
            full_name="User 2",
            is_active=True,
            tenant_id=tenant2_id
        )
        
        test_session.add_all([user1, user2])
        test_session.commit()
        
        # Crea frammenti per entrambi i tenant
        fragment1 = BIMFragment(
            tenant_id=tenant1_id,
            house_id=1,
            bim_model_id=1,
            entity_type='room',
            entity_name='Soggiorno Tenant 1',
            area=25.5,
            level=1
        )
        
        fragment2 = BIMFragment(
            tenant_id=tenant2_id,
            house_id=1,
            bim_model_id=1,
            entity_type='room',
            entity_name='Soggiorno Tenant 2',
            area=30.0,
            level=1
        )
        
        test_session.add_all([fragment1, fragment2])
        test_session.commit()
        
        # Crea token per entrambi gli utenti
        token1 = create_access_token(data={
            "sub": user1.email,
            "tenant_id": str(user1.tenant_id)
        })
        
        token2 = create_access_token(data={
            "sub": user2.email,
            "tenant_id": str(user2.tenant_id)
        })
        
        # Mock get_current_user per user1
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = user1
            
            response = test_client.get(
                "/api/v1/bim/fragments/1",
                headers={"Authorization": f"Bearer {token1}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["fragments"][0]["entity_name"] == "Soggiorno Tenant 1"
        
        # Mock get_current_user per user2
        with patch('app.routers.bim_semantic.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = user2
            
            response = test_client.get(
                "/api/v1/bim/fragments/1",
                headers={"Authorization": f"Bearer {token2}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["fragments"][0]["entity_name"] == "Soggiorno Tenant 2" 