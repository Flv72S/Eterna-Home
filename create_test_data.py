#!/usr/bin/env python3
"""
Script per creare dati di test necessari per i test BIM.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import uuid

# Aggiungi il path del progetto
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.core.config import settings
from app.db.session import get_session
from app.models.user import User
from app.models.house import House
from app.utils.password import get_password_hash
from sqlmodel import Session, select

def create_test_data():
    """Crea i dati di test necessari per i test BIM."""
    print("🚀 Creazione dati di test per BIM...")
    
    db = next(get_session())
    
    try:
        # Verifica se l'utente di test esiste già
        test_user = db.exec(select(User).where(User.id == 1)).first()
        if not test_user:
            # Crea utente di test
            test_user = User(
                id=1,
                email="test@example.com",
                username="testuser",
                hashed_password=get_password_hash("testpassword"),
                full_name="Test User",
                is_active=True,
                is_verified=True,
                tenant_id=uuid.uuid4(),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(test_user)
            print("✅ Utente di test creato (ID: 1)")
        else:
            print("✅ Utente di test già esistente (ID: 1)")
        
        # Verifica se la casa di test esiste già
        test_house = db.exec(select(House).where(House.id == 1)).first()
        if not test_house:
            # Crea casa di test
            test_house = House(
                id=1,
                name="Test House",
                address="Via Test 123",
                city="Test City",
                country="Italy",
                postal_code="12345",
                description="Casa di test per i test BIM",
                total_area=150.0,
                total_rooms=5,
                year_built=2020,
                owner_id=1,  # Riferimento all'utente di test
                tenant_id=test_user.tenant_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(test_house)
            print("✅ Casa di test creata (ID: 1)")
        else:
            print("✅ Casa di test già esistente (ID: 1)")
        
        db.commit()
        print("🎉 Dati di test creati con successo!")
        
    except Exception as e:
        print(f"❌ Errore nella creazione dei dati di test: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    success = create_test_data()
    if not success:
        sys.exit(1) 