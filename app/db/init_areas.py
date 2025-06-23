"""
Script per inizializzare i dati di esempio per NodeArea e MainArea.
Questo file contiene valori predefiniti per testare le funzionalità di gestione aree.
"""

from typing import List, Dict, Any

# Dati di esempio per NodeArea
NODE_AREAS_EXAMPLE = [
    # Aree residenziali
    {"name": "Cucina", "category": "residential", "has_physical_tag": True},
    {"name": "Soggiorno", "category": "residential", "has_physical_tag": True},
    {"name": "Camera da letto", "category": "residential", "has_physical_tag": True},
    {"name": "Bagno", "category": "residential", "has_physical_tag": True},
    {"name": "Corridoio", "category": "residential", "has_physical_tag": True},
    {"name": "Studio", "category": "residential", "has_physical_tag": True},
    {"name": "Lavanderia", "category": "residential", "has_physical_tag": True},
    {"name": "Ripostiglio", "category": "residential", "has_physical_tag": False},
    
    # Aree tecniche
    {"name": "Quadro Elettrico", "category": "technical", "has_physical_tag": True},
    {"name": "Caldaia", "category": "technical", "has_physical_tag": True},
    {"name": "Impianto Idraulico", "category": "technical", "has_physical_tag": True},
    {"name": "Impianto di Ventilazione", "category": "technical", "has_physical_tag": True},
    {"name": "Centrale Termica", "category": "technical", "has_physical_tag": True},
    {"name": "Sala Controlli", "category": "technical", "has_physical_tag": True},
    {"name": "Deposito Attrezzi", "category": "technical", "has_physical_tag": False},
    
    # Aree condivise
    {"name": "Ingresso", "category": "shared", "has_physical_tag": True},
    {"name": "Giardino", "category": "shared", "has_physical_tag": True},
    {"name": "Terrazza", "category": "shared", "has_physical_tag": True},
    {"name": "Cantina", "category": "shared", "has_physical_tag": True},
    {"name": "Soffitta", "category": "shared", "has_physical_tag": False},
]

# Dati di esempio per MainArea
MAIN_AREAS_EXAMPLE = [
    {"name": "Zona Giorno", "description": "Area principale per la vita quotidiana"},
    {"name": "Zona Notte", "description": "Area dedicata al riposo e privacy"},
    {"name": "Zona Servizi", "description": "Area per servizi e utilità"},
    {"name": "Zona Impianti", "description": "Area tecnica per impianti e controlli"},
    {"name": "Zona Esterna", "description": "Area esterna e giardino"},
    {"name": "Zona Deposito", "description": "Area per magazzino e deposito"},
]

def get_node_areas_example() -> List[Dict[str, Any]]:
    """Restituisce la lista dei NodeArea di esempio."""
    return NODE_AREAS_EXAMPLE

def get_main_areas_example() -> List[Dict[str, Any]]:
    """Restituisce la lista dei MainArea di esempio."""
    return MAIN_AREAS_EXAMPLE

def create_sample_areas_for_house(house_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """Crea dati di esempio per una casa specifica."""
    node_areas = []
    for area in NODE_AREAS_EXAMPLE:
        node_areas.append({
            **area,
            "house_id": house_id
        })
    
    main_areas = []
    for area in MAIN_AREAS_EXAMPLE:
        main_areas.append({
            **area,
            "house_id": house_id
        })
    
    return {
        "node_areas": node_areas,
        "main_areas": main_areas
    } 