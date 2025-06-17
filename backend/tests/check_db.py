from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test?sslmode=disable"

def check_database():
    print("Checking database connection...")
    try:
        # Crea l'engine
        engine = create_engine(DATABASE_URL)
        
        # Prova a connettersi
        with engine.connect() as conn:
            # Esegui una query semplice
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful!")
            
            # Lista le tabelle
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print("\nExisting tables:")
            for table in tables:
                print(f"- {table}")
            
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")

if __name__ == "__main__":
    check_database() 