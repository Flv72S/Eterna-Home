#!/usr/bin/env python3
"""
Script per rendere nullable i campi software_origin e level_of_detail nella tabella bim_models.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Configurazione database
DATABASE_URL = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"

def fix_bim_fields():
    """Rende nullable i campi software_origin e level_of_detail."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Rende nullable software_origin
            print("Rendendo nullable software_origin...")
            conn.execute(text("ALTER TABLE bim_models ALTER COLUMN software_origin DROP NOT NULL;"))
            
            # Rende nullable level_of_detail
            print("Rendendo nullable level_of_detail...")
            conn.execute(text("ALTER TABLE bim_models ALTER COLUMN level_of_detail DROP NOT NULL;"))
            
            conn.commit()
            print("✅ Campi resi nullable con successo!")
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            conn.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing BIM fields...")
    success = fix_bim_fields()
    if success:
        print("🎉 Operazione completata con successo!")
    else:
        print("💥 Operazione fallita!")
        sys.exit(1) 