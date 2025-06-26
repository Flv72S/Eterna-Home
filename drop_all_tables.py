#!/usr/bin/env python3
"""
Script per droppare tutte le tabelle del database.
Usa SQLModel/SQLAlchemy per una gestione pulita delle tabelle.
"""

import asyncio
from sqlalchemy import text
from sqlmodel import SQLModel, create_engine
from app.core.config import settings
from app.models import *  # Importa tutti i modelli per assicurarsi che siano registrati

def drop_all_tables():
    """Droppa tutte le tabelle del database."""
    print("🗑️  Dropping tutte le tabelle del database...")
    
    # Crea l'engine per il database
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10, echo=True)
    
    try:
        with engine.connect() as conn:
            # Disabilita temporaneamente i controlli di foreign key
            conn.execute(text("SET session_replication_role = replica;"))
            
            # Droppa tutte le tabelle
            SQLModel.metadata.drop_all(engine)
            
            # Riabilita i controlli di foreign key
            conn.execute(text("SET session_replication_role = DEFAULT;"))
            
            # Commit delle modifiche
            conn.commit()
            
        print("✅ Tutte le tabelle droppate con successo!")
        
    except Exception as e:
        print(f"❌ Errore durante il drop delle tabelle: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    drop_all_tables() 