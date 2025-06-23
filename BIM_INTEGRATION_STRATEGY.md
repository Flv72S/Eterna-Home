# Strategia di Integrazione Servizi BIM Reali

## Panoramica

Questo documento descrive la strategia per integrare servizi di conversione BIM reali (IfcOpenShell, Forge SDK) mantenendo la flessibilità per sviluppo, testing e produzione.

## Architettura Attuale (Simulazione)

### Vantaggi della Simulazione
- ✅ **Sviluppo rapido**: Nessuna dipendenza esterna
- ✅ **Testing facile**: Controllo completo del comportamento
- ✅ **Stabilità**: Nessun problema di connessione o rate limiting
- ✅ **Costi zero**: Nessun costo per servizi esterni

### Configurazione Attuale
```python
# app/core/config.py
USE_REAL_BIM_CONVERSION: bool = False
USE_IFCOPENSHELL: bool = False
USE_FORGE_SDK: bool = False
```

## Strategia di Integrazione Graduale

### Fase 1: Sviluppo (Attuale) ✅
```python
def convert_ifc_to_gltf(self, model_id: int):
    # Simulazione per sviluppo
    time.sleep(5)
    return {"success": True, "simulated": True}
```

### Fase 2: Testing (Opzionale)
```python
def convert_ifc_to_gltf(self, model_id: int):
    if settings.USE_REAL_BIM_CONVERSION:
        return self._real_conversion()
    else:
        return self._simulated_conversion()
```

### Fase 3: Produzione (Finale)
```python
def convert_ifc_to_gltf(self, model_id: int):
    return self._real_conversion()
```

## Integrazione IfcOpenShell

### Prerequisiti
```bash
# Ubuntu/Debian
sudo apt-get install build-essential cmake libboost-all-dev

# Windows
# Install Visual Studio Build Tools

# macOS
xcode-select --install
```

### Installazione
```bash
# Opzione 1: pip (se disponibile)
pip install ifcopenshell

# Opzione 2: Build da sorgente
git clone https://github.com/IfcOpenShell/IfcOpenShell.git
cd IfcOpenShell
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

### Implementazione Reale
```python
import ifcopenshell
import ifcopenshell.geom
import json

def _real_ifc_conversion(self, local_path: str) -> str:
    """Conversione reale IFC → GLTF usando IfcOpenShell."""
    try:
        # Carica file IFC
        ifc_file = ifcopenshell.open(local_path)
        
        # Estrai geometrie
        geometries = []
        for entity in ifc_file.by_type("IfcProduct"):
            if entity.Representation:
                shape = ifcopenshell.geom.create_shape(entity.Representation)
                geometries.append({
                    "id": entity.id(),
                    "type": entity.is_a(),
                    "geometry": shape.brep_data
                })
        
        # Genera GLTF
        gltf_data = {
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": []}],
            "nodes": [],
            "meshes": geometries
        }
        
        # Salva GLTF
        gltf_path = local_path.replace(".ifc", ".gltf")
        with open(gltf_path, "w") as f:
            json.dump(gltf_data, f, indent=2)
        
        return gltf_path
        
    except Exception as e:
        logger.error(f"Errore conversione IFC reale: {e}")
        raise
```

## Integrazione Forge SDK

### Prerequisiti
1. **Account Autodesk Developer**
   - Registrazione su https://forge.autodesk.com/
   - Creazione app con Client ID e Secret

2. **Configurazione**
```env
FORGE_CLIENT_ID=your_app_id_here
FORGE_CLIENT_SECRET=your_secret_here
FORGE_BUCKET_NAME=eterna-home-bim
```

### Installazione
```bash
pip install forge-sdk
# oppure
pip install autodesk-forge-sdk
```

### Implementazione Reale
```python
from forge_sdk import ForgeClient
import asyncio

def _real_rvt_conversion(self, local_path: str) -> str:
    """Conversione reale RVT → IFC usando Forge SDK."""
    try:
        # Inizializza client Forge
        client = ForgeClient(
            settings.FORGE_CLIENT_ID,
            settings.FORGE_CLIENT_SECRET
        )
        
        # Upload file RVT
        bucket_key = settings.FORGE_BUCKET_NAME
        object_key = f"rvt/{os.path.basename(local_path)}"
        
        with open(local_path, "rb") as f:
            client.upload_object(bucket_key, object_key, f)
        
        # Avvia conversione RVT → IFC
        job = client.start_translation_job(
            bucket_key,
            object_key,
            "rvt",
            "ifc",
            settings.FORGE_REGION
        )
        
        # Attendi completamento
        while job.status != "completed":
            time.sleep(10)
            job = client.get_translation_job(job.urn)
        
        # Download file IFC convertito
        ifc_key = f"ifc/{os.path.basename(local_path).replace('.rvt', '.ifc')}"
        ifc_path = local_path.replace(".rvt", ".ifc")
        
        with open(ifc_path, "wb") as f:
            client.download_object(bucket_key, ifc_key, f)
        
        return ifc_path
        
    except Exception as e:
        logger.error(f"Errore conversione RVT reale: {e}")
        raise
```

## Configurazione Condizionale

### Worker Aggiornato
```python
@celery_app.task(bind=True, name="convert_ifc_to_gltf")
def convert_ifc_to_gltf(self, model_id: int) -> Dict[str, Any]:
    worker = BIMConversionWorker()
    
    try:
        # Aggiorna stato iniziale
        worker.update_model_status(model_id, "processing", "Avvio conversione IFC → GLTF", 10)
        
        # Ottieni modello dal database
        db = next(get_session())
        model = db.exec(select(BIMModel).where(BIMModel.id == model_id)).first()
        
        if not model:
            raise Exception(f"Modello BIM {model_id} non trovato")
        
        if model.format != BIMFormat.IFC:
            raise Exception(f"Formato non supportato per conversione GLTF: {model.format}")
        
        # Scarica file
        worker.update_model_status(model_id, "processing", "Download file IFC", 20)
        local_path = worker.download_file(model.file_url)
        
        # Conversione condizionale
        if settings.USE_REAL_BIM_CONVERSION and settings.USE_IFCOPENSHELL:
            worker.update_model_status(model_id, "processing", "Conversione reale in corso", 50)
            gltf_path = worker._real_ifc_conversion(local_path)
        else:
            worker.update_model_status(model_id, "processing", "Conversione simulata in corso", 50)
            gltf_path = worker._simulated_ifc_conversion(local_path)
        
        # Carica file convertito
        worker.update_model_status(model_id, "processing", "Upload file convertito", 80)
        converted_url = worker.upload_converted_file(gltf_path, model.file_url, "gltf")
        
        # Aggiorna modello
        model.converted_file_url = converted_url
        model.conversion_status = "completed"
        model.conversion_message = "Conversione completata con successo"
        model.conversion_progress = 100
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "success": True,
            "model_id": model_id,
            "converted_url": converted_url,
            "real_conversion": settings.USE_REAL_BIM_CONVERSION
        }
        
    except Exception as e:
        worker.update_model_status(model_id, "failed", f"Errore conversione: {str(e)}", 0)
        raise
```

## Variabili d'Ambiente

### Sviluppo (.env.development)
```env
USE_REAL_BIM_CONVERSION=false
USE_IFCOPENSHELL=false
USE_FORGE_SDK=false
```

### Testing (.env.testing)
```env
USE_REAL_BIM_CONVERSION=true
USE_IFCOPENSHELL=true
USE_FORGE_SDK=false
FORGE_CLIENT_ID=test_client_id
FORGE_CLIENT_SECRET=test_secret
```

### Produzione (.env.production)
```env
USE_REAL_BIM_CONVERSION=true
USE_IFCOPENSHELL=true
USE_FORGE_SDK=true
FORGE_CLIENT_ID=prod_client_id
FORGE_CLIENT_SECRET=prod_secret
FORGE_BUCKET_NAME=eterna-home-prod
```

## Gestione Errori

### Fallback Automatico
```python
def convert_with_fallback(self, model_id: int):
    try:
        if settings.USE_REAL_BIM_CONVERSION:
            return self._real_conversion()
    except Exception as e:
        logger.warning(f"Conversione reale fallita, uso simulazione: {e}")
    
    # Fallback a simulazione
    return self._simulated_conversion()
```

### Monitoring
```python
def log_conversion_metrics(self, model_id: int, real_conversion: bool, duration: float):
    metrics = {
        "model_id": model_id,
        "real_conversion": real_conversion,
        "duration": duration,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logger.info(f"Conversion metrics: {metrics}")
```

## Roadmap di Integrazione

### Fase 1: Preparazione (Completata) ✅
- [x] Architettura Celery
- [x] Worker specializzati
- [x] Configurazione condizionale
- [x] Simulazioni funzionanti

### Fase 2: Testing IfcOpenShell (Opzionale)
- [ ] Installazione IfcOpenShell
- [ ] Test conversione IFC reale
- [ ] Validazione output GLTF
- [ ] Performance testing

### Fase 3: Testing Forge SDK (Opzionale)
- [ ] Registrazione account Autodesk
- [ ] Configurazione Forge SDK
- [ ] Test conversione RVT reale
- [ ] Validazione output IFC

### Fase 4: Produzione (Finale)
- [ ] Configurazione produzione
- [ ] Monitoring e alerting
- [ ] Backup e disaster recovery
- [ ] Documentazione operativa

## Vantaggi di Questa Strategia

1. **Sviluppo Continuo**: Nessuna interruzione durante sviluppo
2. **Testing Graduale**: Possibilità di testare servizi reali quando necessario
3. **Flessibilità**: Facile passaggio tra simulazione e conversione reale
4. **Costi Controllati**: Nessun costo durante sviluppo
5. **Stabilità**: Sistema sempre funzionante

## Raccomandazioni

1. **Mantieni le simulazioni** per sviluppo e testing
2. **Configura servizi reali** solo quando necessario
3. **Usa fallback automatico** per robustezza
4. **Monitora costi** per servizi a pagamento
5. **Documenta configurazioni** per ogni ambiente

---

**Nota**: Questa strategia permette di sviluppare e testare il sistema completo senza dipendenze esterne, per poi integrare i servizi reali solo quando si è pronti per la produzione. 