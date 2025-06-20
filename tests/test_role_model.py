"""
Test per il modello Role e la relazione many-to-many con User
"""
import pytest
from sqlmodel import Session
from app.models.role import Role, UserRole, RoleCreate, RoleUpdate, RoleRead
from app.models.user import User
from app.utils.password import get_password_hash


def test_create_role(db_session: Session):
    """Test 4.1.1.1: Creazione di un ruolo."""
    role_data = RoleCreate(
        name="admin",
        description="Amministratore del sistema",
        is_active=True
    )
    
    role = Role.model_validate(role_data)
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    
    assert role.id is not None
    assert role.name == "admin"
    assert role.description == "Amministratore del sistema"
    assert role.is_active is True
    assert role.created_at is not None
    assert role.updated_at is not None


def test_role_unique_name(db_session: Session):
    """Test: Nome ruolo deve essere unico."""
    # Crea primo ruolo
    role1 = Role(name="admin", description="Admin")
    db_session.add(role1)
    db_session.commit()
    
    # Prova a creare secondo ruolo con stesso nome
    role2 = Role(name="admin", description="Another admin")
    db_session.add(role2)
    
    with pytest.raises(Exception):  # Dovrebbe fallire per constraint unique
        db_session.commit()


def test_user_role_relationship(db_session: Session):
    """Test 4.1.1.2: Assegnazione Role ↔ User."""
    # Crea utente
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea ruolo
    role = Role(name="tecnico", description="Tecnico manutenzione")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    
    # Assegna ruolo all'utente
    user_role = UserRole(user_id=user.id, role_id=role.id, assigned_by=user.id)
    db_session.add(user_role)
    db_session.commit()
    
    # Verifica relazione
    db_session.refresh(user)
    db_session.refresh(role)
    
    assert len(user.roles) == 1
    assert user.roles[0].name == "tecnico"
    assert len(role.users) == 1
    assert role.users[0].username == "testuser"


def test_user_role_methods(db_session: Session):
    """Test: Metodi helper per verificare ruoli utente."""
    # Crea utente
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    
    # Crea ruoli
    admin_role = Role(name="admin", description="Admin")
    tecnico_role = Role(name="tecnico", description="Tecnico")
    db_session.add(admin_role)
    db_session.add(tecnico_role)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(admin_role)
    db_session.refresh(tecnico_role)
    
    # Assegna ruoli
    user_role1 = UserRole(user_id=user.id, role_id=admin_role.id, assigned_by=user.id)
    user_role2 = UserRole(user_id=user.id, role_id=tecnico_role.id, assigned_by=user.id)
    db_session.add(user_role1)
    db_session.add(user_role2)
    db_session.commit()
    
    # Verifica metodi
    db_session.refresh(user)
    
    assert user.has_role("admin") is True
    assert user.has_role("tecnico") is True
    assert user.has_role("superuser") is False
    
    assert user.has_any_role(["admin", "superuser"]) is True
    assert user.has_any_role(["superuser", "guest"]) is False
    
    role_names = user.get_role_names()
    assert "admin" in role_names
    assert "tecnico" in role_names
    assert len(role_names) == 2


def test_role_schema_validation():
    """Test: Validazione schemi Pydantic."""
    # Test RoleCreate
    role_data = {
        "name": "admin",
        "description": "Admin role",
        "is_active": True
    }
    role_create = RoleCreate(**role_data)
    assert role_create.name == "admin"
    
    # Test RoleUpdate
    update_data = {
        "description": "Updated description",
        "is_active": False
    }
    role_update = RoleUpdate(**update_data)
    assert role_update.description == "Updated description"
    assert role_update.is_active is False
    assert role_update.name is None


def test_role_inactive(db_session: Session):
    """Test: Ruolo inattivo non viene considerato nei metodi helper."""
    # Crea utente
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    
    # Crea ruolo inattivo
    role = Role(name="inactive_role", description="Inactive role", is_active=False)
    db_session.add(role)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(role)
    
    # Assegna ruolo inattivo
    user_role = UserRole(user_id=user.id, role_id=role.id, assigned_by=user.id)
    db_session.add(user_role)
    db_session.commit()
    
    # Verifica che il ruolo inattivo non sia considerato
    db_session.refresh(user)
    
    assert user.has_role("inactive_role") is False
    assert "inactive_role" not in user.get_role_names() 