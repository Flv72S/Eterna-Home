from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test?sslmode=disable"

def clean_database():
    print("Cleaning database...")
    try:
        # Crea l'engine
        engine = create_engine(DATABASE_URL)
        
        # Connessione al database
        with engine.connect() as conn:
            # Disabilita i foreign key checks
            conn.execute(text("SET session_replication_role = 'replica';"))
            
            # Ottieni la lista delle tabelle
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
            # Elimina ogni tabella
            for table in tables:
                print(f"Dropping table: {table}")
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))
            
            # Riabilita i foreign key checks
            conn.execute(text("SET session_replication_role = 'origin';"))
            
            # Commit delle modifiche
            conn.commit()
            
            print("Database cleaned successfully!")
            
    except Exception as e:
        print(f"Error cleaning database: {str(e)}")

if __name__ == "__main__":
    clean_database() 