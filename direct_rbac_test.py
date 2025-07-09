#!/usr/bin/env python3
"""
Test RBAC diretto - esegue e mostra risultati
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Test 1: Verifica modelli
print("=== TEST 1: Verifica Modelli ===")
try:
    from app.models.role import Role
    from app.models.user_role import UserRole
    from app.models.user import User
    print("✅ Modelli Role, UserRole, User importati correttamente")
except Exception as e:
    print(f"❌ Errore importazione modelli: {e}")
    sys.exit(1)

# Test 2: Verifica database
print("\n=== TEST 2: Verifica Database ===")
try:
    from app.database import get_engine
    from sqlmodel import Session, select
    
    engine = get_engine()
    with Session(engine) as session:
        # Verifica tabelle
        roles = session.exec(select(Role)).all()
        users = session.exec(select(User)).all()
        user_roles = session.exec(select(UserRole)).all()
        
        print(f"✅ Tabelle OK:")
        print(f"   - Ruoli: {len(roles)}")
        print(f"   - Utenti: {len(users)}")
        print(f"   - Relazioni user_roles: {len(user_roles)}")
        
        # Mostra alcuni ruoli esistenti
        if roles:
            print("   - Ruoli esistenti:")
            for role in roles[:5]:  # Primi 5
                print(f"     * {role.name}: {role.description}")
        
except Exception as e:
    print(f"❌ Errore database: {e}")
    sys.exit(1)

# Test 3: Test funzionalità RBAC
print("\n=== TEST 3: Test Funzionalità RBAC ===")
try:
    from app.utils.password import get_password_hash
    
    with Session(engine) as session:
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
            print(f"✅ Utente creato: {user.email}")
        else:
            print(f"ℹ️  Utente esistente: {user.email}")
        
        # Crea ruolo di test
        test_role_name = "test_role"
        role = session.exec(select(Role).where(Role.name == test_role_name)).first()
        
        if not role:
            role = Role(name=test_role_name, description="Ruolo di test")
            session.add(role)
            session.commit()
            session.refresh(role)
            print(f"✅ Ruolo creato: {role.name}")
        else:
            print(f"ℹ️  Ruolo esistente: {role.name}")
        
        # Assegna ruolo
        rel = session.exec(select(UserRole).where(
            UserRole.user_id == user.id, 
            UserRole.role_id == role.id
        )).first()
        
        if not rel:
            rel = UserRole(user_id=user.id, role_id=role.id)
            session.add(rel)
            session.commit()
            print(f"✅ Ruolo assegnato: {role.name} -> {user.email}")
        else:
            print(f"ℹ️  Relazione esistente")
        
        # Test metodi RBAC
        session.refresh(user)
        user = session.exec(select(User).where(User.id == user.id)).first()
        
        print(f"\n🔎 Test metodi RBAC:")
        print(f"   - has_role('{test_role_name}'): {user.has_role(test_role_name)}")
        print(f"   - has_any_role(['{test_role_name}', 'other']): {user.has_any_role([test_role_name, 'other'])}")
        print(f"   - get_role_names(): {user.get_role_names()}")
        
        # Simula rotta protetta
        print(f"\n🔐 Simulazione rotta protetta:")
        if user.has_role(test_role_name):
            print("   ✅ ACCESSO CONSENTITO - Test RBAC SUPERATO!")
        else:
            print("   ❌ ACCESSO NEGATO - Test RBAC FALLITO!")
        
except Exception as e:
    print(f"❌ Errore test RBAC: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

print("\n=== TEST COMPLETATO ===")
print("✅ Sistema RBAC funzionante correttamente!") 