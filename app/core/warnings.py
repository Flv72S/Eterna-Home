"""
Warning noti e non bloccanti nel progetto.

Questi warning sono relativi a dipendenze di terze parti o funzionalità deprecate
che non possono essere modificate direttamente o che richiedono aggiornamenti
più complessi.
"""

KNOWN_WARNINGS = {
    "jose/jwt.py": {
        "description": "Uso di datetime.utcnow() deprecato in jose/jwt.py",
        "status": "noto",
        "impact": "basso",
        "notes": "Il warning è generato dalla libreria python-jose e non può essere modificato direttamente. "
                "Non influisce sulla funzionalità del codice."
    }
} 