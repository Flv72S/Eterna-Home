# Implementazione Modelli Area ↔ Nodo

## 📋 Panoramica

Questa implementazione aggiunge al sistema Eterna Home la gestione razionalizzata delle aree e dei nodi, permettendo di associare nodi fisici/digitali a aree specifiche e aree principali.

## 🏗️ Modelli Implementati

### 1. NodeArea (Area Specifica)
```python
class NodeArea(SQLModel, table=True):
    __tablename__ = "node_areas"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # es. "Cucina", "Bagno", "Quadro Elettrico"
    category: str = Field(index=True)  # es. "residential", "technical", "shared"
    has_physical_tag: bool = True  # se ha attivatore fisico o meno
    house_id: int = Field(foreign_key="houses.id")  # per multi-tenancy
```

**Categorie disponibili:**
- `residential`: Aree residenziali (cucina, soggiorno, camera, bagno, ecc.)
- `technical`: Aree tecniche (quadro elettrico, caldaia, impianti, ecc.)
- `shared`: Aree condivise (ingresso, giardino, cantina, ecc.)

### 2. MainArea (Area Principale)
```python
class MainArea(SQLModel, table=True):
    __tablename__ = "main_areas"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # es. "Zona Giorno", "Zona Impianti"
    description: Optional[str] = None
    house_id: int = Field(foreign_key="houses.id")  # per multi-tenancy
```

**Aree principali predefinite:**
- Zona Giorno (area principale per la vita quotidiana)
- Zona Notte (area dedicata al riposo e privacy)
- Zona Servizi (area per servizi e utilità)
- Zona Impianti (area tecnica per impianti e controlli)
- Zona Esterna (area esterna e giardino)
- Zona Deposito (area per magazzino e deposito)

### 3. Node (Esteso)
Il modello `Node` esistente è stato esteso con i seguenti campi:

```python
class Node(SQLModel, table=True):
    # ... campi esistenti ...
    
    # Nuovi campi aggiunti
    node_area_id: Optional[int] = Field(default=None, foreign_key="node_areas.id", nullable=True)
    main_area_id: Optional[int] = Field(default=None, foreign_key="main_areas.id", nullable=True)
    is_master_node: bool = False  # se rappresenta l'area principale
    has_physical_tag: bool = True  # se ha tag fisico NFC
```

## 🔗 Relazioni Implementate

### Relazioni Dirette
- `Node ↔ NodeArea`: Un nodo può essere associato a un'area specifica
- `Node ↔ MainArea`: Un nodo può essere associato a un'area principale
- `House ↔ NodeArea`: Le aree specifiche appartengono a una casa
- `House ↔ MainArea`: Le aree principali appartengono a una casa

### Relazioni Inverse
- `NodeArea → Node[]`: Un'area specifica può contenere più nodi
- `MainArea → Node[]`: Un'area principale può contenere più nodi
- `House → NodeArea[]`: Una casa può avere multiple aree specifiche
- `House → MainArea[]`: Una casa può avere multiple aree principali

## 🛡️ Sicurezza e Multi-tenancy

- **Isolamento dati**: Tutti i modelli sono collegati a `house_id` per garantire l'isolamento tra utenti
- **Controllo accessi**: Le aree sono associate alle case, quindi ereditano i controlli di sicurezza esistenti
- **Validazione**: I campi obbligatori sono validati tramite SQLModel e Pydantic

## 📊 Dati di Esempio

### NodeArea (Aree Specifiche)
```python
# Aree residenziali
{"name": "Cucina", "category": "residential", "has_physical_tag": True}
{"name": "Soggiorno", "category": "residential", "has_physical_tag": True}
{"name": "Camera da letto", "category": "residential", "has_physical_tag": True}
{"name": "Bagno", "category": "residential", "has_physical_tag": True}

# Aree tecniche
{"name": "Quadro Elettrico", "category": "technical", "has_physical_tag": True}
{"name": "Caldaia", "category": "technical", "has_physical_tag": True}
{"name": "Impianto Idraulico", "category": "technical", "has_physical_tag": True}

# Aree condivise
{"name": "Ingresso", "category": "shared", "has_physical_tag": True}
{"name": "Giardino", "category": "shared", "has_physical_tag": True}
```

### MainArea (Aree Principali)
```python
{"name": "Zona Giorno", "description": "Area principale per la vita quotidiana"}
{"name": "Zona Notte", "description": "Area dedicata al riposo e privacy"}
{"name": "Zona Servizi", "description": "Area per servizi e utilità"}
{"name": "Zona Impianti", "description": "Area tecnica per impianti e controlli"}
{"name": "Zona Esterna", "description": "Area esterna e giardino"}
{"name": "Zona Deposito", "description": "Area per magazzino e deposito"}
```

## 🧪 Test e Verifica

### Script di Test
- `test_gestione_aree_nodi.py`: Test completo dei modelli e delle relazioni
- `create_area_tables.py`: Script per creare le tabelle nel database

### Comandi per Testare
```bash
# 1. Creare le tabelle
python create_area_tables.py

# 2. Eseguire il test completo
python test_gestione_aree_nodi.py
```

## 📁 File Modificati/Creati

### File Modificati
- `app/models/node.py`: Aggiunto NodeArea, MainArea e esteso Node
- `app/models/house.py`: Aggiunte relazioni con NodeArea e MainArea
- `app/models/__init__.py`: Esportati i nuovi modelli

### File Creati
- `app/db/init_areas.py`: Dati di esempio per NodeArea e MainArea
- `test_gestione_aree_nodi.py`: Script di test completo
- `create_area_tables.py`: Script per creare le tabelle
- `AREA_NODE_IMPLEMENTATION.md`: Questa documentazione

## 🎯 Casi d'Uso Supportati

### 1. Nodo Master per Area Principale
```python
# Nodo che rappresenta l'area principale "Zona Giorno"
master_node = Node(
    name="Nodo Master Zona Giorno",
    node_area_id=cucina_area.id,  # Area specifica: Cucina
    main_area_id=zona_giorno.id,  # Area principale: Zona Giorno
    is_master_node=True,          # È il nodo master
    has_physical_tag=True
)
```

### 2. Nodo Tecnico per Impianti
```python
# Nodo per il controllo del quadro elettrico
electrical_node = Node(
    name="Nodo Quadro Elettrico",
    node_area_id=quadro_elettrico.id,  # Area specifica: Quadro Elettrico
    main_area_id=zona_impianti.id,     # Area principale: Zona Impianti
    is_master_node=False,              # Non è master
    has_physical_tag=True
)
```

### 3. Query Avanzate
```python
# Trova tutti i nodi master
master_nodes = session.exec(select(Node).where(Node.is_master_node == True))

# Trova tutti i nodi in area tecnica
technical_nodes = session.exec(
    select(Node)
    .join(NodeArea)
    .where(NodeArea.category == "technical")
)

# Trova tutti i nodi in una specifica area principale
zona_giorno_nodes = session.exec(
    select(Node)
    .join(MainArea)
    .where(MainArea.name == "Zona Giorno")
)
```

## 🚀 Prossimi Step

1. **Endpoint API**: Creare endpoint per CRUD di NodeArea e MainArea
2. **Validazioni**: Aggiungere validazioni specifiche per categorie e nomi
3. **Interfaccia**: Integrare con il frontend per gestione aree
4. **Report**: Creare report per visualizzazione gerarchica aree/nodi
5. **Migrazione**: Preparare migrazione Alembic per produzione

## ✅ Stato Implementazione

- [x] Modelli NodeArea e MainArea creati
- [x] Modello Node esteso con relazioni
- [x] Relazioni House ↔ Area implementate
- [x] Dati di esempio preparati
- [x] Script di test creati
- [x] Documentazione completa
- [ ] Endpoint API (da implementare)
- [ ] Validazioni avanzate (da implementare)
- [ ] Interfaccia utente (da implementare) 