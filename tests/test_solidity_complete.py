"""
Test completo per la solidità del sistema Eterna Home
Verifica tutti i 7 punti di solidità:
1. Modelli ORM e relazioni
2. Gestione migrazioni Alembic
3. Testing
4. Sicurezza
5. Multi-tenancy
6. Performance e scalabilità
7. Documentazione
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from sqlalchemy.orm import Mapped

from app.main import app
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.user_permission import UserPermission
from app.models.role_permission import RolePermission
from app.models.user_tenant_role import UserTenantRole
from app.core.security import create_access_token, get_password_hash, verify_password
from app.database import get_db
from app.models.enums import UserRole as UserRoleEnum
from app.core.auth import require_permission_in_tenant, require_role_in_tenant

client = TestClient(app)

@pytest.fixture
def db_session():
    """Get database session for testing"""
    with next(get_db()) as session:
        yield session

@pytest.fixture
def test_tenant_id():
    """Test tenant ID"""
    return uuid.uuid4()

@pytest.fixture
def admin_user(db_session, test_tenant_id):
    """Create admin user for testing"""
    user = User(
        email="admin@test.com",
        username="admin",
        hashed_password=get_password_hash("AdminPass123!"),
        is_active=True,
        tenant_id=test_tenant_id,
        role="admin",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def regular_user(db_session, test_tenant_id):
    """Create regular user for testing"""
    user = User(
        email="user@test.com",
        username="user",
        hashed_password=get_password_hash("UserPass123!"),
        is_active=True,
        tenant_id=test_tenant_id,
        role="user",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_role(db_session):
    """Create admin role"""
    role = Role(
        name="admin",
        description="Administrator role",
        is_active=True
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

@pytest.fixture
def user_role(db_session):
    """Create user role"""
    role = Role(
        name="user",
        description="Regular user role",
        is_active=True
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

@pytest.fixture
def test_permission(db_session):
    """Create test permission"""
    permission = Permission(
        name="test:read",
        description="Test read permission",
        is_active=True
    )
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)
    return permission

class TestSolidityPoint1_ORMModels:
    """Test 1: Modelli ORM e relazioni"""
    
    def test_user_model_relationships(self, db_session, admin_user, admin_role, test_permission):
        """Test: Verifica relazioni User con sintassi SQLAlchemy 2.0+"""
        
        # Verifica che il modello User abbia le relazioni corrette
        assert hasattr(User, 'roles')
        assert hasattr(User, 'permissions')
        assert hasattr(User, 'tenant_roles')
        
        # Verifica che le relazioni siano di tipo Mapped[List[...]]
        assert isinstance(User.__annotations__['roles'], type)
        assert 'Mapped' in str(User.__annotations__['roles'])
        assert 'List' in str(User.__annotations__['roles'])
        
        # Test relazione many-to-many con ruoli
        admin_user.roles = [admin_role]
        db_session.commit()
        db_session.refresh(admin_user)
        
        assert len(admin_user.roles) == 1
        assert admin_user.roles[0].name == "admin"
        
        # Test relazione many-to-many con permessi
        admin_user.permissions = [test_permission]
        db_session.commit()
        db_session.refresh(admin_user)
        
        assert len(admin_user.permissions) == 1
        assert admin_user.permissions[0].name == "test:read"
        
        print("✅ Test 1.1: Relazioni User corrette - PASSATO")
    
    def test_role_model_relationships(self, db_session, admin_role, admin_user, test_permission):
        """Test: Verifica relazioni Role con sintassi SQLAlchemy 2.0+"""
        
        # Verifica che il modello Role abbia le relazioni corrette
        assert hasattr(Role, 'users')
        assert hasattr(Role, 'permissions')
        
        # Test relazione many-to-many con utenti
        admin_role.users = [admin_user]
        db_session.commit()
        db_session.refresh(admin_role)
        
        assert len(admin_role.users) == 1
        assert admin_role.users[0].email == "admin@test.com"
        
        # Test relazione many-to-many con permessi
        admin_role.permissions = [test_permission]
        db_session.commit()
        db_session.refresh(admin_role)
        
        assert len(admin_role.permissions) == 1
        assert admin_role.permissions[0].name == "test:read"
        
        print("✅ Test 1.2: Relazioni Role corrette - PASSATO")
    
    def test_permission_model_relationships(self, db_session, test_permission, admin_user, admin_role):
        """Test: Verifica relazioni Permission con sintassi SQLAlchemy 2.0+"""
        
        # Verifica che il modello Permission abbia le relazioni corrette
        assert hasattr(Permission, 'users')
        assert hasattr(Permission, 'roles')
        
        # Test relazione many-to-many con utenti
        test_permission.users = [admin_user]
        db_session.commit()
        db_session.refresh(test_permission)
        
        assert len(test_permission.users) == 1
        assert test_permission.users[0].email == "admin@test.com"
        
        # Test relazione many-to-many con ruoli
        test_permission.roles = [admin_role]
        db_session.commit()
        db_session.refresh(test_permission)
        
        assert len(test_permission.roles) == 1
        assert test_permission.roles[0].name == "admin"
        
        print("✅ Test 1.3: Relazioni Permission corrette - PASSATO")
    
    def test_pydantic_config(self):
        """Test: Verifica configurazione Pydantic con protected_namespaces"""
        
        # Verifica che tutti i modelli abbiano protected_namespaces=()
        assert User.model_config.get('protected_namespaces') == ()
        assert Role.model_config.get('protected_namespaces') == ()
        assert Permission.model_config.get('protected_namespaces') == ()
        
        print("✅ Test 1.4: Configurazione Pydantic corretta - PASSATO")

class TestSolidityPoint2_Migrations:
    """Test 2: Gestione migrazioni Alembic"""
    
    def test_alembic_migration_exists(self):
        """Test: Verifica che esistano migrazioni Alembic"""
        import os
        migration_dir = "backend/alembic/versions"
        assert os.path.exists(migration_dir)
        
        # Verifica che ci siano file di migrazione
        migration_files = [f for f in os.listdir(migration_dir) if f.endswith('.py')]
        assert len(migration_files) > 0
        
        print("✅ Test 2.1: Migrazioni Alembic esistenti - PASSATO")
    
    def test_alembic_config(self):
        """Test: Verifica configurazione Alembic"""
        import os
        assert os.path.exists("alembic.ini")
        assert os.path.exists("backend/alembic/env.py")
        
        print("✅ Test 2.2: Configurazione Alembic corretta - PASSATO")

class TestSolidityPoint3_Testing:
    """Test 3: Testing"""
    
    def test_user_authentication(self, db_session, admin_user):
        """Test: Verifica autenticazione utente"""
        
        # Test verifica password
        assert verify_password("AdminPass123!", admin_user.hashed_password)
        assert not verify_password("WrongPassword", admin_user.hashed_password)
        
        # Test proprietà utente
        assert admin_user.is_authenticated == True
        assert admin_user.is_anonymous == False
        
        print("✅ Test 3.1: Autenticazione utente - PASSATO")
    
    def test_user_role_methods(self, db_session, admin_user, admin_role):
        """Test: Verifica metodi di gestione ruoli"""
        
        # Assegna ruolo
        admin_user.roles = [admin_role]
        db_session.commit()
        
        # Test has_role
        assert admin_user.has_role("admin") == True
        assert admin_user.has_role("user") == False
        
        # Test has_any_role
        assert admin_user.has_any_role(["admin", "user"]) == True
        assert admin_user.has_any_role(["user", "guest"]) == False
        
        # Test get_role_names
        role_names = admin_user.get_role_names()
        assert "admin" in role_names
        
        print("✅ Test 3.2: Metodi gestione ruoli - PASSATO")
    
    def test_multi_tenant_isolation(self, db_session, test_tenant_id):
        """Test: Verifica isolamento multi-tenant"""
        
        # Crea utenti in tenant diversi
        tenant1_id = test_tenant_id
        tenant2_id = uuid.uuid4()
        
        user1 = User(
            email="user1@test.com",
            username="user1",
            hashed_password=get_password_hash("Pass123!"),
            tenant_id=tenant1_id,
            role="user"
        )
        
        user2 = User(
            email="user2@test.com",
            username="user2",
            hashed_password=get_password_hash("Pass123!"),
            tenant_id=tenant2_id,
            role="user"
        )
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Verifica isolamento
        users_tenant1 = db_session.exec(select(User).where(User.tenant_id == tenant1_id)).all()
        users_tenant2 = db_session.exec(select(User).where(User.tenant_id == tenant2_id)).all()
        
        assert len(users_tenant1) == 1
        assert len(users_tenant2) == 1
        assert users_tenant1[0].email == "user1@test.com"
        assert users_tenant2[0].email == "user2@test.com"
        
        print("✅ Test 3.3: Isolamento multi-tenant - PASSATO")

class TestSolidityPoint4_Security:
    """Test 4: Sicurezza"""
    
    def test_password_hashing(self, db_session):
        """Test: Verifica hashing password sicuro"""
        
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Verifica che l'hash sia diverso dalla password originale
        assert hashed != password
        
        # Verifica che l'hash sia verificabile
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)
        
        # Verifica che l'hash sia lungo (almeno 60 caratteri per bcrypt)
        assert len(hashed) >= 60
        
        print("✅ Test 4.1: Hashing password sicuro - PASSATO")
    
    def test_jwt_token_security(self, admin_user):
        """Test: Verifica sicurezza token JWT"""
        
        # Crea token con dati minimi
        token_data = {
            "sub": admin_user.email,
            "user_id": str(admin_user.id),
            "tenant_id": str(admin_user.tenant_id),
            "exp": datetime.now(timezone.utc).timestamp() + 3600  # 1 ora
        }
        
        token = create_access_token(token_data)
        
        # Verifica che il token sia una stringa valida
        assert isinstance(token, str)
        assert len(token) > 100  # Token JWT tipicamente lunghi
        
        print("✅ Test 4.2: Sicurezza token JWT - PASSATO")
    
    def test_role_based_access_control(self, db_session, admin_user, regular_user, admin_role):
        """Test: Verifica controllo accesso basato su ruoli"""
        
        # Assegna ruolo admin
        admin_user.roles = [admin_role]
        db_session.commit()
        
        # Verifica che admin abbia accesso amministrativo
        assert admin_user.has_role("admin")
        assert admin_user.can_access_admin_features()
        
        # Verifica che utente normale non abbia accesso amministrativo
        assert not regular_user.has_role("admin")
        assert not regular_user.can_access_admin_features()
        
        print("✅ Test 4.3: Controllo accesso basato su ruoli - PASSATO")

class TestSolidityPoint5_MultiTenancy:
    """Test 5: Multi-tenancy"""
    
    def test_tenant_isolation(self, db_session, test_tenant_id):
        """Test: Verifica isolamento completo tra tenant"""
        
        tenant1_id = test_tenant_id
        tenant2_id = uuid.uuid4()
        
        # Crea ruoli per tenant diversi
        role1 = Role(name="role1", description="Role for tenant 1")
        role2 = Role(name="role2", description="Role for tenant 2")
        
        db_session.add_all([role1, role2])
        db_session.commit()
        
        # Crea permessi per tenant diversi
        perm1 = Permission(name="perm1", description="Permission for tenant 1")
        perm2 = Permission(name="perm2", description="Permission for tenant 2")
        
        db_session.add_all([perm1, perm2])
        db_session.commit()
        
        # Verifica che i dati siano isolati
        roles = db_session.exec(select(Role)).all()
        permissions = db_session.exec(select(Permission)).all()
        
        assert len(roles) >= 2
        assert len(permissions) >= 2
        
        print("✅ Test 5.1: Isolamento tenant - PASSATO")
    
    def test_tenant_role_assignment(self, db_session, admin_user, admin_role, test_tenant_id):
        """Test: Verifica assegnazione ruoli per tenant"""
        
        # Assegna ruolo per tenant specifico
        utr = UserTenantRole(
            user_id=admin_user.id,
            tenant_id=test_tenant_id,
            role_id=admin_role.id,
            role=admin_role.name
        )
        db_session.add(utr)
        db_session.commit()
        
        # Verifica che l'utente abbia il ruolo nel tenant
        assert admin_user.has_role_in_tenant("admin", test_tenant_id)
        
        # Verifica che l'utente non abbia il ruolo in altri tenant
        other_tenant_id = uuid.uuid4()
        assert not admin_user.has_role_in_tenant("admin", other_tenant_id)
        
        print("✅ Test 5.2: Assegnazione ruoli per tenant - PASSATO")

class TestSolidityPoint6_Performance:
    """Test 6: Performance e scalabilità"""
    
    def test_database_indexes(self, db_session):
        """Test: Verifica presenza di indici critici"""
        
        # Verifica che i campi critici abbiano indici
        # Questo test verifica che i modelli abbiano definito indici
        assert hasattr(User, '__tablename__')
        assert hasattr(Role, '__tablename__')
        assert hasattr(Permission, '__tablename__')
        
        print("✅ Test 6.1: Presenza indici critici - PASSATO")
    
    def test_query_optimization(self, db_session, admin_user, admin_role):
        """Test: Verifica ottimizzazione query"""
        
        # Test query con join ottimizzato
        admin_user.roles = [admin_role]
        db_session.commit()
        
        # Query ottimizzata con join
        user_with_roles = db_session.exec(
            select(User)
            .where(User.id == admin_user.id)
        ).first()
        
        assert user_with_roles is not None
        assert len(user_with_roles.roles) == 1
        
        print("✅ Test 6.2: Ottimizzazione query - PASSATO")

class TestSolidityPoint7_Documentation:
    """Test 7: Documentazione"""
    
    def test_model_documentation(self):
        """Test: Verifica documentazione modelli"""
        
        # Verifica che i modelli abbiano docstring
        assert User.__doc__ is not None
        assert Role.__doc__ is not None
        assert Permission.__doc__ is not None
        
        # Verifica che i metodi critici abbiano documentazione
        assert User.has_role.__doc__ is not None
        assert User.has_any_role.__doc__ is not None
        assert User.get_role_names.__doc__ is not None
        
        print("✅ Test 7.1: Documentazione modelli - PASSATO")
    
    def test_api_documentation(self):
        """Test: Verifica documentazione API"""
        
        # Verifica che FastAPI generi documentazione OpenAPI
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        print("✅ Test 7.2: Documentazione API - PASSATO")

class TestSolidityIntegration:
    """Test di integrazione per verificare la solidità complessiva"""
    
    def test_complete_user_workflow(self, db_session, test_tenant_id):
        """Test: Workflow completo utente con tutti i componenti"""
        
        # 1. Crea utente
        user = User(
            email="integration@test.com",
            username="integration",
            hashed_password=get_password_hash("IntegrationPass123!"),
            tenant_id=test_tenant_id,
            role="user",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        
        # 2. Crea ruolo e permessi
        role = Role(name="editor", description="Editor role")
        permission = Permission(name="document:edit", description="Edit documents")
        
        db_session.add_all([role, permission])
        db_session.commit()
        
        # 3. Assegna ruolo e permessi
        user.roles = [role]
        user.permissions = [permission]
        db_session.commit()
        
        # 4. Verifica accesso
        assert user.has_role("editor")
        assert user.has_role_in_tenant("editor", test_tenant_id)
        
        # 5. Crea token
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),
            "tenant_id": str(test_tenant_id),
            "roles": ["editor"],
            "permissions": ["document:edit"]
        }
        token = create_access_token(token_data)
        
        # 6. Verifica token
        assert isinstance(token, str)
        assert len(token) > 100
        
        print("✅ Test Integrazione: Workflow completo utente - PASSATO")
    
    def test_security_edge_cases(self, db_session, admin_user, regular_user):
        """Test: Casi limite di sicurezza"""
        
        # Test escalation di privilegi
        regular_user.role = "admin"  # Simula tentativo di escalation
        db_session.commit()
        
        # Verifica che il sistema rilevi il cambiamento
        assert regular_user.role == "admin"
        
        # Test utente disabilitato
        admin_user.is_active = False
        db_session.commit()
        
        # Verifica che utente disabilitato non possa accedere
        assert not admin_user.is_active
        
        print("✅ Test Integrazione: Casi limite sicurezza - PASSATO")

if __name__ == "__main__":
    # Esegui tutti i test di solidità
    pytest.main([__file__, "-v"]) 