from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

# Database connection string
DATABASE_URL = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"

def reset_alembic_version():
    print("🔄 Inizializzazione reset alembic_version...")
    try:
        print("📡 Connessione al database...")
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        print("🔑 Creazione sessione...")
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("🗑️ Eliminazione tabella alembic_version...")
        # Drop the alembic_version table if it exists
        session.execute(text("DROP TABLE IF EXISTS alembic_version"))
        session.commit()
        
        print("✅ Tabella alembic_version resettata con successo!")
        
    except Exception as e:
        print(f"❌ Errore durante il reset della tabella alembic_version: {str(e)}")
        print(f"Tipo di errore: {type(e).__name__}")
        print(f"Stack trace:", file=sys.stderr)
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        print("🔒 Chiusura sessione...")
        session.close()

if __name__ == "__main__":
    print("🚀 Avvio script reset alembic_version...")
    reset_alembic_version()
    print("🏁 Script completato.") 