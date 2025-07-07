#!/usr/bin/env python3
"""
Script per inizializzare MinIO per Eterna Home.
Crea il bucket e configura le policy di sicurezza.
"""

import os
import sys
import time
from minio import Minio
from minio.error import S3Error
import json
import io

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def init_minio():
    """Inizializza MinIO per Eterna Home."""
    print("🚀 Inizializzazione MinIO per Eterna Home...")
    
    try:
        # Crea il client MinIO
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        
        print(f"✅ Connesso a MinIO su {settings.MINIO_ENDPOINT}")
        
        # Verifica se il bucket esiste
        bucket_name = settings.MINIO_BUCKET_NAME
        if client.bucket_exists(bucket_name):
            print(f"✅ Bucket '{bucket_name}' già esistente")
        else:
            # Crea il bucket
            client.make_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' creato con successo")
        
        # Configura il bucket come privato
        try:
            # Rimuove policy pubbliche esistenti
            try:
                client.delete_bucket_policy(bucket_name)
                print(f"🗑️  Rimosse policy pubbliche dal bucket '{bucket_name}'")
            except S3Error:
                # Il bucket potrebbe non avere policy, ignoriamo l'errore
                pass
            
            # Imposta policy privata semplificata
            private_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "DenyPublicRead",
                        "Effect": "Deny",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }
                ]
            }
            
            client.set_bucket_policy(bucket_name, json.dumps(private_policy))
            print(f"🔒 Bucket '{bucket_name}' configurato come privato")
            
        except S3Error as e:
            print(f"⚠️  Non è stato possibile configurare la policy del bucket: {e}")
        
        # Crea cartelle di base
        base_folders = ["documents", "bim", "media", "backups", "temp"]
        for folder in base_folders:
            try:
                # Crea un file di test per creare la cartella
                test_file = f"{folder}/.keep"
                data = io.BytesIO(b"")
                client.put_object(bucket_name, test_file, data, 0)
                print(f"📁 Cartella '{folder}' creata")
            except S3Error as e:
                print(f"⚠️  Errore nella creazione della cartella '{folder}': {e}")
        
        print("\n🎉 MinIO inizializzato con successo!")
        print(f"📊 Console MinIO: http://localhost:9001")
        print(f"🔑 Access Key: {settings.MINIO_ACCESS_KEY}")
        print(f"🔐 Secret Key: {settings.MINIO_SECRET_KEY}")
        print(f"📦 Bucket: {bucket_name}")
        
    except Exception as e:
        print(f"❌ Errore nell'inizializzazione di MinIO: {e}")
        print("💡 Assicurati che MinIO sia in esecuzione su localhost:9000")
        return False
    
    return True

if __name__ == "__main__":
    # Aspetta un po' per assicurarsi che MinIO sia avviato
    print("⏳ Attendo che MinIO sia pronto...")
    time.sleep(3)
    
    success = init_minio()
    if not success:
        sys.exit(1) 