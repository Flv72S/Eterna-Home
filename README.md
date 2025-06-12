# Eterna-Home

## Novità e Implementazioni Recenti (giugno 2025)

- **Endpoint Export Manutenzione**: `/api/v1/maintenance_records/export` per esportazione CSV/JSON con filtri avanzati.
- **Endpoint Import Storico**: `/api/v1/maintenance_records/import-historical-data` per importazione da CSV/JSON.
- **Fix Routing**: Corretto ordine degli endpoint per evitare conflitti tra `/export` e `/{id}`.
- **Gestione case-insensitive** per il filtro `status`.
- **Gestione errori migliorata** e messaggi di validazione chiari.
- **Test automatici** per export, filtri, errori formato e range date.
- **Best Practice**: separazione logica, logging, test isolati.

Sistema di Gestione Centralizzata della Casa Digitale

## Implementazioni Completate

### Macro-step 1.2 - CRUD Base per User: Schemi Pydantic

#### Micro-step 1.2.1 - Schemi Pydantic per User
- ✅ Implementazione schemi Pydantic per la gestione utenti:
  - `UserBase`: Schema base con campi comuni
  - `UserCreate`: Schema per la creazione utenti
  - `UserUpdate`: Schema per aggiornamenti parziali
  - `UserRead`: Schema per output API (esclude dati sensibili)

#### Test Implementati
- ✅ Test di validazione:
  - Validazione dati corretti
  - Validazione email
  - Validazione password
  - Gestione campi opzionali

- ✅ Test di sicurezza:
  - Esclusione dati sensibili
  - Protezione password/hash
  - Serializzazione sicura

- ✅ Test di compatibilità ORM:
  - Integrazione con modelli ORM
  - Gestione aggiornamenti

- ✅ Test edge-case:
  - Gestione campi mancanti
  - Gestione payload vuoti
  - Validazione tipi di dati

#### Dipendenze
- pydantic>=2.5.0
- email-validator>=2.1.0
- pytest>=7.4.0
- sqlmodel>=0.0.8

## Struttura del Progetto
```
app/
  ├── schemas/
  │   ├── __init__.py
  │   ├── user.py
  │   └── test_user.py
  └── ...
```

## Come Eseguire i Test
```bash
python -m pytest app/schemas/test_user.py -v
```

## Prossimi Step
- Implementazione modelli SQLModel
- Integrazione con database
- Implementazione CRUD operations

## Macro-step 1.2.3 - API RESTful CRUD per User

### Endpoint Implementati
- POST /users/ : Crea un nuovo utente
- GET /users/{id} : Recupera i dettagli di un utente
- GET /users?skip=...&limit=... : Lista utenti con paginazione
- PUT /users/{id} : Aggiorna un utente
- DELETE /users/{id} : Elimina un utente

### Test automatici superati
- test_create_user_success: verifica creazione utente
- test_create_user_duplicate_email: verifica gestione email duplicata
- test_get_user_success: verifica recupero utente esistente
- test_get_user_not_found: verifica gestione utente non trovato
- test_get_users_pagination: verifica paginazione utenti
- test_update_user_success: verifica aggiornamento utente
- test_delete_user_success: verifica eliminazione utente

### Come eseguire i test API

```bash
python -m pytest tests/api/test_user_api.py -v
```

Tutti i test devono risultare PASSED.

## Macro-step 1.3 - Autenticazione e Sicurezza

### Micro-step 1.3.1 - JWT Authentication

- ✅ Implementazione sistema di autenticazione JWT:
  - Generazione token di accesso
  - Validazione token
  - Gestione scadenza token
  - Middleware di autenticazione
  - Riorganizzazione struttura autenticazione:
    * Router in `app/routers/auth.py`
    * Funzioni di utilità in `app/core/auth.py`

### Micro-step 1.3.2 - Redis Caching

- ✅ Implementazione caching con Redis:
  - Cache per dati utente
  - Gestione TTL (Time To Live)
  - Invalidation cache
  - Fallback su database

### Test Implementati

- ✅ Test autenticazione:
  - Login utente
  - Validazione token
  - Protezione endpoint
  - Gestione token scaduti
- ✅ Test caching:
  - Hit/Miss cache
  - Invalidation
  - TTL
  - Fallback DB

### Dipendenze

- pydantic>=2.5.0
- email-validator>=2.1.0
- pytest>=7.4.0
- sqlmodel>=0.0.8
- python-jose[cryptography]>=3.3.0
- redis>=5.0.0
- fakeredis>=2.20.0

## Struttura del Progetto

```
app/
  ├── api/
  │   └── __init__.py
  ├── core/
  │   ├── auth.py
  │   ├── security.py
  │   ├── config.py
  │   └── warnings.py
  ├── models/
  │   ├── user.py
  │   └── house.py
  ├── routers/
  │   ├── users.py
  │   ├── auth.py
  │   └── house.py
  ├── schemas/
  │   ├── user.py
  │   └── house.py
  └── main.py
tests/
  ├── api/
  │   ├── test_user_api.py
  │   └── test_house_api.py
  └── conftest.py
```

## Come Eseguire i Test

```bash
# Test schemi
python -m pytest app/schemas/test_user.py -v

# Test API utenti
python -m pytest tests/api/test_user_api.py -v

# Test API case
python -m pytest tests/api/test_house_api.py -v
```

## Prossimi Step

- Implementazione refresh token
- Rate limiting avanzato
- Logging e monitoring
- Documentazione API con Swagger/OpenAPI
- Implementazione gestione dispositivi
- Integrazione con protocolli IoT

## Macro-step 1.4 - Gestione Case

### Micro-step 1.4.1 - Modello House

- ✅ Implementazione modello House con SQLModel:
  - Relazione many-to-one con User
  - Gestione proprietario della casa
  - Timestamps automatici
  - Risoluzione importazioni circolari

### Micro-step 1.4.2 - API RESTful CRUD per House

- ✅ Implementazione endpoint CRUD:
  - POST /houses/ : Crea una nuova casa
  - GET /houses/ : Lista delle case dell'utente
  - GET /houses/{house_id} : Dettagli di una casa
  - PUT /houses/{house_id} : Aggiorna una casa
  - DELETE /houses/{house_id} : Elimina una casa

- ✅ Funzionalità implementate:
  - Autenticazione JWT per tutti gli endpoint
  - Verifica proprietà casa
  - Field filtering nella lista case
  - Gestione errori e permessi

#### Test Implementati

- ✅ Test modello House:
  - Creazione casa
  - Relazione con utente
  - Validazione dati
  - Timestamps

- ✅ Test API House:
  - Creazione casa
  - Lista case
  - Dettagli casa
  - Aggiornamento casa
  - Eliminazione casa
  - Gestione permessi
  - Field filtering

## Macro-step 2.1 - Gestione Documenti

### Micro-step 2.1.7 - Upload/Download File Document (Storage MinIO)

- ✅ Implementazione storage MinIO:
  - Client MinIO per upload/download file
  - Gestione bucket e path
  - Calcolo checksum SHA256
  - Gestione errori e permessi

- ✅ Endpoint implementati:
  - POST /documents/{document_id}/upload: Upload file
  - GET /documents/{document_id}/download: Download file

- ✅ Funzionalità implementate:
  - Validazione file (tipo, dimensione)
  - Gestione errori
  - Permessi utente
  - Logging operazioni

- ✅ Test implementati:
  - Upload file
  - Download file
  - Validazione file
  - Gestione errori
  - Permessi utente

### Micro-step 2.1.8 - Gestione Versioni Documenti

- ✅ Implementazione gestione versioni:
  - Storage versioni in MinIO
  - Metadati versione
  - Rollback versione
  - Diff tra versioni

- ✅ Endpoint implementati:
  - GET /documents/{document_id}/versions: Lista versioni
  - GET /documents/{document_id}/versions/{version_id}: Dettagli versione
  - POST /documents/{document_id}/versions/{version_id}/rollback: Rollback versione

- ✅ Funzionalità implementate:
  - Storage versioni
  - Metadati versione
  - Rollback versione
  - Diff tra versioni

- ✅ Test implementati:
  - Lista versioni
  - Dettagli versione
  - Rollback versione
  - Diff tra versioni

### Micro-step 2.1.9 - Ricerca Documenti

- ✅ Implementazione ricerca documenti:
  - Ricerca full-text
  - Filtri avanzati
  - Paginazione risultati
  - Ordinamento risultati

- ✅ Endpoint implementati:
  - GET /documents/search: Ricerca documenti

- ✅ Funzionalità implementate:
  - Ricerca full-text
  - Filtri avanzati
  - Paginazione risultati
  - Ordinamento risultati

- ✅ Test implementati:
  - Ricerca full-text
  - Filtri avanzati
  - Paginazione risultati
  - Ordinamento risultati

## Macro-step 2.2 - Gestione Manutenzioni

### Micro-step 2.2.1 - Modello Maintenance

- ✅ Implementazione modello Maintenance con SQLModel:
  - Relazione many-to-one con House
  - Gestione stato manutenzione
  - Timestamps automatici
  - Risoluzione importazioni circolari

### Micro-step 2.2.2 - API RESTful CRUD per Maintenance

- ✅ Implementazione endpoint CRUD:
  - POST /maintenance_records/ : Crea una nuova manutenzione
  - GET /maintenance_records/ : Lista delle manutenzioni della casa
  - GET /maintenance_records/{id} : Dettagli di una manutenzione
  - PUT /maintenance_records/{id} : Aggiorna una manutenzione
  - DELETE /maintenance_records/{id} : Elimina una manutenzione

- ✅ Funzionalità implementate:
  - Autenticazione JWT per tutti gli endpoint
  - Verifica proprietà casa
  - Field filtering nella lista manutenzioni
  - Gestione errori e permessi

#### Test Implementati

- ✅ Test modello Maintenance:
  - Creazione manutenzione
  - Relazione con casa
  - Validazione dati
  - Timestamps

- ✅ Test API Maintenance:
  - Creazione manutenzione
  - Lista manutenzioni
  - Dettagli manutenzione
  - Aggiornamento manutenzione
  - Eliminazione manutenzione
  - Gestione permessi
  - Field filtering

### Micro-step 2.2.3 - Export/Import Manutenzioni

- ✅ Implementazione export/import manutenzioni:
  - Export CSV/JSON
  - Import CSV/JSON
  - Validazione dati
  - Gestione errori

- ✅ Endpoint implementati:
  - GET /maintenance_records/export: Export manutenzioni
  - POST /maintenance_records/import-historical-data: Import manutenzioni

- ✅ Funzionalità implementate:
  - Export CSV/JSON
  - Import CSV/JSON
  - Validazione dati
  - Gestione errori

- ✅ Test implementati:
  - Export CSV/JSON
  - Import CSV/JSON
  - Validazione dati
  - Gestione errori

## Test Falliti

- **ModuleNotFoundError: No module named 'app.db.base_class'**
  - Causa: La directory `backend` non è nel `PYTHONPATH` di pytest.
  - Soluzione: Aggiungere la riga `pythonpath = .` in `pytest.ini`.

- **ImportError: cannot import name 'upload_file' from 'app.services.minio_service'**
  - Causa: La funzione `upload_file` non esiste o non è esportata in `app/services/minio_service.py`.
  - Soluzione: Verificare che la funzione `upload_file` sia definita ed esportata in `app/services/minio_service.py`.

- **ModuleNotFoundError: No module named 'faker'**
  - Causa: La libreria `faker` non è installata.
  - Soluzione: Installare la libreria `faker` con `pip install faker`.

## Prossimi Step

- Risolvere gli errori dei test falliti.
- Implementare la gestione dei file BIM.
- Migliorare la gestione degli errori e il logging.
- Aggiungere documentazione API con Swagger/OpenAPI.
- Implementare la gestione dei dispositivi.
- Integrare con protocolli IoT.

## Implementazioni Realizzate

### 2.1.6 Gestione Utenti
- **Modello User**: Creato in `app/models/user.py` con campi come `id`, `email`, `hashed_password`, `is_active`, `is_superuser`, `created_at`, `updated_at`, `username` (opzionale), `is_verified`, `last_login`, `full_name`, `phone_number` e relazioni con `House` e `Document`.
- **Router per la Gestione Utenti**: Implementato in `app/routers/users.py` con endpoint per creazione, lettura, aggiornamento ed eliminazione utenti.
- **Dipendenze e Autenticazione**: Configurato `get_current_user` in `app/core/deps.py` per gestire l'autenticazione tramite JWT e cache Redis.
- **Test Automatici**: Creati test in `tests/api/test_users.py` per verificare tutte le operazioni CRUD.
- **Configurazione del Database di Test**: Configurato `conftest.py` per creare un database SQLite in memoria per i test.
- **Uniformazione degli Import**: Uniformato l'import di `get_session` da `app.database` in tutti i file rilevanti.
- **Rendere `username` Opzionale**: Modificato il modello `User` per rendere `username` opzionale, garantendo compatibilità con i test e le API.

### Step 3.1: Gestione della manutenzione dei nodi

- **Modello MaintenanceRecord**: Implementato il modello per i record di manutenzione dei nodi, con relazioni verso Node e Document.
- **Enum MaintenanceType**: Definiti i tipi di manutenzione supportati (ROUTINE, PREVENTIVE, CORRECTIVE, EMERGENCY, INSPECTION).
- **Enum MaintenanceStatus**: Definiti gli stati possibili di un record di manutenzione (PENDING, COMPLETED, FAILED).
- **Test**: Implementati test per la creazione di record di manutenzione, la relazione con i nodi e i vincoli NOT NULL.

### Step 3.2: Export e Import dei record di manutenzione

- **Endpoint Export**: Implementato endpoint `/api/v1/maintenance_records/export` per esportare i record di manutenzione in formato CSV o JSON, con filtri su status, tipo, nodo e intervallo date.
- **Endpoint Import**: Implementato endpoint `/api/v1/maintenance_records/import-historical-data` per importare record storici da file CSV o JSON, con validazione e processi asincroni.
- **Fix Routing**: Corretto l'ordine degli endpoint per evitare conflitti tra `/export` e `/{id}`.
- **Gestione Case-insensitive**: Migliorata la gestione del filtro `status` per accettare valori case-insensitive.
- **Gestione errori**: Migliorata la gestione degli errori e dei messaggi di validazione per parametri e filtri.
- **Test Export**: Implementati test automatici per l'export in CSV e JSON, filtri, gestione formati non validi e range date non valido.
- **Best Practice**: Separazione delle logiche di validazione, uso di SQLModel, test isolati, logging dettagliato.

## Struttura aggiornata del progetto

```
backend/
  ├── app/
  │   ├── api/v1/endpoints/maintenance.py  # Endpoint manutenzione (export/import inclusi)
  │   ├── schemas/maintenance.py           # Schemi Pydantic per manutenzione
  │   └── ...
  ├── tests/
  │   ├── test_maintenance_export.py      # Test export manutenzione
  │   └── ...
  └── ...
```

## Prossimi Step
- Pulizia e isolamento dati nei test di export (reset DB tra i test)
- Aggiornamento test per compatibilità Pydantic v2
- Refactoring e documentazione endpoint manutenzione
- Miglioramento UX lato frontend per export/import
- Logging avanzato e monitoraggio errori

## Implementazioni Realizzate (aggiornamento)

### 3.2 Gestione Manutenzione Avanzata
- **Export/Import**: Endpoint per esportazione e importazione record manutenzione, con filtri avanzati e validazione.
- **Test Export**: Test automatici per export CSV/JSON, filtri, errori formato e range date.
- **Fix Routing**: Corretto ordine endpoint per evitare conflitti.
- **Gestione errori**: Migliorata validazione parametri e messaggi di errore.
- **Best Practice**: Logging, separazione responsabilità, test isolati.

## Novità Apportate

- **Test di Autenticazione**: Implementati test per verificare il corretto funzionamento dell'autenticazione, inclusi test per il login e la gestione delle password hashate.
- **Gestione delle Password**: Utilizzo di `bcrypt` per l'hashing delle password, garantendo la sicurezza delle credenziali degli utenti.
- **Logging**: Aggiunto logging per facilitare il debug e il monitoraggio delle operazioni di test.

## Come Eseguire i Test

Per eseguire i test di autenticazione, utilizza il seguente comando:

```bash
pytest tests/api/test_auth.py -v
```

## Contribuire

Se desideri contribuire al progetto, segui le istruzioni nel file `CONTRIBUTING.md`.
