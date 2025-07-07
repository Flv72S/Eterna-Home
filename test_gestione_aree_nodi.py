#!/usr/bin/env python3
"""
Script di test per verificare il funzionamento dei modelli NodeArea e MainArea.
Questo script testa la creazione, le relazioni e la gestione delle aree e nodi.
"""

import sys
import os
from datetime import datetime, timezone

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, create_engine, select
from app.database import get_engine
from app.models import User, House, Node, NodeArea, MainArea
from app.db.init_areas import create_sample_areas_for_house

def test_area_models():
    """Test completo dei modelli NodeArea e MainArea."""
    print("🧪 TEST MODELLI AREA ↔ NODO")
    print("=" * 50)
    
    # Crea engine e sessione
    engine = get_engine()
    
    with Session(engine) as session:
        try:
            # 1. Crea utente di test
            print("1. Creazione utente di test...")
            user = User(
                email="test_areas@example.com",
                username="test_areas_user",
                hashed_password="hashed_password",
                is_active=True,
                role="owner"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"   ✅ Utente creato: {user.username} (ID: {user.id})")
            
            # 2. Crea casa di test
            print("\n2. Creazione casa di test...")
            house = House(
                name="Casa Test Aree",
                address="Via Test Aree 123",
                owner_id=user.id
            )
            session.add(house)
            session.commit()
            session.refresh(house)
            print(f"   ✅ Casa creata: {house.name} (ID: {house.id})")
            
            # 3. Crea NodeArea di esempio
            print("\n3. Creazione NodeArea di esempio...")
            node_areas_data = create_sample_areas_for_house(house.id)["node_areas"]
            
            node_areas = []
            for area_data in node_areas_data[:5]:  # Solo i primi 5 per il test
                node_area = NodeArea(**area_data)
                session.add(node_area)
                node_areas.append(node_area)
            
            session.commit()
            for node_area in node_areas:
                session.refresh(node_area)
                print(f"   ✅ NodeArea creata: {node_area.name} ({node_area.category}) - ID: {node_area.id}")
            
            # 4. Crea MainArea di esempio
            print("\n4. Creazione MainArea di esempio...")
            main_areas_data = create_sample_areas_for_house(house.id)["main_areas"]
            
            main_areas = []
            for area_data in main_areas_data[:3]:  # Solo i primi 3 per il test
                main_area = MainArea(**area_data)
                session.add(main_area)
                main_areas.append(main_area)
            
            session.commit()
            for main_area in main_areas:
                session.refresh(main_area)
                print(f"   ✅ MainArea creata: {main_area.name} - ID: {main_area.id}")
            
            # 5. Crea nodi con associazioni alle aree
            print("\n5. Creazione nodi con associazioni alle aree...")
            
            # Nodo master per Zona Giorno
            master_node = Node(
                name="Nodo Master Zona Giorno",
                description="Nodo principale per la zona giorno",
                nfc_id="MASTER_ZONA_GIORNO_001",
                house_id=house.id,
                node_area_id=node_areas[0].id,  # Cucina
                main_area_id=main_areas[0].id,  # Zona Giorno
                is_master_node=True,
                has_physical_tag=True
            )
            session.add(master_node)
            
            # Nodo per quadro elettrico
            electrical_node = Node(
                name="Nodo Quadro Elettrico",
                description="Nodo per il controllo del quadro elettrico",
                nfc_id="QUADRO_ELETTRICO_001",
                house_id=house.id,
                node_area_id=node_areas[8].id,  # Quadro Elettrico
                main_area_id=main_areas[2].id,  # Zona Impianti
                is_master_node=False,
                has_physical_tag=True
            )
            session.add(electrical_node)
            
            # Nodo per caldaia
            boiler_node = Node(
                name="Nodo Caldaia",
                description="Nodo per il controllo della caldaia",
                nfc_id="CALDAIA_001",
                house_id=house.id,
                node_area_id=node_areas[9].id,  # Caldaia
                main_area_id=main_areas[2].id,  # Zona Impianti
                is_master_node=False,
                has_physical_tag=True
            )
            session.add(boiler_node)
            
            session.commit()
            session.refresh(master_node)
            session.refresh(electrical_node)
            session.refresh(boiler_node)
            
            print(f"   ✅ Nodo Master creato: {master_node.name} - ID: {master_node.id}")
            print(f"   ✅ Nodo Elettrico creato: {electrical_node.name} - ID: {electrical_node.id}")
            print(f"   ✅ Nodo Caldaia creato: {boiler_node.name} - ID: {boiler_node.id}")
            
            # 6. Test delle relazioni
            print("\n6. Test delle relazioni...")
            
            # Verifica relazioni Node → Area
            print(f"   📍 Nodo Master associato a:")
            print(f"      - NodeArea: {master_node.node_area.name if master_node.node_area else 'Nessuna'}")
            print(f"      - MainArea: {master_node.main_area.name if master_node.main_area else 'Nessuna'}")
            
            print(f"   📍 Nodo Elettrico associato a:")
            print(f"      - NodeArea: {electrical_node.node_area.name if electrical_node.node_area else 'Nessuna'}")
            print(f"      - MainArea: {electrical_node.main_area.name if electrical_node.main_area else 'Nessuna'}")
            
            # Verifica relazioni Area → Node
            zona_impianti = main_areas[2]  # Zona Impianti
            print(f"   📍 {zona_impianti.name} contiene {len(zona_impianti.nodes)} nodi:")
            for node in zona_impianti.nodes:
                print(f"      - {node.name} ({node.node_area.name if node.node_area else 'Nessuna area specifica'})")
            
            # 7. Query di test
            print("\n7. Query di test...")
            
            # Trova tutti i nodi master
            master_nodes = session.exec(select(Node).where(Node.is_master_node == True)).all()
            print(f"   🔍 Nodi master trovati: {len(master_nodes)}")
            for node in master_nodes:
                print(f"      - {node.name} in {node.main_area.name if node.main_area else 'Nessuna area'}")
            
            # Trova tutti i nodi con tag fisico
            physical_nodes = session.exec(select(Node).where(Node.has_physical_tag == True)).all()
            print(f"   🔍 Nodi con tag fisico: {len(physical_nodes)}")
            
            # Trova tutte le aree tecniche
            technical_areas = session.exec(select(NodeArea).where(NodeArea.category == "technical")).all()
            print(f"   🔍 Aree tecniche: {len(technical_areas)}")
            for area in technical_areas:
                print(f"      - {area.name} (tag fisico: {area.has_physical_tag})")
            
            print("\n✅ TEST COMPLETATO CON SUCCESSO!")
            print("=" * 50)
            print("📋 RIEPILOGO:")
            print(f"   - Utente: {user.username}")
            print(f"   - Casa: {house.name}")
            print(f"   - NodeArea create: {len(node_areas)}")
            print(f"   - MainArea create: {len(main_areas)}")
            print(f"   - Nodi creati: 3")
            print(f"   - Relazioni testate: ✅")
            print(f"   - Query testate: ✅")
            
        except Exception as e:
            print(f"❌ ERRORE durante il test: {e}")
            session.rollback()
            raise
        finally:
            # Cleanup (opzionale - commentare per mantenere i dati)
            print("\n🧹 Cleanup...")
            try:
                # Rimuovi i dati di test
                session.exec(select(Node).where(Node.house_id == house.id)).delete()
                session.exec(select(NodeArea).where(NodeArea.house_id == house.id)).delete()
                session.exec(select(MainArea).where(MainArea.house_id == house.id)).delete()
                session.exec(select(House).where(House.id == house.id)).delete()
                session.exec(select(User).where(User.id == user.id)).delete()
                session.commit()
                print("   ✅ Dati di test rimossi")
            except Exception as e:
                print(f"   ⚠️ Errore durante cleanup: {e}")

if __name__ == "__main__":
    test_area_models() 