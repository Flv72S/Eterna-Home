# Test Superati

Questo documento contiene l'elenco dei test superati per l'applicazione Eterna-Home. I test sono organizzati per categoria e includono una descrizione dettagliata di ciascun test.

## Autenticazione e Gestione Utenti

### Lettura Dati Utente
1. `test_read_users_me`
   - Verifica che l'endpoint `/users/me` restituisca correttamente i dati dell'utente autenticato
   - Controlla che tutti i campi dell'utente siano presenti e corretti

2. `test_read_users_me_unauthorized`
   - Verifica che l'endpoint `/users/me` restituisca errore 401 se l'utente non è autenticato
   - Controlla il messaggio di errore appropriato

3. `test_read_users_me_invalid_token`
   - Verifica che l'endpoint `/users/me` restituisca errore 401 con un token non valido
   - Controlla il messaggio di errore appropriato

### Creazione Utente
4. `test_create_user_valid_data`
   - Verifica la creazione di un utente con dati validi
   - Controlla che tutti i campi obbligatori siano presenti
   - Verifica i campi di default (is_active, is_superuser)
   - Controlla i campi di audit (created_at, updated_at)
   - Verifica che i campi sensibili non siano esposti

5. `test_create_user_missing_required_fields`
   - Verifica il comportamento quando mancano campi obbligatori:
     - Email mancante
     - Username mancante
     - Password mancante
   - Controlla che vengano restituiti gli appropriati errori 422

6. `test_create_user_invalid_email`
   - Verifica il rifiuto di email non valide in 13 scenari diversi:
     - Email senza @
     - Email senza dominio
     - Email senza username
     - Email con spazi
     - Email senza punto nel dominio
     - Email senza dominio prima del punto
     - Email senza TLD
     - Email con doppio punto nel dominio
     - Email con trattino all'inizio del dominio
     - Email con trattino alla fine del dominio
     - Email con punto alla fine
     - Email con punto all'inizio
     - Email con doppio punto nell'username

7. `test_create_user_invalid_password`
   - Verifica il rifiuto di password non valide in 20 scenari diversi:
     - Password troppo corte
     - Solo numeri
     - Solo lettere minuscole
     - Solo lettere maiuscole
     - Solo caratteri speciali
     - Password comuni (password123, qwerty123, admin123, letmein123, welcome123)
     - Password con spazi
     - Password con caratteri di controllo (tab, newline, carriage return)
     - Password con caratteri non validi (null byte, caratteri di controllo, escape, substitute)

8. `test_create_user_duplicate_username`
   - Verifica il rifiuto della creazione di un utente con username già esistente
   - Controlla il messaggio di errore appropriato

9. `test_create_user_duplicate_email`
   - Verifica il rifiuto della creazione di un utente con email già esistente
   - Controlla il messaggio di errore appropriato

### Operazioni CRUD Utenti
10. `test_read_users`
    - Verifica la lettura della lista completa degli utenti
    - Controlla che i dati siano formattati correttamente

11. `test_read_user`
    - Verifica la lettura di un singolo utente
    - Controlla che tutti i campi siano presenti e corretti

12. `test_read_user_not_found`
    - Verifica il comportamento quando si tenta di leggere un utente non esistente
    - Controlla il messaggio di errore appropriato

13. `test_update_user`
    - Verifica l'aggiornamento dei dati di un utente
    - Controlla che le modifiche siano state applicate correttamente

14. `test_update_user_not_found`
    - Verifica il comportamento quando si tenta di aggiornare un utente non esistente
    - Controlla il messaggio di errore appropriato

15. `test_delete_user`
    - Verifica l'eliminazione di un utente
    - Controlla che l'utente sia stato effettivamente rimosso

16. `test_delete_user_not_found`
    - Verifica il comportamento quando si tenta di eliminare un utente non esistente
    - Controlla il messaggio di errore appropriato

### Test di Base
17. `test_pytest_works`
    - Test di base per verificare il corretto funzionamento dell'ambiente di test

## Note
- Tutti i test sono stati eseguiti con successo
- I test utilizzano un database di test separato
- Le fixture gestiscono automaticamente la creazione e pulizia del database di test
- I test includono controlli di timeout per evitare blocchi
- I test verificano sia i casi positivi che negativi
- I test includono validazioni di sicurezza e protezione dei dati sensibili 