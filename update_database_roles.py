#!/usr/bin/env python3
"""
Script per aggiornare il database e aggiungere il campo role alla tabella users.
Esegue le operazioni necessarie per completare l'integrazione dei ruoli.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from sqlmodel import SQLModel, Session, select, text
from app.database import get_engine
from app.models.user import User
from app.models.enums import UserRole

def check_database_structure():
    """Verifica la struttura del database e aggiunge il campo role se necessario."""
    print("🔍 Verifica struttura database...")
    engine = get_engine()
    with Session(engine) as session:
        # Verifica se il campo role esiste
        try:
            result = session.exec(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'role'
            """))
            role_column_exists = result.first() is not None
            
            if not role_column_exists:
                print("📝 Campo 'role' non trovato. Aggiungendo...")
                session.exec(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'owner'"))
                session.commit()
                print("✅ Campo 'role' aggiunto con successo")
            else:
                print("✅ Campo 'role' già presente")
                
        except Exception as e:
            print(f"❌ Errore durante la verifica: {e}")
            return False
    
    return True

def update_existing_users():
    """Aggiorna gli utenti esistenti con ruoli appropriati."""
    print("🔄 Aggiornamento utenti esistenti...")
    engine = get_engine()
    with Session(engine) as session:
        # Trova tutti gli utenti senza ruolo o con ruolo NULL
        statement = select(User).where(
            (User.role.is_(None)) | (User.role == "")
        )
        users_without_role = session.exec(statement).all()
        
        if users_without_role:
            print(f"📝 Trovati {len(users_without_role)} utenti senza ruolo")
            
            for user in users_without_role:
                # Assegna ruolo di default
                if user.is_superuser:
                    user.role = UserRole.SUPER_ADMIN.value
                    print(f"  - {user.email}: {UserRole.SUPER_ADMIN.value}")
                elif user.is_admin:
                    user.role = UserRole.ADMIN.value
                    print(f"  - {user.email}: {UserRole.ADMIN.value}")
                else:
                    user.role = UserRole.OWNER.value
                    print(f"  - {user.email}: {UserRole.OWNER.value}")
            
            session.commit()
            print("✅ Utenti aggiornati con successo")
        else:
            print("✅ Tutti gli utenti hanno già un ruolo assegnato")

def verify_roles():
    """Verifica che tutti i ruoli siano validi."""
    print("🔍 Verifica validità ruoli...")
    engine = get_engine()
    with Session(engine) as session:
        statement = select(User)
        users = session.exec(statement).all()
        
        valid_roles = [role.value for role in UserRole]
        invalid_users = []
        
        for user in users:
            if user.role not in valid_roles:
                invalid_users.append((user.email, user.role))
        
        if invalid_users:
            print("⚠️  Utenti con ruoli non validi trovati:")
            for email, role in invalid_users:
                print(f"  - {email}: '{role}' (non valido)")
                print(f"    Ruoli validi: {', '.join(valid_roles)}")
        else:
            print("✅ Tutti i ruoli sono validi")

def create_test_users():
    """Crea alcuni utenti di test con ruoli diversi."""
    print("👥 Creazione utenti di test...")
    from app.utils.password import get_password_hash
    engine = get_engine()
    test_users = [
        {
            "email": "superadmin@example.com",
            "username": "superadmin",
            "hashed_password": get_password_hash("SuperAdmin123!"),
            "is_active": True,
            "is_superuser": True,
            "role": UserRole.SUPER_ADMIN.value,
            "full_name": "Super Administrator"
        },
        {
            "email": "admin@test.com", 
            "username": "admin",
            "full_name": "Local Administrator",
            "role": UserRole.ADMIN.value,
            "is_superuser": False
        },
        {
            "email": "owner@test.com",
            "username": "owner",
            "full_name": "Property Owner",
            "role": UserRole.OWNER.value,
            "is_superuser": False
        },
        {
            "role": UserRole.TECHNICIAN.value,
            "email": "technician@example.com",
            "username": "technician",
            "full_name": "Technician User",
            "hashed_password": get_password_hash("password123"),
            "is_active": True,
            "is_superuser": False
        },
        {
            "role": UserRole.BUILDER.value,
            "email": "builder@example.com",
            "username": "builder",
            "full_name": "Builder User",
            "hashed_password": get_password_hash("password123"),
            "is_active": True,
            "is_superuser": False
        },
        {
            "role": UserRole.MANAGER.value,
            "email": "manager@test.com",
            "username": "manager",
            "full_name": "Condominium Manager",
            "is_superuser": False
        }
    ]
    with Session(engine) as session:
        for user_data in test_users:
            # Verifica se l'utente esiste già
            existing_user = session.exec(
                select(User).where(User.email == user_data["email"])
            ).first()
            
            if not existing_user:
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=user_data["hashed_password"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_superuser=user_data["is_superuser"],
                    is_active=user_data["is_active"]
                )
                session.add(user)
                print(f"  ✅ Creato: {user_data['email']} ({user_data['role']})")
            else:
                print(f"  ⏭️  Esistente: {user_data['email']}")
        
        session.commit()
        print("✅ Utenti di test creati/verificati")

def show_database_stats():
    """Mostra statistiche del database."""
    print("📊 Statistiche database...")
    engine = get_engine()
    with Session(engine) as session:
        # Conta utenti per ruolo
        for role in UserRole:
            count = session.exec(
                select(User).where(User.role == role.value)
            ).all()
            print(f"  {role.value}: {len(count)} utenti")
        
        # Totale utenti
        total = session.exec(select(User)).all()
        print(f"  Totale: {len(total)} utenti")

def main():
    """Funzione principale."""
    print("🚀 Aggiornamento Database per Sistema Ruoli")
    print("=" * 50)
    
    try:
        # 1. Verifica e aggiorna struttura
        if not check_database_structure():
            print("❌ Errore nella verifica struttura database")
            return
        
        # 2. Aggiorna utenti esistenti
        update_existing_users()
        
        # 3. Verifica validità ruoli
        verify_roles()
        
        # 4. Crea utenti di test
        create_test_users()
        
        # 5. Mostra statistiche
        show_database_stats()
        
        print("\n✅ Aggiornamento database completato con successo!")
        print("\n🔑 Credenziali utenti di test:")
        print("  - superadmin@example.com / SuperAdmin123!")
        print("  - admin@test.com / TestPassword123!")
        print("  - owner@test.com / TestPassword123!")
        print("  - technician@test.com / TestPassword123!")
        print("  - builder@test.com / TestPassword123!")
        print("  - manager@test.com / TestPassword123!")
        
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 