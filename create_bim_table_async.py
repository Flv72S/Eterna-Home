#!/usr/bin/env python3
"""
Script per creare la tabella BIM con supporto per conversione asincrona.
Aggiorna la tabella esistente aggiungendo i nuovi campi necessari.
"""

import sys
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, DateTime, Boolean
from sqlalchemy.exc import OperationalError

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.db.session import engine

def create_bim_table_async():
    """Crea o aggiorna la tabella bim_models con supporto per conversione asincrona."""
    
    try:
        # Verifica se la tabella esiste
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'bim_models'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ Tabella bim_models esistente trovata")
                
                # Verifica se i nuovi campi esistono già
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'bim_models' 
                    AND column_name IN ('conversion_status', 'conversion_message', 'conversion_progress');
                """))
                existing_columns = [row[0] for row in result.fetchall()]
                
                if len(existing_columns) >= 3:
                    print("✅ Campi di conversione asincrona già presenti")
                    return
                
                print("🔄 Aggiungendo campi per conversione asincrona...")
                
                # Aggiungi i nuovi campi
                columns_to_add = [
                    "conversion_status VARCHAR(50) DEFAULT 'pending'",
                    "conversion_message TEXT",
                    "conversion_progress INTEGER DEFAULT 0",
                    "converted_file_url TEXT",
                    "validation_report_url TEXT",
                    "conversion_started_at TIMESTAMP WITH TIME ZONE",
                    "conversion_completed_at TIMESTAMP WITH TIME ZONE"
                ]
                
                for column_def in columns_to_add:
                    try:
                        column_name = column_def.split()[0]
                        if column_name not in existing_columns:
                            conn.execute(text(f"ALTER TABLE bim_models ADD COLUMN {column_def}"))
                            print(f"✅ Aggiunto campo: {column_name}")
                    except Exception as e:
                        print(f"⚠️ Campo {column_name} già presente o errore: {e}")
                
                conn.commit()
                print("✅ Tabella bim_models aggiornata con successo")
                
            else:
                print("🔄 Creando tabella bim_models con supporto conversione asincrona...")
                
                # Crea la tabella completa
                conn.execute(text("""
                    CREATE TABLE bim_models (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        format VARCHAR(10) NOT NULL,
                        software_origin VARCHAR(50) NOT NULL,
                        level_of_detail VARCHAR(20) NOT NULL,
                        revision_date TIMESTAMP WITH TIME ZONE,
                        file_url TEXT NOT NULL,
                        file_size BIGINT NOT NULL,
                        checksum VARCHAR(64) NOT NULL,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        house_id INTEGER NOT NULL REFERENCES houses(id),
                        node_id INTEGER REFERENCES nodes(id),
                        conversion_status VARCHAR(50) DEFAULT 'pending',
                        conversion_message TEXT,
                        conversion_progress INTEGER DEFAULT 0,
                        converted_file_url TEXT,
                        validation_report_url TEXT,
                        conversion_started_at TIMESTAMP WITH TIME ZONE,
                        conversion_completed_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                # Crea indici
                conn.execute(text("CREATE INDEX idx_bim_models_user_id ON bim_models(user_id);"))
                conn.execute(text("CREATE INDEX idx_bim_models_house_id ON bim_models(house_id);"))
                conn.execute(text("CREATE INDEX idx_bim_models_conversion_status ON bim_models(conversion_status);"))
                conn.execute(text("CREATE INDEX idx_bim_models_format ON bim_models(format);"))
                
                conn.commit()
                print("✅ Tabella bim_models creata con successo")
        
        print("\n🎉 Setup tabella BIM completato!")
        print("📋 Campi disponibili:")
        print("   - conversion_status: Stato della conversione")
        print("   - conversion_message: Messaggio di stato")
        print("   - conversion_progress: Progresso (0-100)")
        print("   - converted_file_url: URL del file convertito")
        print("   - validation_report_url: URL del report di validazione")
        print("   - conversion_started_at: Data inizio conversione")
        print("   - conversion_completed_at: Data completamento conversione")
        
    except Exception as e:
        print(f"❌ Errore durante la creazione della tabella: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Avvio setup tabella BIM con conversione asincrona...")
    create_bim_table_async()
    print("✅ Setup completato!") 