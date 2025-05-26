# Eterna-Home

Sistema di gestione documenti legacy per Eterna-Home.

## Infrastruttura

Il sistema è composto da:

1. **Backend FastAPI** (Python)
   - Gestisce le API REST
   - Integrazione con MinIO per lo storage dei file
   - Database PostgreSQL per la persistenza dei dati

2. **MinIO** (Object Storage)
   - Gestisce lo storage dei file
   - Accessibile su http://localhost:9000
   - Console di amministrazione su http://localhost:9001

3. **PostgreSQL** (Database)
   - Database relazionale per la persistenza dei dati
   - Porta: 5432

## Prerequisiti

- Python 3.13+
- Docker Desktop
- PostgreSQL
- Git

## Configurazione Iniziale

1. **Clona il repository**
   ```bash
   git clone https://github.com/Flv72S/Eterna-Home.git
   cd Eterna-Home
   ```

2. **Configura l'ambiente Python**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configura le variabili d'ambiente**
   Crea un file `.env` nella cartella `backend` con il seguente contenuto:
   ```env
   # Configurazioni Database
   database_url=postgresql://postgres:postgres@localhost:5432/eterna_home_db

   # Configurazioni JWT
   secret_key=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
   algorithm=HS256
   access_token_expire_minutes=30

   # Configurazioni MinIO
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   MINIO_SECURE=false

   # Configurazioni Crittografia
   MINIO_ENCRYPTION_KEY=your-encryption-key-here
   ```

## Riavvio dell'Infrastruttura

### 1. Avvio di MinIO
```bash
docker run -d -p 9000:9000 -p 9001:9001 --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

### 2. Verifica PostgreSQL
Assicurati che PostgreSQL sia in esecuzione e che il database `eterna_home_db` esista:
```bash
# Connessione a PostgreSQL
psql -U postgres

# Creazione del database (se non esiste)
CREATE DATABASE eterna_home_db;
```

### 3. Avvio del Backend
```bash
cd backend
python -m uvicorn main:app --reload
```

## Verifica del Sistema

1. **API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

2. **MinIO Console**
   - URL: http://localhost:9001
   - Credenziali:
     - Username: minioadmin
     - Password: minioadmin

## Struttura del Progetto

```
backend/
├── config/             # Configurazioni
├── db/                 # Database e modelli
├── models/             # Modelli SQLAlchemy
├── routers/            # Endpoint API
├── schemas/            # Schemi Pydantic
├── utils/              # Utility functions
├── .env               # Variabili d'ambiente
├── main.py            # Entry point
└── requirements.txt   # Dipendenze Python
```

## Endpoint Principali

- `POST /legacy-documents/` - Carica un nuovo documento
- `GET /legacy-documents/{node_id}` - Ottiene i documenti di un nodo

## Troubleshooting

1. **MinIO non risponde**
   - Verifica che il container Docker sia in esecuzione: `docker ps`
   - Riavvia il container: `docker restart minio`

2. **Database non accessibile**
   - Verifica che PostgreSQL sia in esecuzione
   - Controlla le credenziali nel file `.env`

3. **Backend non si avvia**
   - Verifica che tutte le dipendenze siano installate
   - Controlla i log per eventuali errori

## Manutenzione

- I file vengono salvati in MinIO nei bucket:
  - `eterna-manuals`
  - `eterna-audio`
  - `eterna-legacy`

- I backup sono configurati per essere eseguiti giornalmente
- La retention dei backup è impostata a 30 giorni 