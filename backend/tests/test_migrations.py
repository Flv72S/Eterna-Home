import pytest
from sqlalchemy import inspect, text
from alembic import command
from alembic.config import Config

def test_migration_upgrade(alembic_runner, alembic_engine):
    """Test that the migration can be applied."""
    # Run the migration
    alembic_runner.migrate_up_one()
    
    # Verify that the tables were created
    inspector = inspect(alembic_engine)
    tables = inspector.get_table_names()
    
    # Check that all expected tables exist
    expected_tables = ['users', 'houses', 'nodes', 'user_houses', 'documents', 'alembic_version']
    for table in expected_tables:
        assert table in tables, f"Table {table} was not created"

def test_migration_downgrade(alembic_runner, alembic_engine):
    """Test that the migration can be reversed."""
    # First upgrade to create the tables
    alembic_runner.migrate_up_one()
    
    # Then downgrade to remove them
    alembic_runner.migrate_down_one()
    
    # Verify that only the alembic_version table remains
    inspector = inspect(alembic_engine)
    tables = inspector.get_table_names()
    assert len(tables) == 1, f"Expected only alembic_version table, got {tables}"
    assert 'alembic_version' in tables, "alembic_version table was not preserved"

def test_migration_idempotency(alembic_runner, alembic_engine):
    """Test that running the same migration multiple times doesn't cause issues."""
    # Run the migration multiple times
    for _ in range(3):
        alembic_runner.migrate_up_one()

    # Verify that the tables were created correctly
    inspector = inspect(alembic_engine)
    tables = inspector.get_table_names()

    # Check that all expected tables exist
    expected_tables = ['users', 'houses', 'nodes', 'user_houses', 'documents', 'alembic_version']
    for table in expected_tables:
        assert table in tables, f"Table {table} was not created"

    # Get current revision
    with alembic_engine.connect() as conn:
        current_revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()

    # Run the downgrade only if we have a valid revision
    if current_revision:
        for _ in range(3):
            try:
                alembic_runner.migrate_down_one()
            except ValueError as e:
                if "Revision None is not a valid revision" in str(e):
                    break
                raise e

    # Verify that alembic_version table still exists
    tables = inspector.get_table_names()
    assert 'alembic_version' in tables 