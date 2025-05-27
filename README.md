# Eterna Home

Sistema di gestione per case intelligenti che permette di monitorare e controllare vari aspetti della casa attraverso nodi IoT.

## Componenti Principali

### Backend (FastAPI)

* **Autenticazione**: Sistema di login con JWT
* **Gestione Case**: CRUD per le case degli utenti
* **Gestione Nodi**: CRUD per i nodi IoT associati alle case
* **Documenti Legacy**: Sistema di upload e gestione documenti con MinIO
* **Log Audio**: Sistema di registrazione e gestione log audio
* **Manutenzione**: Sistema di gestione e monitoraggio della manutenzione
* **AI Maintenance**: Integrazione con AI per la manutenzione predittiva
* **Voice Interfaces**: Sistema di interfaccia vocale per i comandi
* **BIM Files**: Gestione dei file BIM per la modellazione 3D

## Tecnologie Utilizzate

### Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* MinIO
* JWT
* Python-Multipart
* Redis (per rate limiting)
* FastAPI-Limiter

### Frontend

* React
* Material-UI
* Axios
* React Router

### Testing

* Pytest
* Integration Tests
* Manual Tests

## Setup e Installazione

### Prerequisiti

* Python 3.13+
* Docker Desktop
* PostgreSQL
* Redis
* MinIO Server
* Git

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
   Crea un file `.env` nella cartella root del progetto con il seguente contenuto:
   ```env
   # Configurazioni Database
   database_url=postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_db
   
   # Configurazioni JWT
   secret_key=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
   algorithm=HS256
   access_token_expire_minutes=30
   
   # Configurazioni MinIO
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   MINIO_SECURE=false
   MINIO_BUCKET_MANUALS=eterna-manuals
   MINIO_BUCKET_AUDIO=eterna-audio
   MINIO_BUCKET_LEGACY=eterna-legacy
   MINIO_BUCKET_BIM=eterna-bim
   
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

## Struttura del Progetto

```
backend/
├── config/             # Configurazioni
├── db/                 # Database e modelli
├── models/             # Modelli SQLAlchemy
├── routers/            # Endpoint API
├── schemas/            # Schemi Pydantic
├── services/           # Servizi di business logic
├── utils/              # Utility functions
├── .env               # Variabili d'ambiente
├── main.py            # Entry point
└── requirements.txt   # Dipendenze Python
```

## Modelli e Relazioni

### User
- Relazioni:
  - `houses`: One-to-Many con House
  - `maintenance_tasks`: One-to-Many con Maintenance
  - `annotations`: One-to-Many con Annotation
  - `bim_files`: One-to-Many con BIM

### House
- Relazioni:
  - `owner`: Many-to-One con User
  - `nodes`: One-to-Many con Node
  - `legacy_documents`: One-to-Many con LegacyDocument
  - `bim_files`: One-to-Many con BIM

### Node
- Relazioni:
  - `house`: Many-to-One con House
  - `documents`: One-to-Many con Document
  - `audio_logs`: One-to-Many con AudioLog
  - `legacy_documents`: One-to-Many con LegacyDocument
  - `bim_files`: One-to-Many con BIM
  - `annotations`: One-to-Many con Annotation
  - `maintenance_tasks`: One-to-Many con MaintenanceTask

## Endpoint Principali

* **Autenticazione**:
  * `POST /auth/login` - Login utente
  * `POST /auth/signup` - Registrazione utente

* **Documenti**:
  * `POST /legacy-documents/` - Carica un nuovo documento
  * `GET /legacy-documents/{node_id}` - Ottiene i documenti di un nodo

* **Manutenzione**:
  * `POST /maintenance/tasks/` - Crea un nuovo task
  * `GET /maintenance/tasks/` - Lista dei task

* **AI Maintenance**:
  * `POST /ai-maintenance/predict` - Predizione manutenzione
  * `POST /ai-maintenance/tasks/` - Crea task AI
  * `GET /ai-maintenance/tasks/` - Lista task AI

* **Rate Limiting**:
  * `GET /rate-limited` - Endpoint di test con rate limiting (5 richieste/min)

## Troubleshooting

1. **MinIO non risponde**  
   * Verifica che il container Docker sia in esecuzione: `docker ps`  
   * Riavvia il container: `docker restart minio`

2. **Database non accessibile**  
   * Verifica che PostgreSQL sia in esecuzione  
   * Controlla le credenziali nel file `.env`

3. **Backend non si avvia**  
   * Verifica che tutte le dipendenze siano installate  
   * Controlla i log per eventuali errori
   * Assicurati che il file `.env` sia nella directory root del progetto

4. **Rate Limiting non funziona**
   * Verifica che Redis sia in esecuzione
   * Controlla la connessione Redis nel file `main.py`

5. **Errori di relazione tra modelli**
   * Verifica che i nomi delle classi nelle relazioni corrispondano ai nomi effettivi dei modelli
   * Controlla che tutte le relazioni siano definite correttamente in entrambi i modelli
   * Assicurati che i modelli siano importati correttamente

## Test Eseguiti

### Test di Integrazione

1. **Test Registrazione Utente**
   - Endpoint: `POST /auth/signup`
   - Dati di test: `email=integration_test_user@example.com, full_name=Test User`
   - Risultato: SUCCESSO
   - Verifica: Utente creato correttamente con ID assegnato

2. **Test Login Utente**
   - Endpoint: `POST /auth/login`
   - Dati di test: `username=integration_test_user@example.com`
   - Risultato: SUCCESSO
   - Verifica: Token JWT generato correttamente

3. **Test Creazione Casa**
   - Endpoint: `POST /houses/`
   - Dati di test: `name=Casa di Test, address=Via Roma 123, Milano`
   - Risultato: SUCCESSO
   - Verifica: Casa creata con ID assegnato e timestamp corretti

4. **Test Creazione Nodo**
   - Endpoint: `POST /nodes/`
   - Dati di test: `name=Nodo Test, type=sensor, status=active`
   - Risultato: SUCCESSO
   - Verifica: Nodo creato con ID assegnato e associato alla casa

### Schema Database
- Verificata la corretta creazione delle tabelle:
  - `users`
  - `houses`
  - `nodes`
  - `maintenance`
  - `maintenance_tasks`
  - `bim_files`
  - `legacy_documents`

### Miglioramenti Implementati
1. Aggiunta gestione timestamp (`created_at`, `updated_at`) per le tabelle
2. Implementato sistema di logging dettagliato per i test
3. Aggiunta gestione errori e rollback automatico in caso di fallimento
4. Ottimizzata la gestione delle relazioni tra tabelle

## Manutenzione

* I file vengono salvati in MinIO nei bucket:  
  * `eterna-manuals`  
  * `eterna-audio`  
  * `eterna-legacy`
  * `eterna-bim`
* I backup sono configurati per essere eseguiti giornalmente
* La retention dei backup è impostata a 30 giorni

## Contribuire

1. Fork il repository
2. Crea un branch per la tua feature (`git checkout -b feature/nome-feature`)
3. Commit le tue modifiche (`git commit -m 'feat: Aggiunta nuova feature'`)
4. Push al branch (`git push origin feature/nome-feature`)
5. Apri una Pull Request

## Licenza

MIT 