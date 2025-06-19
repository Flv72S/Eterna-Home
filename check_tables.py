import psycopg2

DB_NAME = "eterna_home_test"
DB_USER = "postgres"
DB_PASSWORD = "N0nn0c4rl0!!"
DB_HOST = "localhost"

def list_tables():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print("Tabelle presenti nel database:")
    for table in tables:
        print(f"- {table[0]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    list_tables() 