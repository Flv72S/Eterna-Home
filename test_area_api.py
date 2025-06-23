#!/usr/bin/env python3
"""
Script di test per verificare le API delle aree (NodeArea e MainArea).
Questo script testa tutti gli endpoint CRUD e i report.
"""

import sys
import os
import requests
import json
from typing import Dict, Any

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurazione
API_BASE = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "test_areas@example.com",
    "username": "test_areas_user",
    "password": "testpassword123"
}

class AreaAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.house_id = None
        
    def login(self):
        """Effettua il login per ottenere il token."""
        print("🔐 Login...")
        
        # Registra l'utente se non esiste
        try:
            response = self.session.post(f"{API_BASE}/auth/register", json=TEST_USER)
            if response.status_code == 201:
                print("   ✅ Utente registrato")
            elif response.status_code == 400 and "already exists" in response.text:
                print("   ℹ️ Utente già esistente")
            else:
                print(f"   ⚠️ Errore registrazione: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ Errore registrazione: {e}")
        
        # Login
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "username": TEST_USER["email"],
                "password": TEST_USER["password"]
            })
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                print("   ✅ Login effettuato")
                return True
            else:
                print(f"   ❌ Errore login: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Errore login: {e}")
            return False
    
    def create_test_house(self):
        """Crea una casa di test."""
        print("\n🏠 Creazione casa di test...")
        
        house_data = {
            "name": "Casa Test Aree API",
            "address": "Via Test API 123, Test City"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/houses/", json=house_data)
            if response.status_code == 201:
                house = response.json()
                self.house_id = house["id"]
                print(f"   ✅ Casa creata: {house['name']} (ID: {self.house_id})")
                return True
            else:
                print(f"   ❌ Errore creazione casa: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Errore creazione casa: {e}")
            return False
    
    def test_main_areas_crud(self):
        """Test CRUD per MainArea."""
        print("\n📋 TEST CRUD MAIN AREAS")
        print("=" * 50)
        
        # CREATE
        print("1. Creazione area principale...")
        main_area_data = {
            "name": "Zona Test API",
            "description": "Area principale creata tramite API test",
            "house_id": self.house_id
        }
        
        try:
            response = self.session.post(f"{API_BASE}/main-areas/", json=main_area_data)
            if response.status_code == 201:
                main_area = response.json()
                main_area_id = main_area["id"]
                print(f"   ✅ Area principale creata: {main_area['name']} (ID: {main_area_id})")
            else:
                print(f"   ❌ Errore creazione: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Errore creazione: {e}")
            return False
        
        # READ
        print("\n2. Lettura area principale...")
        try:
            response = self.session.get(f"{API_BASE}/main-areas/{main_area_id}")
            if response.status_code == 200:
                area = response.json()
                print(f"   ✅ Area letta: {area['name']}")
            else:
                print(f"   ❌ Errore lettura: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Errore lettura: {e}")
            return False
        
        # UPDATE
        print("\n3. Aggiornamento area principale...")
        update_data = {
            "description": "Descrizione aggiornata tramite API test"
        }
        
        try:
            response = self.session.put(f"{API_BASE}/main-areas/{main_area_id}", json=update_data)
            if response.status_code == 200:
                area = response.json()
                print(f"   ✅ Area aggiornata: {area['description']}")
            else:
                print(f"   ❌ Errore aggiornamento: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Errore aggiornamento: {e}")
            return False
        
        # LIST
        print("\n4. Lista aree principali...")
        try:
            response = self.session.get(f"{API_BASE}/main-areas/")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Trovate {len(data['items'])} aree principali")
            else:
                print(f"   ❌ Errore lista: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Errore lista: {e}")
            return False
        
        # DELETE
        print("\n5. Eliminazione area principale...")
        try:
            response = self.session.delete(f"{API_BASE}/main-areas/{main_area_id}")
            if response.status_code == 200:
                print("   ✅ Area principale eliminata")
            else:
                print(f"   ❌ Errore eliminazione: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Errore eliminazione: {e}")
            return False
        
        return True
    
    def test_node_areas_crud(self):
        """Test CRUD per NodeArea."""
        print("\n📋 TEST CRUD NODE AREAS")
        print("=" * 50)
        
        # CREATE
        print("1. Creazione area specifica...")
        node_area_data = {
            "name": "Cucina Test API",
            "category": "residential",
            "has_physical_tag": True,
            "house_id": self.house_id
        }
        
        try:
            response = self.session.post(f"{API_BASE}/node-areas/", json=node_area_data)
            if response.status_code == 201:
                node_area = response.json()
                node_area_id = node_area["id"]
                print(f"   ✅ Area specifica creata: {node_area['name']} (ID: {node_area_id})")
            else:
                print(f"   ❌ Errore creazione: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Errore creazione: {e}")
            return False
        
        # READ
        print("\n2. Lettura area specifica...")
        try:
            response = self.session.get(f"{API_BASE}/node-areas/{node_area_id}")
            if response.status_code == 200:
                area = response.json()
                print(f"   ✅ Area letta: {area['name']} ({area['category']})")
            else:
                print(f"   ❌ Errore lettura: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Errore lettura: {e}")
            return False
        
        # UPDATE
        print("\n3. Aggiornamento area specifica...")
        update_data = {
            "category": "technical",
            "has_physical_tag": False
        }
        
        try:
            response = self.session.put(f"{API_BASE}/node-areas/{node_area_id}", json=update_data)
            if response.status_code == 200:
                area = response.json()
                print(f"   ✅ Area aggiornata: {area['category']} (tag fisico: {area['has_physical_tag']})")
            else:
                print(f"   ❌ Errore aggiornamento: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Errore aggiornamento: {e}")
            return False
        
        # LIST
        print("\n4. Lista aree specifiche...")
        try:
            response = self.session.get(f"{API_BASE}/node-areas/")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Trovate {len(data['items'])} aree specifiche")
            else:
                print(f"   ❌ Errore lista: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Errore lista: {e}")
            return False
        
        # FILTER BY CATEGORY
        print("\n5. Filtro per categoria...")
        try:
            response = self.session.get(f"{API_BASE}/node-areas/?category=technical")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Trovate {len(data['items'])} aree tecniche")
            else:
                print(f"   ❌ Errore filtro: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Errore filtro: {e}")
            return False
        
        # CATEGORIES LIST
        print("\n6. Lista categorie...")
        try:
            response = self.session.get(f"{API_BASE}/node-areas/categories/list")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Categorie disponibili: {', '.join(data['categories'])}")
            else:
                print(f"   ❌ Errore categorie: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Errore categorie: {e}")
            return False
        
        # DELETE
        print("\n7. Eliminazione area specifica...")
        try:
            response = self.session.delete(f"{API_BASE}/node-areas/{node_area_id}")
            if response.status_code == 200:
                print("   ✅ Area specifica eliminata")
            else:
                print(f"   ❌ Errore eliminazione: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Errore eliminazione: {e}")
            return False
        
        return True
    
    def test_reports(self):
        """Test dei report."""
        print("\n📊 TEST REPORT")
        print("=" * 50)
        
        # Crea alcune aree per il test
        print("1. Creazione aree per test report...")
        
        # Main areas
        main_areas = [
            {"name": "Zona Giorno", "description": "Area principale per la vita quotidiana"},
            {"name": "Zona Impianti", "description": "Area tecnica per impianti"}
        ]
        
        created_main_areas = []
        for area_data in main_areas:
            area_data["house_id"] = self.house_id
            try:
                response = self.session.post(f"{API_BASE}/main-areas/", json=area_data)
                if response.status_code == 201:
                    area = response.json()
                    created_main_areas.append(area)
                    print(f"   ✅ Area principale creata: {area['name']}")
            except Exception as e:
                print(f"   ❌ Errore creazione area principale: {e}")
        
        # Node areas
        node_areas = [
            {"name": "Cucina", "category": "residential", "has_physical_tag": True},
            {"name": "Quadro Elettrico", "category": "technical", "has_physical_tag": True},
            {"name": "Ingresso", "category": "shared", "has_physical_tag": True}
        ]
        
        created_node_areas = []
        for area_data in node_areas:
            area_data["house_id"] = self.house_id
            try:
                response = self.session.post(f"{API_BASE}/node-areas/", json=area_data)
                if response.status_code == 201:
                    area = response.json()
                    created_node_areas.append(area)
                    print(f"   ✅ Area specifica creata: {area['name']}")
            except Exception as e:
                print(f"   ❌ Errore creazione area specifica: {e}")
        
        # Test summary report
        print("\n2. Test report riepilogo...")
        try:
            response = self.session.get(f"{API_BASE}/area-reports/summary/{self.house_id}")
            if response.status_code == 200:
                summary = response.json()
                print(f"   ✅ Report riepilogo: {summary['statistics']['main_areas_count']} aree principali, {summary['statistics']['nodes']['total']} nodi")
            else:
                print(f"   ❌ Errore report riepilogo: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Errore report riepilogo: {e}")
        
        # Test hierarchy report
        print("\n3. Test report gerarchia...")
        try:
            response = self.session.get(f"{API_BASE}/area-reports/hierarchy/{self.house_id}")
            if response.status_code == 200:
                hierarchy = response.json()
                print(f"   ✅ Report gerarchia: {len(hierarchy['main_areas'])} aree principali")
            else:
                print(f"   ❌ Errore report gerarchia: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Errore report gerarchia: {e}")
        
        # Test nodes by area
        print("\n4. Test nodi per area...")
        try:
            response = self.session.get(f"{API_BASE}/area-reports/nodes-by-area/{self.house_id}?area_type=main")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Nodi per area principale: {len(data['areas'])} aree")
            else:
                print(f"   ❌ Errore nodi per area: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Errore nodi per area: {e}")
        
        # Cleanup
        print("\n5. Cleanup aree di test...")
        for area in created_main_areas:
            try:
                self.session.delete(f"{API_BASE}/main-areas/{area['id']}")
            except:
                pass
        
        for area in created_node_areas:
            try:
                self.session.delete(f"{API_BASE}/node-areas/{area['id']}")
            except:
                pass
        
        print("   ✅ Cleanup completato")
        
        return True
    
    def run_all_tests(self):
        """Esegue tutti i test."""
        print("🧪 TEST API GESTIONE AREE")
        print("=" * 60)
        
        # Login
        if not self.login():
            print("❌ Impossibile effettuare il login. Test interrotti.")
            return False
        
        # Crea casa di test
        if not self.create_test_house():
            print("❌ Impossibile creare casa di test. Test interrotti.")
            return False
        
        # Esegui test
        tests = [
            ("CRUD Main Areas", self.test_main_areas_crud),
            ("CRUD Node Areas", self.test_node_areas_crud),
            ("Reports", self.test_reports)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    print(f"✅ {test_name}: SUCCESSO")
                else:
                    print(f"❌ {test_name}: FALLITO")
            except Exception as e:
                print(f"❌ {test_name}: ERRORE - {e}")
                results.append((test_name, False))
        
        # Riepilogo
        print("\n" + "="*60)
        print("📋 RIEPILOGO TEST")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nRisultato finale: {passed}/{total} test passati")
        
        if passed == total:
            print("🎉 TUTTI I TEST PASSATI!")
        else:
            print("⚠️ Alcuni test sono falliti")
        
        return passed == total

def main():
    """Funzione principale."""
    tester = AreaAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 API delle aree funzionanti correttamente!")
        print("📝 Prossimi step:")
        print("   1. Testare l'interfaccia HTML: frontend/area_management.html")
        print("   2. Integrare con il frontend principale")
        print("   3. Aggiungere validazioni avanzate")
        print("   4. Preparare per produzione")
    else:
        print("\n❌ Alcuni test sono falliti. Controllare i log per dettagli.")

if __name__ == "__main__":
    main() 