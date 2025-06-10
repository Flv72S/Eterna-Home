import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, UTC
from app.main import app
from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.node import Node
import logging
from tests.utils import get_superuser_token_headers

# Configura il logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def test_node(db):
    """Fixture per creare un nodo di test."""
    logger.info("Creazione nodo di test...")
    node = Node(
        name="Test Node",
        type="sensor",
        location="Test Location",
        status="active"
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    logger.info(f"Nodo creato con ID: {node.id}")
    return node

@pytest.fixture
def test_maintenance_record(db, test_node):
    """Fixture per creare un record di manutenzione di test."""
    logger.info("Creazione record di manutenzione di test...")
    record = MaintenanceRecord(
        node_id=test_node.id,
        type="preventive",
        description="Test maintenance",
        status=MaintenanceStatus.COMPLETED,
        date=datetime.now(UTC),
        notes="Test notes"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Record creato con ID: {record.id}")
    return record

def test_node_creation(test_node):
    """Test la creazione di un nodo."""
    assert test_node.id is not None
    assert test_node.type == "sensor"
    assert test_node.status == "active"

def test_maintenance_record_creation(test_maintenance_record, test_node):
    """Test la creazione di un record di manutenzione."""
    assert test_maintenance_record.id is not None
    assert test_maintenance_record.node_id == test_node.id
    assert test_maintenance_record.type == "preventive"
    assert test_maintenance_record.status == MaintenanceStatus.COMPLETED

def test_export_json(client, test_maintenance_record):
    """Test l'endpoint di export JSON."""
    logger.info("Test endpoint export JSON...")
    response = client.get("/api/v1/maintenance_records/export?format=json", headers=get_superuser_token_headers(client))
    logger.info(f"Status code: {response.status_code}")
    logger.info(f"Headers: {response.headers}")
    assert response.status_code == 200
    data = response.json()
    logger.info(f"Numero di record: {len(data)}")
    if data:
        logger.info(f"Esempio di record: {data[0]}")
    assert len(data) > 0

def test_export_csv(client, test_maintenance_record):
    """Test l'endpoint di export CSV."""
    logger.info("Test endpoint export CSV...")
    response = client.get("/api/v1/maintenance_records/export?format=csv", headers=get_superuser_token_headers(client))
    logger.info(f"Status code: {response.status_code}")
    logger.info(f"Headers: {response.headers}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    logger.info(f"Contenuto CSV: {response.text[:200]}...") 