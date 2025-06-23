# Gestione Aree e Nodi - Eterna Home

## 📋 Panoramica

Il sistema di gestione aree e nodi di Eterna Home permette di organizzare razionalmente i nodi IoT in aree specifiche e principali, creando una gerarchia logica che facilita la gestione e il controllo della casa intelligente.

## 🏗️ Architettura

### Modelli di Dati

#### 1. NodeArea (Aree Specifiche)
```python
class NodeArea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # es. "Cucina", "Bagno", "Quadro Elettrico"
    category: str = Field(index=True)  # "residential", "technical", "shared"
    has_physical_tag: bool = True  # se ha attivatore fisico NFC
    house_id: int = Field(foreign_key="houses.id")  # multi-tenancy
```

**Categorie disponibili:**
- `residential`: Aree residenziali (cucina, soggiorno, camera, bagno)
- `technical`: Aree tecniche (quadro elettrico, caldaia, impianti)
- `shared`: Aree condivise (ingresso, giardino, cantina)

#### 2. MainArea (Aree Principali)
```python
class MainArea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # es. "Zona Giorno", "Zona Impianti"
    description: Optional[str] = None
    house_id: int = Field(foreign_key="houses.id")  # multi-tenancy
```

#### 3. Node (Esteso)
```python
class Node(SQLModel, table=True):
    # ... campi esistenti ...
    node_area_id: Optional[int] = Field(default=None, foreign_key="node_areas.id")
    main_area_id: Optional[int] = Field(default=None, foreign_key="main_areas.id")
    is_master_node: bool = False  # se rappresenta l'area principale
    has_physical_tag: bool = True  # se ha tag fisico NFC
```

## 🔗 Relazioni

```
House (1) ←→ (N) MainArea
House (1) ←→ (N) NodeArea
MainArea (1) ←→ (N) Node
NodeArea (1) ←→ (N) Node
```

## 🛡️ Sicurezza

- **Multi-tenancy**: Tutti i modelli sono collegati a `house_id`
- **Ownership**: Controlli di proprietà per tutte le operazioni
- **Validazione**: Campi obbligatori e categorie validate
- **Autenticazione**: JWT obbligatorio per tutti gli endpoint

## 📡 API Endpoints

### NodeArea Endpoints

#### CRUD Operations
- `POST /api/v1/node-areas/` - Crea area specifica
- `GET /api/v1/node-areas/` - Lista aree specifiche (con filtri)
- `GET /api/v1/node-areas/{id}` - Ottieni area specifica
- `PUT /api/v1/node-areas/{id}` - Aggiorna area specifica
- `DELETE /api/v1/node-areas/{id}` - Elimina area specifica

#### Endpoint Specializzati
- `GET /api/v1/node-areas/house/{house_id}` - Aree per casa specifica
- `GET /api/v1/node-areas/categories/list` - Lista categorie disponibili

#### Parametri di Filtro
- `house_id`: Filtra per casa
- `category`: Filtra per categoria (residential, technical, shared)
- `page`: Numero di pagina
- `size`: Dimensione pagina

### MainArea Endpoints

#### CRUD Operations
- `POST /api/v1/main-areas/` - Crea area principale
- `GET /api/v1/main-areas/` - Lista aree principali (con filtri)
- `GET /api/v1/main-areas/{id}` - Ottieni area principale
- `PUT /api/v1/main-areas/{id}` - Aggiorna area principale
- `DELETE /api/v1/main-areas/{id}` - Elimina area principale

#### Endpoint Specializzati
- `GET /api/v1/main-areas/house/{house_id}` - Aree principali per casa

### Report Endpoints

#### Report Gerarchici
- `GET /api/v1/area-reports/hierarchy/{house_id}` - Report gerarchico completo
- `GET /api/v1/area-reports/summary/{house_id}` - Riepilogo statistiche
- `GET /api/v1/area-reports/nodes-by-area/{house_id}` - Nodi raggruppati per area

#### Parametri Report
- `area_type`: "main" o "node" per raggruppamento

## 📊 Esempi di Utilizzo

### 1. Creazione Area Specifica
```bash
curl -X POST "http://localhost:8000/api/v1/node-areas/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cucina",
    "category": "residential",
    "has_physical_tag": true,
    "house_id": 1
  }'
```

### 2. Creazione Area Principale
```bash
curl -X POST "http://localhost:8000/api/v1/main-areas/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Zona Giorno",
    "description": "Area principale per la vita quotidiana",
    "house_id": 1
  }'
```

### 3. Report Gerarchico
```bash
curl -X GET "http://localhost:8000/api/v1/area-reports/hierarchy/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Filtro Aree per Categoria
```bash
curl -X GET "http://localhost:8000/api/v1/node-areas/?category=technical" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🧪 Test

### Script di Test API
```bash
python test_area_api.py
```

### Script di Test Modelli
```bash
python test_gestione_aree_nodi.py
```

### Creazione Tabelle
```bash
python create_area_tables.py
```

## 🖥️ Interfaccia Frontend

### Avvio Interfaccia
1. Apri `frontend/area_management.html` nel browser
2. L'interfaccia si connette automaticamente all'API locale
3. Effettua il login con le credenziali di test

### Funzionalità Interfaccia
- **Tab Aree Principali**: Gestione MainArea
- **Tab Aree Specifiche**: Gestione NodeArea
- **Tab Report**: Visualizzazione gerarchica e statistiche
- **Form Validati**: Controlli in tempo reale
- **Feedback Visivo**: Alert di successo/errore
- **Design Responsive**: Ottimizzato per mobile

## 📈 Report e Statistiche

### Report Gerarchico
```json
{
  "house": {
    "id": 1,
    "name": "Casa Test",
    "address": "Via Test 123"
  },
  "main_areas": [
    {
      "id": 1,
      "name": "Zona Giorno",
      "description": "Area principale per la vita quotidiana",
      "nodes_count": 3,
      "node_areas": [
        {
          "id": 1,
          "name": "Cucina",
          "category": "residential",
          "nodes_count": 2
        }
      ],
      "nodes": [...]
    }
  ],
  "statistics": {
    "total_main_areas": 2,
    "total_node_areas": 5,
    "total_nodes": 8,
    "master_nodes": 2,
    "physical_tag_nodes": 6
  }
}
```

### Report Riepilogo
```json
{
  "house": {
    "id": 1,
    "name": "Casa Test"
  },
  "statistics": {
    "main_areas_count": 2,
    "node_areas_by_category": {
      "residential": 3,
      "technical": 2,
      "shared": 1
    },
    "nodes": {
      "total": 8,
      "master": 2,
      "physical_tag": 6
    }
  },
  "areas_by_category": {
    "residential": [...],
    "technical": [...],
    "shared": [...]
  }
}
```

## 🔧 Configurazione

### Variabili d'Ambiente
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/eterna_home

# API
API_HOST=0.0.0.0
API_PORT=8000

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### Dipendenze
```bash
pip install fastapi sqlmodel pydantic psycopg2-binary
```

## 🚀 Deployment

### 1. Preparazione Database
```bash
# Crea le tabelle
python create_area_tables.py

# Verifica le tabelle
python test_gestione_aree_nodi.py
```

### 2. Avvio API
```bash
# Sviluppo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Produzione
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 3. Test API
```bash
# Test completi
python test_area_api.py

# Test specifici
curl -X GET "http://localhost:8000/api/v1/node-areas/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📝 Validazioni

### NodeArea Validazioni
- **Nome**: Obbligatorio, 1-100 caratteri, unico per casa
- **Categoria**: Obbligatorio, deve essere residential/technical/shared
- **Tag fisico**: Booleano, default true
- **Casa**: Obbligatorio, deve appartenere all'utente

### MainArea Validazioni
- **Nome**: Obbligatorio, 1-100 caratteri, unico per casa
- **Descrizione**: Opzionale, max 500 caratteri
- **Casa**: Obbligatorio, deve appartenere all'utente

### Controlli di Sicurezza
- Verifica proprietà casa per tutte le operazioni
- Controllo esistenza nodi associati prima dell'eliminazione
- Validazione token JWT per tutti gli endpoint
- Rate limiting sui endpoint sensibili

## 🐛 Troubleshooting

### Errori Comuni

#### 1. "Casa non trovata"
- Verifica che la casa esista e appartenga all'utente
- Controlla il token JWT

#### 2. "Esiste già un'area con questo nome"
- I nomi delle aree devono essere unici per casa
- Usa un nome diverso o elimina l'area esistente

#### 3. "Non è possibile eliminare l'area perché ha nodi associati"
- Elimina prima i nodi associati
- Oppure sposta i nodi in un'altra area

#### 4. "Categoria non valida"
- Usa solo: residential, technical, shared
- Controlla la sintassi esatta

### Log e Debug
```bash
# Abilita log dettagliati
export LOG_LEVEL=DEBUG

# Verifica connessione database
python -c "from app.database import get_engine; print('DB OK')"

# Test endpoint health
curl http://localhost:8000/health
```

## 🔮 Roadmap

### Prossime Funzionalità
1. **Integrazione Frontend**: Connessione con app principale
2. **Notifiche**: Alert per modifiche aree
3. **Import/Export**: Backup configurazioni aree
4. **Templates**: Aree predefinite per tipi di casa
5. **Analytics**: Statistiche avanzate utilizzo aree

### Miglioramenti
1. **Performance**: Ottimizzazione query complesse
2. **Caching**: Redis per report frequenti
3. **WebSocket**: Aggiornamenti real-time
4. **Mobile**: App nativa per gestione aree

## 📞 Supporto

Per supporto tecnico o domande:
- Documentazione: `AREA_NODE_IMPLEMENTATION.md`
- Test: `test_area_api.py`
- Interfaccia: `frontend/area_management.html`
- Log: Controlla i log dell'applicazione

---

**Versione**: 1.0.0  
**Data**: 23/06/2025  
**Autore**: Eterna Home Team 