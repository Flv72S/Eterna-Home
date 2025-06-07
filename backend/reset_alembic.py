from sqlalchemy import text
from app.db.session import engine

def reset_alembic():
    # Elimina la tabella alembic_version se esiste
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
    print("Tabella alembic_version eliminata con successo.")

if __name__ == "__main__":
    reset_alembic() 