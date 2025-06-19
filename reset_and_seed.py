from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
from app.models.user import User
from app.models.house import House
from app.models.node import Node
from app.models.document import Document
from app.models.maintenance import MaintenanceRecord
from app.models.room import Room
from app.models.booking import Booking
from app.utils.password import get_password_hash
import sys

DB_URL = settings.DATABASE_URL
engine = create_engine(DB_URL, echo=True)

def drop_all():
    print("[RESET] Dropping all tables...")
    SQLModel.metadata.drop_all(engine)
    print("[RESET] All tables dropped.")

def create_all():
    print("[RESET] Creating all tables...")
    SQLModel.metadata.create_all(engine)
    print("[RESET] All tables created.")

def seed():
    print("[RESET] Inserting test data...")
    with Session(engine) as session:
        pass  # Nessun inserimento utente di test

def main():
    print(f"[RESET] DB URL: {DB_URL}")
    drop_all()
    create_all()
    seed()
    print("[RESET] Database pronto!")

if __name__ == "__main__":
    main() 