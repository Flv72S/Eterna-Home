import pytest
from fastapi.testclient import TestClient
from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.node import Node
from datetime import datetime, timedelta
import pandas as pd
import json
import io
from sqlalchemy.orm import Session
from sqlalchemy import delete
from app.core.config import settings

API_PREFIX = f"{settings.API_V1_STR}/maintenance_records"

@pytest.fixture(autouse=True)
def setup_teardown(db: Session):
    """Setup e teardown per ogni test."""
    yield

def test_create_maintenance_record_api(client: TestClient, db):
    """Test per la creazione di un record di manutenzione tramite API."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()
    node_id = node.id

    # Dati per il nuovo record
    data = {
        "node_id": node_id,
        "date": datetime.utcnow().isoformat(),
        "type": "Routine",
        "description": "Test maintenance",
        "status": MaintenanceStatus.PENDING,
        "notes": "Test notes"
    }

    # Chiamata API
    response = client.post(f"{API_PREFIX}/", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["node_id"] == node_id
    assert result["type"] == "Routine"
    assert result["description"] == "Test maintenance"
    assert result["status"] == MaintenanceStatus.PENDING
    assert result["notes"] == "Test notes"

def test_read_maintenance_record_api(client: TestClient, db):
    """Test per la lettura di un record di manutenzione tramite API."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()
    node_id = node.id

    # Crea un record di manutenzione
    record = MaintenanceRecord(
        node_id=node_id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance",
        status=MaintenanceStatus.PENDING,
        notes="Test notes"
    )
    db.add(record)
    db.commit()
    record_id = record.id

    # Chiamata API
    response = client.get(f"{API_PREFIX}/{record_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == record_id
    assert result["node_id"] == node_id
    assert result["type"] == "Routine"
    assert result["description"] == "Test maintenance"
    assert result["status"] == MaintenanceStatus.PENDING
    assert result["notes"] == "Test notes"

def test_update_maintenance_record_api(client: TestClient, db):
    """Test per l'aggiornamento di un record di manutenzione tramite API."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()
    node_id = node.id

    # Crea un record di manutenzione
    record = MaintenanceRecord(
        node_id=node_id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance",
        status=MaintenanceStatus.PENDING,
        notes="Test notes"
    )
    db.add(record)
    db.commit()
    record_id = record.id

    # Dati per l'aggiornamento
    update_data = {
        "description": "Updated maintenance",
        "status": MaintenanceStatus.COMPLETED
    }

    # Chiamata API
    response = client.put(f"{API_PREFIX}/{record_id}", json=update_data)
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == record_id
    assert result["description"] == "Updated maintenance"
    assert result["status"] == MaintenanceStatus.COMPLETED

def test_delete_maintenance_record_api(client: TestClient, db):
    """Test per l'eliminazione di un record di manutenzione tramite API."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()
    node_id = node.id

    # Crea un record di manutenzione
    record = MaintenanceRecord(
        node_id=node_id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance",
        status=MaintenanceStatus.PENDING,
        notes="Test notes"
    )
    db.add(record)
    db.commit()
    record_id = record.id

    # Chiamata API
    response = client.delete(f"{API_PREFIX}/{record_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == record_id

    # Verifica che il record sia stato eliminato
    response = client.get(f"{API_PREFIX}/{record_id}")
    assert response.status_code == 404

def test_import_csv_valid(client: TestClient, db):
    """Test per l'importazione di record di manutenzione da file CSV."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()
    node_id = node.id

    # Crea un file CSV di test
    csv_data = pd.DataFrame({
        'node_id': [node_id],
        'date': [datetime.utcnow().isoformat()],
        'type': ['Routine'],
        'description': ['Test maintenance'],
        'status': [MaintenanceStatus.PENDING.value],
        'notes': ['Test notes']
    })
    csv_file = io.BytesIO()
    csv_data.to_csv(csv_file, index=False)
    csv_file.seek(0)

    # Chiamata API
    files = {'file': ('test.csv', csv_file, 'text/csv')}
    response = client.post(f"{API_PREFIX}/import-historical-data", files=files)
    
    assert response.status_code == 202
    result = response.json()
    assert result["message"] == "Import started"
    assert result["file_name"] == "test.csv"
    assert result["rows_accepted"] == 1

    # Verifica che il record sia stato creato
    records = db.query(MaintenanceRecord).filter(MaintenanceRecord.node_id == node_id).all()
    assert len(records) == 1
    record = records[0]
    assert record.type == "Routine"
    assert record.description == "Test maintenance"
    assert record.status == MaintenanceStatus.PENDING
    assert record.notes == "Test notes"

def test_import_json_valid(client: TestClient, db):
    """Test per l'importazione di record di manutenzione da file JSON."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()
    node_id = node.id

    # Crea un file JSON di test
    json_data = [{
        'node_id': node_id,
        'date': datetime.utcnow().isoformat(),
        'type': 'Routine',
        'description': 'Test maintenance',
        'status': MaintenanceStatus.PENDING.value,
        'notes': 'Test notes'
    }]
    json_file = io.BytesIO()
    json_file.write(json.dumps(json_data).encode())
    json_file.seek(0)

    # Chiamata API
    files = {'file': ('test.json', json_file, 'application/json')}
    response = client.post(f"{API_PREFIX}/import-historical-data", files=files)
    
    assert response.status_code == 202
    result = response.json()
    assert result["message"] == "Import started"
    assert result["file_name"] == "test.json"
    assert result["rows_accepted"] == 1

    # Verifica che il record sia stato creato
    records = db.query(MaintenanceRecord).filter(MaintenanceRecord.node_id == node_id).all()
    assert len(records) == 1
    record = records[0]
    assert record.type == "Routine"
    assert record.description == "Test maintenance"
    assert record.status == MaintenanceStatus.PENDING
    assert record.notes == "Test notes"

def test_search_by_node_id(client: TestClient, db):
    """Test per la ricerca di record di manutenzione per node_id."""
    # Crea due nodi di test
    node1 = Node(name="Test Node 1", type="Test Type", location="Test Location", status="active")
    node2 = Node(name="Test Node 2", type="Test Type", location="Test Location", status="active")
    db.add_all([node1, node2])
    db.commit()

    # Crea record di manutenzione per entrambi i nodi
    record1 = MaintenanceRecord(
        node_id=node1.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 1",
        status=MaintenanceStatus.PENDING,
        notes="Test notes 1"
    )
    record2 = MaintenanceRecord(
        node_id=node2.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 2",
        status=MaintenanceStatus.PENDING,
        notes="Test notes 2"
    )
    db.add_all([record1, record2])
    db.commit()

    # Chiamata API
    response = client.get(f"{API_PREFIX}/search?node_id={node1.id}")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["node_id"] == node1.id
    assert result[0]["description"] == "Test maintenance 1"

def test_search_by_status(client: TestClient, db):
    """Test per la ricerca di record di manutenzione per status."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record di manutenzione con status diversi
    record1 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 1",
        status=MaintenanceStatus.PENDING,
        notes="Test notes 1"
    )
    record2 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 2",
        status=MaintenanceStatus.COMPLETED,
        notes="Test notes 2"
    )
    db.add_all([record1, record2])
    db.commit()

    # Chiamata API
    response = client.get(f"{API_PREFIX}/search?status={MaintenanceStatus.PENDING}")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["status"] == MaintenanceStatus.PENDING
    assert result[0]["description"] == "Test maintenance 1"

def test_search_by_created_at_range(client: TestClient, db):
    """Test per la ricerca di record di manutenzione per range di date."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record di manutenzione con date diverse
    record1 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow() - timedelta(days=2),
        type="Routine",
        description="Test maintenance 1",
        status=MaintenanceStatus.PENDING,
        notes="Test notes 1"
    )
    record2 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 2",
        status=MaintenanceStatus.PENDING,
        notes="Test notes 2"
    )
    db.add_all([record1, record2])
    db.commit()

    # Chiamata API
    start_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
    end_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
    response = client.get(f"{API_PREFIX}/search?start_date={start_date}&end_date={end_date}")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["description"] == "Test maintenance 2"

def test_search_by_notes_keyword(client: TestClient, db):
    """Test per la ricerca di record di manutenzione per keyword nelle note."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record di manutenzione con note diverse
    record1 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 1",
        status=MaintenanceStatus.PENDING,
        notes="Test notes 1"
    )
    record2 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 2",
        status=MaintenanceStatus.PENDING,
        notes="Test notes 2"
    )
    db.add_all([record1, record2])
    db.commit()

    # Chiamata API
    response = client.get(f"{API_PREFIX}/search?notes=Test notes 1")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["notes"] == "Test notes 1"

def test_search_pagination_limit_and_skip(client: TestClient, db):
    """Test per la paginazione dei risultati di ricerca."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record di manutenzione
    records = []
    for i in range(5):
        record = MaintenanceRecord(
            node_id=node.id,
            date=datetime.utcnow(),
            type="Routine",
            description=f"Test maintenance {i}",
            status=MaintenanceStatus.PENDING,
            notes=f"Test notes {i}"
        )
        records.append(record)
    db.add_all(records)
    db.commit()

    # Chiamata API con limit e skip
    response = client.get(f"{API_PREFIX}/search?limit=2&skip=1")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2
    assert result[0]["description"] == "Test maintenance 1"
    assert result[1]["description"] == "Test maintenance 2"

def test_search_combined_filters(client: TestClient, db):
    """Test per la ricerca con filtri combinati."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record di manutenzione
    record1 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 1",
        status=MaintenanceStatus.PENDING,
        notes="Test notes 1"
    )
    record2 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 2",
        status=MaintenanceStatus.COMPLETED,
        notes="Test notes 2"
    )
    db.add_all([record1, record2])
    db.commit()

    # Chiamata API con filtri combinati
    response = client.get(f"{API_PREFIX}/search?node_id={node.id}&status={MaintenanceStatus.PENDING}")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["node_id"] == node.id
    assert result[0]["status"] == MaintenanceStatus.PENDING
    assert result[0]["description"] == "Test maintenance 1"

def test_search_empty_result(client: TestClient, db):
    """Test per la ricerca che non restituisce risultati."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record di manutenzione
    record = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance",
        status=MaintenanceStatus.PENDING,
        notes="Test notes"
    )
    db.add(record)
    db.commit()

    # Chiamata API con filtro che non restituisce risultati
    response = client.get(f"{API_PREFIX}/search?status={MaintenanceStatus.COMPLETED}")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 0

def test_export_csv(client: TestClient, db):
    """Test per l'export dei record di manutenzione in formato CSV."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record di manutenzione
    record = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance",
        status=MaintenanceStatus.PENDING,
        notes="Test notes"
    )
    db.add(record)
    db.commit()

    # Chiamata API
    response = client.get(f"{API_PREFIX}/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert response.headers["content-disposition"] == "attachment; filename=maintenance_records.csv"

def test_export_json(client: TestClient, db):
    """Test per l'export dei record di manutenzione in formato JSON."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record di manutenzione
    record = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance",
        status=MaintenanceStatus.PENDING,
        notes="Test notes"
    )
    db.add(record)
    db.commit()

    # Chiamata API
    response = client.get(f"{API_PREFIX}/export?format=json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["content-disposition"] == "attachment; filename=maintenance_records.json"

def test_export_filters(client: TestClient, db):
    """Test per l'export dei record di manutenzione con filtri."""
    # Crea un nodo di test
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()

    # Crea record di manutenzione
    record1 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 1",
        status=MaintenanceStatus.PENDING,
        notes="Test notes 1"
    )
    record2 = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance 2",
        status=MaintenanceStatus.COMPLETED,
        notes="Test notes 2"
    )
    db.add_all([record1, record2])
    db.commit()

    # Chiamata API con filtri
    response = client.get(f"{API_PREFIX}/export?format=csv&status={MaintenanceStatus.PENDING}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert response.headers["content-disposition"] == "attachment; filename=maintenance_records.csv"

def test_export_invalid_format(client: TestClient):
    """Test per l'export con formato non valido."""
    # Chiamata API con formato non valido
    response = client.get(f"{API_PREFIX}/export?format=invalid")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid export format. Supported formats: csv, json" 