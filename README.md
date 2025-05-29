# Eterna Home

Sistema di gestione domotica avanzato con integrazione AI.

## Struttura del Progetto

```
Eterna-Home/
├── backend/
│   ├── core/
│   │   └── config.py         # Configurazione dell'applicazione
│   ├── models/
│   │   ├── node.py          # Modelli SQLModel per i nodi
│   │   └── ...
│   ├── schemas/
│   │   ├── node.py          # Schemi Pydantic per i nodi
│   │   └── ...
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── nodes.py  # API endpoints per i nodi
│   └── main.py              # Entry point dell'applicazione
├── frontend/
│   └── ...
└── venv/                    # Ambiente virtuale Python
```

## Requisiti

- Python 3.8+
- PostgreSQL 13+
- Node.js 16+
- Redis (per rate limiting)

## Installazione

### Backend

1. Crea e attiva l'ambiente virtuale:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate # Linux/Mac
   ```

2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

3. Configura il database:
   - Crea un database PostgreSQL
   - Aggiorna `backend/core/config.py` con le credenziali corrette

4. Avvia il server:
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Frontend

1. Installa le dipendenze:
   ```bash
   cd frontend
   npm install
   ```

2. Avvia il server di sviluppo:
   ```bash
   npm run dev
   ```

## Troubleshooting

### Backend

1. **Errore "Module not found"**
   - Verifica che l'ambiente virtuale sia attivo
   - Reinstalla le dipendenze: `pip install -r requirements.txt`

2. **Errore di connessione al database**
   - Verifica che PostgreSQL sia in esecuzione
   - Controlla le credenziali in `backend/core/config.py`

3. **Errore di importazione circolare**
   - Usa importazioni lazy con `from __future__ import annotations`
   - Riorganizza la struttura dei moduli se necessario

### Frontend

1. **Errore di compilazione**
   - Cancella la cache: `npm run clean`
   - Reinstalla le dipendenze: `npm install`

## Contribuire

1. Fork il repository
2. Crea un branch per la tua feature
3. Committa le modifiche
4. Pusha al branch
5. Crea una Pull Request

## Licenza

MIT 