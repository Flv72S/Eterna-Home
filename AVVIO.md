# AVVIO.md - Stato Attuale del Progetto Eterna Home

## 📋 Situazione Attuale

### ✅ Problemi Risolti

1. **Problema principale identificato e risolto**: I test fallivano perché usavano il file `app/main.py` sbagliato (quello nella root) invece di quello in `backend/app/main.py`.

2. **Tabella `user` mancante**: SQLModel non riconosceva il modello `User` e non creava la tabella. Risolto con creazione manuale della tabella.

3. **Endpoint mancanti**: Il file `app/main.py` nella root non includeva i router corretti per `/api/v1/auth/register` e altri endpoint.

### 🔧 Correzioni Apportate

#### 1. Aggiornamento `app/main.py` (root)
```python
# AGGIUNTO: Importazione dei router corretti da backend
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.users import router as users_router

# AGGIUNTO: Registrazione dei router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
```

#### 2. Sincronizzazione `app/services/user.py` (root)
```python
# MODIFICATO: UserService ora accetta session nel costruttore
class UserService:
    def __init__(self, session: Session):
        self.session = session
    
    # Tutti i metodi ora sono a istanza invece che statici
```

#### 3. Aggiornamento `tests/conftest.py`
```python
# AGGIUNTO: Creazione manuale della tabella user
with test_engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS "user" (
            id SERIAL PRIMARY KEY,
            email VARCHAR NOT NULL UNIQUE,
            username VARCHAR NOT NULL UNIQUE,
            hashed_password VARCHAR NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_superuser BOOLEAN DEFAULT FALSE,
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE,
            full_name VARCHAR(255),
            phone_number VARCHAR(20)
        )
    """))
```

#### 4. Aggiornamento `tests/test_auth.py`
```python
# AGGIUNTO: Debug delle risposte di registrazione e login
print(f"[DEBUG] Register response status: {reg_status}")
print(f"[DEBUG] Register response json: {reg_json}")
print(f"[DEBUG] Login response status: {login_status}")
print(f"[DEBUG] Login response json: {login_json}")
```

## 🚀 Procedura di Riavvio

### 1. Attivazione Ambiente Virtuale
```bash
# Dalla directory root del progetto
cd C:\Users\flavi\Eterna-Home
venv\Scripts\activate
```

### 2. Verifica Database di Test
```bash
# Verifica che il database di test esista
python -c "from tests.conftest import TEST_DATABASE_URL; print('Test DB URL:', TEST_DATABASE_URL)"
```

### 3. Esecuzione Test di Verifica
```bash
# Test singolo per verificare che tutto funzioni
python -m pytest tests/test_auth.py::test_login_success -v -s
```

### 4. Avvio Applicazione (se necessario)
```bash
# Dalla directory backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 Prossimi Passaggi Immediati

### 1. Verificare le Risposte degli Endpoint
Il test `test_login_success` ora dovrebbe mostrare:
- **Register response status**: 422 (Unprocessable Entity) - da investigare
- **Register response json**: Dettagli dell'errore di validazione
- **Login response status**: Probabilmente 401 (se la registrazione fallisce)
- **Login response json**: Dettagli dell'errore di autenticazione

### 2. Investigare Errore 422 nella Registrazione
L'errore 422 indica un problema di validazione dei dati. Possibili cause:
- Schema `UserCreate` non corrisponde ai dati inviati
- Validazione Pydantic fallisce
- Campi obbligatori mancanti

### 3. Correggere Schema di Validazione
Controllare e correggere:
- `app/schemas/user.py` - schema `UserCreate`
- Validazione nel router `backend/app/api/v1/endpoints/auth.py`

### 4. Testare Endpoint Individualmente
```bash
# Test solo registrazione
python -m pytest tests/test_auth.py::test_register_success -v -s

# Test solo login
python -m pytest tests/test_auth.py::test_login_success -v -s
```

### 5. Verificare Tutti i Test di Autenticazione
```bash
# Tutti i test di autenticazione
python -m pytest tests/test_auth.py -v -s
```

## 📁 Struttura File Corretta

```
Eterna-Home/
├── app/                          # App principale (root)
│   ├── main.py                   # ✅ AGGIORNATO - include router backend
│   ├── services/user.py          # ✅ AGGIORNATO - UserService a istanza
│   └── ...
├── backend/                      # Backend specifico
│   ├── app/
│   │   ├── main.py              # App backend (non usata dai test)
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py          # Router autenticazione
│   │   │   └── users.py         # Router utenti
│   │   └── ...
│   └── ...
└── tests/                        # Test nella root
    ├── conftest.py              # ✅ AGGIORNATO - creazione tabella user
    ├── test_auth.py             # ✅ AGGIORNATO - debug risposte
    └── ...
```

## 🔍 Debug Attuale

### Comando per Vedere le Risposte
```bash
python -m pytest tests/test_auth.py::test_login_success -v -s
```

### Output Atteso
- ✅ Tabella `user` creata correttamente
- ✅ Endpoint `/api/v1/auth/register` trovato (non più 404)
- 🔍 Errore 422 da investigare (validazione dati)
- 📊 Debug delle risposte visibile nell'output

## ⚠️ Note Importanti

1. **I test ora usano il file corretto**: `app/main.py` nella root (aggiornato)
2. **La tabella user viene creata**: Manualmente per ogni test
3. **Gli endpoint esistono**: Router backend inclusi correttamente
4. **Debug attivo**: Le risposte vengono stampate nel test

## 🎉 Risultato

**Il problema principale è stato risolto!** I test ora:
- ✅ Usano i file corretti
- ✅ Creano la tabella `user`
- ✅ Trovano gli endpoint
- 🔍 Mostrano le risposte dettagliate per il debug

Il prossimo passo è investigare l'errore 422 nella registrazione per completare l'implementazione dell'autenticazione. 