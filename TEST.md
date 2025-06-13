# TEST.md

## Test: `test_login_invalid_credentials`

**Descrizione:**
Verifica che il sistema restituisca un errore 401 (Unauthorized) quando vengono forniti credenziali non valide al login.

**Modalità di correzione:**
- Aggiornamento degli endpoint e delle URL nei test per riflettere la struttura attuale dell'applicazione.
- Correzione della configurazione del router di autenticazione in `main.py`.
- Risoluzione dei warning di deprecazione relativi a `datetime.utcnow()` nei modelli.
- Correzione di errori di indentazione nel file `tests/conftest.py`.

**Comando di avvio:**
```bash
pytest -v -s -k "test_login_invalid_credentials"
```

**Esito attuale:**
- Il test viene eseguito correttamente e passa senza warning. 

## Test di Autenticazione

### test_login_success
- **File**: `tests/api/test_auth.py`
- **Descrizione**: Verifica che il login con credenziali valide restituisca un token JWT
- **Prerequisiti**: 
  - Database di test configurato
  - Utente di test creato con email `testuser@example.com` e password `testpassword123`
- **Test Case**:
  1. Invia una richiesta POST a `/api/v1/auth/token` con le credenziali valide
  2. Verifica che la risposta abbia status code 200
  3. Verifica che la risposta contenga un token JWT valido
- **Risultato Atteso**: Il test passa quando viene restituito un token JWT valido
- **Stato**: ✅ PASSED
- **Note**: Il test utilizza il client di test configurato in `conftest.py` e verifica l'integrazione con il sistema di autenticazione JWT 

### test_password_hashing
- **File**: `tests/api/test_auth.py`
- **Descrizione**: Verifica che la password sia stata hashata correttamente
- **Prerequisiti**: 
  - Database di test configurato
  - Utente di test creato
- **Test Case**:
  1. Verifica che la password hashata sia diversa dalla password in chiaro
  2. Verifica che l'hash inizi con "$2b$" (formato bcrypt)
- **Risultato Atteso**: Il test passa quando la password è stata hashata correttamente
- **Stato**: ✅ PASSED
- **Note**: Verifica l'implementazione della sicurezza delle password

### test_login_invalid_credentials
- **File**: `tests/api/test_auth.py`
- **Descrizione**: Verifica il comportamento del sistema con credenziali errate
- **Prerequisiti**: 
  - Database di test configurato
  - Utente di test creato
- **Test Case**:
  1. Invia una richiesta POST a `/api/v1/auth/token` con password errata
  2. Verifica che la risposta abbia status code 401
  3. Verifica che il messaggio di errore sia appropriato
- **Risultato Atteso**: Il test passa quando viene restituito l'errore appropriato
- **Stato**: ✅ PASSED
- **Note**: Verifica la gestione degli errori di autenticazione

### test_rate_limiting
- **File**: `tests/api/test_auth.py`
- **Descrizione**: Verifica il corretto funzionamento del rate limiting per prevenire attacchi di forza bruta
- **Prerequisiti**: 
  - Database di test configurato
  - Utente di test creato
- **Test Case**:
  1. Esegue 6 tentativi di login consecutivi con credenziali non valide
  2. Verifica che i primi 5 tentativi ricevano 401
  3. Verifica che il sesto tentativo riceva 429 (Too Many Requests)
- **Risultato Atteso**: 
  - 5 risposte 401 (Unauthorized)
  - 1 risposta 429 (Too Many Requests)
  - Messaggio di errore appropriato
- **Stato Attuale**: PASSED
- **Note**: 
  - Implementato correttamente il rate limiting con limite di 5 richieste al minuto
  - Il sistema ora protegge efficacemente contro attacchi di forza bruta
  - La risposta 429 viene restituita correttamente con un messaggio di errore chiaro 

# Test Results

## Authentication Tests

### test_password_hashing
- **Status**: PASSED
- **Description**: Verifica che l'hashing delle password funzioni correttamente
- **Prerequisites**: 
  - Database di test configurato
  - Utente di test creato
- **Test Steps**:
  1. Crea un utente di test con password nota
  2. Verifica che la password sia stata hashata correttamente
- **Expected Results**:
  - La password deve essere hashata usando bcrypt
  - L'hash deve essere diverso dalla password originale
- **Actual Results**:
  - Password hashata correttamente con bcrypt
  - Hash generato: $2b$12$c/WtxPUmxcr5e8wPKuQam.vgwWBs2vU4rkZsuRlwa1nSyPzlscQky

### test_login_success
- **Status**: PASSED
- **Description**: Verifica il login con credenziali valide
- **Prerequisites**: 
  - Database di test configurato
  - Utente di test creato con credenziali note
- **Test Steps**:
  1. Invia richiesta di login con credenziali valide
  2. Verifica la risposta del server
- **Expected Results**:
  - Status code 200
  - Token JWT valido nella risposta
- **Actual Results**:
  - Login completato con successo
  - Token JWT generato e restituito correttamente

### test_login_invalid_credentials
- **Status**: PASSED
- **Description**: Verifica il comportamento con credenziali non valide
- **Prerequisites**: 
  - Database di test configurato
  - Utente di test creato
- **Test Steps**:
  1. Invia richiesta di login con credenziali non valide
  2. Verifica la risposta del server
- **Expected Results**:
  - Status code 401 (Unauthorized)
  - Messaggio di errore appropriato
- **Actual Results**:
  - Errore 401 restituito correttamente
  - Messaggio di errore appropriato per credenziali non valide

### test_rate_limiting
- **Status**: PASSED
- **Description**: Verifica il funzionamento del rate limiting per prevenire attacchi di forza bruta
- **Prerequisites**: 
  - Database di test configurato
  - Utente di test creato
  - Rate limiting configurato (5 richieste per minuto)
- **Test Steps**:
  1. Esegui 6 tentativi di login consecutivi con credenziali non valide
  2. Verifica le risposte del server
- **Expected Results**:
  - Prime 5 richieste: status code 401 (credenziali non valide)
  - Sesta richiesta e successive: status code 429 (Too Many Requests)
  - Messaggio di errore appropriato per il rate limiting
- **Actual Results**:
  - Prime 5 richieste: ricevuto 401 come previsto
  - Sesta richiesta e successive: ricevuto 429 come previsto
  - Messaggio di errore corretto: "Rate limit exceeded: 5 per 1 minute"

## Summary
Tutti i test di autenticazione sono stati completati con successo. Il sistema:
- Implementa correttamente l'hashing delle password
- Gestisce correttamente il login con credenziali valide e non valide
- Implementa efficacemente il rate limiting per prevenire attacchi di forza bruta
- Fornisce messaggi di errore appropriati in tutti i casi 