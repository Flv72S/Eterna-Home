from sqlalchemy import create_engine, text

# Modifica qui se la tua connessione cambia
DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home'
REVISION_ID = 'a597191c5a59'

def main():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Droppa e ricrea la tabella alembic_version
        conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
        conn.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)'))
        # Inserisci solo la revisione corretta
        conn.execute(text('INSERT INTO alembic_version (version_num) VALUES (:rev)'), {'rev': REVISION_ID})
        conn.commit()  # Assicurati che le modifiche vengano salvate
        print(f"Tabella alembic_version ripristinata con la revisione: {REVISION_ID}")

if __name__ == '__main__':
    main() 