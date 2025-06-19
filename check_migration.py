import os
import sys
import subprocess
import psycopg2

DB_NAME = "eterna_home_test"
DB_USER = "postgres"
DB_PASSWORD = "N0nn0c4rl0!!"
DB_HOST = "localhost"

# Ottieni il percorso assoluto della directory backend/alembic
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALEMBIC_DIR = os.path.join(BASE_DIR, "backend", "alembic")

print(f"📂 Alembic path calcolato: {ALEMBIC_DIR}")

if not os.path.exists(ALEMBIC_DIR):
    raise FileNotFoundError(f"❌ Alembic directory not found at {ALEMBIC_DIR}")
else:
    print("✅ Alembic directory trovata.")

# Verifica il contenuto della directory
required = ["env.py", "versions"]
for name in required:
    path = os.path.join(ALEMBIC_DIR, name)
    if not os.path.exists(path):
        print(f"❌ {name} mancante")
    else:
        print(f"✅ {name} presente")

# Aggiungi il path base se necessario
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_user_table():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'user'
        );
    """)
    exists = cur.fetchone()[0]
    cur.close()
    conn.close()
    return exists

def run_migration():
    # Esegui la migrazione Alembic usando il percorso assoluto
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=os.path.join(BASE_DIR, "backend"),
        capture_output=True,
        text=True
    )
    print("Output della migrazione:")
    print(result.stdout)
    if result.stderr:
        print("Errori durante la migrazione:")
        print(result.stderr)
    return result.returncode == 0

if __name__ == "__main__":
    # [DISABILITATO TEMPORANEAMENTE: Alembic]
    # Tutta la logica che richiama Alembic via subprocess o path
    if not run_migration():
        print("La migrazione Alembic è fallita.")
        sys.exit(1)
    if not check_user_table():
        print("ERRORE: La tabella 'user' non è stata creata dalla migrazione.")
        sys.exit(1)
    print("OK: La tabella 'user' è stata creata correttamente.") 