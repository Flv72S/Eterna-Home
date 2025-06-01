# Dettagli di Implementazione

## Sistema di Autenticazione JWT

### Implementazione
- ✅ Endpoint `/token` per l'autenticazione
- ✅ Generazione e validazione token JWT
- ✅ Rate limiting (5 richieste/minuto)
- ✅ Gestione utenti disabilitati
- ✅ Password hashing con bcrypt

### Test di Sicurezza
- ✅ Validazione struttura token JWT
- ✅ Verifica scadenza token
- ✅ Test login utente disabilitato
- ✅ Test rate limiting

### Struttura Token JWT
```json
{
  "sub": "user@email.com",
  "exp": 1234567890,
  "type": "bearer"
}
```

### Rate Limiting
- Limite: 5 richieste al minuto
- Risposta 429 con messaggio di errore
- Headers: X-RateLimit-Limit, X-RateLimit-Remaining

### Sicurezza Password
- Hashing con bcrypt
- Salt automatico
- Verifica sicura delle password

### Gestione Errori
- 401: Credenziali non valide
- 403: Utente disabilitato
- 422: Token non valido
- 429: Rate limit exceeded

## Struttura File
```
app/
  ├── api/
  │   ├── auth.py      # Endpoint autenticazione
  │   └── user.py      # Endpoint utenti
  ├── utils/
  │   ├── password.py  # Funzioni hashing password
  │   └── security.py  # Funzioni JWT e autenticazione
  └── models/
      └── user.py      # Modello utente
```

## Dipendenze
- python-jose[cryptography]
- passlib[bcrypt]
- slowapi
- fastapi
- sqlmodel 