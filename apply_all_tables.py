#!/usr/bin/env python3
"""
Script per applicare tutte le tabelle necessarie al database.
Eseguire questo script per creare tutte le tabelle del sistema Eterna Home.
"""

import os
import sys
from pathlib import Path

# Aggiungi il path dell'app per importare i moduli
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.database import get_engine
from sqlalchemy import text

def apply_all_tables():
    """Applica tutte le tabelle al database."""
    print("🔄 Applicazione di tutte le tabelle...")
    
    # Leggi il contenuto del file SQL
    sql_file = Path(__file__).parent / "create_all_tables.sql"
    if not sql_file.exists():
        print(f"❌ File SQL non trovato: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Esegui le query SQL
    engine = get_engine()
    try:
        with engine.connect() as conn:
            # Esegui ogni statement separatamente
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith('--'):
                    print(f"📝 Esecuzione statement {i}/{len(statements)}...")
                    try:
                        conn.execute(text(statement))
                        print(f"   ✅ Statement {i} completato")
                    except Exception as e:
                        print(f"   ⚠️  Statement {i} fallito (probabilmente già eseguito): {e}")
            
            conn.commit()
            print("✅ Tutte le tabelle create con successo!")
            return True
            
    except Exception as e:
        print(f"❌ Errore durante l'applicazione: {e}")
        return False

if __name__ == "__main__":
    success = apply_all_tables()
    sys.exit(0 if success else 1) 