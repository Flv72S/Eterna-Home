#!/bin/bash

# Nikto Security Scanner per Eterna Home
# Esegue test automatici di vulnerabilità server e headers

set -e

# Configurazione
BASE_URL="${BASE_URL:-http://localhost:8000}"
REPORT_DIR="${REPORT_DIR:-docs/security}"
LOG_FILE="${LOG_FILE:-logs/security/pentest_nikto.log}"

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

log_message "🚀 Avvio Nikto Security Scan per Eterna Home"
log_message "Target URL: $BASE_URL"

# Verifica che Nikto sia installato
if ! command -v nikto &> /dev/null; then
    log_error "Nikto non trovato. Installa Nikto per eseguire i test."
    log_message "Installazione Nikto:"
    log_message "  Ubuntu/Debian: sudo apt-get install nikto"
    log_message "  CentOS/RHEL: sudo yum install nikto"
    log_message "  macOS: brew install nikto"
    exit 1
fi

# Test di base con Nikto
log_message "🔍 Esecuzione test di sicurezza Nikto..."

# 1. Scan completo del server
log_message "📊 Scan completo del server..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_full_scan.txt" \
    -Format txt \
    -Tuning 1234567890abcx \
    -maxtime 1h \
    -ask no

# 2. Scan specifico per vulnerabilità comuni
log_message "🔬 Scan per vulnerabilità comuni..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_common_vulns.txt" \
    -Format txt \
    -Tuning 1234567890abcx \
    -maxtime 30m \
    -ask no

# 3. Scan per file e directory pericolose
log_message "📁 Scan per file e directory pericolose..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_dangerous_files.txt" \
    -Format txt \
    -Tuning 4 \
    -maxtime 15m \
    -ask no

# 4. Scan per problemi di configurazione
log_message "⚙️ Scan per problemi di configurazione..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_config_issues.txt" \
    -Format txt \
    -Tuning 5 \
    -maxtime 15m \
    -ask no

# 5. Scan per problemi di informazioni
log_message "ℹ️ Scan per problemi di informazioni..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_info_disclosure.txt" \
    -Format txt \
    -Tuning 6 \
    -maxtime 15m \
    -ask no

# 6. Scan per problemi di autenticazione
log_message "🔐 Scan per problemi di autenticazione..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_auth_issues.txt" \
    -Format txt \
    -Tuning 7 \
    -maxtime 15m \
    -ask no

# 7. Scan per problemi di XSS
log_message "🎯 Scan per problemi di XSS..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_xss_issues.txt" \
    -Format txt \
    -Tuning 8 \
    -maxtime 15m \
    -ask no

# 8. Scan per problemi di SQL Injection
log_message "💉 Scan per problemi di SQL Injection..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_sql_injection.txt" \
    -Format txt \
    -Tuning 9 \
    -maxtime 15m \
    -ask no

# 9. Scan per problemi di inclusione file
log_message "📄 Scan per problemi di inclusione file..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_file_inclusion.txt" \
    -Format txt \
    -Tuning a \
    -maxtime 15m \
    -ask no

# 10. Scan per problemi di directory traversal
log_message "🗂️ Scan per problemi di directory traversal..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_directory_traversal.txt" \
    -Format txt \
    -Tuning b \
    -maxtime 15m \
    -ask no

# 11. Scan per problemi di remote file inclusion
log_message "🌐 Scan per problemi di remote file inclusion..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_remote_file_inclusion.txt" \
    -Format txt \
    -Tuning c \
    -maxtime 15m \
    -ask no

# 12. Scan per problemi di web services
log_message "🔌 Scan per problemi di web services..."
nikto -h "$BASE_URL" \
    -output "$REPORT_DIR/nikto_web_services.txt" \
    -Format txt \
    -Tuning x \
    -maxtime 15m \
    -ask no

# Test specifici per endpoint API
log_message "🎯 Test specifici per endpoint API..."

API_ENDPOINTS=(
    "/api/v1/auth/token"
    "/api/v1/documents"
    "/api/v1/bim"
    "/api/v1/voice"
    "/health"
    "/ready"
    "/metrics"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
    log_message "  - Test endpoint: $endpoint"
    nikto -h "${BASE_URL}${endpoint}" \
        -output "$REPORT_DIR/nikto_api_${endpoint//\//_}.txt" \
        -Format txt \
        -Tuning 1234567890abcx \
        -maxtime 10m \
        -ask no
done

# Test per headers di sicurezza
log_message "🛡️ Test per headers di sicurezza..."

# Test manuale per headers
curl -I "$BASE_URL" \
    -o "$REPORT_DIR/security_headers.txt" \
    2>/dev/null || true

# Test per CORS
curl -H "Origin: https://evil.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     "$BASE_URL" \
     -o "$REPORT_DIR/cors_test.txt" \
     2>/dev/null || true

# Genera report consolidato
log_message "📋 Generazione report consolidato..."

cat > "$REPORT_DIR/nikto_report.html" << 'EOF'
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nikto Security Report - Eterna Home</title>
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
        pre { background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Nikto Security Report</h1>
        <h2>Eterna Home - Server Vulnerability Scan</h2>
        <p class="timestamp">Generato il: $(date '+%Y-%m-%d %H:%M:%S')</p>
    </div>

    <div class="section info">
        <h3>📊 Riepilogo Test</h3>
        <p><strong>Target URL:</strong> $BASE_URL</p>
        <p><strong>Tipi di test:</strong> Server Scan, Common Vulnerabilities, Dangerous Files, Configuration Issues, Info Disclosure, Authentication, XSS, SQL Injection, File Inclusion, Directory Traversal, Remote File Inclusion, Web Services</p>
    </div>

    <div class="section">
        <h3>📁 File di Report Generati</h3>
        <table>
            <tr><th>Test Type</th><th>File</th><th>Descrizione</th></tr>
            <tr><td>Full Scan</td><td>nikto_full_scan.txt</td><td>Scan completo del server</td></tr>
            <tr><td>Common Vulnerabilities</td><td>nikto_common_vulns.txt</td><td>Vulnerabilità comuni</td></tr>
            <tr><td>Dangerous Files</td><td>nikto_dangerous_files.txt</td><td>File e directory pericolose</td></tr>
            <tr><td>Configuration Issues</td><td>nikto_config_issues.txt</td><td>Problemi di configurazione</td></tr>
            <tr><td>Info Disclosure</td><td>nikto_info_disclosure.txt</td><td>Disclosure di informazioni</td></tr>
            <tr><td>Authentication Issues</td><td>nikto_auth_issues.txt</td><td>Problemi di autenticazione</td></tr>
            <tr><td>XSS Issues</td><td>nikto_xss_issues.txt</td><td>Problemi di Cross-Site Scripting</td></tr>
            <tr><td>SQL Injection</td><td>nikto_sql_injection.txt</td><td>Problemi di SQL Injection</td></tr>
            <tr><td>File Inclusion</td><td>nikto_file_inclusion.txt</td><td>Problemi di inclusione file</td></tr>
            <tr><td>Directory Traversal</td><td>nikto_directory_traversal.txt</td><td>Problemi di directory traversal</td></tr>
            <tr><td>Remote File Inclusion</td><td>nikto_remote_file_inclusion.txt</td><td>Problemi di remote file inclusion</td></tr>
            <tr><td>Web Services</td><td>nikto_web_services.txt</td><td>Problemi di web services</td></tr>
            <tr><td>Security Headers</td><td>security_headers.txt</td><td>Test headers di sicurezza</td></tr>
            <tr><td>CORS Test</td><td>cors_test.txt</td><td>Test configurazione CORS</td></tr>
        </table>
    </div>

    <div class="section">
        <h3>🎯 Endpoint API Testati</h3>
        <ul>
EOF

for endpoint in "${API_ENDPOINTS[@]}"; do
    echo "            <li><strong>$endpoint</strong> - nikto_api_${endpoint//\//_}.txt</li>" >> "$REPORT_DIR/nikto_report.html"
done

cat >> "$REPORT_DIR/nikto_report.html" << 'EOF'
        </ul>
    </div>

    <div class="section">
        <h3>⚠️ Raccomandazioni</h3>
        <ul>
            <li>Verificare tutti i file di report per vulnerabilità specifiche</li>
            <li>Controllare la configurazione del server web</li>
            <li>Verificare i headers di sicurezza</li>
            <li>Controllare la configurazione CORS</li>
            <li>Rimuovere file e directory non necessarie</li>
            <li>Aggiornare software e librerie</li>
        </ul>
    </div>

    <div class="section info">
        <h3>📝 Note</h3>
        <p>Questo report è stato generato automaticamente da Nikto. Per un'analisi completa, consultare tutti i file di report generati.</p>
        <p>Log completi disponibili in: $LOG_FILE</p>
    </div>
</body>
</html>
EOF

# Genera report JSON consolidato
cat > "$REPORT_DIR/nikto_report.json" << EOF
{
    "scan_info": {
        "target_url": "$BASE_URL",
        "scan_date": "$(date -Iseconds)",
        "scanner": "nikto",
        "test_types": [
            "full_scan",
            "common_vulnerabilities",
            "dangerous_files",
            "configuration_issues",
            "info_disclosure",
            "authentication_issues",
            "xss_issues",
            "sql_injection",
            "file_inclusion",
            "directory_traversal",
            "remote_file_inclusion",
            "web_services"
        ]
    },
    "api_endpoints_tested": [
EOF

for endpoint in "${API_ENDPOINTS[@]}"; do
    echo "        \"$endpoint\"," >> "$REPORT_DIR/nikto_report.json"
done

cat >> "$REPORT_DIR/nikto_report.json" << 'EOF'
    ],
    "files_generated": [
        "nikto_full_scan.txt",
        "nikto_common_vulns.txt",
        "nikto_dangerous_files.txt",
        "nikto_config_issues.txt",
        "nikto_info_disclosure.txt",
        "nikto_auth_issues.txt",
        "nikto_xss_issues.txt",
        "nikto_sql_injection.txt",
        "nikto_file_inclusion.txt",
        "nikto_directory_traversal.txt",
        "nikto_remote_file_inclusion.txt",
        "nikto_web_services.txt",
        "security_headers.txt",
        "cors_test.txt",
        "nikto_api_*.txt"
    ],
    "recommendations": [
        "Review all generated report files for specific vulnerabilities",
        "Check server web configuration",
        "Verify security headers",
        "Check CORS configuration",
        "Remove unnecessary files and directories",
        "Update software and libraries"
    ]
}
EOF

# Log del completamento
log_success "✅ Nikto Security Scan completato!"
log_message "📁 Report salvati in: $REPORT_DIR/"
log_message "📋 Report principale: $REPORT_DIR/nikto_report.html"
log_message "📊 Report JSON: $REPORT_DIR/nikto_report.json"
log_message "📝 Log completi: $LOG_FILE"

# Log dell'evento di sicurezza
log_message "🔒 Evento di sicurezza registrato: pentest_nikto_completed"

echo "🎉 Nikto Security Scan completato con successo!"
echo "📁 Controlla i report in: $REPORT_DIR/" 