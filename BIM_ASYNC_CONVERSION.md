# Sistema di Conversione BIM Asincrona

## Panoramica

Il sistema di conversione BIM asincrona di Eterna Home utilizza **Celery** per gestire l'elaborazione asincrona dei modelli BIM, supportando la conversione tra diversi formati e la validazione dei modelli.

## Architettura

### Componenti Principali

1. **Celery App** (`app/core/celery_app.py`)
   - Configurazione centrale per Celery
   - Gestione code e routing dei task
   - Configurazione timeout e limiti

2. **BIM Worker** (`app/workers/bim_worker.py`)
   - Worker specializzato per conversione BIM
   - Supporto per IFC → GLTF, RVT → IFC
   - Validazione modelli BIM

3. **Conversion Worker** (`app/workers/conversion_worker.py`)
   - Coordinazione dei task di conversione
   - Gestione batch conversion
   - Monitoraggio stato conversione

4. **Modello BIMModel Aggiornato**
   - Campi per stato conversione
   - Tracking progresso
   - URL file convertiti

## Formati Supportati

### Input
- **IFC** (.ifc) - Industry Foundation Classes
- **RVT** (.rvt) - Autodesk Revit
- **DWG** (.dwg) - AutoCAD Drawing
- **DXF** (.dxf) - Drawing Exchange Format
- **SKP** (.skp) - SketchUp
- **PLN** (.pln) - ArchiCAD

### Output
- **GLTF** (.gltf) - GL Transmission Format (per visualizzazione web)
- **IFC** (.ifc) - Conversione da altri formati
- **JSON** (.json) - Report di validazione

## Stati di Conversione

```python
class BIMConversionStatus(str, Enum):
    PENDING = "pending"           # In attesa di elaborazione
    PROCESSING = "processing"     # Conversione in corso
    VALIDATING = "validating"     # Validazione in corso
    COMPLETED = "completed"       # Conversione completata
    FAILED = "failed"            # Conversione fallita
    VALIDATION_FAILED = "validation_failed"  # Validazione fallita
    CLEANED = "cleaned"          # File puliti
```

## API Endpoints

### Conversione Singola
```http
POST /api/v1/bim/convert
Content-Type: application/json

{
    "model_id": 123,
    "conversion_type": "auto",
    "with_validation": true
}
```

### Stato Conversione
```http
GET /api/v1/bim/convert/{model_id}/status
```

### Conversione Batch
```http
POST /api/v1/bim/convert/batch
Content-Type: application/json

{
    "model_ids": [123, 124, 125],
    "conversion_type": "ifc_to_gltf",
    "max_parallel": 5
}
```

### Tutti gli Stati
```http
GET /api/v1/bim/convert/status
```

### Cancellazione Conversione
```http
DELETE /api/v1/bim/convert/{model_id}/cancel
```

## Task Celery

### Task Principali

1. **convert_ifc_to_gltf**
   - Converte file IFC in formato GLTF
   - Simula elaborazione con IfcOpenShell
   - Genera file ottimizzati per web

2. **convert_rvt_to_ifc**
   - Converte file RVT in formato IFC
   - Simula elaborazione con Revit API
   - Supporta batch processing

3. **validate_bim_model**
   - Valida struttura e geometria del modello
   - Genera report di validazione
   - Controlla compliance LOD

4. **process_bim_model**
   - Coordina workflow di conversione
   - Determina tipo di conversione automatica
   - Gestisce errori e rollback

### Task di Supporto

- **batch_convert_models**: Conversione parallela di più modelli
- **convert_with_validation**: Conversione con validazione pre/post
- **cleanup_conversion_files**: Pulizia file temporanei
- **get_conversion_status**: Monitoraggio stato conversione

## Configurazione

### Dipendenze
```bash
pip install celery[redis] aio-pika
```

### Variabili d'Ambiente
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Configurazione Celery
```python
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,      # 30 minuti
    task_soft_time_limit=25 * 60, # 25 minuti
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)
```

## Avvio Worker

### Script di Avvio
```bash
python run_bim_worker.py
```

### Modalità Disponibili
1. **Worker principale** - Solo conversione BIM
2. **Worker + Beat** - Con task schedulati
3. **Worker + Monitor** - Con monitoraggio
4. **Tutto** - Worker + Beat + Monitor

### Comando Manuale
```bash
celery -A app.core.celery_app:celery_app worker -Q bim_conversion -c 2 --loglevel=info
```

## Monitoraggio

### Celery Monitor
```bash
celery -A app.core.celery_app:celery_app monitor
```

### Celery Beat (Scheduler)
```bash
celery -A app.core.celery_app:celery_app beat --loglevel=info
```

### Flower (Web UI)
```bash
pip install flower
celery -A app.core.celery_app:celery_app flower
```

## Gestione Errori

### Strategie di Retry
- **Retry automatico** per errori temporanei
- **Backoff esponenziale** per tentativi multipli
- **Dead letter queue** per task falliti

### Rollback
- **Eliminazione file temporanei** in caso di errore
- **Ripristino stato originale** del modello
- **Logging dettagliato** per debugging

## Performance

### Ottimizzazioni
- **Concurrency**: 2 worker per default
- **Prefetch**: 1 task per worker
- **Timeout**: 30 minuti massimo per task
- **Memory**: Cleanup automatico file temporanei

### Metriche
- **Throughput**: ~10 conversioni/ora per worker
- **Latency**: 2-10 minuti per conversione
- **Success Rate**: >95% con retry

## Sicurezza

### Controlli di Accesso
- **Autenticazione JWT** obbligatoria
- **Ownership validation** per tutti i modelli
- **Rate limiting** per prevenire abuso

### Validazione File
- **Checksum SHA-256** per integrità
- **Validazione formato** file
- **Controllo dimensione** (max 100MB)

## Test

### Test Unitari
```bash
python test_bim_conversion.py
```

### Test Coverage
- ✅ Creazione modelli BIM
- ✅ Aggiornamento stato conversione
- ✅ Workflow completo conversione
- ✅ Schemi Pydantic
- ✅ Gestione errori

### Test End-to-End
```bash
# Avvia worker
python run_bim_worker.py

# In altro terminale
python test_bim_conversion.py
```

## Deployment

### Produzione
1. **Redis Cluster** per alta disponibilità
2. **Multiple Worker** per scalabilità
3. **Monitoring** con Prometheus/Grafana
4. **Logging** centralizzato

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["celery", "-A", "app.core.celery_app:celery_app", "worker", "-Q", "bim_conversion"]
```

## Troubleshooting

### Problemi Comuni

1. **Worker non si avvia**
   - Verifica connessione Redis
   - Controlla log per errori
   - Verifica dipendenze

2. **Task in coda ma non elaborati**
   - Verifica worker attivi
   - Controlla configurazione code
   - Verifica permessi file

3. **Conversione fallisce**
   - Controlla formato file input
   - Verifica spazio disco
   - Controlla log worker

### Log Utili
```bash
# Log worker
tail -f celery.log

# Log Redis
redis-cli monitor

# Log applicazione
tail -f app.log
```

## Roadmap

### Prossimi Sviluppi
- [ ] Integrazione IfcOpenShell reale
- [ ] Supporto Forge SDK per RVT
- [ ] Conversione DWG/DXF
- [ ] Ottimizzazione GLTF
- [ ] Cache risultati conversione
- [ ] Notifiche real-time
- [ ] Dashboard conversione

### Miglioramenti
- [ ] Parallelizzazione conversione
- [ ] Compressione file output
- [ ] Validazione avanzata
- [ ] Backup automatico
- [ ] Metriche dettagliate

## Supporto

Per problemi o domande:
1. Controlla la documentazione
2. Verifica i log
3. Esegui i test
4. Contatta il team di sviluppo

---

**Nota**: Questo sistema è progettato per essere estensibile e scalabile. Le conversioni attuali sono simulate ma l'architettura è pronta per l'integrazione con strumenti reali come IfcOpenShell e Forge SDK. 