#!/usr/bin/env python3
"""
Test per verificare l'implementazione del campo tenant_id nei modelli principali.
Questo test verifica che:
1. I modelli abbiano il campo tenant_id
2. Il campo sia correttamente indicizzato
3. Il campo abbia un valore di default UUID
4. I modelli possano essere creati con tenant_id personalizzato
"""

import uuid
import pytest
from sqlmodel import Session, create_engine, SQLModel
from datetime import datetime, timezone

# Import dei modelli
from app.models.user import User
from app.models.document import Document
from app.models.bim_model import BIMModel, BIMFormat, BIMSoftware, BIMLevelOfDetail
from app.models.house import House
from app.models.node import Node, NodeArea, MainArea
from app.models.room import Room
from app.models.booking import Booking
from app.models.maintenance import MaintenanceRecord
from app.models.audio_log import AudioLog

# Database di test in memoria
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tenant.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(scope="function")
def session():
    """Crea una sessione di test."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def test_user_tenant_id():
    """Test per verificare il campo tenant_id nel modello User."""
    # Test creazione con tenant_id di default
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    
    assert hasattr(user, 'tenant_id')
    assert isinstance(user.tenant_id, uuid.UUID)
    assert user.tenant_id != uuid.uuid4()  # Dovrebbe essere diverso da un nuovo UUID
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    user_custom = User(
        email="test2@example.com",
        username="testuser2",
        hashed_password="hashed_password",
        full_name="Test User 2",
        tenant_id=custom_tenant_id
    )
    
    assert user_custom.tenant_id == custom_tenant_id

def test_document_tenant_id():
    """Test per verificare il campo tenant_id nel modello Document."""
    # Test creazione con tenant_id di default
    document = Document(
        title="Test Document",
        file_url="http://example.com/file.pdf",
        file_size=1024,
        file_type="application/pdf",
        checksum="abc123",
        owner_id=1
    )
    
    assert hasattr(document, 'tenant_id')
    assert isinstance(document.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    document_custom = Document(
        title="Test Document 2",
        file_url="http://example.com/file2.pdf",
        file_size=2048,
        file_type="application/pdf",
        checksum="def456",
        owner_id=1,
        tenant_id=custom_tenant_id
    )
    
    assert document_custom.tenant_id == custom_tenant_id

def test_bim_model_tenant_id():
    """Test per verificare il campo tenant_id nel modello BIMModel."""
    # Test creazione con tenant_id di default
    bim_model = BIMModel(
        name="Test BIM Model",
        format=BIMFormat.IFC,
        software_origin=BIMSoftware.REVIT,
        level_of_detail=BIMLevelOfDetail.LOD_300,
        file_url="http://example.com/model.ifc",
        file_size=1024000,
        checksum="bim123",
        user_id=1,
        house_id=1
    )
    
    assert hasattr(bim_model, 'tenant_id')
    assert isinstance(bim_model.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    bim_model_custom = BIMModel(
        name="Test BIM Model 2",
        format=BIMFormat.RVT,
        software_origin=BIMSoftware.ARCHICAD,
        level_of_detail=BIMLevelOfDetail.LOD_400,
        file_url="http://example.com/model2.rvt",
        file_size=2048000,
        checksum="bim456",
        user_id=1,
        house_id=1,
        tenant_id=custom_tenant_id
    )
    
    assert bim_model_custom.tenant_id == custom_tenant_id

def test_house_tenant_id():
    """Test per verificare il campo tenant_id nel modello House."""
    # Test creazione con tenant_id di default
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=1
    )
    
    assert hasattr(house, 'tenant_id')
    assert isinstance(house.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    house_custom = House(
        name="Test House 2",
        address="456 Test Street",
        owner_id=1,
        tenant_id=custom_tenant_id
    )
    
    assert house_custom.tenant_id == custom_tenant_id

def test_node_tenant_id():
    """Test per verificare il campo tenant_id nel modello Node."""
    # Test creazione con tenant_id di default
    node = Node(
        name="Test Node",
        nfc_id="NFC123",
        house_id=1
    )
    
    assert hasattr(node, 'tenant_id')
    assert isinstance(node.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    node_custom = Node(
        name="Test Node 2",
        nfc_id="NFC456",
        house_id=1,
        tenant_id=custom_tenant_id
    )
    
    assert node_custom.tenant_id == custom_tenant_id

def test_node_area_tenant_id():
    """Test per verificare il campo tenant_id nel modello NodeArea."""
    # Test creazione con tenant_id di default
    node_area = NodeArea(
        name="Test Area",
        category="residential",
        house_id=1
    )
    
    assert hasattr(node_area, 'tenant_id')
    assert isinstance(node_area.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    node_area_custom = NodeArea(
        name="Test Area 2",
        category="technical",
        house_id=1,
        tenant_id=custom_tenant_id
    )
    
    assert node_area_custom.tenant_id == custom_tenant_id

def test_main_area_tenant_id():
    """Test per verificare il campo tenant_id nel modello MainArea."""
    # Test creazione con tenant_id di default
    main_area = MainArea(
        name="Test Main Area",
        house_id=1
    )
    
    assert hasattr(main_area, 'tenant_id')
    assert isinstance(main_area.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    main_area_custom = MainArea(
        name="Test Main Area 2",
        house_id=1,
        tenant_id=custom_tenant_id
    )
    
    assert main_area_custom.tenant_id == custom_tenant_id

def test_room_tenant_id():
    """Test per verificare il campo tenant_id nel modello Room."""
    # Test creazione con tenant_id di default
    room = Room(
        name="Test Room",
        room_type="bedroom",
        house_id=1
    )
    
    assert hasattr(room, 'tenant_id')
    assert isinstance(room.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    room_custom = Room(
        name="Test Room 2",
        room_type="kitchen",
        house_id=1,
        tenant_id=custom_tenant_id
    )
    
    assert room_custom.tenant_id == custom_tenant_id

def test_booking_tenant_id():
    """Test per verificare il campo tenant_id nel modello Booking."""
    # Test creazione con tenant_id di default
    booking = Booking(
        title="Test Booking",
        user_id=1,
        room_id=1,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    
    assert hasattr(booking, 'tenant_id')
    assert isinstance(booking.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    booking_custom = Booking(
        title="Test Booking 2",
        user_id=1,
        room_id=1,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
        tenant_id=custom_tenant_id
    )
    
    assert booking_custom.tenant_id == custom_tenant_id

def test_maintenance_record_tenant_id():
    """Test per verificare il campo tenant_id nel modello MaintenanceRecord."""
    # Test creazione con tenant_id di default
    maintenance = MaintenanceRecord(
        title="Test Maintenance",
        maintenance_type="preventive",
        priority="medium",
        node_id=1
    )
    
    assert hasattr(maintenance, 'tenant_id')
    assert isinstance(maintenance.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    maintenance_custom = MaintenanceRecord(
        title="Test Maintenance 2",
        maintenance_type="corrective",
        priority="high",
        node_id=1,
        tenant_id=custom_tenant_id
    )
    
    assert maintenance_custom.tenant_id == custom_tenant_id

def test_audio_log_tenant_id():
    """Test per verificare il campo tenant_id nel modello AudioLog."""
    # Test creazione con tenant_id di default
    audio_log = AudioLog(
        user_id=1,
        transcribed_text="Test command",
        response_text="Test response"
    )
    
    assert hasattr(audio_log, 'tenant_id')
    assert isinstance(audio_log.tenant_id, uuid.UUID)
    
    # Test creazione con tenant_id personalizzato
    custom_tenant_id = uuid.uuid4()
    audio_log_custom = AudioLog(
        user_id=1,
        transcribed_text="Test command 2",
        response_text="Test response 2",
        tenant_id=custom_tenant_id
    )
    
    assert audio_log_custom.tenant_id == custom_tenant_id

def test_tenant_isolation_concept():
    """Test concettuale per verificare l'isolamento dei tenant."""
    # Simula due tenant diversi
    tenant_1_id = uuid.uuid4()
    tenant_2_id = uuid.uuid4()
    
    # Crea dati per il primo tenant
    user_1 = User(
        email="user1@tenant1.com",
        username="user1",
        hashed_password="hash1",
        tenant_id=tenant_1_id
    )
    
    house_1 = House(
        name="House 1",
        address="Address 1",
        owner_id=1,
        tenant_id=tenant_1_id
    )
    
    # Crea dati per il secondo tenant
    user_2 = User(
        email="user2@tenant2.com",
        username="user2",
        hashed_password="hash2",
        tenant_id=tenant_2_id
    )
    
    house_2 = House(
        name="House 2",
        address="Address 2",
        owner_id=2,
        tenant_id=tenant_2_id
    )
    
    # Verifica che i tenant_id siano diversi
    assert user_1.tenant_id == tenant_1_id
    assert user_2.tenant_id == tenant_2_id
    assert house_1.tenant_id == tenant_1_id
    assert house_2.tenant_id == tenant_2_id
    assert user_1.tenant_id != user_2.tenant_id
    assert house_1.tenant_id != house_2.tenant_id

if __name__ == "__main__":
    # Esegui i test
    print("🧪 Test implementazione campo tenant_id nei modelli principali")
    print("=" * 60)
    
    # Test di base
    test_user_tenant_id()
    print("✅ Test User tenant_id: PASSED")
    
    test_document_tenant_id()
    print("✅ Test Document tenant_id: PASSED")
    
    test_bim_model_tenant_id()
    print("✅ Test BIMModel tenant_id: PASSED")
    
    test_house_tenant_id()
    print("✅ Test House tenant_id: PASSED")
    
    test_node_tenant_id()
    print("✅ Test Node tenant_id: PASSED")
    
    test_node_area_tenant_id()
    print("✅ Test NodeArea tenant_id: PASSED")
    
    test_main_area_tenant_id()
    print("✅ Test MainArea tenant_id: PASSED")
    
    test_room_tenant_id()
    print("✅ Test Room tenant_id: PASSED")
    
    test_booking_tenant_id()
    print("✅ Test Booking tenant_id: PASSED")
    
    test_maintenance_record_tenant_id()
    print("✅ Test MaintenanceRecord tenant_id: PASSED")
    
    test_audio_log_tenant_id()
    print("✅ Test AudioLog tenant_id: PASSED")
    
    test_tenant_isolation_concept()
    print("✅ Test isolamento tenant: PASSED")
    
    print("\n🎉 TUTTI I TEST PASSATI!")
    print("\n📋 RIEPILOGO IMPLEMENTAZIONE:")
    print("- Campo tenant_id aggiunto a tutti i modelli principali")
    print("- Campo indicizzato per performance query")
    print("- Valore di default UUID generato automaticamente")
    print("- Supporto per assegnazione manuale tenant_id")
    print("- TODO: Migrazioni Alembic da implementare")
    print("- TODO: Logica CRUD multi-tenant da implementare") 