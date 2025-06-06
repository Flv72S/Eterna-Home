import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.node import Node
from app.core.config import settings

API_PREFIX = f"{settings.API_V1_STR}/maintenance_records"

def test_export_csv(client: TestClient, db):
    """Test per l'export dei record di manutenzione in formato CSV."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea alcuni record di manutenzione
    records = [
        MaintenanceRecord(
            node_id=node.id,
            date=datetime.utcnow(),
            type="Routine",
            description=f"Test maintenance {i}",
            status=MaintenanceStatus.PENDING,
            notes=f"Test notes {i}"
        ) for i in range(3)
    ]
    db.add_all(records)
    db.commit()

    # Test export CSV
    response = client.get(f"{API_PREFIX}/export?format=csv")
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    
    # Verifica il contenuto CSV
    content = response.text
    lines = content.strip().split("\n")
    assert len(lines) == 4  # Header + 3 record
    
    # Verifica header
    headers = lines[0].split(",")
    expected_headers = ["id", "node_id", "date", "type", "description", "status", "notes", "created_at", "updated_at"]
    assert all(h in headers for h in expected_headers)

def test_export_json(client: TestClient, db):
    """Test per l'export dei record di manutenzione in formato JSON."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea alcuni record di manutenzione
    records = [
        MaintenanceRecord(
            node_id=node.id,
            date=datetime.utcnow(),
            type="Routine",
            description=f"Test maintenance {i}",
            status=MaintenanceStatus.PENDING,
            notes=f"Test notes {i}"
        ) for i in range(3)
    ]
    db.add_all(records)
    db.commit()

    # Test export JSON
    response = client.get(f"{API_PREFIX}/export?format=json")
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    # Verifica il contenuto JSON
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    
    # Verifica la struttura dei record
    for record in data:
        assert "id" in record
        assert "node_id" in record
        assert "date" in record
        assert "type" in record
        assert "description" in record
        assert "status" in record
        assert "notes" in record

def test_export_filters(client: TestClient, db):
    """Test per l'export dei record di manutenzione con filtri."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record con stati diversi
    now = datetime.utcnow()
    records = [
        MaintenanceRecord(
            node_id=node.id,
            date=now,
            type="Routine",
            description="Test maintenance 1",
            status=MaintenanceStatus.PENDING,
            notes="Test notes 1"
        ),
        MaintenanceRecord(
            node_id=node.id,
            date=now,
            type="Emergency",
            description="Test maintenance 2",
            status=MaintenanceStatus.COMPLETED,
            notes="Test notes 2"
        )
    ]
    db.add_all(records)
    db.commit()

    # Test export con filtro status
    response = client.get(f"{API_PREFIX}/export?format=json&status=pending")
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"

    # Test export con filtro type
    response = client.get(f"{API_PREFIX}/export?format=json&record_type=Emergency")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "Emergency"

def test_export_invalid_format(client: TestClient):
    """Test per l'export con formato non valido."""
    response = client.get(f"{API_PREFIX}/export?format=invalid")
    assert response.status_code == 422

def test_export_invalid_date_range(client: TestClient):
    """Test per l'export con range date non valido."""
    response = client.get(f"{API_PREFIX}/export?start_date=2024-03-20&end_date=2024-03-19")
    assert response.status_code == 422 