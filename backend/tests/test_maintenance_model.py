import pytest
from datetime import datetime
from sqlalchemy import inspect
from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.node import Node

def test_maintenance_records_table_structure(db):
    """Test that the maintenance_records table exists with the correct structure"""
    inspector = inspect(db.bind)
    columns = inspector.get_columns('maintenance_records')
    
    # Check that all required columns exist
    column_names = {col['name'] for col in columns}
    required_columns = {'id', 'node_id', 'date', 'type', 'description', 'status', 'notes', 'created_at', 'updated_at'}
    assert required_columns.issubset(column_names)
    
    # Check column types and constraints
    for col in columns:
        if col['name'] == 'id':
            assert col['type'].python_type == int
            # Check primary key constraint
            pk_constraint = inspector.get_pk_constraint('maintenance_records')
            assert 'id' in pk_constraint['constrained_columns']
        elif col['name'] == 'node_id':
            assert col['type'].python_type == int
            assert not col['nullable']
        elif col['name'] == 'date':
            assert col['type'].python_type == datetime
            assert not col['nullable']
        elif col['name'] == 'type':
            assert col['type'].python_type == str
            assert not col['nullable']
        elif col['name'] == 'description':
            assert col['type'].python_type == str
            assert not col['nullable']
        elif col['name'] == 'status':
            assert col['type'].python_type == str
            assert not col['nullable']
        elif col['name'] == 'notes':
            assert col['type'].python_type == str
            assert col['nullable']  # Notes can be null
        elif col['name'] in ('created_at', 'updated_at'):
            assert col['type'].python_type == datetime
            assert not col['nullable']

def test_maintenance_record_node_relationship(db):
    """Test the relationship between MaintenanceRecord and Node"""
    # Create a test node
    node = Node(
        name="Test Node",
        type="Test Type",
        location="Test Location",
        status="active"
    )
    db.add(node)
    db.commit()
    
    # Create a maintenance record
    maintenance = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance",
        status=MaintenanceStatus.PENDING
    )
    db.add(maintenance)
    db.commit()
    
    # Test the relationship
    assert maintenance.node_id == node.id
    assert maintenance.node == node
    assert maintenance in node.maintenance_records

def test_create_maintenance_record(db):
    """Test creating a valid maintenance record"""
    # Create a test node
    node = Node(
        name="Test Node",
        type="Test Type",
        location="Test Location",
        status="active"
    )
    db.add(node)
    db.commit()
    
    # Create a maintenance record
    maintenance = MaintenanceRecord(
        node_id=node.id,
        date=datetime.utcnow(),
        type="Routine",
        description="Test maintenance",
        status=MaintenanceStatus.PENDING,
        notes="Test notes"
    )
    db.add(maintenance)
    db.commit()
    
    # Verify the record was created correctly
    assert maintenance.id is not None
    assert maintenance.node_id == node.id
    assert maintenance.type == "Routine"
    assert maintenance.description == "Test maintenance"
    assert maintenance.status == MaintenanceStatus.PENDING
    assert maintenance.notes == "Test notes"
    assert maintenance.created_at is not None
    assert maintenance.updated_at is not None

def test_maintenance_record_node_integration(db):
    """Test the bidirectional relationship between Node and MaintenanceRecord"""
    # Create a test node
    node = Node(
        name="Test Node",
        type="Test Type",
        location="Test Location",
        status="active"
    )
    db.add(node)
    db.commit()
    
    # Create multiple maintenance records
    maintenance_records = [
        MaintenanceRecord(
            node_id=node.id,
            date=datetime.utcnow(),
            type="Routine",
            description=f"Test maintenance {i}",
            status=MaintenanceStatus.PENDING
        )
        for i in range(3)
    ]
    db.add_all(maintenance_records)
    db.commit()
    
    # Test that node can access its maintenance records
    assert len(node.maintenance_records) == 3
    for i, record in enumerate(node.maintenance_records):
        assert record.description == f"Test maintenance {i}"
        assert record.node == node

