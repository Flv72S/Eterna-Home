#!/usr/bin/env python3
"""
Script per verificare i ruoli esistenti nel database
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.database import get_engine
from sqlmodel import Session, text

def check_roles():
    """Verifica i ruoli esistenti nel database"""
    print("🔍 Verifica ruoli esistenti...")
    engine = get_engine()
    with Session(engine) as session:
        # Verifica ruoli nella tabella roles
        result = session.exec(text("SELECT * FROM roles LIMIT 10"))
        roles = result.all()
        
        if roles:
            print("✅ Ruoli trovati nella tabella 'roles':")
            for role in roles:
                print(f"  - ID: {role[0]}, Nome: {role[1]}, Descrizione: {role[2]}, Attivo: {role[3]}")
        else:
            print("⚠️  Nessun ruolo trovato nella tabella 'roles'")
        
        # Verifica relazioni user_roles
        result = session.exec(text("SELECT COUNT(*) FROM user_roles"))
        user_roles_count = result.first()[0]
        print(f"📊 Relazioni user_roles: {user_roles_count}")

if __name__ == "__main__":
    check_roles() 