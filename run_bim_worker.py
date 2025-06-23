#!/usr/bin/env python3
"""
Script per avviare i worker Celery per la conversione BIM asincrona.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Aggiungi il path del progetto
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_redis_connection():
    """Verifica la connessione a Redis."""
    try:
        import redis
        from app.core.config import settings
        
        r = redis.from_url(settings.REDIS_URL or "redis://localhost:6379/0")
        r.ping()
        print("✅ Connessione Redis OK")
        return True
    except Exception as e:
        print(f"❌ Errore connessione Redis: {e}")
        print("💡 Assicurati che Redis sia in esecuzione:")
        print("   - Windows: redis-server")
        print("   - Docker: docker run -d -p 6379:6379 redis:alpine")
        return False

def start_celery_worker():
    """Avvia il worker Celery per la conversione BIM."""
    
    print("🚀 Avvio worker Celery per conversione BIM...")
    
    # Verifica connessione Redis
    if not check_redis_connection():
        return False
    
    # Configurazione worker
    worker_config = {
        "app": "app.core.celery_app:celery_app",
        "queues": "bim_conversion",
        "concurrency": 2,
        "loglevel": "info",
        "hostname": "bim-worker@%h",
        "max-tasks-per-child": 1000,
        "time-limit": 1800,  # 30 minuti
        "soft-time-limit": 1500,  # 25 minuti
    }
    
    # Costruisci comando Celery
    cmd = [
        sys.executable, "-m", "celery", "worker",
        "-A", worker_config["app"],
        "-Q", worker_config["queues"],
        "-c", str(worker_config["concurrency"]),
        "--loglevel", worker_config["loglevel"],
        "-n", worker_config["hostname"],
        "--max-tasks-per-child", str(worker_config["max-tasks-per-child"]),
        "--time-limit", str(worker_config["time-limit"]),
        "--soft-time-limit", str(worker_config["soft-time-limit"]),
    ]
    
    print(f"📋 Comando: {' '.join(cmd)}")
    print("🔄 Avvio worker...")
    
    try:
        # Avvia processo
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print(f"✅ Worker avviato con PID: {process.pid}")
        print("📝 Log del worker:")
        print("-" * 50)
        
        # Monitora output
        for line in process.stdout:
            print(line.rstrip())
            
            # Controlla se il processo è ancora attivo
            if process.poll() is not None:
                break
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Interruzione richiesta dall'utente")
        if process:
            process.terminate()
            process.wait()
        return True
        
    except Exception as e:
        print(f"❌ Errore durante l'avvio del worker: {e}")
        return False

def start_celery_beat():
    """Avvia Celery Beat per task schedulati (opzionale)."""
    
    print("🕐 Avvio Celery Beat per task schedulati...")
    
    cmd = [
        sys.executable, "-m", "celery", "beat",
        "-A", "app.core.celery_app:celery_app",
        "--loglevel", "info",
        "--scheduler", "celery.beat:PersistentScheduler",
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        print(f"✅ Celery Beat avviato con PID: {process.pid}")
        return process
        
    except Exception as e:
        print(f"❌ Errore durante l'avvio di Celery Beat: {e}")
        return None

def start_celery_monitor():
    """Avvia Celery Monitor per monitoraggio (opzionale)."""
    
    print("📊 Avvio Celery Monitor...")
    
    cmd = [
        sys.executable, "-m", "celery", "monitor",
        "-A", "app.core.celery_app:celery_app",
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        print(f"✅ Celery Monitor avviato con PID: {process.pid}")
        return process
        
    except Exception as e:
        print(f"❌ Errore durante l'avvio di Celery Monitor: {e}")
        return None

def main():
    """Funzione principale."""
    
    print("🏗️  Sistema di Conversione BIM Asincrona")
    print("=" * 50)
    
    # Menu di selezione
    print("\nSeleziona modalità di avvio:")
    print("1. Worker principale (conversione BIM)")
    print("2. Worker + Beat (con task schedulati)")
    print("3. Worker + Monitor (con monitoraggio)")
    print("4. Tutto (Worker + Beat + Monitor)")
    print("5. Solo Beat")
    print("6. Solo Monitor")
    
    try:
        choice = input("\nScelta (1-6): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Arrivederci!")
        return
    
    processes = []
    
    try:
        if choice == "1":
            start_celery_worker()
            
        elif choice == "2":
            beat_process = start_celery_beat()
            if beat_process:
                processes.append(beat_process)
            time.sleep(2)
            start_celery_worker()
            
        elif choice == "3":
            monitor_process = start_celery_monitor()
            if monitor_process:
                processes.append(monitor_process)
            time.sleep(2)
            start_celery_worker()
            
        elif choice == "4":
            beat_process = start_celery_beat()
            if beat_process:
                processes.append(beat_process)
            time.sleep(2)
            
            monitor_process = start_celery_monitor()
            if monitor_process:
                processes.append(monitor_process)
            time.sleep(2)
            
            start_celery_worker()
            
        elif choice == "5":
            start_celery_beat()
            
        elif choice == "6":
            start_celery_monitor()
            
        else:
            print("❌ Scelta non valida")
            return
            
    except KeyboardInterrupt:
        print("\n🛑 Interruzione richiesta dall'utente")
        
    finally:
        # Termina processi secondari
        for process in processes:
            if process and process.poll() is None:
                process.terminate()
                process.wait()
                print(f"✅ Processo {process.pid} terminato")

if __name__ == "__main__":
    main() 