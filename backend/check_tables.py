import psycopg2
import logging

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurazione del database
DB_NAME = "eterna_home_test"
DB_USER = "postgres"
DB_PASSWORD = "N0nn0c4rl0!!"
DB_HOST = "localhost"

def check_tables():
    """Verifica le tabelle presenti nel database."""
    try:
        # Connessione al database
        print("Connecting to database...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        cur = conn.cursor()
        
        # Query per ottenere tutte le tabelle
        print("Querying tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        # Stampa le tabelle
        tables = cur.fetchall()
        print("\nTables in database:")
        if not tables:
            print("No tables found!")
        else:
            for table in tables:
                print(f"- {table[0]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking tables: {str(e)}")
        raise

if __name__ == "__main__":
    check_tables() 