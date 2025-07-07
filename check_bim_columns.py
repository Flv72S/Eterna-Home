#!/usr/bin/env python3
"""
Script per verificare lo stato delle colonne BIM nel database.
"""

from app.db.session import get_session
from sqlmodel import text

def check_bim_columns():
    """Verifica lo stato delle colonne software_origin e level_of_detail."""
    print("🔍 Verifica colonne BIM nel database...")
    
    db = next(get_session())
    
    try:
        # Query per verificare le colonne
        query = text("""
            SELECT column_name, is_nullable, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'bim_models' 
            AND column_name IN ('software_origin', 'level_of_detail')
            ORDER BY column_name
        """)
        
        result = db.exec(query).fetchall()
        
        print("\n📊 Stato colonne BIM:")
        print("-" * 50)
        
        for row in result:
            column_name, is_nullable, data_type, column_default = row
            print(f"Colonna: {column_name}")
            print(f"  - Nullable: {is_nullable}")
            print(f"  - Tipo: {data_type}")
            print(f"  - Default: {column_default}")
            print()
        
        # Verifica anche la struttura completa della tabella
        print("📋 Struttura completa tabella bim_models:")
        print("-" * 50)
        
        full_query = text("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns 
            WHERE table_name = 'bim_models'
            ORDER BY ordinal_position
        """)
        
        full_result = db.exec(full_query).fetchall()
        
        for row in full_result:
            column_name, is_nullable, data_type = row
            nullable_status = "NULL" if is_nullable == "YES" else "NOT NULL"
            print(f"{column_name:<25} {data_type:<15} {nullable_status}")
            
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_bim_columns() 