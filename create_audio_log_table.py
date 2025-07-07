#!/usr/bin/env python3
"""
Script per creare la tabella AudioLog senza Alembic.
Da eseguire manualmente per aggiungere la nuova tabella al database.
"""

import sys
import os
from sqlalchemy import text
from sqlmodel import SQLModel, select

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.models.audio_log import AudioLog

def create_audio_log_table():
    """Crea la tabella audio_logs nel database."""
    try:
        print("Creazione tabella audio_logs...")
        
        # Crea la tabella AudioLog
        AudioLog.metadata.create_all(bind=engine, tables=[AudioLog.__table__])
        
        print("✅ Tabella audio_logs creata con successo!")
        
        # Verifica che la tabella sia stata creata
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'audio_logs'
            """))
            
            if result.fetchone():
                print("✅ Verifica: tabella audio_logs presente nel database")
                
                # Mostra la struttura della tabella
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'audio_logs'
                    ORDER BY ordinal_position
                """))
                
                print("\n📋 Struttura tabella audio_logs:")
                print("-" * 50)
                for row in result:
                    nullable = "NULL" if row.is_nullable == "YES" else "NOT NULL"
                    print(f"{row.column_name:<20} {row.data_type:<15} {nullable}")
                
            else:
                print("❌ Errore: tabella audio_logs non trovata")
                return False
                
    except Exception as e:
        print(f"❌ Errore durante la creazione della tabella: {e}")
        return False
    
    return True

def insert_sample_data():
    """Inserisce dati di esempio nella tabella audio_logs."""
    try:
        print("\nInserimento dati di esempio...")
        
        from app.database import get_db
        from app.models.audio_log import AudioLog
        from datetime import datetime, timezone
        
        db = next(get_db())
        
        # Trova un utente esistente
        user = db.exec(text("SELECT id FROM users LIMIT 1")).first()
        if not user:
            print("❌ Nessun utente trovato nel database")
            return False
        
        # Trova una casa esistente
        house = db.exec(text("SELECT id FROM houses LIMIT 1")).first()
        if not house:
            print("❌ Nessuna casa trovata nel database")
            return False
        
        # Trova un nodo esistente
        node = db.exec(text("SELECT id FROM nodes LIMIT 1")).first()
        
        # Dati di esempio
        sample_logs = [
            {
                "user_id": user[0],
                "house_id": house[0],
                "node_id": node[0] if node else None,
                "transcribed_text": "Accendi la luce in cucina",
                "response_text": "Luce in cucina accesa",
                "processing_status": "completed"
            },
            {
                "user_id": user[0],
                "house_id": house[0],
                "node_id": node[0] if node else None,
                "transcribed_text": "Imposta la temperatura a 22 gradi",
                "response_text": "Temperatura impostata a 22°C",
                "processing_status": "completed"
            },
            {
                "user_id": user[0],
                "house_id": house[0],
                "node_id": node[0] if node else None,
                "transcribed_text": "Chiudi le tapparelle",
                "response_text": "Tapparelle chiuse",
                "processing_status": "completed"
            },
            {
                "user_id": user[0],
                "house_id": house[0],
                "node_id": node[0] if node else None,
                "transcribed_text": "Attiva la modalità notte",
                "processing_status": "analyzing"
            },
            {
                "user_id": user[0],
                "house_id": house[0],
                "node_id": node[0] if node else None,
                "transcribed_text": "Mostra lo stato del sistema",
                "processing_status": "transcribing"
            }
        ]
        
        # Inserisci i dati
        for log_data in sample_logs:
            audio_log = AudioLog(**log_data)
            db.add(audio_log)
        
        db.commit()
        print(f"✅ {len(sample_logs)} record di esempio inseriti")
        
    except Exception as e:
        print(f"❌ Errore durante l'inserimento dei dati di esempio: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Creazione tabella AudioLog per Eterna-Home")
    print("=" * 50)
    
    # Crea la tabella
    if create_audio_log_table():
        # Inserisci dati di esempio
        insert_sample_data()
        
        print("\n🎉 Setup completato con successo!")
        print("\n📝 Prossimi passi:")
        print("1. Testa le API vocali con: python test_voice_api.py")
        print("2. Verifica la tabella nel database")
        print("3. Integra con il sistema di coda per elaborazione NLP")
    else:
        print("\n❌ Setup fallito!")
        sys.exit(1) 