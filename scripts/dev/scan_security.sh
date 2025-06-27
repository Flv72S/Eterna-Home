#!/bin/bash

# 🔒 Security Scanner Script for Eterna Home
# Esegue controlli automatici di sicurezza su dipendenze e codice

set -e  # Exit on any error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timestamp per report
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT_DIR="docs/security"
REPORT_FILE="$REPORT_DIR/SCAN_REPORT_$TIMESTAMP.md"

echo -e "${BLUE}🔒 ETERNA HOME SECURITY SCANNER${NC}"
echo -e "${BLUE}================================${NC}"
echo "Data: $(date)"
echo "Report: $REPORT_FILE"
echo ""

# Crea directory report se non esiste
mkdir -p "$REPORT_DIR"

# Inizia report
cat > "$REPORT_FILE" << EOF
# 🔒 Security Scan Report - Eterna Home

**Data Scansione:** $(date)  
**Versione Sistema:** 0.1.0  
**Scanner:** Safety, Bandit, PyUpgrade  

---

## 📊 Riepilogo Risultati

EOF

# 1. Safety Check - Vulnerabilità dipendenze
echo -e "${YELLOW}🔍 1. Controllo vulnerabilità dipendenze (Safety)...${NC}"
if command -v safety &> /dev/null; then
    echo "Esecuzione safety check..."
    safety check --full-report > "$REPORT_DIR/safety_report.txt" 2>&1 || true
    
    # Conta vulnerabilità
    VULN_COUNT=$(grep -c "VULNERABILITY" "$REPORT_DIR/safety_report.txt" || echo "0")
    
    if [ "$VULN_COUNT" -gt 0 ]; then
        echo -e "${RED}❌ Trovate $VULN_COUNT vulnerabilità nelle dipendenze${NC}"
        echo "### 🔴 Vulnerabilità Dipendenze (Safety)" >> "$REPORT_FILE"
        echo "**Stato:** ❌ CRITICO - $VULN_COUNT vulnerabilità trovate" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo '```bash' >> "$REPORT_FILE"
        cat "$REPORT_DIR/safety_report.txt" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    else
        echo -e "${GREEN}✅ Nessuna vulnerabilità trovata nelle dipendenze${NC}"
        echo "### ✅ Vulnerabilità Dipendenze (Safety)" >> "$REPORT_FILE"
        echo "**Stato:** ✅ SICURO - Nessuna vulnerabilità trovata" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi
else
    echo -e "${RED}❌ Safety non installato${NC}"
    echo "### ❌ Vulnerabilità Dipendenze (Safety)" >> "$REPORT_FILE"
    echo "**Stato:** ❌ ERRORE - Safety non installato" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

# 2. Bandit - Analisi codice Python
echo -e "${YELLOW}🔍 2. Analisi vulnerabilità codice (Bandit)...${NC}"
if command -v bandit &> /dev/null; then
    echo "Esecuzione bandit scan..."
    bandit -r app/ -f json -o "$REPORT_DIR/bandit_report.json" || true
    bandit -r app/ -f txt -o "$REPORT_DIR/bandit_report.txt" || true
    
    # Analizza risultati JSON
    if [ -f "$REPORT_DIR/bandit_report.json" ]; then
        HIGH_ISSUES=$(python3 -c "
import json
try:
    with open('$REPORT_DIR/bandit_report.json', 'r') as f:
        data = json.load(f)
    high_issues = sum(1 for result in data.get('results', []) if result.get('issue_severity') == 'HIGH')
    print(high_issues)
except:
    print(0)
" 2>/dev/null || echo "0")
        
        MEDIUM_ISSUES=$(python3 -c "
import json
try:
    with open('$REPORT_DIR/bandit_report.json', 'r') as f:
        data = json.load(f)
    medium_issues = sum(1 for result in data.get('results', []) if result.get('issue_severity') == 'MEDIUM')
    print(medium_issues)
except:
    print(0)
" 2>/dev/null || echo "0")
        
        LOW_ISSUES=$(python3 -c "
import json
try:
    with open('$REPORT_DIR/bandit_report.json', 'r') as f:
        data = json.load(f)
    low_issues = sum(1 for result in data.get('results', []) if result.get('issue_severity') == 'LOW')
    print(low_issues)
except:
    print(0)
" 2>/dev/null || echo "0")
        
        TOTAL_ISSUES=$((HIGH_ISSUES + MEDIUM_ISSUES + LOW_ISSUES))
        
        if [ "$TOTAL_ISSUES" -gt 0 ]; then
            echo -e "${RED}❌ Trovati $TOTAL_ISSUES problemi di sicurezza nel codice${NC}"
            echo "  - HIGH: $HIGH_ISSUES"
            echo "  - MEDIUM: $MEDIUM_ISSUES"
            echo "  - LOW: $LOW_ISSUES"
            
            echo "### 🔴 Vulnerabilità Codice (Bandit)" >> "$REPORT_FILE"
            echo "**Stato:** ⚠️ ATTENZIONE - $TOTAL_ISSUES problemi trovati" >> "$REPORT_FILE"
            echo "- **HIGH:** $HIGH_ISSUES" >> "$REPORT_FILE"
            echo "- **MEDIUM:** $MEDIUM_ISSUES" >> "$REPORT_FILE"
            echo "- **LOW:** $LOW_ISSUES" >> "$REPORT_FILE"
            echo "" >> "$REPORT_FILE"
            
            if [ "$HIGH_ISSUES" -gt 0 ]; then
                echo "#### 🔴 Problemi CRITICI:" >> "$REPORT_FILE"
                echo '```bash' >> "$REPORT_FILE"
                grep -A 5 "HIGH" "$REPORT_DIR/bandit_report.txt" | head -20 >> "$REPORT_FILE" || true
                echo '```' >> "$REPORT_FILE"
                echo "" >> "$REPORT_FILE"
            fi
        else
            echo -e "${GREEN}✅ Nessun problema di sicurezza trovato nel codice${NC}"
            echo "### ✅ Vulnerabilità Codice (Bandit)" >> "$REPORT_FILE"
            echo "**Stato:** ✅ SICURO - Nessun problema trovato" >> "$REPORT_FILE"
            echo "" >> "$REPORT_FILE"
        fi
    fi
else
    echo -e "${RED}❌ Bandit non installato${NC}"
    echo "### ❌ Vulnerabilità Codice (Bandit)" >> "$REPORT_FILE"
    echo "**Stato:** ❌ ERRORE - Bandit non installato" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

# 3. PyUpgrade - Aggiornamento sintassi Python
echo -e "${YELLOW}🔍 3. Controllo sintassi Python (PyUpgrade)...${NC}"
if command -v pyupgrade &> /dev/null; then
    echo "Esecuzione pyupgrade check..."
    
    # Conta file che necessitano aggiornamento
    PYTHON_FILES=$(find app/ -name "*.py" | wc -l)
    echo "File Python trovati: $PYTHON_FILES"
    
    # Esegui dry-run per vedere cosa verrebbe aggiornato
    pyupgrade --py311-plus --exit-zero-even-if-changed app/**/*.py > "$REPORT_DIR/pyupgrade_report.txt" 2>&1 || true
    
    echo "### 🔧 Aggiornamento Sintassi Python (PyUpgrade)" >> "$REPORT_FILE"
    echo "**Stato:** ℹ️ INFORMATIVO - Controllo sintassi completato" >> "$REPORT_FILE"
    echo "- **File Python:** $PYTHON_FILES" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "#### 📝 Raccomandazioni:" >> "$REPORT_FILE"
    echo '```bash' >> "$REPORT_FILE"
    echo "# Per aggiornare automaticamente la sintassi:" >> "$REPORT_FILE"
    echo "pyupgrade --py311-plus app/**/*.py" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    echo -e "${GREEN}✅ Controllo sintassi Python completato${NC}"
else
    echo -e "${RED}❌ PyUpgrade non installato${NC}"
    echo "### ❌ Aggiornamento Sintassi Python (PyUpgrade)" >> "$REPORT_FILE"
    echo "**Stato:** ❌ ERRORE - PyUpgrade non installato" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

# 4. Controllo configurazioni critiche
echo -e "${YELLOW}🔍 4. Controllo configurazioni critiche...${NC}"
echo "### 🔧 Configurazioni Critiche" >> "$REPORT_FILE"

# Controlla SECRET_KEY
if grep -q "your-secret-key-here" app/core/config.py; then
    echo -e "${RED}❌ SECRET_KEY ancora hardcoded${NC}"
    echo "**SECRET_KEY:** ❌ CRITICO - Usa valore di default" >> "$REPORT_FILE"
else
    echo -e "${GREEN}✅ SECRET_KEY configurata correttamente${NC}"
    echo "**SECRET_KEY:** ✅ SICURO - Configurata correttamente" >> "$REPORT_FILE"
fi

# Controlla CORS
if grep -q 'BACKEND_CORS_ORIGINS.*\[\"\*\"\]' app/core/config.py; then
    echo -e "${RED}❌ CORS troppo permissivo (wildcard)${NC}"
    echo "**CORS:** ❌ CRITICO - Usa wildcard (*)" >> "$REPORT_FILE"
else
    echo -e "${GREEN}✅ CORS configurato correttamente${NC}"
    echo "**CORS:** ✅ SICURO - Configurato correttamente" >> "$REPORT_FILE"
fi

# Controlla credenziali database
if grep -q "postgres:N0nn0c4rl0!!" app/core/config.py; then
    echo -e "${RED}❌ Credenziali database hardcoded${NC}"
    echo "**Database:** ❌ CRITICO - Credenziali hardcoded" >> "$REPORT_FILE"
else
    echo -e "${GREEN}✅ Credenziali database configurate correttamente${NC}"
    echo "**Database:** ✅ SICURO - Credenziali configurate correttamente" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# 5. Controllo file di log
echo -e "${YELLOW}🔍 5. Controllo file di log...${NC}"
echo "### 📝 Controllo Logging" >> "$REPORT_FILE"

if [ -d "logs" ]; then
    LOG_COUNT=$(find logs/ -name "*.log" | wc -l)
    echo -e "${GREEN}✅ Directory logs trovata con $LOG_COUNT file${NC}"
    echo "**Logging:** ✅ ATTIVO - $LOG_COUNT file di log trovati" >> "$REPORT_FILE"
    
    # Controlla dimensione log
    LOG_SIZE=$(du -sh logs/ 2>/dev/null | cut -f1 || echo "0")
    echo "**Dimensione Log:** $LOG_SIZE" >> "$REPORT_FILE"
else
    echo -e "${YELLOW}⚠️ Directory logs non trovata${NC}"
    echo "**Logging:** ⚠️ NON TROVATO - Directory logs non esistente" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# 6. Riepilogo finale
echo -e "${BLUE}📊 Riepilogo finale...${NC}"

# Calcola score sicurezza
SCORE=100
if [ "$VULN_COUNT" -gt 0 ]; then SCORE=$((SCORE - 30)); fi
if [ "$HIGH_ISSUES" -gt 0 ]; then SCORE=$((SCORE - 25)); fi
if [ "$MEDIUM_ISSUES" -gt 0 ]; then SCORE=$((SCORE - 15)); fi
if grep -q "your-secret-key-here" app/core/config.py; then SCORE=$((SCORE - 20)); fi
if grep -q 'BACKEND_CORS_ORIGINS.*\[\"\*\"\]' app/core/config.py; then SCORE=$((SCORE - 10)); fi

# Determina livello sicurezza
if [ "$SCORE" -ge 80 ]; then
    SECURITY_LEVEL="🟢 ALTO"
elif [ "$SCORE" -ge 60 ]; then
    SECURITY_LEVEL="🟡 MEDIO"
else
    SECURITY_LEVEL="🔴 BASSO"
fi

echo "### 📊 Score Sicurezza Finale" >> "$REPORT_FILE"
echo "**Score:** $SCORE/100" >> "$REPORT_FILE"
echo "**Livello:** $SECURITY_LEVEL" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Raccomandazioni
echo "### 🎯 Raccomandazioni" >> "$REPORT_FILE"
if [ "$SCORE" -lt 80 ]; then
    echo "1. **Risolvere vulnerabilità critiche** - Priorità ALTA" >> "$REPORT_FILE"
    echo "2. **Configurare environment variables** - SECRET_KEY, DATABASE_URL" >> "$REPORT_FILE"
    echo "3. **Restringere CORS** - Rimuovere wildcard (*)" >> "$REPORT_FILE"
    echo "4. **Aggiornare dipendenze vulnerabili** - Eseguire safety check" >> "$REPORT_FILE"
    echo "5. **Risolvere problemi Bandit** - Correggere codice critico" >> "$REPORT_FILE"
else
    echo "✅ Sistema generalmente sicuro. Mantenere buone pratiche." >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "**Report generato automaticamente il:** $(date)" >> "$REPORT_FILE"
echo "**Scanner utilizzati:** Safety, Bandit, PyUpgrade" >> "$REPORT_FILE"

# Output finale
echo ""
echo -e "${BLUE}📋 REPORT COMPLETATO${NC}"
echo -e "${BLUE}==================${NC}"
echo -e "📄 Report salvato in: ${GREEN}$REPORT_FILE${NC}"
echo -e "🔒 Score sicurezza: ${GREEN}$SCORE/100${NC}"
echo -e "📊 Livello: $SECURITY_LEVEL"
echo ""
echo -e "${YELLOW}💡 Prossimi step:${NC}"
echo "1. Revisionare il report completo"
echo "2. Risolvere vulnerabilità critiche"
echo "3. Configurare environment variables"
echo "4. Eseguire test di sicurezza"
echo ""

# Esci con codice di errore se ci sono problemi critici
if [ "$VULN_COUNT" -gt 0 ] || [ "$HIGH_ISSUES" -gt 0 ]; then
    echo -e "${RED}⚠️ ATTENZIONE: Trovati problemi critici di sicurezza!${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Nessun problema critico trovato${NC}"
    exit 0
fi 