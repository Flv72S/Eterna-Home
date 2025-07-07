#!/usr/bin/env python3
"""
Script per controllare la struttura della tabella documents
"""

from app.database import engine
from sqlalchemy import text

def check_documents_table():
    """Controlla la struttura della tabella documents"""
    with engine.connect() as conn:
        # Controlla le colonne esistenti
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'documents' 
            ORDER BY ordinal_position
        """))
        
        print("=== STRUTTURA ATTUALE TABELLA DOCUMENTS ===")
        for row in result:
            print(f"{row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
        
        print("\n=== COLONNE MANCANTI RISPETTO AL MODELLO ===")
        expected_columns = [
            'id', 'title', 'description', 'document_type', 'file_url', 
            'file_size', 'file_type', 'checksum', 'tenant_id', 'owner_id',
            'is_encrypted', 'house_id', 'node_id', 'created_at', 'updated_at'
        ]
        
        existing_columns = [row[0] for row in conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'documents'
        """))]
        
        missing_columns = [col for col in expected_columns if col not in existing_columns]
        if missing_columns:
            print("Colonne mancanti:")
            for col in missing_columns:
                print(f"  - {col}")
        else:
            print("Tutte le colonne sono presenti!")

if __name__ == "__main__":
    check_documents_table() 