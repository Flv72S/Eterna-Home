from app.db.session import engine
from app.models.user import User
from app.models.house import House
from app.models.node import Node
from app.models.document import Document
from app.models.maintenance import MaintenanceRecord
from sqlmodel import SQLModel, select
import traceback

def test_create_tables():
    try:
        # Importa tutti i modelli per assicurarsi che siano registrati
        print("Importing models...")
        print(f"User: {User.__tablename__}")
        print(f"House: {House.__tablename__}")
        print(f"Node: {Node.__tablename__}")
        print(f"Document: {Document.__tablename__}")
        print(f"MaintenanceRecord: {MaintenanceRecord.__tablename__}")
        
        # Crea le tabelle
        print("\nCreating tables...")
        SQLModel.metadata.create_all(engine)
        print("✅ Tutte le tabelle sono state create con successo!")
    except Exception as e:
        print(f"❌ Errore durante la creazione delle tabelle: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_create_tables() 