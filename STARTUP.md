# Guida all'Avvio di Eterna Home

Questa guida ti aiuterà a configurare e avviare il sistema Eterna Home.

## Prerequisiti

- Python 3.8+
- PostgreSQL 13+
- Redis (per rate limiting)
- Node.js 16+ (per il frontend)

## Configurazione Iniziale

### 1. Ambiente Virtuale Python

```bash
# Crea l'ambiente virtuale
python -m venv venv

# Attiva l'ambiente virtuale
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Installazione Dipendenze Backend

```bash
pip install -r requirements.txt
```

Dipendenze principali:
- fastapi
- sqlmodel
- uvicorn
- pydantic-settings
- fastapi-limiter
- redis
- psycopg2-binary

### 3. Configurazione Database

1. Crea un database PostgreSQL:
```sql
CREATE DATABASE eterna_home_db;
```

2. Verifica le credenziali in `backend/core/config.py`:
```python
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_db"
)
```

### 4. Avvio del Backend

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Verifica che il server sia in esecuzione visitando:
- API Docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Troubleshooting

### Problemi Comuni

1. **Errore "Module not found"**
   - Verifica che l'ambiente virtuale sia attivo
   - Reinstalla le dipendenze: `pip install -r requirements.txt`

2. **Errore di connessione al database**
   - Verifica che PostgreSQL sia in esecuzione
   - Controlla le credenziali in `backend/core/config.py`

3. **Errore di importazione circolare**
   - Usa importazioni lazy con `from __future__ import annotations`
   - Riorganizza la struttura dei moduli se necessario

4. **Rate Limiting non funziona**
   - Verifica che Redis sia in esecuzione
   - Controlla la configurazione Redis in `backend/core/config.py`

### Log e Debug

- I log dell'applicazione sono disponibili in `logs/app.log`
- Per debug dettagliato, modifica il livello di log in `backend/config/logging_config.py`

## Struttura delle Directory

```
backend/
├── core/
│   └── config.py         # Configurazione dell'applicazione
├── models/
│   ├── node.py          # Modelli SQLModel per i nodi
│   └── ...
├── schemas/
│   ├── node.py          # Schemi Pydantic per i nodi
│   └── ...
├── api/
│   └── v1/
│       └── endpoints/
│           └── nodes.py  # API endpoints per i nodi
└── main.py              # Entry point dell'applicazione
```

## Note Importanti

1. **Ambiente Virtuale**
   - Usa SEMPRE l'ambiente virtuale per lo sviluppo
   - Non committare mai la cartella `venv`

2. **Configurazione**
   - Le configurazioni sensibili vanno in variabili d'ambiente
   - Non committare mai file `.env` o credenziali

3. **Database**
   - Usa migrazioni per modifiche al database
   - Backup regolari del database

4. **Sicurezza**
   - Mantieni aggiornate tutte le dipendenze
   - Usa HTTPS in produzione
   - Implementa rate limiting per tutte le API pubbliche 