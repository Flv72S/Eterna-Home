from sqlmodel import create_engine, select, Session
from sqlalchemy import text

DATABASE_URL = "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test?sslmode=disable"

def check_database():
    print("Verifico connessione al database...")
    engine = create_engine(DATABASE_URL)
    
    try:
        with Session(engine) as session:
            # Provo a eseguire una query semplice
            result = session.execute(text("SELECT 1"))
            print("✓ Connessione al database riuscita!")
            
            # Verifico le tabelle esistenti
            result = session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print("\nTabelle presenti nel database:")
            for table in tables:
                print(f"- {table}")
                
    except Exception as e:
        print(f"✗ Errore di connessione: {str(e)}")

if __name__ == "__main__":
    check_database() 