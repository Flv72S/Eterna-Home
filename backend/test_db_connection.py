#!/usr/bin/env python3

import psycopg2
from app.core.config import settings

def test_connection():
    try:
        # Test con psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="eterna_home_test",
            user="postgres",
            password="N0nn0c4rl0!!",
            port="5432"
        )
        print("✅ Connessione al database riuscita con psycopg2")
        conn.close()
        
        # Test con SQLAlchemy
        from app.db.session import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Connessione al database riuscita con SQLAlchemy")
            
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")

if __name__ == "__main__":
    test_connection() 