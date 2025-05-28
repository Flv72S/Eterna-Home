# Guida all'Avvio del Sistema Eterna Home

Questa guida fornisce istruzioni dettagliate per l'avvio e la configurazione del sistema Eterna Home.

## Prerequisiti

Assicurati di avere installato:
- Python 3.13+
- Docker Desktop
- PostgreSQL
- Redis
- Git

## 1. Setup Iniziale

### 1.1 Clonazione del Repository
```bash
git clone https://github.com/Flv72S/Eterna-Home.git
cd Eterna-Home
```

### 1.2 Installazione Dipendenze
```bash
pip install -r requirements.txt
```

### 1.3 Configurazione Variabili d'Ambiente
Crea un file `.env` nella root del progetto con le seguenti variabili:
```env
# Database
database_url=postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_db

# JWT
secret_key=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
algorithm=HS256
access_token_expire_minutes=30

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_MANUALS=eterna-manuals
MINIO_BUCKET_AUDIO=eterna-audio
MINIO_BUCKET_LEGACY=eterna-legacy
MINIO_BUCKET_BIM=eterna-bim

# Crittografia
MINIO_ENCRYPTION_KEY=your-encryption-key-here
```

## 2. Avvio dei Servizi

### 2.1 Avvio di MinIO
```bash
# Rimuovi eventuali container esistenti
docker rm -f minio

# Avvia un nuovo container MinIO
docker run -d -p 9000:9000 -p 9001:9001 --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

### 2.2 Configurazione PostgreSQL
```bash
# Connessione a PostgreSQL
psql -U postgres

# Creazione del database (se non esiste)
CREATE DATABASE eterna_home_db;

# Uscita da psql
\q
```

### 2.3 Migrazioni Database con Alembic
```bash
# Inizializza le migrazioni (solo la prima volta)
alembic init alembic

# Crea una nuova migrazione
alembic revision --autogenerate -m "descrizione della migrazione"

# Applica le migrazioni
alembic upgrade head
```

### 2.4 Avvio di Redis
```bash
# Avvia Redis in modalità standalone
redis-server
```

### 2.5 Avvio del Backend
```bash
# Avvia il server FastAPI con hot-reload
uvicorn backend.main:app --reload
```

## 3. Verifica del Sistema

### 3.1 Controllo Servizi
```bash
# Verifica container Docker
docker ps

# Verifica connessione PostgreSQL
psql -U postgres -d eterna_home_db -c "\dt"

# Verifica Redis
redis-cli ping

# Verifica MinIO
curl http://localhost:9000/minio/health/live
```

### 3.2 Test API
```bash
# Test endpoint di salute
curl http://localhost:8000/health

# Test rate limiting
curl http://localhost:8000/rate-limited
```

## 4. Risoluzione Problemi Comuni

### 4.1 Problemi di Connessione Database
```bash
# Verifica credenziali PostgreSQL
psql -U postgres -d eterna_home_db

# Reset database (se necessario)
python reset_db.py
```

### 4.2 Problemi MinIO
```bash
# Verifica log MinIO
docker logs minio

# Riavvio MinIO
docker restart minio
```

### 4.3 Problemi Redis
```bash
# Verifica stato Redis
redis-cli info

# Riavvio Redis
redis-cli shutdown
redis-server
```

### 4.4 Problemi Backend
```bash
# Verifica log backend
tail -f logs/backend.log

# Riavvio backend
pkill -f uvicorn
uvicorn backend.main:app --reload
```

## 5. Comandi Utili

### 5.1 Gestione Database
```bash
# Backup database
pg_dump -U postgres eterna_home_db > backup.sql

# Ripristino database
psql -U postgres eterna_home_db < backup.sql
```

### 5.2 Gestione Log
```bash
# Visualizza log backend
tail -f logs/backend.log

# Visualizza log MinIO
docker logs -f minio
```

### 5.3 Pulizia Sistema
```bash
# Rimuovi container non utilizzati
docker system prune

# Pulisci cache Redis
redis-cli FLUSHALL
```

## 6. Note Importanti

- Mantieni sempre una copia di backup del database
- Monitora regolarmente i log per eventuali errori
- Aggiorna regolarmente le dipendenze con `pip install -r requirements.txt --upgrade`
- Esegui i test dopo ogni aggiornamento significativo
- Mantieni aggiornato il file `.env` con le configurazioni corrette 