# Procedura di Migrazione Database PostgreSQL

Questo documento descrive la procedura corretta per eseguire la migrazione del database PostgreSQL per il progetto Eterna Home.

## Prerequisiti

- PostgreSQL installato e in esecuzione
- Credenziali di accesso al database:
  - Username: postgres
  - Password: N0nn0c4rl0!!
  - Host: localhost
  - Port: 5432

## Passaggi per la Migrazione

### 1. Creazione del Database

Se il database non esiste, crearlo usando lo script `create_db.py`:

```python
# create_db.py
from sqlalchemy import create_engine, text

# Connessione al database postgres (default)
engine = create_engine('postgresql://postgres:N0nn0c4rl0!!@localhost/postgres')

# Creazione del database
with engine.connect() as conn:
    conn.execute(text('commit'))  # Necessario per creare un nuovo database
    conn.execute(text('CREATE DATABASE eterna_home'))
    print("Database 'eterna_home' creato con successo!")
```

Eseguire lo script:
```bash
python create_db.py
```

### 2. Reset della Tabella Alembic

Se necessario, resettare la tabella alembic_version usando lo script `reset_alembic.py`:

```python
# reset_alembic.py
from sqlalchemy import create_engine, text

# Connessione al database eterna_home
engine = create_engine('postgresql://postgres:N0nn0c4rl0!!@localhost/eterna_home')

# Eliminazione della tabella alembic_version se esiste
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
    conn.commit()
    print("Tabella alembic_version resettata con successo!")
```

Eseguire lo script:
```bash
python reset_alembic.py
```

### 3. Esecuzione della Migrazione

Eseguire la migrazione con Alembic:
```bash
alembic upgrade head
```

### 4. Verifica della Migrazione

Per verificare che la migrazione sia stata eseguita correttamente, utilizzare lo script `check_tables.py`:

```python
# check_tables.py
from sqlalchemy import create_engine, text, inspect

# Connessione al database eterna_home
engine = create_engine('postgresql://postgres:N0nn0c4rl0!!@localhost/eterna_home')

# Verifica delle tabelle esistenti
inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tabelle presenti nel database:", tables)

# Verifica della struttura della tabella users
if 'users' in tables:
    columns = inspector.get_columns('users')
    print("\nStruttura della tabella users:")
    for column in columns:
        print(f"- {column['name']}: {column['type']}")
```

Eseguire lo script:
```bash
python check_tables.py
```

## Struttura Attesa del Database

Dopo una migrazione corretta, dovresti vedere:

1. La tabella `alembic_version` per il tracciamento delle migrazioni
2. La tabella `users` con le seguenti colonne:
   - `id` (INTEGER)
   - `username` (VARCHAR(50))
   - `full_name` (VARCHAR(100))
   - `updated_at` (TIMESTAMP)
   - `last_login` (TIMESTAMP)

## Risoluzione dei Problemi

Se incontri errori durante la migrazione:

1. Verifica che PostgreSQL sia in esecuzione
2. Controlla che le credenziali nel file `alembic.ini` siano corrette
3. Assicurati che il database `eterna_home` esista
4. Se necessario, resetta la tabella `alembic_version` e riprova la migrazione

## Note Importanti

- Non eliminare mai i file di migrazione esistenti
- Mantieni sempre un backup del database prima di eseguire migrazioni in produzione
- Verifica sempre la struttura del database dopo una migrazione 