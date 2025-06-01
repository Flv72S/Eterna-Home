import pytest
from pytest_alembic import MigrationContext
from sqlalchemy import inspect, text
from app.db.session import engine

def test_migration_creates_users_table(alembic_runner: MigrationContext):
    """Test che verifica la creazione della tabella users."""
    # Esegui la migrazione
    alembic_runner.migrate_up_to("head")
    
    # Verifica che la tabella users esista
    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()

def test_migration_creates_correct_columns(alembic_runner: MigrationContext):
    """Test che verifica la presenza di tutte le colonne nella tabella users."""
    # Esegui la migrazione
    alembic_runner.migrate_up_to("head")
    
    # Verifica le colonne
    inspector = inspect(engine)
    columns = {col["name"]: col["type"] for col in inspector.get_columns("users")}
    
    # Verifica le colonne obbligatorie
    assert "id" in columns
    assert "username" in columns
    assert "email" in columns
    assert "hashed_password" in columns
    assert "is_active" in columns
    assert "is_superuser" in columns
    assert "is_verified" in columns
    assert "created_at" in columns
    assert "updated_at" in columns

def test_migration_creates_indexes(alembic_runner: MigrationContext):
    """Test che verifica la creazione degli indici."""
    # Esegui la migrazione
    alembic_runner.migrate_up_to("head")
    
    # Verifica gli indici
    inspector = inspect(engine)
    indexes = inspector.get_indexes("users")
    index_names = {index["name"] for index in indexes}
    
    assert "ix_users_username" in index_names
    assert "ix_users_email" in index_names

def test_migration_is_reversible(alembic_runner: MigrationContext):
    """Test che verifica che la migrazione sia reversibile."""
    # Esegui la migrazione
    alembic_runner.migrate_up_to("head")
    
    # Verifica che la tabella esista
    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()
    
    # Esegui il downgrade
    alembic_runner.migrate_down_to("base")
    
    # Verifica che la tabella non esista più
    assert "users" not in inspector.get_table_names()

def test_migration_sets_default_values(alembic_runner: MigrationContext):
    """Test che verifica i valori di default delle colonne."""
    # Esegui la migrazione
    alembic_runner.migrate_up_to("head")
    
    # Inserisci un utente di test
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO users (username, email, hashed_password)
            VALUES ('testuser', 'test@example.com', 'hashed_password')
        """))
        conn.commit()
    
    # Verifica i valori di default
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT is_active, is_superuser, is_verified
            FROM users
            WHERE username = 'testuser'
        """)).fetchone()
        
        assert result[0] is True  # is_active
        assert result[1] is False  # is_superuser
        assert result[2] is False  # is_verified 