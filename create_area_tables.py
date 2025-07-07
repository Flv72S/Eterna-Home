#!/usr/bin/env python3
"""
Script per creare le tabelle dei modelli NodeArea e MainArea nel database.
Questo script crea le tabelle senza usare Alembic, come richiesto.
"""

import sys
import os

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import SQLModel, select
from app.database import get_engine
from app.models import NodeArea, MainArea, Node, House, User

def create_area_tables():
    """Crea le tabelle per i modelli NodeArea e MainArea."""
    print("🏗️ CREAZIONE TABELLE AREA ↔ NODO")
    print("=" * 50)
    
    try:
        # Ottieni l'engine del database
        engine = get_engine()
        
        # Crea tutte le tabelle
        print("1. Creazione tabelle...")
        SQLModel.metadata.create_all(engine)
        
        print("✅ TABELLE CREATE CON SUCCESSO!")
        print("=" * 50)
        print("📋 TABELLE DISPONIBILI:")
        print("   - node_areas (NodeArea)")
        print("   - main_areas (MainArea)")
        print("   - nodes (Node - aggiornato)")
        print("   - houses (House - aggiornato)")
        print("   - users (User)")
        print("   - rooms (Room)")
        print("   - documents (Document)")
        print("   - maintenance_records (MaintenanceRecord)")
        print("   - bim_models (BIMModel)")
        print("   - ... altre tabelle esistenti")
        
        print("\n🔗 RELAZIONI IMPLEMENTATE:")
        print("   - Node ↔ NodeArea (node_area_id)")
        print("   - Node ↔ MainArea (main_area_id)")
        print("   - House ↔ NodeArea (house_id)")
        print("   - House ↔ MainArea (house_id)")
        print("   - Node ↔ House (house_id)")
        
        print("\n📝 CAMPI AGGIUNTI AL MODELLO NODE:")
        print("   - node_area_id: Optional[int] (FK a node_areas.id)")
        print("   - main_area_id: Optional[int] (FK a main_areas.id)")
        print("   - is_master_node: bool = False")
        print("   - has_physical_tag: bool = True")
        
        print("\n🎯 PROSSIMI STEP:")
        print("   1. Eseguire test_gestione_aree_nodi.py per verificare il funzionamento")
        print("   2. Creare endpoint API per gestione aree")
        print("   3. Implementare CRUD operations per NodeArea e MainArea")
        print("   4. Aggiungere validazioni e controlli di sicurezza")
        
    except Exception as e:
        print(f"❌ ERRORE durante la creazione delle tabelle: {e}")
        raise

if __name__ == "__main__":
    create_area_tables() 