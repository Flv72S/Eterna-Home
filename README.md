# Eterna-Home

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

## Macro-step 2.1 - Gestione Nodi

### Micro-step 2.1.4 - CRUD API per Node

- ✅ Implementazione modello Node:
  - Campi: `id`, `name`, `description`, `nfc_id`, `house_id`
  - Vincoli: `nfc_id` univoco e indicizzato
  - Relazione con `House`
  - Validazione campi obbligatori

- ✅ Implementazione API Endpoints (`/nodes/`):
  - POST / : Creazione nodo
  - GET /{node_id} : Lettura singolo nodo
  - GET / : Lista nodi con filtri
  - PUT /{node_id} : Aggiornamento nodo
  - DELETE /{node_id} : Eliminazione nodo

- ✅ Funzionalità implementate:
  - Validazione `nfc_id` duplicato
  - Ricerca case-insensitive
  - Filtri multipli (name, nfc_id, house_id)
  - Autenticazione JWT
  - Gestione errori e permessi

- ✅ Test Suite:
  - Test di base (CRUD)
  - Test di filtro e ricerca
  - Test di validazione
  - Test di sicurezza
  - Test di robustezza

- ✅ Miglioramenti:
  - Aggiornamento a Pydantic v2
  - Gestione timezone
  - Documentazione warning
  - Ottimizzazioni performance

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
  │   ├── house.py
  │   └── node.py
  ├── routers/
  │   ├── users.py
  │   ├── auth.py
  │   ├── house.py
  │   └── node.py
  ├── schemas/
  │   ├── user.py
  │   ├── house.py
  │   └── node.py
  └── main.py
tests/
  ├── api/
  │   ├── test_user_api.py
  │   ├── test_house_api.py
  │   └── test_node_api.py
  ├── models/
  │   ├── test_user.py
  │   ├── test_house.py
  │   └── test_node.py
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

# Test API nodi
python -m pytest tests/api/test_node_api.py -v
```

## Dipendenze

* pydantic>=2.5.0
* email-validator>=2.1.0
* pytest>=7.4.0
* sqlmodel>=0.0.8
* python-jose[cryptography]>=3.3.0
* redis>=5.0.0
* fakeredis>=2.20.0

## Prossimi Step

* Implementazione refresh token
* Rate limiting avanzato
* Logging e monitoring
* Documentazione API con Swagger/OpenAPI
* Implementazione gestione dispositivi
* Integrazione con protocolli IoT
