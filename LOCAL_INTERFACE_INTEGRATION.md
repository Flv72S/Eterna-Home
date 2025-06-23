# Integrazione Interfacce Locali e Servizi Trascrizione Audio

## Panoramica

Questo documento descrive l'integrazione delle interfacce locali con servizi di trascrizione audio reali (Google Speech-to-Text e Azure Speech Services) nel sistema Eterna Home.

## Architettura

### Componenti Principali

1. **SpeechToTextService** - Servizio per trascrizione audio
2. **LocalInterfaceService** - Servizio per interfacce locali
3. **VoiceWorker** - Worker asincrono per elaborazione comandi vocali
4. **LocalInterfaceRouter** - API endpoints per interfacce locali

### Flusso di Elaborazione

```
Comando Vocale → AudioLog → Speech-to-Text → LocalInterface → Azioni Sistema
```

## Servizi di Trascrizione Audio

### Google Speech-to-Text

**Configurazione:**
```python
# settings.py
GOOGLE_SPEECH_ENABLED = True
GOOGLE_APPLICATION_CREDENTIALS = "path/to/credentials.json"
GOOGLE_SPEECH_LANGUAGE = "it-IT"
GOOGLE_SPEECH_MODEL = "latest_long"
```

**Installazione:**
```bash
pip install google-cloud-speech
```

**Setup:**
1. Crea progetto Google Cloud
2. Abilita Speech-to-Text API
3. Crea service account e scarica credentials
4. Imposta variabile d'ambiente `GOOGLE_APPLICATION_CREDENTIALS`

### Azure Speech Services

**Configurazione:**
```python
# settings.py
AZURE_SPEECH_ENABLED = True
AZURE_SPEECH_KEY = "your-azure-speech-key"
AZURE_SPEECH_REGION = "westeurope"
AZURE_SPEECH_LANGUAGE = "it-IT"
```

**Installazione:**
```bash
pip install azure-cognitiveservices-speech
```

**Setup:**
1. Crea risorsa Azure Speech Services
2. Ottieni chiave API e regione
3. Configura nel file settings

## Interfacce Locali

### Integrazioni Supportate

1. **IoT Integration**
   - Controllo luci (accendi/spegni)
   - Lettura sensori (temperatura, umidità)
   - Stato nodi

2. **BIM Integration**
   - Conversione modelli BIM
   - Stato conversioni
   - Gestione file

3. **Document Integration**
   - Lista documenti
   - Ricerca documenti
   - Gestione file

4. **Maintenance Integration**
   - Stato manutenzioni
   - Creazione manutenzioni
   - Controllo scadenze

5. **Booking Integration**
   - Prenotazioni stanze
   - Lista prenotazioni
   - Gestione calendario

### Comandi Vocali Supportati

#### Comandi IoT
- "Accendi le luci del soggiorno"
- "Spegni tutte le luci"
- "Qual è la temperatura?"
- "Stato umidità"

#### Comandi BIM
- "Converti modello BIM"
- "Stato conversioni BIM"
- "Carica nuovo modello"

#### Comandi Informativi
- "Stato sistema"
- "Aiuto"
- "Comandi disponibili"

#### Comandi Documenti
- "Lista documenti"
- "Cerca documento"
- "Carica file"

## API Endpoints

### Interfacce Locali

```http
GET /api/v1/local-interface/status
POST /api/v1/local-interface/voice-command/process
GET /api/v1/local-interface/voice-command/status/{audio_log_id}
GET /api/v1/local-interface/speech-to-text/languages
POST /api/v1/local-interface/speech-to-text/transcribe
GET /api/v1/local-interface/worker/status
POST /api/v1/local-interface/test/voice-command
GET /api/v1/local-interface/integrations/iot/status
GET /api/v1/local-interface/integrations/bim/status
```

### Esempi di Utilizzo

#### Processare Comando Vocale
```bash
curl -X POST "http://localhost:8000/api/v1/local-interface/voice-command/process" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"audio_log_id": 123}'
```

#### Trascrivere Audio
```bash
curl -X POST "http://localhost:8000/api/v1/local-interface/speech-to-text/transcribe" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "minio/voice-commands/audio.wav", "language_code": "it-IT"}'
```

#### Testare Comando
```bash
curl -X POST "http://localhost:8000/api/v1/local-interface/test/voice-command" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command_text": "Accendi le luci del soggiorno"}'
```

## Configurazione

### Variabili d'Ambiente

```bash
# Speech-to-Text
USE_REAL_SPEECH_TO_TEXT=true
GOOGLE_SPEECH_ENABLED=true
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
AZURE_SPEECH_ENABLED=false
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=westeurope

# Local Interfaces
ENABLE_LOCAL_INTERFACES=true
ENABLE_VOICE_COMMANDS=true
ENABLE_IOT_INTEGRATION=true
ENABLE_BIM_INTEGRATION=true
ENABLE_DOCUMENT_INTEGRATION=true

# Processing
VOICE_PROCESSING_TIMEOUT=300
VOICE_MAX_FILE_SIZE=52428800
```

### File di Configurazione

```python
# app/core/config.py
class Settings(BaseModel):
    # Speech-to-Text Settings
    USE_REAL_SPEECH_TO_TEXT: bool = False
    GOOGLE_SPEECH_ENABLED: bool = False
    AZURE_SPEECH_ENABLED: bool = False
    
    # Local Interface Settings
    ENABLE_LOCAL_INTERFACES: bool = True
    ENABLE_VOICE_COMMANDS: bool = True
    
    # Integration Settings
    ENABLE_IOT_INTEGRATION: bool = True
    ENABLE_BIM_INTEGRATION: bool = True
    ENABLE_DOCUMENT_INTEGRATION: bool = True
```

## Testing

### Test Manuali

```bash
# Test servizi di trascrizione
python test_local_interface.py

# Test worker vocale
python run_voice_worker.py

# Test API endpoints
curl -X GET "http://localhost:8000/api/v1/local-interface/status"
```

### Test Automatici

```bash
# Esegui tutti i test
pytest tests/ -v

# Test specifici interfacce locali
pytest tests/test_local_interface.py -v
```

## Deployment

### Produzione

1. **Configura servizi di trascrizione:**
   ```bash
   # Google Speech-to-Text
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/prod-credentials.json"
   export GOOGLE_SPEECH_ENABLED=true
   
   # Azure Speech Services
   export AZURE_SPEECH_KEY="prod-key"
   export AZURE_SPEECH_ENABLED=true
   ```

2. **Avvia worker vocale:**
   ```bash
   python run_voice_worker.py
   ```

3. **Verifica stato:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/local-interface/status"
   ```

### Sviluppo

1. **Modalità simulazione:**
   ```bash
   export USE_REAL_SPEECH_TO_TEXT=false
   export GOOGLE_SPEECH_ENABLED=false
   export AZURE_SPEECH_ENABLED=false
   ```

2. **Test locale:**
   ```bash
   python test_local_interface.py
   ```

## Monitoraggio

### Logs

```python
# Logs di trascrizione
logger.info(f"Trascrizione completata: {transcribed_text}")

# Logs di elaborazione
logger.info(f"Comando elaborato: {len(actions)} azioni")

# Logs di errore
logger.error(f"Errore trascrizione: {error}")
```

### Metriche

- Tempo di trascrizione audio
- Accuratezza trascrizione
- Numero comandi elaborati
- Tasso di successo azioni
- Tempo di risposta sistema

## Troubleshooting

### Problemi Comuni

1. **Errore Google Speech:**
   - Verifica credentials
   - Controlla quota API
   - Verifica formato audio

2. **Errore Azure Speech:**
   - Verifica chiave API
   - Controlla regione
   - Verifica formato audio

3. **Comandi non riconosciuti:**
   - Controlla lingua impostata
   - Verifica qualità audio
   - Controlla log di elaborazione

4. **Azioni non eseguite:**
   - Verifica integrazioni abilitate
   - Controlla permessi utente
   - Verifica stato worker

### Debug

```python
# Abilita debug logs
logging.getLogger("app.services.speech_to_text").setLevel(logging.DEBUG)
logging.getLogger("app.services.local_interface").setLevel(logging.DEBUG)

# Test singolo servizio
speech_service = SpeechToTextService()
status = speech_service.get_service_status()
print(status)
```

## Sicurezza

### Considerazioni

1. **Autenticazione:** Tutti gli endpoint richiedono autenticazione
2. **Autorizzazione:** Verifica proprietà AudioLog
3. **Rate Limiting:** Limiti su trascrizione audio
4. **Validazione:** Controllo formato e dimensione file
5. **Logging:** Tracciamento accessi e operazioni

### Best Practices

1. Usa HTTPS in produzione
2. Limita accesso a servizi esterni
3. Monitora uso API
4. Implementa retry logic
5. Valida input utente

## Roadmap

### Funzionalità Future

1. **Supporto più lingue**
2. **Comandi personalizzati**
3. **Integrazione con assistenti vocali**
4. **Analisi sentiment**
5. **Sintesi vocale risposta**

### Miglioramenti

1. **Caching trascrizioni**
2. **Batch processing**
3. **Offline processing**
4. **Custom models**
5. **Real-time streaming** 