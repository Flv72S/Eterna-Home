#!/usr/bin/env python3
"""
Test manuale RBAC: crea utente e ruolo di test, assegna il ruolo, verifica i metodi has_role/has_any_role e simula accesso a rotta protetta.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.database import get_engine
from sqlmodel import Session, select
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.utils.password import get_password_hash

TEST_USER_EMAIL = "rbac_test_user@example.com"
TEST_ROLE_NAME = "rbac_test_role"

def log_message(message):
    """Scrive messaggio su console e file di log"""
    print(message)
    with open("rbac_test_results.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

def get_or_create_user(session):
    user = session.exec(select(User).where(User.email == TEST_USER_EMAIL)).first()
    if not user:
        user = User(
            email=TEST_USER_EMAIL,
            username="rbac_test_user",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False,
            full_name="RBAC Test User"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        log_message(f"✅ Utente creato: {user.email}")
    else:
        log_message(f"ℹ️  Utente già esistente: {user.email}")
    return user

def get_or_create_role(session):
    role = session.exec(select(Role).where(Role.name == TEST_ROLE_NAME)).first()
    if not role:
        role = Role(name=TEST_ROLE_NAME, description="Ruolo di test RBAC")
        session.add(role)
        session.commit()
        session.refresh(role)
        log_message(f"✅ Ruolo creato: {role.name}")
    else:
        log_message(f"ℹ️  Ruolo già esistente: {role.name}")
    return role

def assign_role_to_user(session, user, role):
    # Verifica se la relazione esiste già
    rel = session.exec(select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)).first()
    if not rel:
        rel = UserRole(user_id=user.id, role_id=role.id)
        session.add(rel)
        session.commit()
        log_message(f"✅ Ruolo '{role.name}' assegnato a utente '{user.email}'")
    else:
        log_message(f"ℹ️  Relazione utente-ruolo già esistente")

def test_role_methods(user, role_name):
    log_message(f"🔎 Test has_role('{role_name}'): {user.has_role(role_name)}")
    log_message(f"🔎 Test has_any_role(['{role_name}', 'other_role']): {user.has_any_role([role_name, 'other_role'])}")
    log_message(f"🔎 Ruoli attivi dell'utente: {user.get_role_names()}")

def simulate_protected_route(user, required_role):
    log_message(f"🔐 Simulazione accesso a rotta protetta per ruolo '{required_role}'...")
    if user.has_role(required_role):
        log_message("✅ Accesso consentito!")
    else:
        log_message("❌ Accesso negato!")

def main():
    # Pulisci il file di log
    with open("rbac_test_results.log", "w", encoding="utf-8") as f:
        f.write("=== TEST RBAC MANUALE ===\n")
    
    log_message("🚀 Inizio test RBAC...")
    engine = get_engine()
    with Session(engine) as session:
        user = get_or_create_user(session)
        role = get_or_create_role(session)
        assign_role_to_user(session, user, role)
        # Ricarica user con relazione roles
        session.refresh(user)
        session.refresh(role)
        # Forza caricamento relazione many-to-many
        user = session.exec(select(User).where(User.id == user.id)).first()
        _ = user.roles
        test_role_methods(user, TEST_ROLE_NAME)
        simulate_protected_route(user, TEST_ROLE_NAME)
    
    log_message("🏁 Test RBAC completato!")
    log_message("📄 Risultati salvati in: rbac_test_results.log")

if __name__ == "__main__":
    main() 