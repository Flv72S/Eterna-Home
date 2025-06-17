from sqlmodel import SQLModel, create_engine
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.booking import Booking
from app.models.room import Room
from app.models.node import Node

# Configurazione del database
DATABASE_URL = "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test?sslmode=disable"

def create_tables():
    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    print("Tabelle create con successo!")

if __name__ == "__main__":
    create_tables() 