from backend.db.session import engine
from backend.models import user, house, node, maintenance, legacy_documents, bim, audio_log, document, annotation
from sqlalchemy import text

def reset_database():
    with engine.connect() as conn:
        conn.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
        conn.commit()
    # Ricrea tutte le tabelle
    user.Base.metadata.create_all(bind=engine)
    print("Database resettato con successo!")

if __name__ == "__main__":
    reset_database() 