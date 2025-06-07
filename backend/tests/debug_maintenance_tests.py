import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, UTC
from app.main import app
from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.node import Node
from sqlalchemy import inspect
import logging

# Configura il logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_node_creation(db):
    """Verifica la creazione di un nodo di test."""
    try:
        logger.info("Tentativo di creazione nodo di test...")
        node = Node(
            name="Test Node",
            type="sensor",
            location="Test Location",
            status="active"
        )
        db.add(node)
        db.commit()
        db.refresh(node)
        logger.info(f"Nodo creato con successo. ID: {node.id}")
        return node
    except Exception as e:
        logger.error(f"Errore nella creazione del nodo: {str(e)}")
        raise

def debug_maintenance_record_creation(db, node):
    """Verifica la creazione di un record di manutenzione."""
    try:
        logger.info("Tentativo di creazione record di manutenzione...")
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
        logger.info(f"Record creato con successo. ID: {record.id}")
        return record
    except Exception as e:
        logger.error(f"Errore nella creazione del record: {str(e)}")
        raise

def debug_export_endpoint(client, format="json"):
    """Verifica l'endpoint di export."""
    try:
        logger.info(f"Test export in formato {format}...")
        response = client.get(f"/api/v1/maintenance_records/export?format={format}")
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Headers: {response.headers}")
        if response.status_code == 200:
            if format == "json":
                data = response.json()
                logger.info(f"Numero di record: {len(data)}")
                if data:
                    logger.info(f"Esempio di record: {data[0]}")
            else:
                logger.info(f"Contenuto CSV: {response.text[:200]}...")
        else:
            logger.error(f"Errore nella risposta: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Errore nel test export: {str(e)}")
        raise

def debug_database_schema(db):
    """Verifica lo schema del database."""
    try:
        logger.info("Verifica schema database...")
        inspector = inspect(db.get_bind())
        
        # Verifica tabella nodes
        logger.info("\nSchema tabella nodes:")
        for column in inspector.get_columns('nodes'):
            logger.info(f"Colonna: {column['name']}, Tipo: {column['type']}, Nullable: {column['nullable']}")
        
        # Verifica tabella maintenance_records
        logger.info("\nSchema tabella maintenance_records:")
        for column in inspector.get_columns('maintenance_records'):
            logger.info(f"Colonna: {column['name']}, Tipo: {column['type']}, Nullable: {column['nullable']}")
    except Exception as e:
        logger.error(f"Errore nella verifica dello schema: {str(e)}")
        raise

def main():
    """Funzione principale di diagnostica."""
    try:
        # Crea il client di test
        client = TestClient(app)
        
        # Ottieni la sessione del database
        from app.db.session import SessionLocal
        db = SessionLocal()
        
        try:
            # Verifica lo schema del database
            debug_database_schema(db)
            
            # Verifica la creazione del nodo
            node = debug_node_creation(db)
            
            # Verifica la creazione del record
            record = debug_maintenance_record_creation(db, node)
            
            # Verifica l'endpoint di export
            debug_export_endpoint(client, "json")
            debug_export_endpoint(client, "csv")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Errore durante la diagnostica: {str(e)}")
        raise

if __name__ == "__main__":
    main() 