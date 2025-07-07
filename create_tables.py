#!/usr/bin/env python3
"""
Script per creare tutte le tabelle del database Eterna Home
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from sqlmodel import SQLModel, select
from app.database import get_engine
from app.models.user import User
from app.models.house import House
from app.models.room import Room
from app.models.booking import Booking
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.node import Node
from app.models.maintenance import MaintenanceRecord
from app.models.role import Role
from app.models.user_role import UserRole

def create_all_tables():
    """Crea tutte le tabelle del database."""
    print("🚀 Creazione tabelle database...")
    
    try:
        engine = get_engine()
        
        # Crea tutte le tabelle
        SQLModel.metadata.create_all(engine)
        
        print("✅ Tutte le tabelle create con successo!")
        print("\n📋 Tabelle create:")
        print("  - users")
        print("  - houses") 
        print("  - rooms")
        print("  - bookings")
        print("  - documents")
        print("  - document_versions")
        print("  - nodes")
        print("  - maintenance_records")
        print("  - roles")
        print("  - user_roles")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la creazione delle tabelle: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_all_tables() 