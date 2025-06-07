import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, UTC
from app.main import app
from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.node import Node

# Usa i fixture definiti in conftest.py
# Non è necessario definire qui la configurazione del database

@pytest.fixture
def test_node(db):
    node = Node(
        name="Test Node",
        type="sensor",
        location="Test Location",
        status="active"
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node

@pytest.fixture
def test_maintenance_records(db, test_node):
    records = []
    for i in range(3):
        record = MaintenanceRecord(
            node_id=test_node.id,
            type="preventive",
            description=f"Test maintenance {i}",
            status=MaintenanceStatus.COMPLETED,
            date=datetime.now(UTC) - timedelta(days=i),
            notes=f"Test notes {i}"
        )
        db.add(record)
        records.append(record)
    db.commit()
    for record in records:
        db.refresh(record)
    return records

def test_export_csv(client, test_maintenance_records):
    response = client.get("/api/v1/maintenance_records/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "node_id,type,description,status" in response.text

def test_export_json(client, test_maintenance_records):
    response = client.get("/api/v1/maintenance_records/export?format=json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert len(data) == 3
    assert all(isinstance(record, dict) for record in data)

def test_export_filters(client, test_maintenance_records):
    response = client.get(
        "/api/v1/maintenance_records/export?format=json&status=completed"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(record["status"] == "COMPLETED" for record in data)

def test_export_invalid_format(client):
    response = client.get("/api/v1/maintenance_records/export?format=invalid")
    assert response.status_code == 422
    assert "Format must be either 'csv' or 'json'" in response.text

def test_export_date_range(client, test_maintenance_records):
    start_date = (datetime.now(UTC) - timedelta(days=2)).strftime("%Y-%m-%d")
    end_date = datetime.now(UTC).strftime("%Y-%m-%d")
    response = client.get(
        f"/api/v1/maintenance_records/export?format=json&start_date={start_date}&end_date={end_date}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_export_invalid_date_range(client):
    response = client.get(
        "/api/v1/maintenance_records/export?format=json&start_date=2025-01-01&end_date=2024-01-01"
    )
    assert response.status_code == 422
    assert "end_date must be after start_date" in response.text 