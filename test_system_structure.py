#!/usr/bin/env python3
"""
Test della struttura del sistema di monitoraggio Eterna Home
Verifica la presenza di file e configurazioni senza dipendenze esterne
"""

import os
import sys
import json
import time
from typing import Dict, Any, List

def test_file_structure() -> Dict[str, Any]:
    """Test della struttura dei file del sistema di monitoraggio"""
    print("🔍 Testando struttura dei file...")
    
    required_files = [
        "app/routers/system.py",
        "app/core/deps.py", 
        "app/core/config.py",
        "app/core/redis.py",
        "app/services/minio_service.py",
        "app/core/logging_multi_tenant.py",
        "scripts/security/owasp_zap_scan.ps1",
        "scripts/security/nikto_scan.ps1",
        "docs/security/",
        "test_system_direct.py"
    ]
    
    results = {"found": [], "missing": []}
    
    for file_path in required_files:
        if os.path.exists(file_path):
            results["found"].append(file_path)
            print(f"   ✅ {file_path}")
        else:
            results["missing"].append(file_path)
            print(f"   ❌ {file_path}")
    
    success = len(results["missing"]) == 0
    return {
        "status": "success" if success else "failed",
        "found_count": len(results["found"]),
        "missing_count": len(results["missing"]),
        "missing_files": results["missing"]
    }

def test_system_router_content() -> Dict[str, Any]:
    """Test del contenuto del router system"""
    print("\n🔍 Testando contenuto del router system...")
    
    system_router = "app/routers/system.py"
    if not os.path.exists(system_router):
        return {"status": "failed", "error": "Router system.py non trovato"}
    
    try:
        with open(system_router, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_endpoints = [
            "@router.get(\"/health\")",
            "@router.get(\"/ready\")", 
            "@router.get(\"/metrics\""
        ]
        
        found_endpoints = []
        for endpoint in required_endpoints:
            if endpoint in content:
                found_endpoints.append(endpoint)
                print(f"   ✅ {endpoint}")
            else:
                print(f"   ❌ {endpoint}")
        
        success = len(found_endpoints) == len(required_endpoints)
        return {
            "status": "success" if success else "failed",
            "found_endpoints": found_endpoints,
            "total_endpoints": len(required_endpoints)
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def test_security_scripts() -> Dict[str, Any]:
    """Test degli script di sicurezza"""
    print("\n🔍 Testando script di sicurezza...")
    
    scripts = {
        "owasp_zap": "scripts/security/owasp_zap_scan.ps1",
        "nikto": "scripts/security/nikto_scan.ps1"
    }
    
    results = {}
    for name, path in scripts.items():
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verifica che sia uno script PowerShell
                if content.startswith("#!/usr/bin/env pwsh") or "<#" in content:
                    print(f"   ✅ {name}: Script PowerShell valido")
                    results[name] = "valid"
                else:
                    print(f"   ⚠️ {name}: Formato non riconosciuto")
                    results[name] = "invalid_format"
            except Exception as e:
                print(f"   ❌ {name}: Errore lettura - {str(e)}")
                results[name] = "error"
        else:
            print(f"   ❌ {name}: File non trovato")
            results[name] = "not_found"
    
    success = all(status == "valid" for status in results.values())
    return {
        "status": "success" if success else "failed",
        "scripts": results
    }

def test_dependencies() -> Dict[str, Any]:
    """Test delle dipendenze Python"""
    print("\n🔍 Testando dipendenze Python...")
    
    required_modules = [
        "fastapi",
        "sqlmodel", 
        "psutil",
        "redis",
        "requests"
    ]
    
    results = {}
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
            results[module] = "available"
        except ImportError:
            print(f"   ❌ {module}")
            results[module] = "missing"
    
    success = all(status == "available" for status in results.values())
    return {
        "status": "success" if success else "failed",
        "modules": results
    }

def test_configuration() -> Dict[str, Any]:
    """Test della configurazione"""
    print("\n🔍 Testando configurazione...")
    
    config_file = "app/core/config.py"
    if not os.path.exists(config_file):
        return {"status": "failed", "error": "File di configurazione non trovato"}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_settings = [
            "DATABASE_URL",
            "REDIS_URL", 
            "SECRET_KEY",
            "MINIO_ENDPOINT"
        ]
        
        found_settings = []
        for setting in required_settings:
            if setting in content:
                found_settings.append(setting)
                print(f"   ✅ {setting}")
            else:
                print(f"   ❌ {setting}")
        
        success = len(found_settings) == len(required_settings)
        return {
            "status": "success" if success else "failed",
            "found_settings": found_settings,
            "total_settings": len(required_settings)
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def main():
    """Funzione principale di test"""
    print("🚀 TEST STRUTTURA SISTEMA DI MONITORAGGIO ETERNA HOME")
    print("=" * 60)
    
    # Esegui test
    results = {
        "file_structure": test_file_structure(),
        "system_router": test_system_router_content(),
        "security_scripts": test_security_scripts(),
        "dependencies": test_dependencies(),
        "configuration": test_configuration()
    }
    
    # Riepilogo risultati
    print("\n" + "=" * 60)
    print("📊 RIEPILOGO RISULTATI")
    print("=" * 60)
    
    success_count = 0
    total_count = len(results)
    
    for test_name, result in results.items():
        if result["status"] == "success":
            success_count += 1
            print(f"✅ {test_name.upper()}: {result['status']}")
        else:
            print(f"❌ {test_name.upper()}: {result['status']}")
            if "error" in result:
                print(f"   Errore: {result['error']}")
    
    print(f"\n📈 RISULTATO FINALE: {success_count}/{total_count} test superati")
    
    if success_count == total_count:
        print("🎉 STRUTTURA COMPLETA! Sistema di monitoraggio configurato correttamente.")
        print("\n💡 Prossimi passi:")
        print("   1. Avvia il server: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("   2. Esegui test completi: python test_system_direct.py")
        print("   3. Installa OWASP ZAP e Nikto per test di sicurezza completi")
    else:
        print("⚠️ ALCUNI TEST FALLITI. Controlla i file mancanti o le configurazioni.")
    
    # Salva risultati
    with open("test_structure_results.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "results": results,
            "summary": {
                "total": total_count,
                "success": success_count,
                "failed": total_count - success_count
            }
        }, f, indent=2)
    
    print(f"\n💾 Risultati salvati in: test_structure_results.json")

if __name__ == "__main__":
    main() 