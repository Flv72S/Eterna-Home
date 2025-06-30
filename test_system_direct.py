#!/usr/bin/env python3
"""
Test diretto del sistema di monitoraggio Eterna Home
Versione semplificata senza dipendenze esterne
"""

import sys
import os
import time
import json
import requests
from typing import Dict, Any

# Aggiungi il path del progetto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_health_endpoint() -> Dict[str, Any]:
    """Test dell'endpoint /health"""
    print("🔍 Testando endpoint /health...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Database: {data.get('database', {}).get('status', 'unknown')}")
            print(f"   Redis: {data.get('redis', {}).get('status', 'unknown')}")
            print(f"   MinIO: {data.get('minio', {}).get('status', 'unknown')}")
            print("   ✅ Health check completato con successo")
            return {"status": "success", "data": data}
        else:
            print(f"   ❌ Health check fallito con status {response.status_code}")
            print(f"   Response: {response.text}")
            return {"status": "failed", "error": f"Status {response.status_code}"}
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossibile connettersi al server (server non avviato?)")
        return {"status": "failed", "error": "Connection refused"}
    except Exception as e:
        print(f"   ❌ Errore durante health check: {str(e)}")
        return {"status": "failed", "error": str(e)}

def test_ready_endpoint() -> Dict[str, Any]:
    """Test dell'endpoint /ready"""
    print("\n🔍 Testando endpoint /ready...")
    
    try:
        response = requests.get("http://localhost:8000/ready", timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Ready: {data.get('ready', False)}")
            print(f"   Checks: {data.get('checks', {})}")
            print("   ✅ Readiness check completato con successo")
            return {"status": "success", "data": data}
        else:
            print(f"   ❌ Readiness check fallito con status {response.status_code}")
            print(f"   Response: {response.text}")
            return {"status": "failed", "error": f"Status {response.status_code}"}
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossibile connettersi al server (server non avviato?)")
        return {"status": "failed", "error": "Connection refused"}
    except Exception as e:
        print(f"   ❌ Errore durante readiness check: {str(e)}")
        return {"status": "failed", "error": str(e)}

def test_metrics_endpoint() -> Dict[str, Any]:
    """Test dell'endpoint /metrics"""
    print("\n🔍 Testando endpoint /metrics...")
    
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=15)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
            print(f"   System Uptime: {data.get('system', {}).get('uptime_seconds', 0):.1f}s")
            print(f"   Memory Usage: {data.get('system', {}).get('memory_usage_mb', 0):.1f}MB")
            print(f"   CPU Usage: {data.get('system', {}).get('cpu_percent', 0):.1f}%")
            print("   ✅ Metrics collection completata con successo")
            return {"status": "success", "data": data}
        else:
            print(f"   ❌ Metrics collection fallita con status {response.status_code}")
            print(f"   Response: {response.text}")
            return {"status": "failed", "error": f"Status {response.status_code}"}
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossibile connettersi al server (server non avviato?)")
        return {"status": "failed", "error": "Connection refused"}
    except Exception as e:
        print(f"   ❌ Errore durante metrics collection: {str(e)}")
        return {"status": "failed", "error": str(e)}

def test_security_scanners() -> Dict[str, Any]:
    """Test degli scanner di sicurezza"""
    print("\n🔍 Testando scanner di sicurezza...")
    
    results = {}
    
    # Test OWASP ZAP
    print("   Testing OWASP ZAP...")
    zap_script = "scripts/security/owasp_zap_scan.ps1"
    if os.path.exists(zap_script):
        try:
            import subprocess
            # Usa PowerShell per eseguire lo script
            result = subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", "-File", zap_script
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("   ✅ OWASP ZAP scan completato")
                results["owasp_zap"] = "success"
            else:
                print(f"   ⚠️ OWASP ZAP scan fallito: {result.stderr}")
                results["owasp_zap"] = "failed"
        except Exception as e:
            print(f"   ❌ Errore OWASP ZAP: {str(e)}")
            results["owasp_zap"] = "error"
    else:
        print("   ⚠️ Script OWASP ZAP non trovato")
        results["owasp_zap"] = "not_found"
    
    # Test Nikto
    print("   Testing Nikto...")
    nikto_script = "scripts/security/nikto_scan.ps1"
    if os.path.exists(nikto_script):
        try:
            import subprocess
            # Usa PowerShell per eseguire lo script
            result = subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", "-File", nikto_script
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("   ✅ Nikto scan completato")
                results["nikto"] = "success"
            else:
                print(f"   ⚠️ Nikto scan fallito: {result.stderr}")
                results["nikto"] = "failed"
        except Exception as e:
            print(f"   ❌ Errore Nikto: {str(e)}")
            results["nikto"] = "error"
    else:
        print("   ⚠️ Script Nikto non trovato")
        results["nikto"] = "not_found"
    
    return results

def main():
    """Funzione principale di test"""
    print("🚀 AVVIO TEST SISTEMA DI MONITORAGGIO ETERNA HOME")
    print("=" * 60)
    
    # Verifica che il server sia in esecuzione
    print("📡 Verificando connessione al server...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print("   ✅ Server raggiungibile")
    except:
        print("   ❌ Server non raggiungibile. Avvia il server con:")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\n   Oppure continua per testare solo gli script di sicurezza...")
        choice = input("   Continuare? (y/n): ")
        if choice.lower() != 'y':
            return
    
    # Esegui test
    results = {
        "health": test_health_endpoint(),
        "ready": test_ready_endpoint(),
        "metrics": test_metrics_endpoint(),
        "security": test_security_scanners()
    }
    
    # Riepilogo risultati
    print("\n" + "=" * 60)
    print("📊 RIEPILOGO RISULTATI")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    for test_name, result in results.items():
        if test_name == "security":
            print(f"\n🔒 {test_name.upper()}:")
            for scanner, status in result.items():
                total_count += 1
                if status == "success":
                    success_count += 1
                    print(f"   ✅ {scanner}: {status}")
                else:
                    print(f"   ❌ {scanner}: {status}")
        else:
            total_count += 1
            if result["status"] == "success":
                success_count += 1
                print(f"✅ {test_name.upper()}: {result['status']}")
            else:
                print(f"❌ {test_name.upper()}: {result['status']} - {result.get('error', 'Unknown error')}")
    
    print(f"\n📈 RISULTATO FINALE: {success_count}/{total_count} test superati")
    
    if success_count == total_count:
        print("🎉 TUTTI I TEST SUPERATI! Sistema di monitoraggio funzionante.")
    else:
        print("⚠️ ALCUNI TEST FALLITI. Controlla i log per dettagli.")
    
    # Salva risultati
    with open("test_system_results.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "results": results,
            "summary": {
                "total": total_count,
                "success": success_count,
                "failed": total_count - success_count
            }
        }, f, indent=2)
    
    print(f"\n💾 Risultati salvati in: test_system_results.json")

if __name__ == "__main__":
    main() 