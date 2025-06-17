import os
import sys
from pathlib import Path
import sqlite3
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory

def check_database():
    """Verifica la configurazione del database"""
    print("\n=== Verifica Database ===")
    try:
        # Verifica file database
        db_path = Path("app.db")
        if not db_path.exists():
            print("❌ File database non trovato")
            return False
        print("✅ File database trovato")

        # Verifica connessione
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Connessione al database riuscita")
        print(f"   Tabelle trovate: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Errore nella verifica del database: {str(e)}")
        return False

def check_migrations():
    """Verifica lo stato delle migrazioni"""
    print("\n=== Verifica Migrazioni ===")
    try:
        # Verifica file alembic.ini
        if not Path("alembic.ini").exists():
            print("❌ File alembic.ini non trovato")
            return False
        print("✅ File alembic.ini trovato")

        # Verifica directory versions
        versions_dir = Path("alembic/versions")
        if not versions_dir.exists():
            print("❌ Directory versions non trovata")
            return False
        print("✅ Directory versions trovata")

        # Verifica migrazioni
        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        revisions = list(script.walk_revisions())
        print(f"✅ {len(revisions)} migrazioni trovate")
        return True
    except Exception as e:
        print(f"❌ Errore nella verifica delle migrazioni: {str(e)}")
        return False

def check_environment():
    """Verifica l'ambiente Python"""
    print("\n=== Verifica Ambiente Python ===")
    try:
        # Verifica Python version
        print(f"✅ Python version: {sys.version}")

        # Verifica variabili d'ambiente
        required_env_vars = ["DATABASE_URL", "SECRET_KEY"]
        for var in required_env_vars:
            if var not in os.environ:
                print(f"❌ Variabile d'ambiente {var} non trovata")
                return False
            print(f"✅ Variabile d'ambiente {var} trovata")
        return True
    except Exception as e:
        print(f"❌ Errore nella verifica dell'ambiente: {str(e)}")
        return False

def check_dependencies():
    """Verifica le dipendenze Python"""
    print("\n=== Verifica Dipendenze ===")
    try:
        import fastapi
        import sqlmodel
        import alembic
        import pydantic
        print("✅ Tutte le dipendenze principali sono installate")
        return True
    except ImportError as e:
        print(f"❌ Dipendenza mancante: {str(e)}")
        return False

def main():
    """Funzione principale"""
    print("=== Verifica Ambiente per i Test ===")
    
    checks = [
        ("Database", check_database),
        ("Migrazioni", check_migrations),
        ("Ambiente", check_environment),
        ("Dipendenze", check_dependencies)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\nEsecuzione verifica: {name}")
        if not check_func():
            all_passed = False
            print(f"❌ Verifica {name} fallita")
        else:
            print(f"✅ Verifica {name} completata con successo")
    
    if all_passed:
        print("\n✅ Tutte le verifiche completate con successo")
        print("L'ambiente è pronto per l'esecuzione dei test")
    else:
        print("\n❌ Alcune verifiche sono fallite")
        print("Correggere i problemi prima di procedere con i test")

if __name__ == "__main__":
    main() 