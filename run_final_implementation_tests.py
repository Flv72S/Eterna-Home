#!/usr/bin/env python3
"""
Script principale per eseguire i test implementativi finali di Eterna Home.
Esegue tutti i micro-step A-F per completare la validazione funzionale.
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timezone
from pathlib import Path

def run_test_module(module_path, description):
    """Esegue un modulo di test e restituisce il risultato."""
    print(f"\n{'='*80}")
    print(f"[TEST] {description}")
    print(f"{'='*80}")
    
    try:
        # Esegui il test come modulo Python
        result = subprocess.run(
            [sys.executable, module_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minuti di timeout
        )
        
        if result.returncode == 0:
            print("[OK] TEST PASSATO")
            return True, result.stdout
        else:
            print("[FAIL] TEST FALLITO")
            print(f"Errore: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] TEST TIMEOUT")
        return False, "Timeout dopo 5 minuti"
    except Exception as e:
        print(f"[ERROR] ERRORE ESEGUENDO TEST: {e}")
        return False, str(e)

def create_test_report(results, output_file):
    """Crea il report finale dei test."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    report = {
        "timestamp": timestamp,
        "total_tests": len(results),
        "passed_tests": sum(1 for result in results.values() if result["passed"]),
        "failed_tests": sum(1 for result in results.values() if not result["passed"]),
        "success_rate": 0,
        "results": results
    }
    
    if report["total_tests"] > 0:
        report["success_rate"] = (report["passed_tests"] / report["total_tests"]) * 100
    
    # Salva report JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report

def create_markdown_report(report, output_file):
    """Crea il report Markdown finale."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    markdown_content = f"""# [OK] TEST IMPLEMENTATIVI FINALI – ETERNA HOME

## [SUMMARY] Riepilogo Esecuzione
- **Data/Ora**: {timestamp}
- **Test Totali**: {report['total_tests']}
- **Test Passati**: {report['passed_tests']}
- **Test Falliti**: {report['failed_tests']}
- **Tasso di Successo**: {report['success_rate']:.1f}%

## [A] Micro-step A – Estensioni per Categorie Fragili
**Status**: {'[OK] COMPLETATO' if report['results']['accessibility']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Test UI vocale con fallback per utenti ciechi
- [x] Test input manuale e feedback visivo per utenti sordi
- [x] Test screen reader e markup ARIA sulle pagine
- [x] Test riduzione movimenti per utenti con epilessia
- [x] Test accesso vocale protetto per utenti cognitivamente fragili

**Risultato**: {report['results']['accessibility']['output'][:200]}...

## [B] Micro-step B – Gestione Case e Aree
**Status**: {'[OK] COMPLETATO' if report['results']['house_area']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Test CRUD aree (nodi ambientali)
- [x] Test associazione nodo → house
- [x] Test protezione RBAC/PBAC tra case
- [x] Test cambio "casa attiva" → filtra nodi corretti

**Risultato**: {report['results']['house_area']['output'][:200]}...

## [C] Micro-step C – Gestione Nodi & IoT
**Status**: {'[OK] COMPLETATO' if report['results']['nodes_iot']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Test associazione attivatori NFC/BLE → nodo
- [x] Test trigger da attivatore → verifica mappatura
- [x] Test ricezione evento da sensore (mock IoT)
- [x] Test logging attivazioni

**Risultato**: {report['results']['nodes_iot']['output'][:200]}...

## [D] Micro-step D – Interazioni AI Contestuali
**Status**: {'[OK] COMPLETATO' if report['results']['ai_contextual']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Test POST /voice/commands con prompt e response
- [x] Verifica logging AI per tenant_id e house_id
- [x] Test isolamento prompt AI tra tenant
- [x] Test blocco prompt sospetto/injection

**Risultato**: {report['results']['ai_contextual']['output'][:200]}...

## [E] Micro-step E – Aree Sicure
**Status**: {'[OK] COMPLETATO' if report['results']['secure_area']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Test accesso a route protette da permessi elevati
- [x] Test logging eventi security.json
- [x] Test blocco accesso non autorizzato (403)
- [x] Test trigger eventi critici (upload, AI, configurazioni)

**Risultato**: {report['results']['secure_area']['output'][:200]}...

## [F] Micro-step F – Pannello Amministrativo (UI)
**Status**: {'[OK] COMPLETATO' if report['results']['admin_panel']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Test UI utenti → modifica ruoli, MFA
- [x] Test visualizzazione utenti/case/permessi
- [x] Test assegnazione ruolo multi-house
- [x] Test visualizzazione log su admin

**Risultato**: {report['results']['admin_panel']['output'][:200]}...

## [TARGET] Risultato Finale

"""
    
    if report['success_rate'] == 100:
        markdown_content += """## [OK] TUTTI I TEST PASSATI!

Il sistema Eterna Home è pronto per il deployment in produzione. Tutte le funzionalità chiave sono state validate e testate con successo.

### [OK] Funzionalità Validated:
- **Accessibilità**: Supporto completo per utenti con disabilità
- **Gestione Multi-House**: Isolamento e gestione case multiple
- **IoT Integration**: Gestione nodi e attivatori fisici
- **AI Contestuale**: Interazioni AI sicure e isolate
- **Sicurezza**: Aree protette e logging completo
- **Amministrazione**: Pannello admin completo e funzionale

### [NEXT] Prossimi Passi:
1. Deployment in ambiente di staging
2. Test di carico e performance
3. Validazione con utenti reali
4. Go-live in produzione

"""
    else:
        markdown_content += f"""## [WARNING] TEST PARZIALMENTE COMPLETATI

Il sistema ha completato {report['success_rate']:.1f}% dei test. Alcuni test sono falliti e richiedono attenzione prima del deployment.

### [FIX] Azioni Richieste:
1. Rivedere i test falliti
2. Correggere le funzionalità problematiche
3. Rieseguire i test
4. Validare nuovamente prima del deployment

"""
    
    markdown_content += f"""
## [TECH] Dettagli Tecnici

### Ambiente di Test:
- **Python**: {sys.version}
- **Sistema Operativo**: {os.name}
- **Directory di Lavoro**: {os.getcwd()}

### File di Output:
- **Report JSON**: `docs/testing/FINAL_IMPLEMENTATION_REPORT.json`
- **Report Markdown**: `docs/testing/FINAL_IMPLEMENTATION_REPORT.md`
- **Matrix CSV**: `docs/testing/FINAL_IMPLEMENTATION_MATRIX.csv`

---
*Report generato automaticamente da Eterna Home Test Suite*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

def create_csv_matrix(report, output_file):
    """Crea la matrix CSV dei risultati."""
    import csv
    
    # Mappatura delle categorie per le chiavi corrette
    category_mapping = {
        'Estensioni per Categorie Fragili': 'accessibility',
        'Gestione Case e Aree': 'house_area',
        'Gestione Nodi & IoT': 'nodes_iot',
        'Interazioni AI Contestuali': 'ai_contextual',
        'Aree Sicure': 'secure_area',
        'Pannello Amministrativo (UI)': 'admin_panel'
    }
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Micro-Step', 'Test', 'Status', 'Description'])
        
        # Dati
        test_matrix = [
            ('A', 'Accessibilità', 'UI vocale fallback', 'Test UI vocale con fallback per utenti ciechi'),
            ('A', 'Accessibilità', 'Input manuale feedback', 'Test input manuale e feedback visivo per utenti sordi'),
            ('A', 'Accessibilità', 'Screen reader ARIA', 'Test screen reader e markup ARIA sulle pagine'),
            ('A', 'Accessibilità', 'Riduzione movimenti', 'Test riduzione movimenti per utenti con epilessia'),
            ('A', 'Accessibilità', 'Accesso vocale protetto', 'Test accesso vocale protetto per utenti cognitivamente fragili'),
            
            ('B', 'Gestione Case e Aree', 'CRUD aree', 'Test CRUD aree (nodi ambientali)'),
            ('B', 'Gestione Case e Aree', 'Associazione nodo-house', 'Test associazione nodo → house'),
            ('B', 'Gestione Case e Aree', 'Protezione RBAC/PBAC', 'Test protezione RBAC/PBAC tra case'),
            ('B', 'Gestione Case e Aree', 'Cambio casa attiva', 'Test cambio "casa attiva" → filtra nodi corretti'),
            
            ('C', 'Gestione Nodi & IoT', 'Associazione attivatori', 'Test associazione attivatori NFC/BLE → nodo'),
            ('C', 'Gestione Nodi & IoT', 'Trigger attivatore', 'Test trigger da attivatore → verifica mappatura'),
            ('C', 'Gestione Nodi & IoT', 'Eventi sensori', 'Test ricezione evento da sensore (mock IoT)'),
            ('C', 'Gestione Nodi & IoT', 'Logging attivazioni', 'Test logging attivazioni'),
            
            ('D', 'Interazioni AI Contestuali', 'Voice commands', 'Test POST /voice/commands con prompt e response'),
            ('D', 'Interazioni AI Contestuali', 'Logging AI tenant', 'Verifica logging AI per tenant_id e house_id'),
            ('D', 'Interazioni AI Contestuali', 'Isolamento prompt', 'Test isolamento prompt AI tra tenant'),
            ('D', 'Interazioni AI Contestuali', 'Blocco prompt sospetto', 'Test blocco prompt sospetto/injection'),
            
            ('E', 'Aree Sicure', 'Route protette', 'Test accesso a route protette da permessi elevati'),
            ('E', 'Aree Sicure', 'Logging security', 'Test logging eventi security.json'),
            ('E', 'Aree Sicure', 'Blocco accesso', 'Test blocco accesso non autorizzato (403)'),
            ('E', 'Aree Sicure', 'Eventi critici', 'Test trigger eventi critici (upload, AI, configurazioni)'),
            
            ('F', 'Pannello Amministrativo', 'UI utenti', 'Test UI utenti → modifica ruoli, MFA'),
            ('F', 'Pannello Amministrativo', 'Visualizzazione permessi', 'Test visualizzazione utenti/case/permessi'),
            ('F', 'Pannello Amministrativo', 'Assegnazione ruoli', 'Test assegnazione ruolo multi-house'),
            ('F', 'Pannello Amministrativo', 'Visualizzazione log', 'Test visualizzazione log su admin')
        ]
        
        for step, category, test, description in test_matrix:
            # Usa la mappatura per ottenere la chiave corretta
            key = category_mapping.get(category, category.lower().replace(' ', '_').replace('&', '_'))
            status = "PASSED" if report['results'].get(key, {}).get('passed', False) else "FAILED"
            writer.writerow([step, test, status, description])

def main():
    """Funzione principale per eseguire tutti i test."""
    print("[TEST] TEST IMPLEMENTATIVI FINALI – ETERNA HOME")
    print("=" * 80)
    print("Esecuzione di tutti i micro-step A-F per completare la validazione funzionale")
    print("=" * 80)
    
    # Definizione dei test da eseguire
    test_modules = {
        'accessibility': {
            'path': 'tests/accessibility/test_voice_ui_fallback.py',
            'description': 'Micro-step A – Estensioni per Categorie Fragili'
        },
        'house_area': {
            'path': 'tests/routers/test_house_area.py',
            'description': 'Micro-step B – Gestione Case e Aree'
        },
        'nodes_iot': {
            'path': 'tests/routers/test_nodes_iot.py',
            'description': 'Micro-step C – Gestione Nodi & IoT'
        },
        'ai_contextual': {
            'path': 'tests/ai/test_voice_ai_contextual.py',
            'description': 'Micro-step D – Interazioni AI Contestuali'
        },
        'secure_area': {
            'path': 'tests/routers/test_secure_area.py',
            'description': 'Micro-step E – Aree Sicure'
        },
        'admin_panel': {
            'path': 'tests/ui/test_admin_panel.py',
            'description': 'Micro-step F – Pannello Amministrativo (UI)'
        }
    }
    
    # Esegui tutti i test
    results = {}
    
    for test_key, test_info in test_modules.items():
        print(f"\n{'='*80}")
        print(f"[TEST] {test_info['description']}")
        print(f"{'='*80}")
        
        # Verifica che il file esista
        if not os.path.exists(test_info['path']):
            print(f"[FAIL] File di test non trovato: {test_info['path']}")
            results[test_key] = {
                'passed': False,
                'output': f"File non trovato: {test_info['path']}"
            }
            continue
        
        # Esegui il test
        passed, output = run_test_module(test_info['path'], test_info['description'])
        
        results[test_key] = {
            'passed': passed,
            'output': output
        }
    
    # Crea directory per i report se non esiste
    docs_dir = Path('docs/testing')
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Genera report
    print(f"\n{'='*80}")
    print("[REPORT] GENERAZIONE REPORT FINALI")
    print(f"{'='*80}")
    
    # Report JSON
    json_report = create_test_report(results, 'docs/testing/FINAL_IMPLEMENTATION_REPORT.json')
    print("[OK] Report JSON generato: docs/testing/FINAL_IMPLEMENTATION_REPORT.json")
    
    # Report Markdown
    create_markdown_report(json_report, 'docs/testing/FINAL_IMPLEMENTATION_REPORT.md')
    print("[OK] Report Markdown generato: docs/testing/FINAL_IMPLEMENTATION_REPORT.md")
    
    # Matrix CSV
    create_csv_matrix(json_report, 'docs/testing/FINAL_IMPLEMENTATION_MATRIX.csv')
    print("[OK] Matrix CSV generata: docs/testing/FINAL_IMPLEMENTATION_MATRIX.csv")
    
    # Riepilogo finale
    print(f"\n{'='*80}")
    print("[SUMMARY] RIEPILOGO FINALE")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result['passed'])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"[STATS] Statistiche:")
    print(f"  • Test Totali: {total_tests}")
    print(f"  • Test Passati: {passed_tests}")
    print(f"  • Test Falliti: {failed_tests}")
    print(f"  • Tasso di Successo: {success_rate:.1f}%")
    
    print(f"\n[RESULTS] Risultati per Micro-step:")
    for test_key, result in results.items():
        status = "[OK] PASSATO" if result['passed'] else "[FAIL] FALLITO"
        print(f"  • {test_key}: {status}")
    
    if success_rate == 100:
        print(f"\n[OK] TUTTI I TEST PASSATI!")
        print("Il sistema Eterna Home è pronto per il deployment in produzione.")
        return 0
    else:
        print(f"\n[WARNING] ALCUNI TEST SONO FALLITI")
        print("Rivedere i test falliti prima del deployment.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 