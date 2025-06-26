import uuid
from sqlmodel import Session, create_engine, SQLModel, select
from app.core.config import settings
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission, RolePermission, UserPermission

# Permessi di esempio
PERMISSIONS = [
    {"name": "view_documents", "description": "Visualizza documenti", "resource": "document", "action": "view"},
    {"name": "edit_documents", "description": "Modifica documenti", "resource": "document", "action": "edit"},
    {"name": "upload_bim", "description": "Upload modelli BIM", "resource": "bim_model", "action": "upload"},
    {"name": "manage_users", "description": "Gestione utenti", "resource": "user", "action": "manage"},
    {"name": "read_ai_logs", "description": "Lettura log AI", "resource": "ai_log", "action": "read"},
]


def test_pbac_permissions():
    print("\n🧪 Test PBAC: creazione permessi, ruoli, assegnazione e verifica relazioni")
    engine = create_engine(settings.DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        # Crea permessi solo se non esistono
        perms = []
        for p in PERMISSIONS:
            perm = db.exec(select(Permission).where(Permission.name == p["name"])).first()
            if not perm:
                perm = Permission(**p)
                db.add(perm)
                db.commit()
                db.refresh(perm)
            perms.append(perm)
        print(f"Permessi di esempio disponibili: {[p.name for p in perms]}")

        # Crea ruolo e assegna permessi
        admin_role = db.exec(select(Role).where(Role.name == "admin")).first()
        if not admin_role:
            admin_role = Role(name="admin", description="Amministratore")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
        for perm in perms:
            if not db.exec(select(RolePermission).where(RolePermission.role_id == admin_role.id, RolePermission.permission_id == perm.id)).first():
                db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
        db.commit()
        print(f"Ruolo 'admin' associato a tutti i permessi.")

        # Crea utente e assegna ruolo
        user = db.exec(select(User).where(User.username == "testuser")).first()
        if not user:
            user = User(
                username="testuser",
                email="testuser@example.com",
                hashed_password="fakehash",
                tenant_id=uuid.uuid4(),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        if admin_role not in user.roles:
            user.roles.append(admin_role)
            db.commit()
        print(f"Utente 'testuser' associato al ruolo 'admin'.")

        # Assegna permesso diretto all'utente
        if not db.exec(select(UserPermission).where(UserPermission.user_id == user.id, UserPermission.permission_id == perms[0].id)).first():
            db.add(UserPermission(user_id=user.id, permission_id=perms[0].id))
            db.commit()
        print(f"Utente 'testuser' ha anche permesso diretto '{perms[0].name}'.")

        # Verifica relazioni
        user = db.get(User, user.id)
        assert any(r.name == "admin" for r in user.roles)
        assert any(p.name == "view_documents" for p in user.permissions)
        print("Relazioni utente-ruolo-permesso verificate.")

        # Riepilogo permessi
        print("\nPermessi associati all'utente:")
        for p in user.permissions:
            print(f"  - {p.name} ({p.resource}:{p.action})")
        print("\nPermessi associati al ruolo 'admin':")
        for p in admin_role.permissions:
            print(f"  - {p.name} ({p.resource}:{p.action})")

        print("\n✅ Test PBAC completato con successo!")

if __name__ == "__main__":
    test_pbac_permissions() 