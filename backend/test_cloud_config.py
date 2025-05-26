from config.cloud_config import settings

def test_cloud_settings():
    try:
        # Verifica che le impostazioni obbligatorie siano presenti
        print("MinIO Endpoint:", settings.MINIO_ENDPOINT)
        print("MinIO Access Key:", settings.MINIO_ACCESS_KEY)
        print("MinIO Secret Key:", settings.MINIO_SECRET_KEY)
        print("MinIO Encryption Key:", settings.MINIO_ENCRYPTION_KEY)
        
        # Verifica le impostazioni con valori predefiniti
        print("\nImpostazioni predefinite:")
        print("MinIO Secure:", settings.MINIO_SECURE)
        print("MinIO Pool Size:", settings.MINIO_POOL_SIZE)
        print("MinIO Timeout:", settings.MINIO_TIMEOUT)
        print("Backup Enabled:", settings.MINIO_BACKUP_ENABLED)
        print("Backup Frequency:", settings.MINIO_BACKUP_FREQUENCY)
        print("Backup Retention:", settings.MINIO_BACKUP_RETENTION)
        print("Encryption Enabled:", settings.MINIO_ENCRYPTION_ENABLED)
        print("Cache Enabled:", settings.MINIO_CACHE_ENABLED)
        print("Cache TTL:", settings.MINIO_CACHE_TTL)
        
        print("\nTest completato con successo!")
        return True
    except Exception as e:
        print(f"Errore durante il test: {str(e)}")
        return False

if __name__ == "__main__":
    test_cloud_settings() 