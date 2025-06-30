#!/bin/bash

# OWASP ZAP Security Scanner per Eterna Home
# Esegue test automatici di sicurezza su API e endpoint

set -e

# Configurazione
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_BASE="${API_BASE:-$BASE_URL/api/v1}"
REPORT_DIR="${REPORT_DIR:-docs/security}"
LOG_FILE="${LOG_FILE:-logs/security/pentest_owasp.log}"
ZAP_CONTAINER="${ZAP_CONTAINER:-owasp/zap2docker-stable}"

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzione per logging
log_message() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Crea directory se non esistono
mkdir -p "$REPORT_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

log_message "🚀 Avvio OWASP ZAP Security Scan per Eterna Home"
log_message "Target URL: $BASE_URL"
log_message "API Base: $API_BASE"

# Verifica che Docker sia disponibile
if ! command -v docker &> /dev/null; then
    log_error "Docker non trovato. Installa Docker per eseguire i test OWASP ZAP."
    exit 1
fi

# Verifica che il container ZAP sia disponibile
if ! docker images | grep -q "owasp/zap2docker-stable"; then
    log_message "Scaricamento immagine OWASP ZAP..."
    docker pull "$ZAP_CONTAINER"
fi

# Lista degli endpoint da testare
ENDPOINTS=(
    "/api/v1/auth/token"
    "/api/v1/auth/refresh"
    "/api/v1/auth/register"
    "/api/v1/documents"
    "/api/v1/documents/upload"
    "/api/v1/bim"
    "/api/v1/bim/upload"
    "/api/v1/voice"
    "/api/v1/voice/process"
    "/api/v1/areas"
    "/api/v1/maintenance"
    "/api/v1/bookings"
    "/api/v1/users"
    "/api/v1/roles"
    "/api/v1/permissions"
    "/health"
    "/ready"
    "/metrics"
)

# Test di base con ZAP
log_message "🔍 Esecuzione test di sicurezza OWASP ZAP..."

# 1. Spider scan per mappare l'applicazione
log_message "📊 Spider scan per mappare l'applicazione..."
docker run --rm -v "$(pwd)/$REPORT_DIR:/zap/wrk" "$ZAP_CONTAINER" \
    zap-baseline.py -t "$BASE_URL" \
    -J zap_spider_report.json \
    -r zap_spider_report.html \
    -l INFO

# 2. Active scan per vulnerabilità
log_message "🔬 Active scan per vulnerabilità..."
docker run --rm -v "$(pwd)/$REPORT_DIR:/zap/wrk" "$ZAP_CONTAINER" \
    zap-full-scan.py -t "$BASE_URL" \
    -J zap_active_report.json \
    -r zap_active_report.html \
    -l INFO

# 3. API scan specifico
log_message "🔌 API scan specifico..."
docker run --rm -v "$(pwd)/$REPORT_DIR:/zap/wrk" "$ZAP_CONTAINER" \
    zap-api-scan.py -t "$API_BASE" \
    -f openapi \
    -J zap_api_report.json \
    -r zap_api_report.html \
    -l INFO

# 4. Test specifici per endpoint critici
log_message "🎯 Test specifici per endpoint critici..."

# Test SQL Injection
log_message "  - Test SQL Injection..."
for endpoint in "${ENDPOINTS[@]}"; do
    if [[ "$endpoint" == *"?"* ]]; then
        # Endpoint con parametri
        test_url="${BASE_URL}${endpoint}' OR '1'='1"
    else
        # Endpoint senza parametri
        test_url="${BASE_URL}${endpoint}"
    fi
    
    docker run --rm -v "$(pwd)/$REPORT_DIR:/zap/wrk" "$ZAP_CONTAINER" \
        zap-cli quick-scan --self-contained \
        --start-options "-config api.disablekey=true" \
        "$test_url" \
        --spider \
        --ajax-spider \
        --scan \
        --output-format json \
        --output "sql_injection_${endpoint//\//_}.json"
done

# Test XSS
log_message "  - Test XSS..."
for endpoint in "${ENDPOINTS[@]}"; do
    if [[ "$endpoint" == *"?"* ]]; then
        test_url="${BASE_URL}${endpoint}<script>alert('XSS')</script>"
    else
        test_url="${BASE_URL}${endpoint}"
    fi
    
    docker run --rm -v "$(pwd)/$REPORT_DIR:/zap/wrk" "$ZAP_CONTAINER" \
        zap-cli quick-scan --self-contained \
        --start-options "-config api.disablekey=true" \
        "$test_url" \
        --spider \
        --ajax-spider \
        --scan \
        --output-format json \
        --output "xss_${endpoint//\//_}.json"
done

# Test Path Traversal
log_message "  - Test Path Traversal..."
PATH_TRAVERSAL_PAYLOADS=(
    "../../../etc/passwd"
    "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"
    "....//....//....//etc/passwd"
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
)

for payload in "${PATH_TRAVERSAL_PAYLOADS[@]}"; do
    for endpoint in "${ENDPOINTS[@]}"; do
        test_url="${BASE_URL}${endpoint}/${payload}"
        
        docker run --rm -v "$(pwd)/$REPORT_DIR:/zap/wrk" "$ZAP_CONTAINER" \
            zap-cli quick-scan --self-contained \
            --start-options "-config api.disablekey=true" \
            "$test_url" \
            --spider \
            --ajax-spider \
            --scan \
            --output-format json \
            --output "path_traversal_${payload//\//_}_${endpoint//\//_}.json"
    done
done

# Test CORS
log_message "  - Test CORS..."
for endpoint in "${ENDPOINTS[@]}"; do
    test_url="${BASE_URL}${endpoint}"
    
    # Test con Origin header malevolo
    curl -H "Origin: https://evil.com" \
         -H "Access-Control-Request-Method: POST" \
         -H "Access-Control-Request-Headers: X-Requested-With" \
         -X OPTIONS \
         "$test_url" \
         -o "$REPORT_DIR/cors_test_${endpoint//\//_}.txt" \
         2>/dev/null || true
done

# Test Headers di Sicurezza
log_message "  - Test Headers di Sicurezza..."
for endpoint in "${ENDPOINTS[@]}"; do
    test_url="${BASE_URL}${endpoint}"
    
    curl -I "$test_url" \
         -o "$REPORT_DIR/headers_test_${endpoint//\//_}.txt" \
         2>/dev/null || true
done

# Genera report consolidato
log_message "📋 Generazione report consolidato..."

cat > "$REPORT_DIR/owasp_report.html" << 'EOF'
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OWASP ZAP Security Report - Eterna Home</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .critical { background: #ffebee; border-left: 5px solid #f44336; }
        .high { background: #fff3e0; border-left: 5px solid #ff9800; }
        .medium { background: #fff8e1; border-left: 5px solid #ffc107; }
        .low { background: #f1f8e9; border-left: 5px solid #4caf50; }
        .info { background: #e3f2fd; border-left: 5px solid #2196f3; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .timestamp { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 OWASP ZAP Security Report</h1>
        <h2>Eterna Home - Pentest Automatico</h2>
        <p class="timestamp">Generato il: $(date '+%Y-%m-%d %H:%M:%S')</p>
    </div>

    <div class="section info">
        <h3>📊 Riepilogo Test</h3>
        <p><strong>Target URL:</strong> $BASE_URL</p>
        <p><strong>Endpoint testati:</strong> ${#ENDPOINTS[@]}</p>
        <p><strong>Tipi di test:</strong> Spider Scan, Active Scan, API Scan, SQL Injection, XSS, Path Traversal, CORS, Headers</p>
    </div>

    <div class="section">
        <h3>📁 File di Report Generati</h3>
        <ul>
            <li><strong>Spider Report:</strong> zap_spider_report.html</li>
            <li><strong>Active Scan Report:</strong> zap_active_report.html</li>
            <li><strong>API Scan Report:</strong> zap_api_report.html</li>
            <li><strong>Test Specifici:</strong> File JSON per ogni tipo di test</li>
        </ul>
    </div>

    <div class="section">
        <h3>🎯 Endpoint Testati</h3>
        <table>
            <tr><th>Endpoint</th><th>Test Eseguiti</th></tr>
EOF

for endpoint in "${ENDPOINTS[@]}"; do
    echo "            <tr><td>$endpoint</td><td>Spider, Active, SQL Injection, XSS, Path Traversal, CORS, Headers</td></tr>" >> "$REPORT_DIR/owasp_report.html"
done

cat >> "$REPORT_DIR/owasp_report.html" << 'EOF'
        </table>
    </div>

    <div class="section">
        <h3>⚠️ Raccomandazioni</h3>
        <ul>
            <li>Verificare tutti i report JSON generati per vulnerabilità specifiche</li>
            <li>Controllare i file di test CORS e Headers per configurazioni di sicurezza</li>
            <li>Implementare rate limiting se non già presente</li>
            <li>Verificare la validazione input su tutti gli endpoint</li>
            <li>Controllare la configurazione CORS per limitare origini consentite</li>
        </ul>
    </div>

    <div class="section info">
        <h3>📝 Note</h3>
        <p>Questo report è stato generato automaticamente da OWASP ZAP. Per un'analisi completa, consultare i file JSON dettagliati e i report HTML specifici.</p>
        <p>Log completi disponibili in: $LOG_FILE</p>
    </div>
</body>
</html>
EOF

# Genera report JSON consolidato
cat > "$REPORT_DIR/owasp_report.json" << EOF
{
    "scan_info": {
        "target_url": "$BASE_URL",
        "api_base": "$API_BASE",
        "scan_date": "$(date -Iseconds)",
        "endpoints_tested": ${#ENDPOINTS[@]},
        "test_types": [
            "spider_scan",
            "active_scan", 
            "api_scan",
            "sql_injection",
            "xss",
            "path_traversal",
            "cors",
            "security_headers"
        ]
    },
    "endpoints": [
EOF

for endpoint in "${ENDPOINTS[@]}"; do
    echo "        \"$endpoint\"," >> "$REPORT_DIR/owasp_report.json"
done

cat >> "$REPORT_DIR/owasp_report.json" << 'EOF'
    ],
    "files_generated": [
        "zap_spider_report.html",
        "zap_spider_report.json", 
        "zap_active_report.html",
        "zap_active_report.json",
        "zap_api_report.html",
        "zap_api_report.json",
        "cors_test_*.txt",
        "headers_test_*.txt",
        "sql_injection_*.json",
        "xss_*.json",
        "path_traversal_*.json"
    ],
    "recommendations": [
        "Review all generated JSON reports for specific vulnerabilities",
        "Check CORS and Headers test files for security configurations",
        "Implement rate limiting if not already present",
        "Verify input validation on all endpoints",
        "Check CORS configuration to limit allowed origins"
    ]
}
EOF

# Log del completamento
log_success "✅ OWASP ZAP Security Scan completato!"
log_message "📁 Report salvati in: $REPORT_DIR/"
log_message "📋 Report principale: $REPORT_DIR/owasp_report.html"
log_message "📊 Report JSON: $REPORT_DIR/owasp_report.json"
log_message "📝 Log completi: $LOG_FILE"

# Log dell'evento di sicurezza
log_message "🔒 Evento di sicurezza registrato: pentest_owasp_completed"

echo "🎉 OWASP ZAP Security Scan completato con successo!"
echo "📁 Controlla i report in: $REPORT_DIR/" 