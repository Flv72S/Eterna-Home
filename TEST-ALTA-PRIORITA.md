# Test di Alta Priorità

Questo documento elenca i test di alta priorità per il progetto Eterna-Home, suddivisi nelle tre macrocategorie principali.

## 1. Test degli endpoint API critici

### Gestione Utenti
- [ ] `POST /api/users/` - Creazione nuovo utente
  - [ ] Test validazione dati obbligatori
  - [ ] Test validazione formato email
  - [ ] Test validazione password
  - [ ] Test gestione username duplicato
  - [ ] Test gestione email duplicata

- [ ] `GET /api/users/me` - Recupero profilo utente corrente
  - [ ] Test autenticazione richiesta
  - [ ] Test dati completi restituiti
  - [ ] Test gestione token non valido

### Gestione Case
- [ ] `POST /api/houses/` - Creazione nuova casa
  - [ ] Test validazione dati obbligatori
  - [ ] Test associazione con utente proprietario
  - [ ] Test validazione indirizzo
  - [ ] Test gestione permessi

- [ ] `GET /api/houses/{house_id}` - Recupero dettagli casa
  - [ ] Test autenticazione richiesta
  - [ ] Test verifica proprietà
  - [ ] Test dati completi restituiti
  - [ ] Test gestione casa non esistente

### Gestione Documenti
- [ ] `POST /api/documents/` - Upload documento
  - [ ] Test validazione file
  - [ ] Test limiti dimensione
  - [ ] Test tipi file supportati
  - [ ] Test associazione con casa/nodo
  - [ ] Test gestione errori upload

- [ ] `GET /api/documents/{document_id}` - Download documento
  - [ ] Test autenticazione richiesta
  - [ ] Test verifica permessi
  - [ ] Test gestione file non esistente
  - [ ] Test verifica integrità file

## 2. Test di autenticazione e autorizzazione

### Login/Logout
- [ ] `POST /api/auth/login` - Login utente
  - [ ] Test credenziali valide
  - [ ] Test credenziali non valide
  - [ ] Test account disabilitato
  - [ ] Test rate limiting
  - [ ] Test generazione token

- [ ] `POST /api/auth/logout` - Logout utente
  - [ ] Test invalidazione token
  - [ ] Test gestione token non valido
  - [ ] Test gestione sessione

### Gestione Token
- [ ] `POST /api/auth/refresh` - Refresh token
  - [ ] Test refresh token valido
  - [ ] Test refresh token scaduto
  - [ ] Test refresh token revocato
  - [ ] Test generazione nuovo token

### Autorizzazione
- [ ] Test ruoli utente
  - [ ] Test permessi proprietario casa
  - [ ] Test permessi utente standard
  - [ ] Test permessi admin
  - [ ] Test accesso risorse protette

- [ ] Test middleware autorizzazione
  - [ ] Test verifica token
  - [ ] Test verifica ruoli
  - [ ] Test verifica proprietà risorse
  - [ ] Test gestione errori autorizzazione

## 3. Test di integrazione con il database

### Connessione e Configurazione
- [ ] Test connessione database
  - [ ] Test connessione valida
  - [ ] Test gestione errori connessione
  - [ ] Test timeout connessione
  - [ ] Test riconnessione automatica

### Operazioni CRUD
- [ ] Test transazioni
  - [ ] Test commit transazione
  - [ ] Test rollback transazione
  - [ ] Test gestione errori transazione
  - [ ] Test isolamento transazioni

- [ ] Test query complesse
  - [ ] Test join multiple tabelle
  - [ ] Test filtri avanzati
  - [ ] Test ordinamento
  - [ ] Test paginazione
  - [ ] Test performance query

### Integrità Dati
- [ ] Test vincoli database
  - [ ] Test unique constraints
  - [ ] Test foreign key constraints
  - [ ] Test check constraints
  - [ ] Test gestione violazioni vincoli

- [ ] Test migrazioni
  - [ ] Test applicazione migrazione
  - [ ] Test rollback migrazione
  - [ ] Test gestione errori migrazione
  - [ ] Test compatibilità dati

### Performance
- [ ] Test indici
  - [ ] Test utilizzo indici
  - [ ] Test performance query con indici
  - [ ] Test manutenzione indici

- [ ] Test concorrenza
  - [ ] Test accesso concorrente
  - [ ] Test deadlock
  - [ ] Test race conditions
  - [ ] Test gestione lock

## Note
Questi test sono considerati di alta priorità perché:
1. Verificano le funzionalità core dell'applicazione
2. Sono critici per la sicurezza del sistema
3. Garantiscono l'integrità dei dati
4. Prevengono problemi di performance
5. Assicurano la corretta gestione degli errori

## Implementazione
Per ogni test è necessario:
1. Creare un file di test dedicato nella directory appropriata
2. Implementare i test utilizzando pytest
3. Verificare la copertura del codice
4. Documentare i casi di test
5. Integrare i test nel pipeline CI/CD 