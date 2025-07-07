from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from tests.utils import random_lower_string
from tests.utils.maintenance import create_random_maintenance_record
from tests.utils.user import create_random_user
from tests.utils import get_superuser_token_headers
from app.models.node import Node


def test_export_maintenance_records_csv(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create test records
    user = create_random_user(db)
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()
    db.refresh(node)
    record1 = create_random_maintenance_record(db, user=user, node=node)
    record2 = create_random_maintenance_record(db, user=user, node=node)
    
    response = client.get(
        f"{settings.API_V1_STR}/maintenance_records/export",
        headers=superuser_token_headers,
        params={"format": "csv"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers.get("content-disposition", "").startswith("attachment; filename=maintenance_records")


def test_export_maintenance_records_json(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create test records
    user = create_random_user(db)
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()
    db.refresh(node)
    record1 = create_random_maintenance_record(db, user=user, node=node)
    record2 = create_random_maintenance_record(db, user=user, node=node)
    
    response = client.get(
        f"{settings.API_V1_STR}/maintenance_records/export",
        headers=superuser_token_headers,
        params={"format": "json"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers.get("content-disposition", "").startswith("attachment; filename=maintenance_records")


def test_export_maintenance_records_with_filters(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create test records
    user = create_random_user(db)
    node = Node(name="Test Node", type="Test Type", location="Test Location", status="active")
    db.add(node)
    db.commit()
    db.refresh(node)
    record1 = create_random_maintenance_record(db, user=user, node=node)
    record2 = create_random_maintenance_record(db, user=user, node=node)
    
    # Test with various filters
    filters = {
        "format": "json",
        "start_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "end_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "type": record1.type,
        "status": "completed",
        "search": record1.description[:5]  # Search by partial description
    }
    
    response = client.get(
        f"{settings.API_V1_STR}/maintenance_records/export",
        headers=superuser_token_headers,
        params=filters
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers.get("content-disposition", "").startswith("attachment; filename=maintenance_records")


def test_export_maintenance_records_invalid_format(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/maintenance_records/export",
        headers=superuser_token_headers,
        params={"format": "invalid"}
    )
    assert response.status_code == 422


def test_export_maintenance_records_unauthorized(
    client: TestClient, db: Session
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/maintenance_records/export",
        params={"format": "json"}
    )
    assert response.status_code == 401 