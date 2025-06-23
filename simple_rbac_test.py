#!/usr/bin/env python3
"""
Test RBAC semplice - scrive solo su file
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def write_log(message):
    with open("rbac_test_simple.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

try:
    write_log("=== INIZIO TEST RBAC SEMPLICE ===")
    
    # Importa moduli
    write_log("Importazione moduli...")
    from app.database import get_engine
    from sqlmodel import Session, select
    from app.models.user import User
    from app.models.role import Role
    from app.models.user_role import UserRole
    from app.utils.password import get_password_hash
    write_log("✅ Moduli importati con successo")
    
    # Test connessione database
    write_log("Test connessione database...")
    engine = get_engine()
    with Session(engine) as session:
        write_log("✅ Connessione database OK")
        
        # Verifica tabelle esistenti
        write_log("Verifica tabelle...")
        roles_count = session.exec(select(Role)).all()
        users_count = session.exec(select(User)).all()
        write_log(f"✅ Tabelle OK - Ruoli: {len(roles_count)}, Utenti: {len(users_count)}")
        
        # Crea utente di test
        test_email = "rbac_test@example.com"
        user = session.exec(select(User).where(User.email == test_email)).first()
        if not user:
            user = User(
                email=test_email,
                username="rbac_test",
                hashed_password=get_password_hash("test123"),
                is_active=True,
                full_name="Test User"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            write_log(f"✅ Utente creato: {user.email}")
        else:
            write_log(f"ℹ️  Utente esistente: {user.email}")
        
        # Crea ruolo di test
        test_role_name = "test_role"
        role = session.exec(select(Role).where(Role.name == test_role_name)).first()
        if not role:
            role = Role(name=test_role_name, description="Ruolo di test")
            session.add(role)
            session.commit()
            session.refresh(role)
            write_log(f"✅ Ruolo creato: {role.name}")
        else:
            write_log(f"ℹ️  Ruolo esistente: {role.name}")
        
        # Assegna ruolo
        rel = session.exec(select(UserRole).where(
            UserRole.user_id == user.id, 
            UserRole.role_id == role.id
        )).first()
        
        if not rel:
            rel = UserRole(user_id=user.id, role_id=role.id)
            session.add(rel)
            session.commit()
            write_log(f"✅ Ruolo assegnato: {role.name} -> {user.email}")
        else:
            write_log(f"ℹ️  Relazione esistente")
        
        # Test metodi
        session.refresh(user)
        user = session.exec(select(User).where(User.id == user.id)).first()
        _ = user.roles  # Forza caricamento
        
        write_log(f"🔎 Test has_role('{test_role_name}'): {user.has_role(test_role_name)}")
        write_log(f"🔎 Test has_any_role(['{test_role_name}', 'other']): {user.has_any_role([test_role_name, 'other'])}")
        write_log(f"🔎 Ruoli utente: {user.get_role_names()}")
        
        # Simula rotta protetta
        if user.has_role(test_role_name):
            write_log("✅ ACCESSO CONSENTITO - Test RBAC SUPERATO!")
        else:
            write_log("❌ ACCESSO NEGATO - Test RBAC FALLITO!")
    
    write_log("=== FINE TEST RBAC SEMPLICE ===")
    
except Exception as e:
    write_log(f"❌ ERRORE: {str(e)}")
    import traceback
    write_log(f"Traceback: {traceback.format_exc()}") 