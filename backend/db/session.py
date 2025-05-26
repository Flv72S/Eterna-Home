from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Usa l'URL del database da .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Database URL: {SQLALCHEMY_DATABASE_URL}")  # Debug print

# Crea l'engine per PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 