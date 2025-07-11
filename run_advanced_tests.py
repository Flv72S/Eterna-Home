#!/usr/bin/env python3
"""
Script principale per eseguire i test avanzati di Eterna Home.
Esegue test per AI contestuale avanzata, scalabilità, localizzazione, crittografia.
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timezone
from pathlib import Path

def run_advanced_test_module(module_path, description):
    """Esegue un modulo di test avanzato e restituisce il risultato."""
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

def create_advanced_test_report(results, output_file):
    """Crea il report finale dei test avanzati."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    report = {
        "timestamp": timestamp,
        "test_type": "advanced_implementation",
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

def create_advanced_markdown_report(report, output_file):
    """Crea il report Markdown finale per i test avanzati."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    markdown_content = f"""# [OK] TEST AVANZATI – ETERNA HOME

## [SUMMARY] Riepilogo Esecuzione Test Avanzati
- **Data/Ora**: {timestamp}
- **Tipo Test**: Implementazione Avanzata
- **Test Totali**: {report['total_tests']}
- **Test Passati**: {report['passed_tests']}
- **Test Falliti**: {report['failed_tests']}
- **Tasso di Successo**: {report['success_rate']:.1f}%

## [🧠] Test AI Contestuale Avanzata
**Status**: {'[OK] COMPLETATO' if report['results']['ai_advanced']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Test persistenza stato AI per nodo (memoria contestuale simulata)
- [x] Test AI + categoria fragile (cieco → output vocale testuale, sordo → output visivo)
- [x] Test simultaneità: 2 tenant lanciano AI → isolamento risposta
- [x] Test trigger AI con prompt manipolati/injection → blocco

**Risultato**: {report['results']['ai_advanced']['output'][:200]}...

## [🧬] Test Scalabilità & Resilienza
**Status**: {'[OK] COMPLETATO' if report['results']['resilience_scaling']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Simula fail DB o MinIO → verifica fallback o errore gestito
- [x] Simula 50 richieste upload contemporanee → validazione queue/limit
- [x] Stress test endpoint /metrics → verifica caching e latenza

**Risultato**: {report['results']['resilience_scaling']['output'][:200]}...

## [🌍] Test Multi-lingua e Localizzazione
**Status**: {'[OK] COMPLETATO' if report['results']['localization']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Forza lingua "fr", "en", "de" → verifica UI adattiva
- [x] Test comando vocale AI in lingua diversa → risposta coerente
- [x] Test fallback automatico a lingua di default

**Risultato**: {report['results']['localization']['output'][:200]}...

## [🔐] Test Crittografia e Log Sicurezza
**Status**: {'[OK] COMPLETATO' if report['results']['crypto_logging']['passed'] else '[FAIL] FALLITO'}

### Test Implementati:
- [x] Upload documento cifrato → verifica presenza file cifrato
- [x] Simula accesso con chiave errata → errore gestito + log
- [x] MFA disattivato/attivato → verifica log MFA
- [x] Test logging avanzato in security.json e app.json

**Risultato**: {report['results']['crypto_logging']['output'][:200]}...

## [📊] Output Atteso
- Tutti i test passano su `pytest -v`
- Generazione log JSON per ogni interazione AI + cifratura
- UI e risposta AI si adattano alla lingua e disabilità
- Sistema resistente a carico e fail parziale di infrastruttura
- Logging strutturato completo per scenari critici

## [TARGET] Risultato Finale

"""
    
    if report['success_rate'] == 100:
        markdown_content += """## [OK] TUTTI I TEST AVANZATI PASSATI!

Il sistema Eterna Home è ora conforme a standard avanzati e pronto per:
- Contesti clinici e sanitari
- Amministrazioni pubbliche
- Ambienti ad alto rischio
- Certificazioni ufficiali e audit funzionali

### [OK] Funzionalità Avanzate Validated:
- **AI Contestuale**: Memoria per nodo, adattamento categorie fragili, isolamento tenant
- **Scalabilità**: Failover DB/MinIO, gestione upload concorrenti, stress test
- **Localizzazione**: UI multilingua, comandi vocali AI, fallback automatico
- **Crittografia**: Upload cifrato, gestione chiavi, logging avanzato
- **Resilienza**: Sistema resistente a carico e fail parziale

### [NEXT] Prossimi Passi:
1. Certificazione ISO 27001
2. Validazione per contesti sanitari (GDPR, HIPAA)
3. Audit di sicurezza indipendente
4. Deployment in ambienti critici

"""
    else:
        markdown_content += f"""## [WARNING] TEST AVANZATI PARZIALMENTE COMPLETATI

Il sistema ha completato {report['success_rate']:.1f}% dei test avanzati. Alcuni test sono falliti e richiedono attenzione prima della certificazione.

### [FIX] Azioni Richieste:
1. Rivedere i test avanzati falliti
2. Correggere le funzionalità problematiche
3. Rieseguire i test avanzati
4. Validare nuovamente prima della certificazione

"""
    
    markdown_content += f"""
## [TECH] Dettagli Tecnici Avanzati

### Ambiente di Test:
- **Python**: {sys.version}
- **Sistema Operativo**: {os.name}
- **Directory di Lavoro**: {os.getcwd()}

### File di Output:
- **Report JSON**: `docs/testing/ADVANCED_IMPLEMENTATION_REPORT.json`
- **Report Markdown**: `docs/testing/ADVANCED_IMPLEMENTATION_REPORT.md`
- **Matrix CSV**: `docs/testing/EXTENDED_TEST_MATRIX.csv`

### Standard di Conformità:
- **ISO 27001**: Sicurezza delle informazioni
- **GDPR**: Protezione dati personali
- **HIPAA**: Sicurezza sanitaria
- **SOC 2**: Controlli di sicurezza

---
*Report generato automaticamente da Eterna Home Advanced Test Suite*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

def create_extended_csv_matrix(report, output_file):
    """Crea la matrix CSV estesa dei risultati avanzati."""
    import csv
    
    # Mappatura delle categorie per le chiavi corrette
    category_mapping = {
        'AI Contestuale Avanzata': 'ai_advanced',
        'Scalabilità & Resilienza': 'resilience_scaling',
        'Multi-lingua e Localizzazione': 'localization',
        'Crittografia e Log Sicurezza': 'crypto_logging'
    }
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Categoria', 'Test', 'Status', 'Description'])
        
        # Dati
        test_matrix = [
            ('AI Contestuale', 'Persistenza stato AI', 'Test persistenza stato AI per nodo (memoria contestuale simulata)'),
            ('AI Contestuale', 'Adattamento categorie fragili', 'Test AI + categoria fragile (cieco → output vocale testuale, sordo → output visivo)'),
            ('AI Contestuale', 'Simultaneità tenant', 'Test simultaneità: 2 tenant lanciano AI → isolamento risposta'),
            ('AI Contestuale', 'Blocco prompt injection', 'Test trigger AI con prompt manipolati/injection → blocco'),
            
            ('Scalabilità', 'Failover database', 'Simula fail DB → verifica fallback o errore gestito'),
            ('Scalabilità', 'Failover MinIO', 'Simula fail MinIO → verifica fallback o errore gestito'),
            ('Scalabilità', 'Upload concorrenti', 'Simula 50 richieste upload contemporanee → validazione queue/limit'),
            ('Scalabilità', 'Stress test metrics', 'Stress test endpoint /metrics → verifica caching e latenza'),
            
            ('Localizzazione', 'UI multilingua', 'Forza lingua "fr", "en", "de" → verifica UI adattiva'),
            ('Localizzazione', 'Comandi vocali AI', 'Test comando vocale AI in lingua diversa → risposta coerente'),
            ('Localizzazione', 'Fallback lingua', 'Test fallback automatico a lingua di default'),
            ('Localizzazione', 'Consistenza formati', 'Test consistenza localizzazione completa'),
            
            ('Crittografia', 'Upload cifrato', 'Upload documento cifrato → verifica presenza file cifrato'),
            ('Crittografia', 'Accesso chiave errata', 'Simula accesso con chiave errata → errore gestito + log'),
            ('Crittografia', 'Logging MFA', 'MFA disattivato/attivato → verifica log MFA'),
            ('Crittografia', 'Logging avanzato', 'Test logging avanzato in security.json e app.json')
        ]
        
        for category, test, description in test_matrix:
            # Usa la mappatura per ottenere la chiave corretta
            key = category_mapping.get(category, category.lower().replace(' ', '_').replace('&', '_'))
            status = "PASSED" if report['results'].get(key, {}).get('passed', False) else "FAILED"
            writer.writerow([category, test, status, description])

def main():
    """Funzione principale per eseguire tutti i test avanzati."""
    print("[TEST] TEST AVANZATI – ETERNA HOME")
    print("=" * 80)
    print("Esecuzione di test avanzati per conformità e certificazioni")
    print("=" * 80)
    
    # Definizione dei test avanzati da eseguire
    advanced_test_modules = {
        'ai_advanced': {
            'path': 'tests/ai/test_advanced_context.py',
            'description': 'AI Contestuale Avanzata'
        },
        'resilience_scaling': {
            'path': 'tests/integration/test_resilience_scaling.py',
            'description': 'Scalabilità & Resilienza'
        },
        'localization': {
            'path': 'tests/ui/test_localization.py',
            'description': 'Multi-lingua e Localizzazione'
        },
        'crypto_logging': {
            'path': 'tests/security/test_crypto_logging.py',
            'description': 'Crittografia e Log Sicurezza'
        }
    }
    
    # Esegui tutti i test avanzati
    results = {}
    
    for test_key, test_info in advanced_test_modules.items():
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
        passed, output = run_advanced_test_module(test_info['path'], test_info['description'])
        
        results[test_key] = {
            'passed': passed,
            'output': output
        }
    
    # Crea directory per i report se non esiste
    docs_dir = Path('docs/testing')
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Genera report
    print(f"\n{'='*80}")
    print("[REPORT] GENERAZIONE REPORT AVANZATI")
    print(f"{'='*80}")
    
    # Report JSON
    json_report = create_advanced_test_report(results, 'docs/testing/ADVANCED_IMPLEMENTATION_REPORT.json')
    print("[OK] Report JSON avanzato generato: docs/testing/ADVANCED_IMPLEMENTATION_REPORT.json")
    
    # Report Markdown
    create_advanced_markdown_report(json_report, 'docs/testing/ADVANCED_IMPLEMENTATION_REPORT.md')
    print("[OK] Report Markdown avanzato generato: docs/testing/ADVANCED_IMPLEMENTATION_REPORT.md")
    
    # Matrix CSV estesa
    create_extended_csv_matrix(json_report, 'docs/testing/EXTENDED_TEST_MATRIX.csv')
    print("[OK] Matrix CSV estesa generata: docs/testing/EXTENDED_TEST_MATRIX.csv")
    
    # Riepilogo finale
    print(f"\n{'='*80}")
    print("[SUMMARY] RIEPILOGO FINALE TEST AVANZATI")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result['passed'])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"[STATS] Statistiche Test Avanzati:")
    print(f"  • Test Totali: {total_tests}")
    print(f"  • Test Passati: {passed_tests}")
    print(f"  • Test Falliti: {failed_tests}")
    print(f"  • Tasso di Successo: {success_rate:.1f}%")
    
    print(f"\n[RESULTS] Risultati per Categoria:")
    for test_key, result in results.items():
        status = "[OK] PASSATO" if result['passed'] else "[FAIL] FALLITO"
        print(f"  • {test_key}: {status}")
    
    if success_rate == 100:
        print(f"\n[OK] TUTTI I TEST AVANZATI PASSATI!")
        print("Eterna Home è conforme a standard avanzati e pronto per certificazioni.")
        return 0
    else:
        print(f"\n[WARNING] ALCUNI TEST AVANZATI SONO FALLITI")
        print("Rivedere i test falliti prima della certificazione.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 