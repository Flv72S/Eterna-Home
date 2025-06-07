from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.utils import random_lower_string
from app.tests.utils.maintenance import create_random_maintenance_record
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import get_superuser_token_headers


def test_export_maintenance_records_csv(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create test records
    user = create_random_user(db)
    record1 = create_random_maintenance_record(db, user_id=user.id)
    record2 = create_random_maintenance_record(db, user_id=user.id)
    
    response = client.get(
        f"{settings.API_V1_STR}/maintenance/export",
        headers=superuser_token_headers,
        params={"format": "csv"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert "attachment; filename=maintenance_records" in response.headers["content-disposition"]


def test_export_maintenance_records_json(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create test records
    user = create_random_user(db)
    record1 = create_random_maintenance_record(db, user_id=user.id)
    record2 = create_random_maintenance_record(db, user_id=user.id)
    
    response = client.get(
        f"{settings.API_V1_STR}/maintenance/export",
        headers=superuser_token_headers,
        params={"format": "json"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment; filename=maintenance_records" in response.headers["content-disposition"]


def test_export_maintenance_records_with_filters(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create test records
    user = create_random_user(db)
    record1 = create_random_maintenance_record(db, user_id=user.id)
    record2 = create_random_maintenance_record(db, user_id=user.id)
    
    # Test with various filters
    filters = {
        "format": "json",
        "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "maintenance_type": record1.maintenance_type,
        "status": record1.status,
        "priority": record1.priority,
        "search": record1.title[:5]  # Search by partial title
    }
    
    response = client.get(
        f"{settings.API_V1_STR}/maintenance/export",
        headers=superuser_token_headers,
        params=filters
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_export_maintenance_records_invalid_format(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/maintenance/export",
        headers=superuser_token_headers,
        params={"format": "invalid"}
    )
    assert response.status_code == 422


def test_export_maintenance_records_unauthorized(
    client: TestClient, db: Session
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/maintenance/export",
        params={"format": "json"}
    )
    assert response.status_code == 401 