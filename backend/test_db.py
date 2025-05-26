import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = psycopg2.connect(
        dbname="eterna_home_db",
        user="postgres",
        password="N0nn0c4rl0!!",
        host="localhost",
        port="5432"
    )
    print("Connessione al database riuscita!")
    conn.close()
except Exception as e:
    print(f"Errore durante la connessione: {str(e)}") 