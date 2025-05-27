# Eterna Home

Sistema di gestione per case intelligenti che permette di monitorare e controllare vari aspetti della casa attraverso nodi IoT.

## Componenti Principali

### Backend (FastAPI)
- **Autenticazione**: Sistema di login con JWT
- **Gestione Case**: CRUD per le case degli utenti
- **Gestione Nodi**: CRUD per i nodi IoT associati alle case
- **Documenti Legacy**: Sistema di upload e gestione documenti con MinIO
- **Log Audio**: Sistema di registrazione e gestione log audio
- **Manutenzione**: Sistema di gestione manutenzioni

### Frontend (React)
- **Dashboard**: Visualizzazione stato generale della casa
- **Gestione Nodi**: Configurazione e monitoraggio nodi
- **Documenti**: Visualizzazione e gestione documenti
- **Log Audio**: Ascolto e gestione log audio
- **Manutenzioni**: Pianificazione e monitoraggio manutenzioni

## Funzionalità Implementate

### 1. Sistema di Autenticazione
- Login/Logout con JWT
- Protezione delle rotte
- Gestione utenti

### 2. Gestione Case
- Creazione case
- Assegnazione proprietari
- Visualizzazione dettagli

### 3. Gestione Nodi
- Creazione nodi
- Assegnazione a case
- Monitoraggio stato
- Configurazione parametri

### 4. Documenti Legacy
- Upload file su MinIO
- Gestione metadati
- Visualizzazione documenti
- Download file

### 5. Log Audio
- Registrazione audio
- Storage su MinIO
- Visualizzazione e ascolto
- Gestione metadati

### 6. Manutenzioni
- Pianificazione interventi
- Assegnazione tecnici
- Monitoraggio stato
- Storico interventi

## Tecnologie Utilizzate

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- MinIO
- JWT
- Python-Multipart

### Frontend
- React
- Material-UI
- Axios
- React Router

### Testing
- Pytest
- Integration Tests
- Manual Tests

## Setup e Installazione

### Prerequisiti
- Python 3.8+
- Node.js 14+
- PostgreSQL
- MinIO Server

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### MinIO
```bash
# Avvia MinIO server
minio server /data
```

## Testing

### Test di Integrazione
```bash
python run_integration_tests.py
```

### Test Manuali
```bash
python test_manual_upload.py
```

## Note di Sviluppo

### Gestione File
Il sistema gestisce correttamente sia file binari che file di testo, con supporto per:
- Upload multipart
- Conversione automatica tra bytes e file-like objects
- Storage su MinIO
- Gestione metadati

### Sicurezza
- Autenticazione JWT
- Validazione input
- Protezione rotte
- Gestione sicura file

### Performance
- Upload asincrono
- Gestione efficiente file
- Caching quando appropriato
- Query ottimizzate

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

# Eterna Home Backend

## Descrizione
Backend per l'applicazione Eterna Home, sviluppato con FastAPI e PostgreSQL.

## Funzionalità Implementate

### 1. Autenticazione e Gestione Utenti
- **JWT Authentication**: Implementata con `python-jose` e `passlib`.
- **Gestione Ruoli (RBAC)**: Sistema di ruoli per utenti (user, admin, maintenance_manager).
- **Rate Limiting**: Protezione degli endpoint con `fastapi-limiter` (es. 5 richieste al minuto).

### 2. Gestione Documenti
- **Upload e Download**: Supporto per file PDF, immagini e documenti BIM.
- **Storage MinIO**: Integrazione con MinIO per lo storage dei file.
- **Documenti Legacy**: Supporto per documenti legacy con OCR.

### 3. Gestione Manutenzione
- **Task di Manutenzione**: Creazione, assegnazione e monitoraggio dei task.
- **AI Maintenance**: Integrazione con AI per la gestione predittiva della manutenzione.
- **Voice Interfaces**: Endpoint per l'elaborazione dei comandi vocali.

### 4. Logging e Monitoraggio
- **Logging Centralizzato**: Configurazione robusta per log su console e file.
- **Middleware per Logging**: Tracciamento delle richieste HTTP.

## Requisiti
- Python 3.8+
- PostgreSQL
- Redis (per rate limiting)
- MinIO (per storage file)

## Installazione
1. Clona il repository:
   ```bash
   git clone https://github.com/yourusername/eterna-home.git
   cd eterna-home
   ```

2. Installa le dipendenze:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Configura le variabili d'ambiente:
   ```bash
   cp .env.example .env
   # Modifica .env con le tue configurazioni
   ```

4. Avvia il server:
   ```bash
   uvicorn backend.main:app --reload
   ```

## API Endpoints
- **Autenticazione**: `POST /auth/login`, `POST /auth/register`
- **Utenti**: `GET /users/me`, `GET /users/admin-only` (solo admin)
- **Documenti**: `POST /documents/upload`, `GET /documents/{id}`
- **Manutenzione**: `POST /maintenance/tasks`, `GET /maintenance/tasks`
- **Voice Interfaces**: `POST /voice-interfaces/command`
- **Rate Limiting**: `GET /rate-limited` (5 richieste al minuto)

## Contribuire
1. Fork il repository
2. Crea un branch per la tua feature (`git checkout -b feature/nome-feature`)
3. Commit le tue modifiche (`git commit -m 'feat: Aggiunta nuova feature'`)
4. Push al branch (`git push origin feature/nome-feature`)
5. Apri una Pull Request

## Licenza
MIT 