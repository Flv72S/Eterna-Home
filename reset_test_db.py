import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess
import sys
import os

def reset_test_db():
    TEST_DATABASE_NAME = "eterna_home_test"
    POSTGRES_USER = "postgres"
    POSTGRES_PASSWORD = "N0nn0c4rl0!!"
    POSTGRES_HOST = "localhost"
    POSTGRES_PORT = 5432
    # 1. Connessione a postgres
    conn = psycopg2.connect(
        dbname="postgres",
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    # 2. Termina connessioni attive
    cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{TEST_DATABASE_NAME}' AND pid <> pg_backend_pid();")
    # 3. Drop DB
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DATABASE_NAME};")
    print(f"[RESET-DB] Dropped {TEST_DATABASE_NAME}")
    # 4. Create DB
    cur.execute(f"CREATE DATABASE {TEST_DATABASE_NAME};")
    print(f"[RESET-DB] Created {TEST_DATABASE_NAME}")
    cur.close()
    conn.close()
    # [DISABILITATO TEMPORANEAMENTE: Alembic]
    # alembic_cmd = ...
    # print(f"[RESET-DB] Running Alembic migrations...")
    # result = subprocess.run(alembic_cmd, env=env, capture_output=True, text=True)
    # ... existing code ...

if __name__ == "__main__":
    reset_test_db() 