import os
import sys
from pathlib import Path

# Aggiungi la directory root del progetto al PYTHONPATH
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, UTC
from app.main import app
from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.node import Node
from app.db.session import SessionLocal
import logging

# Configura il logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_debug():
    """Test di diagnostica per verificare i problemi nei test di manutenzione."""
    client = TestClient(app)
    db = SessionLocal()
    
    try:
        # 1. Verifica creazione nodo
        logger.info("1. Test creazione nodo...")
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
        
        # 2. Verifica creazione record di manutenzione
        logger.info("2. Test creazione record di manutenzione...")
        record = MaintenanceRecord(
            node_id=node.id,
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
        
        # 3. Verifica endpoint export JSON
        logger.info("3. Test endpoint export JSON...")
        response = client.get("/api/v1/maintenance_records/export?format=json")
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Headers: {response.headers}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Numero di record: {len(data)}")
            if data:
                logger.info(f"Esempio di record: {data[0]}")
        else:
            logger.error(f"Errore nella risposta: {response.text}")
        
        # 4. Verifica endpoint export CSV
        logger.info("4. Test endpoint export CSV...")
        response = client.get("/api/v1/maintenance_records/export?format=csv")
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Headers: {response.headers}")
        if response.status_code == 200:
            logger.info(f"Contenuto CSV: {response.text[:200]}...")
        else:
            logger.error(f"Errore nella risposta: {response.text}")
            
    except Exception as e:
        logger.error(f"Errore durante il test: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_debug() 