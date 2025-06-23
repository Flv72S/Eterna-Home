#!/usr/bin/env python3
"""
Test RBAC con output JSON
"""
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.abspath('.'))

def run_rbac_test():
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "success": False,
        "error": None
    }
    
    try:
        # Test 1: Importazione modelli
        results["tests"]["import_models"] = {"success": False, "error": None}
        try:
            from app.models.role import Role
            from app.models.user_role import UserRole
            from app.models.user import User
            results["tests"]["import_models"]["success"] = True
            results["tests"]["import_models"]["message"] = "Modelli importati correttamente"
        except Exception as e:
            results["tests"]["import_models"]["error"] = str(e)
            raise
        
        # Test 2: Connessione database
        results["tests"]["database_connection"] = {"success": False, "error": None}
        try:
            from app.database import get_engine
            from sqlmodel import Session, select
            
            engine = get_engine()
            with Session(engine) as session:
                roles = session.exec(select(Role)).all()
                users = session.exec(select(User)).all()
                user_roles = session.exec(select(UserRole)).all()
                
                results["tests"]["database_connection"]["success"] = True
                results["tests"]["database_connection"]["data"] = {
                    "roles_count": len(roles),
                    "users_count": len(users),
                    "user_roles_count": len(user_roles),
                    "existing_roles": [{"name": r.name, "description": r.description} for r in roles[:5]]
                }
        except Exception as e:
            results["tests"]["database_connection"]["error"] = str(e)
            raise
        
        # Test 3: Funzionalità RBAC
        results["tests"]["rbac_functionality"] = {"success": False, "error": None}
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
                    user_created = True
                else:
                    user_created = False
                
                # Crea ruolo di test
                test_role_name = "test_role"
                role = session.exec(select(Role).where(Role.name == test_role_name)).first()
                
                if not role:
                    role = Role(name=test_role_name, description="Ruolo di test")
                    session.add(role)
                    session.commit()
                    session.refresh(role)
                    role_created = True
                else:
                    role_created = False
                
                # Assegna ruolo
                rel = session.exec(select(UserRole).where(
                    UserRole.user_id == user.id, 
                    UserRole.role_id == role.id
                )).first()
                
                if not rel:
                    rel = UserRole(user_id=user.id, role_id=role.id)
                    session.add(rel)
                    session.commit()
                    role_assigned = True
                else:
                    role_assigned = False
                
                # Test metodi RBAC
                session.refresh(user)
                user = session.exec(select(User).where(User.id == user.id)).first()
                _ = user.roles  # Forza caricamento
                
                has_role_result = user.has_role(test_role_name)
                has_any_role_result = user.has_any_role([test_role_name, 'other'])
                role_names = user.get_role_names()
                
                results["tests"]["rbac_functionality"]["success"] = True
                results["tests"]["rbac_functionality"]["data"] = {
                    "user_created": user_created,
                    "role_created": role_created,
                    "role_assigned": role_assigned,
                    "has_role": has_role_result,
                    "has_any_role": has_any_role_result,
                    "role_names": role_names,
                    "access_granted": has_role_result
                }
        
        except Exception as e:
            results["tests"]["rbac_functionality"]["error"] = str(e)
            raise
        
        results["success"] = True
        
    except Exception as e:
        results["error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()
    
    return results

if __name__ == "__main__":
    results = run_rbac_test()
    
    # Salva risultati su file
    with open("rbac_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Stampa riassunto
    if results["success"]:
        print("✅ TEST RBAC COMPLETATO CON SUCCESSO")
        print(f"📄 Risultati salvati in: rbac_test_results.json")
        
        # Mostra risultati principali
        rbac_data = results["tests"]["rbac_functionality"]["data"]
        print(f"🔎 Test has_role: {rbac_data['has_role']}")
        print(f"🔎 Test has_any_role: {rbac_data['has_any_role']}")
        print(f"🔎 Ruoli utente: {rbac_data['role_names']}")
        print(f"🔐 Accesso: {'CONSENTITO' if rbac_data['access_granted'] else 'NEGATO'}")
    else:
        print("❌ TEST RBAC FALLITO")
        print(f"📄 Dettagli salvati in: rbac_test_results.json")
        print(f"Errore: {results['error']}") 