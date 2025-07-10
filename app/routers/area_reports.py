from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models import House, Node

router = APIRouter()

@router.get("/hierarchy/{house_id}", summary="Report gerarchico aree e nodi")
async def get_area_hierarchy(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ottiene il report gerarchico completo delle aree e nodi per una casa."""
    
    # Verifica che la casa appartenga all'utente
    house = db.exec(
        select(House).where(
            House.id == house_id,
            House.owner_id == current_user.id
        )
    ).first()
    
    if not house:
        raise HTTPException(status_code=404, detail="Casa non trovata")
    
    # Ottieni tutte le aree principali della casa
    # Query per aree principali
    # main_areas_query = (
    #     select(MainArea)
    #     .where(MainArea.house_id == house_id)
    #     .order_by(MainArea.name)
    # )
    # main_areas = session.exec(main_areas_query).all()
    
    main_areas = []  # Placeholder, as MainArea is removed
    
    # Ottieni tutte le aree specifiche della casa
    # Query per aree specifiche
    # areas_query = (
    #     select(NodeArea)
    #     .where(NodeArea.house_id == house_id)
    #     .order_by(NodeArea.category, NodeArea.name)
    # )
    # areas = session.exec(areas_query).all()
    
    # areas_data = []
    # for area in areas:
    #     # Conta nodi per area
    #     nodes_count = session.exec(
    #         select(func.count(Node.id))
    #         .where(Node.node_area_id == area.id)
    #     ).first() or 0
        
    #     areas_data.append({
    #         "id": area.id,
    #         "name": area.name,
    #         "category": area.category,
    #         "has_physical_tag": area.has_physical_tag,
    #         "nodes_count": nodes_count
    #     })
    
    areas_data = []  # Placeholder, as NodeArea is removed
    
    # Ottieni tutti i nodi della casa
    nodes = db.exec(
        select(Node)
        .where(Node.house_id == house_id)
        .order_by(Node.name)
    ).all()
    
    # Costruisci la gerarchia
    hierarchy = {
        "house": {
            "id": house.id,
            "name": house.name,
            "address": house.address
        },
        "main_areas": []
    }
    
    for main_area in main_areas:
        main_area_data = {
            "id": main_area.id,
            "name": main_area.name,
            "description": main_area.description,
            "nodes_count": 0,
            "node_areas": [],
            "nodes": []
        }
        
        # Trova i nodi associati a questa area principale
        main_area_nodes = [n for n in nodes if n.main_area_id == main_area.id]
        main_area_data["nodes_count"] = len(main_area_nodes)
        main_area_data["nodes"] = [
            {
                "id": node.id,
                "name": node.name,
                "description": node.description,
                "nfc_id": node.nfc_id,
                "is_master_node": node.is_master_node,
                "has_physical_tag": node.has_physical_tag,
                "node_area": None
            }
            for node in main_area_nodes
        ]
        
        # Trova le aree specifiche associate ai nodi di questa area principale
        node_area_ids = set(node.node_area_id for node in main_area_nodes if node.node_area_id)
        for area in areas_data: # Use areas_data here
            if area["id"] in node_area_ids:
                node_area_data = {
                    "id": area["id"],
                    "name": area["name"],
                    "category": area["category"],
                    "has_physical_tag": area["has_physical_tag"],
                    "nodes_count": len([n for n in main_area_nodes if n.node_area_id == area["id"]])
                }
                main_area_data["node_areas"].append(node_area_data)
        
        hierarchy["main_areas"].append(main_area_data)
    
    # Aggiungi statistiche generali
    hierarchy["statistics"] = {
        "total_main_areas": len(main_areas),
        "total_node_areas": len(areas_data), # Use areas_data here
        "total_nodes": len(nodes),
        "master_nodes": len([n for n in nodes if n.is_master_node]),
        "physical_tag_nodes": len([n for n in nodes if n.has_physical_tag])
    }
    
    return hierarchy

@router.get("/summary/{house_id}", summary="Riepilogo aree e nodi")
async def get_area_summary(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ottiene un riepilogo delle aree e nodi per una casa."""
    
    # Verifica che la casa appartenga all'utente
    house = db.exec(
        select(House).where(
            House.id == house_id,
            House.owner_id == current_user.id
        )
    ).first()
    
    if not house:
        raise HTTPException(status_code=404, detail="Casa non trovata")
    
    # Statistiche per categorie di aree specifiche
    category_stats = db.exec(
        select(
            # NodeArea.category, # NodeArea is removed
            func.count(NodeArea.id).label("count") # Placeholder, as NodeArea is removed
        )
        .where(NodeArea.house_id == house_id) # Placeholder, as NodeArea is removed
        .group_by(NodeArea.category) # Placeholder, as NodeArea is removed
    ).all()
    
    # Statistiche per nodi
    nodes_stats = db.exec(
        select(
            func.count(Node.id).label("total"),
            func.count(Node.id).filter(Node.is_master_node == True).label("master"),
            func.count(Node.id).filter(Node.has_physical_tag == True).label("physical_tag")
        )
        .where(Node.house_id == house_id)
    ).first()
    
    # Aree specifiche per categoria
    areas_by_category = {}
    for category, count in category_stats:
        areas = db.exec(
            select(NodeArea)
            .where(NodeArea.house_id == house_id, NodeArea.category == category) # Placeholder, as NodeArea is removed
            .order_by(NodeArea.name)
        ).all()
        areas_by_category[category] = [
            {
                "id": area.id,
                "name": area.name,
                "has_physical_tag": area.has_physical_tag,
                "nodes_count": db.exec(
                    select(func.count(Node.id))
                    .where(Node.node_area_id == area.id) # Placeholder, as NodeArea is removed
                ).first()
            }
            for area in areas
        ]
    
    return {
        "house": {
            "id": house.id,
            "name": house.name
        },
        "statistics": {
            "main_areas_count": db.exec(
                select(func.count(MainArea.id))
                .where(MainArea.house_id == house_id)
            ).first(),
            "node_areas_by_category": dict(category_stats),
            "nodes": {
                "total": nodes_stats.total,
                "master": nodes_stats.master,
                "physical_tag": nodes_stats.physical_tag
            }
        },
        "areas_by_category": areas_by_category
    }

@router.get("/nodes-by-area/{house_id}", summary="Nodi raggruppati per area")
async def get_nodes_by_area(
    house_id: int,
    area_type: str = Query("main", description="Tipo di area: 'main' o 'node'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ottiene i nodi raggruppati per area principale o specifica."""
    
    # Verifica che la casa appartenga all'utente
    house = db.exec(
        select(House).where(
            House.id == house_id,
            House.owner_id == current_user.id
        )
    ).first()
    
    if not house:
        raise HTTPException(status_code=404, detail="Casa non trovata")
    
    if area_type == "main":
        # Raggruppa per aree principali
        areas = db.exec(
            select(MainArea)
            .where(MainArea.house_id == house_id)
            .order_by(MainArea.name)
        ).all()
        
        result = []
        for area in areas:
            nodes = db.exec(
                select(Node)
                .where(Node.main_area_id == area.id)
                .order_by(Node.name)
            ).all()
            
            result.append({
                "area": {
                    "id": area.id,
                    "name": area.name,
                    "description": area.description
                },
                "nodes": [
                    {
                        "id": node.id,
                        "name": node.name,
                        "description": node.description,
                        "nfc_id": node.nfc_id,
                        "is_master_node": node.is_master_node,
                        "has_physical_tag": node.has_physical_tag
                    }
                    for node in nodes
                ],
                "nodes_count": len(nodes)
            })
    
    elif area_type == "node":
        # Raggruppa per aree specifiche
        areas = db.exec(
            select(NodeArea)
            .where(NodeArea.house_id == house_id) # Placeholder, as NodeArea is removed
            .order_by(NodeArea.category, NodeArea.name) # Placeholder, as NodeArea is removed
        ).all()
        
        result = []
        for area in areas:
            nodes = db.exec(
                select(Node)
                .where(Node.node_area_id == area.id) # Placeholder, as NodeArea is removed
                .order_by(Node.name)
            ).all()
            
            result.append({
                "area": {
                    "id": area.id,
                    "name": area.name,
                    "category": area.category,
                    "has_physical_tag": area.has_physical_tag
                },
                "nodes": [
                    {
                        "id": node.id,
                        "name": node.name,
                        "description": node.description,
                        "nfc_id": node.nfc_id,
                        "is_master_node": node.is_master_node,
                        "has_physical_tag": node.has_physical_tag
                    }
                    for node in nodes
                ],
                "nodes_count": len(nodes)
            })
    
    else:
        raise HTTPException(status_code=400, detail="Tipo di area deve essere 'main' o 'node'")
    
    return {
        "house": {
            "id": house.id,
            "name": house.name
        },
        "area_type": area_type,
        "areas": result
    } 