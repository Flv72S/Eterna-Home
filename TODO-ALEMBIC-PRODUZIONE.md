# TODO Alembic per la Produzione

Quando sarai pronto a riattivare Alembic per la gestione delle migrazioni in produzione, **ricordati di:**

1. **Sbloccare gli import Alembic**  
   In tutti i file dove trovi il tag  
   `# [DISABILITATO TEMPORANEAMENTE: Alembic]`
   - Sblocca le righe:
     ```python
     from alembic.config import Config
     from alembic import command
     from alembic.script import ScriptDirectory
     ```

2. **Riattivare le funzioni/fixture di migrazione**  
   - In `tests/conftest.py`, `backend/tests/conftest.py`, `backend/tests/create_test_db.py`, `backend/scripts/create_test_db.py`, ecc.
   - Sblocca le funzioni che applicano le migrazioni (`apply_migrations`, fixture che usano Alembic, ecc).

3. **Riattivare gli script di utility**  
   - `reset_test_db.py`, `check_migration.py`, `backend/run_migrations.py`, ecc.
   - Sblocca le parti che eseguono Alembic via subprocess o Python.

4. **Riattivare i test sulle migrazioni**  
   - In `backend/tests/test_migrations.py` e simili, sblocca import e funzioni di test che usano Alembic.

5. **Verifica la presenza e correttezza di `alembic.ini` e delle directory `alembic/` o `backend/alembic/`**  
   - Assicurati che il path e la configurazione siano aggiornati.

6. **Rimuovi o aggiorna la dipendenza da `reset_and_seed.py`**  
   - In produzione, la preparazione del DB deve avvenire solo tramite Alembic.

---

**Quando tutte queste azioni sono state completate, puoi tornare a gestire il database e le migrazioni in modo sicuro e strutturato con Alembic!** 