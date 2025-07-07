"""
Utility functions for authentication in tests.
"""

import uuid
from sqlmodel import Session
from app.models.user import User
from app.core.security import create_access_token

def create_test_user_with_tenant(session: Session):
    """Crea un utente di test con un tenant."""
    tenant_id = uuid.uuid4()
    unique_id = str(uuid.uuid4())[:8]  # Usa solo i primi 8 caratteri per brevità
    
    user = User(
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        hashed_password="hashed_password",
        full_name="Test User",
        tenant_id=tenant_id,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user, tenant_id

def get_auth_headers(user, tenant_id: uuid.UUID):
    """Crea gli header di autenticazione per un utente."""
    token = create_access_token(
        data={"sub": user.email, "tenant_id": str(tenant_id)}
    )
    return {"Authorization": f"Bearer {token}"} 