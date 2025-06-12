import pytest
from sqlmodel import Session
from datetime import datetime, timezone
from app.models.user import User
from app.models.house import House
from app.models.room import Room
from app.models.node import Node
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.booking import Booking
from app.models.maintenance import MaintenanceRecord
from sqlalchemy import delete

@pytest.fixture(autouse=True)
def cleanup_database(session: Session):
    """Clean up the database before each test."""
    # Clean up in reverse order of dependencies
    session.exec(delete(MaintenanceRecord))
    session.exec(delete(Booking))
    session.exec(delete(DocumentVersion))
    session.exec(delete(Document))
    session.exec(delete(Node))
    session.exec(delete(Room))
    session.exec(delete(House))
    session.exec(delete(User))
    session.commit()
    yield
    # Clean up after test
    session.exec(delete(MaintenanceRecord))
    session.exec(delete(Booking))
    session.exec(delete(DocumentVersion))
    session.exec(delete(Document))
    session.exec(delete(Node))
    session.exec(delete(Room))
    session.exec(delete(House))
    session.exec(delete(User))
    session.commit()

@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def house(session: Session, user: User) -> House:
    """Create a test house."""
    house = House(
        name="Test House",
        address="123 Test St",
        owner_id=user.id
    )
    session.add(house)
    session.commit()
    session.refresh(house)
    return house

@pytest.fixture
def room(session: Session, house: House) -> Room:
    """Create a test room."""
    room = Room(
        name="Test Room",
        house_id=house.id,
        floor=1,
        area=25.5
    )
    session.add(room)
    session.commit()
    session.refresh(room)
    return room

@pytest.fixture
def node(session: Session, house: House, room: Room) -> Node:
    """Create a test node."""
    node = Node(
        name="Test Node",
        nfc_id="NFC123456",
        house_id=house.id,
        room_id=room.id
    )
    session.add(node)
    session.commit()
    session.refresh(node)
    return node

@pytest.fixture
def document(session: Session, user: User, house: House, node: Node) -> Document:
    """Create a test document."""
    document = Document(
        title="Test Document",
        description="Test Description",
        owner_id=user.id,
        name="manuale_test.pdf",
        type="application/pdf",
        size=1024,
        path="/documents/manuali/manuale_test.pdf",
        checksum="abc123",
        house_id=house.id,
        node_id=node.id
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document

@pytest.fixture
def document_version(session: Session, document: Document, user: User) -> DocumentVersion:
    """Create a test document version."""
    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        file_path="/test/path",
        file_size=1000,
        checksum="checksum123",
        created_by_id=user.id
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return version

@pytest.fixture
def booking(session: Session, room: Room, user: User) -> Booking:
    """Create a test booking."""
    booking = Booking(
        room_id=room.id,
        user_id=user.id,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status="confirmed"
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking

@pytest.fixture
def maintenance_record(session: Session, node: Node) -> MaintenanceRecord:
    """Create a test maintenance record."""
    record = MaintenanceRecord(
        node_id=node.id,
        maintenance_type="routine",
        description="Test maintenance",
        status="pending"
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

def test_user_creation(user: User):
    """Test user creation."""
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.is_active is True
    assert user.is_superuser is False

def test_house_creation(house: House):
    """Test house creation."""
    assert house.id is not None
    assert house.name == "Test House"
    assert house.address == "123 Test St"

def test_room_creation(room: Room):
    """Test room creation."""
    assert room.id is not None
    assert room.name == "Test Room"
    assert room.floor == 1
    assert room.area == 25.5

def test_node_creation(node: Node):
    """Test node creation."""
    assert node.id is not None
    assert node.name == "Test Node"
    assert node.nfc_id == "NFC123456"
    assert node.house_id is not None
    assert node.room_id is not None

def test_document_creation(document: Document):
    """Test document creation."""
    assert document.id is not None
    assert document.title == "Test Document"
    assert document.description == "Test Description"
    assert document.name == "manuale_test.pdf"
    assert document.type == "application/pdf"
    assert document.size == 1024
    assert document.path == "/documents/manuali/manuale_test.pdf"
    assert document.checksum == "abc123"

def test_document_version_creation(document_version: DocumentVersion):
    """Test document version creation."""
    assert document_version.id is not None
    assert document_version.version_number == 1
    assert document_version.file_path == "/test/path"
    assert document_version.file_size == 1000
    assert document_version.checksum == "checksum123"

def test_booking_creation(booking: Booking):
    """Test booking creation."""
    assert booking.id is not None
    assert booking.status == "confirmed"

def test_maintenance_record_creation(maintenance_record: MaintenanceRecord):
    """Test maintenance record creation."""
    assert maintenance_record.id is not None
    assert maintenance_record.description == "Test maintenance"
    assert maintenance_record.status == "pending"
    assert maintenance_record.maintenance_type == "routine" 