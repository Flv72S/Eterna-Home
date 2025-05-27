from minio import Minio
import logging

# Configura il logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_minio_bucket():
    try:
        # Inizializza il client MinIO con le credenziali corrette
        endpoint = "localhost:9000"
        access_key = "minioadmin"
        secret_key = "minioadmin"
        bucket_name = "eterna-legacy"
        
        logger.info(f"Connessione a MinIO su {endpoint}")
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        
        # Lista tutti i bucket
        logger.info("Recupero lista dei bucket...")
        buckets = client.list_buckets()
        logger.info("Bucket disponibili:")
        for bucket in buckets:
            logger.info(f"- {bucket.name} (creato il {bucket.creation_date})")
        
        # Verifica specificamente il bucket eterna-legacy
        logger.info(f"\nVerifica del bucket {bucket_name}...")
        
        if client.bucket_exists(bucket_name):
            logger.info(f"Il bucket {bucket_name} esiste")
            
            # Lista gli oggetti nel bucket
            logger.info(f"Contenuto del bucket {bucket_name}:")
            objects = client.list_objects(bucket_name)
            for obj in objects:
                logger.info(f"- {obj.object_name} (dimensione: {obj.size} bytes)")
        else:
            logger.warning(f"Il bucket {bucket_name} non esiste")
            
            # Prova a creare il bucket
            logger.info(f"Tentativo di creazione del bucket {bucket_name}...")
            client.make_bucket(bucket_name)
            logger.info(f"Bucket {bucket_name} creato con successo")
            
    except Exception as e:
        logger.error(f"Errore durante la verifica di MinIO: {str(e)}")
        raise

if __name__ == "__main__":
    check_minio_bucket() 