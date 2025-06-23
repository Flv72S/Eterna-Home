# Sistema Asincrono di Elaborazione Comandi Vocali

## Panoramica

Il sistema asincrono di elaborazione comandi vocali permette di disaccoppiare l'API FastAPI dall'elaborazione NLP, migliorando le performance e la scalabilità del sistema.

## Architettura

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│  FastAPI    │───▶│  RabbitMQ   │───▶│   Worker    │
│             │    │   API       │    │   Queue     │    │  Asincrono  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                                      │
                          ▼                                      ▼
                   ┌─────────────┐                      ┌─────────────┐
                   │  Database   │                      │   NLP/LLM   │
                   │  (AudioLog) │                      │   Service   │
                   └─────────────┘                      └─────────────┘
```

## Componenti

### 1. RabbitMQ Manager (`app/core/queue.py`)

Gestisce la connessione e le operazioni con RabbitMQ:

- **Connessione**: Configurazione automatica di exchange e coda
- **Pubblicazione**: Invio messaggi alla coda `voice_commands`
- **Consumo**: Lettura messaggi dalla coda per elaborazione

### 2. Voice Worker (`app/workers/voice_worker.py`)

Worker asincrono che elabora i comandi vocali:

- **Ascolto coda**: Consuma messaggi da RabbitMQ
- **Elaborazione audio**: Trascrizione file audio (simulata)
- **Elaborazione NLP**: Analisi comandi testuali (simulata)
- **Aggiornamento stato**: Modifica `processing_status` in tempo reale

### 3. API Integration (`app/routers/voice.py`)

Endpoint aggiornati per integrazione con la coda:

- **Pubblicazione messaggi**: Invio automatico alla coda
- **Gestione errori**: Fallback se RabbitMQ non disponibile
- **Logging**: Tracciamento completo delle operazioni

## Stati di Elaborazione

Il sistema gestisce 5 stati di elaborazione:

1. **`received`**: Comando ricevuto dall'API
2. **`transcribing`**: Trascrizione audio in corso
3. **`analyzing`**: Analisi NLP in corso
4. **`completed`**: Elaborazione completata con successo
5. **`failed`**: Elaborazione fallita

## Configurazione

### Dipendenze

Aggiunte al `requirements.txt`:

```txt
# RabbitMQ dependencies for async voice processing
pika==1.3.2
aio-pika==9.3.1
```

### Variabili d'Ambiente

```bash
# RabbitMQ (opzionale, default per sviluppo)
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

## Utilizzo

### 1. Avvio del Worker

```bash
# Avvio worker asincrono
python run_voice_worker.py
```

### 2. Invio Comandi

```bash
# Comando testuale
curl -X POST "http://localhost:8000/api/v1/voice/commands" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "transcribed_text": "Accendi le luci del soggiorno",
    "node_id": 1,
    "house_id": 1
  }'

# Comando audio
curl -X POST "http://localhost:8000/api/v1/voice/commands/audio" \
  -H "Authorization: Bearer <token>" \
  -F "audio_file=@audio.wav" \
  -F "node_id=1" \
  -F "house_id=1"
```

### 3. Monitoraggio Stato

```bash
# Controlla stato elaborazione
curl -X GET "http://localhost:8000/api/v1/voice/logs/1" \
  -H "Authorization: Bearer <token>"
```

## Test del Sistema

### Test Completo

```bash
# Esegue test completo del sistema asincrono
python test_voice_worker.py
```

Il test verifica:
- Invio comandi testuali e audio
- Pubblicazione messaggi nella coda
- Elaborazione asincrona
- Aggiornamento stati in tempo reale
- Risposte generate dal sistema

### Test Manuale

1. **Avvia il server FastAPI**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Avvia il worker** (in un terminale separato):
   ```bash
   python run_voice_worker.py
   ```

3. **Invia comandi** tramite API o script di test

4. **Monitora i log** per vedere l'elaborazione in tempo reale

## Logging e Monitoraggio

### Log del Worker

Il worker genera log dettagliati:

```
2025-06-23 12:30:00 - Voice Worker - INFO - Avvio Voice Worker...
2025-06-23 12:30:01 - Voice Worker - INFO - Connessione RabbitMQ stabilita
2025-06-23 12:30:02 - Voice Worker - INFO - Messaggio ricevuto: {...}
2025-06-23 12:30:03 - Voice Worker - INFO - Elaborazione audio per AudioLog 1
2025-06-23 12:30:05 - Voice Worker - INFO - Simulazione trascrizione audio...
2025-06-23 12:30:07 - Voice Worker - INFO - Elaborazione testo per AudioLog 1
2025-06-23 12:30:08 - Voice Worker - INFO - Simulazione elaborazione NLP per: 'Accendi le luci del soggiorno'
2025-06-23 12:30:09 - Voice Worker - INFO - Elaborazione completata per AudioLog 1
```

### Monitoraggio Stati

Gli stati vengono aggiornati in tempo reale nel database:

```sql
SELECT id, processing_status, transcribed_text, response_text, timestamp 
FROM audio_logs 
ORDER BY timestamp DESC;
```

## Estensioni Future

### 1. Servizi di Trascrizione

Integrazione con servizi reali:

- **Google Speech-to-Text**
- **Azure Speech Services**
- **Amazon Transcribe**
- **Whisper (OpenAI)**

### 2. Servizi NLP/LLM

Integrazione con modelli avanzati:

- **OpenAI GPT**
- **Azure Cognitive Services**
- **Hugging Face Transformers**
- **Modelli custom**

### 3. Orchestrazione

Sistema di orchestrazione avanzato:

- **Celery** per task distribuiti
- **Kubernetes** per deployment
- **Prometheus/Grafana** per monitoring
- **Redis** per cache e sessioni

### 4. Notifiche Real-time

Sistema di notifiche:

- **WebSocket** per aggiornamenti in tempo reale
- **Push notifications** per dispositivi mobili
- **Email/SMS** per notifiche importanti

## Troubleshooting

### Problemi Comuni

1. **RabbitMQ non raggiungibile**:
   - Verifica che RabbitMQ sia in esecuzione
   - Controlla le credenziali e l'URL
   - Il sistema continua a funzionare senza RabbitMQ

2. **Worker non elabora messaggi**:
   - Verifica i log del worker
   - Controlla la connessione al database
   - Riavvia il worker se necessario

3. **Stati non aggiornati**:
   - Verifica che il worker sia in esecuzione
   - Controlla i log per errori di database
   - Verifica i permessi di scrittura

### Debug

```bash
# Log dettagliati del worker
python run_voice_worker.py --debug

# Test connessione RabbitMQ
python -c "import aio_pika; print('RabbitMQ OK')"

# Verifica tabella AudioLog
python -c "from app.models.audio_log import AudioLog; print('AudioLog OK')"
```

## Performance

### Metriche Attese

- **Latenza API**: < 100ms (senza elaborazione)
- **Elaborazione audio**: 2-5 secondi (simulata)
- **Elaborazione NLP**: 1-3 secondi (simulata)
- **Throughput**: 100+ comandi/minuto per worker

### Ottimizzazioni

- **Pool di worker**: Più istanze per scalabilità
- **Caching**: Redis per risultati frequenti
- **Batch processing**: Elaborazione in lotti
- **Load balancing**: Distribuzione carico

## Sicurezza

### Considerazioni

- **Autenticazione**: Token JWT per tutte le operazioni
- **Autorizzazione**: Controllo accessi per AudioLog
- **Isolamento**: Multi-tenancy garantito
- **Audit**: Log completi per tracciabilità

### Best Practices

- **Validazione input**: Controllo rigoroso dei dati
- **Sanitizzazione**: Pulizia testo prima elaborazione
- **Rate limiting**: Protezione da abuso
- **Encryption**: Crittografia dati sensibili 