# 🎤 Interfacce Vocali - Eterna Home

## Panoramica

Il sistema di interfacce vocali di Eterna Home permette agli utenti di interagire con la casa intelligente tramite comandi vocali. Il sistema è progettato per ricevere input vocali (testo o audio), elaborarli in modo asincrono e fornire risposte intelligenti.

## 🏗️ Architettura

### Componenti Principali

1. **AudioLog Model**: Modello per la gestione dei comandi vocali
2. **Voice API**: Endpoint REST per ricezione comandi
3. **Audio Storage**: Storage MinIO per file audio
4. **Processing Queue**: Coda per elaborazione asincrona (futuro)

### Flusso di Elaborazione

```
Utente → Voice API → AudioLog → Queue → NLP Worker → Response
```

## 📊 Modello AudioLog

### Struttura

```python
class AudioLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    node_id: Optional[int] = Field(default=None, foreign_key="nodes.id")
    house_id: Optional[int] = Field(default=None, foreign_key="houses.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audio_url: Optional[str] = None
    transcribed_text: Optional[str] = None
    response_text: Optional[str] = None
    processing_status: str = Field(default="received")
```

### Stati di Elaborazione

- **received**: Comando ricevuto
- **transcribing**: In trascrizione audio
- **analyzing**: In analisi NLP
- **completed**: Elaborazione completata
- **failed**: Elaborazione fallita

### Relazioni

- `User` → `AudioLog` (1:N)
- `Node` → `AudioLog` (1:N)
- `House` → `AudioLog` (1:N)

## 🔌 API Endpoints

### POST /api/v1/voice/commands

Riceve comandi vocali in formato testuale.

**Request:**
```json
{
  "transcribed_text": "Accendi la luce in cucina",
  "node_id": 12,
  "house_id": 3
}
```

**Response:**
```json
{
  "request_id": "audiolog-1234",
  "status": "accepted",
  "message": "Comando vocale ricevuto e inviato in elaborazione"
}
```

### POST /api/v1/voice/commands/audio

Riceve file audio per comandi vocali.

**Request:**
- `audio_file`: File audio (WAV, MP3, M4A, AAC, OGG)
- `node_id`: ID nodo (opzionale)
- `house_id`: ID casa (opzionale)

**Validazioni:**
- Dimensione max: 50MB
- Formati supportati: WAV, MP3, M4A, AAC, OGG

### GET /api/v1/voice/logs

Lista AudioLog con filtri e paginazione.

**Query Parameters:**
- `house_id`: Filtra per casa
- `node_id`: Filtra per nodo
- `status`: Filtra per stato
- `page`: Numero pagina
- `size`: Elementi per pagina

### GET /api/v1/voice/logs/{id}

Ottiene un AudioLog specifico.

### PUT /api/v1/voice/logs/{id}

Aggiorna un AudioLog.

**Request:**
```json
{
  "transcribed_text": "Testo aggiornato",
  "response_text": "Risposta aggiornata",
  "processing_status": "completed"
}
```

### DELETE /api/v1/voice/logs/{id}

Elimina un AudioLog.

### GET /api/v1/voice/statuses

Ottiene gli stati di elaborazione disponibili.

### GET /api/v1/voice/stats

Statistiche comandi vocali dell'utente.

## 🔒 Sicurezza

### Autenticazione
- Tutti gli endpoint richiedono autenticazione JWT
- Token di accesso obbligatorio

### Autorizzazione
- Isolamento dati per utente (ownership security)
- Controllo accessi basato su proprietà delle risorse
- Verifica appartenenza casa/nodo all'utente

### Validazioni
- Lunghezza testo: max 1000 caratteri
- Stati di elaborazione: valori predefiniti
- Formati file audio: estensioni consentite
- Dimensione file: limite configurabile

## 💾 Storage

### MinIO Integration
- Bucket: `voice-commands`
- Struttura: `{user_id}/{file_id}.{extension}`
- Gestione errori e rollback
- Controllo accessi per file

### File Management
- Upload asincrono
- Validazione contenuto
- Cleanup automatico (futuro)

## 🧪 Testing

### Test Modello
```bash
python test_audio_log_model.py
```

**Cosa testa:**
- Creazione AudioLog
- Relazioni con User/Node/House
- Validazioni campi
- Aggiornamento record
- Query e filtri

### Test API
```bash
python test_voice_api.py
```

**Cosa testa:**
- Endpoint comandi vocali
- Autenticazione e autorizzazione
- Upload file audio
- CRUD operazioni
- Filtri e paginazione
- Statistiche

## 🚀 Setup

### 1. Creazione Tabella
```bash
python create_audio_log_table.py
```

### 2. Verifica Database
```sql
-- Controlla tabella
SELECT table_name FROM information_schema.tables WHERE table_name = 'audio_logs';

-- Controlla struttura
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'audio_logs';
```

### 3. Test Funzionalità
```bash
# Test modello
python test_audio_log_model.py

# Test API (richiede server attivo)
python test_voice_api.py
```

## 🔮 Roadmap

### Fase 1: Worker NLP (Futuro)
- [ ] Integrazione RabbitMQ/Celery
- [ ] Worker per trascrizione audio
- [ ] Worker per analisi NLP
- [ ] Sistema di risposte intelligenti

### Fase 2: Comandi Avanzati
- [ ] Comandi complessi multi-step
- [ ] Contesto conversazione
- [ ] Apprendimento preferenze utente
- [ ] Integrazione con altri sistemi

### Fase 3: Interfaccia Utente
- [ ] Dashboard comandi vocali
- [ ] Visualizzazione cronologia
- [ ] Configurazione comandi personalizzati
- [ ] Statistiche avanzate

## 📝 Esempi di Utilizzo

### Comando Testuale
```bash
curl -X POST "http://localhost:8000/api/v1/voice/commands" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transcribed_text": "Imposta la temperatura a 22 gradi",
    "house_id": 1
  }'
```

### Upload Audio
```bash
curl -X POST "http://localhost:8000/api/v1/voice/commands/audio" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_file=@comando.wav" \
  -F "house_id=1"
```

### Lista Comandi
```bash
curl -X GET "http://localhost:8000/api/v1/voice/logs?status=completed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🛠️ Troubleshooting

### Problemi Comuni

1. **Errore 401 Unauthorized**
   - Verifica token JWT valido
   - Controlla scadenza token

2. **Errore 400 Bad Request**
   - Verifica formato JSON
   - Controlla validazioni campi

3. **Errore upload file**
   - Verifica formato file supportato
   - Controlla dimensione file
   - Verifica connessione MinIO

4. **Tabella non trovata**
   - Esegui `create_audio_log_table.py`
   - Verifica connessione database

### Log e Debug
```python
# Abilita logging dettagliato
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Riferimenti

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [MinIO Documentation](https://docs.min.io/)
- [Pydantic Validation](https://pydantic-docs.helpmanual.io/)

---

**Versione**: 1.0.0  
**Data**: 23/06/2025  
**Autore**: Eterna Home Team 