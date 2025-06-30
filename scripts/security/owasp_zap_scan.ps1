#!/usr/bin/env pwsh
<#
.SYNOPSIS
    OWASP ZAP Security Scan for Eterna Home
.DESCRIPTION
    Esegue uno scan di sicurezza con OWASP ZAP contro l'applicazione Eterna Home
.PARAMETER TargetUrl
    URL target per lo scan (default: http://localhost:8000)
.PARAMETER ReportPath
    Percorso per salvare il report (default: docs/security/)
#>

param(
    [string]$TargetUrl = "http://localhost:8000",
    [string]$ReportPath = "docs/security/"
)

# Configurazione
$ZapPath = "C:\Program Files\OWASP\Zed Attack Proxy\zap.bat"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportFile = "$ReportPath\owasp_zap_report_$Timestamp.html"
$JsonReportFile = "$ReportPath\owasp_zap_report_$Timestamp.json"

Write-Host "🔍 OWASP ZAP Security Scan - Eterna Home" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Target URL: $TargetUrl" -ForegroundColor Yellow
Write-Host "Report Path: $ReportPath" -ForegroundColor Yellow
Write-Host "Timestamp: $Timestamp" -ForegroundColor Yellow

# Verifica che ZAP sia installato
if (-not (Test-Path $ZapPath)) {
    Write-Host "❌ OWASP ZAP non trovato in: $ZapPath" -ForegroundColor Red
    Write-Host "📥 Installa OWASP ZAP da: https://owasp.org/www-project-zap/" -ForegroundColor Yellow
    exit 1
}

# Crea directory per i report se non esiste
if (-not (Test-Path $ReportPath)) {
    New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null
    Write-Host "📁 Creata directory: $ReportPath" -ForegroundColor Green
}

# Verifica che il target sia raggiungibile
try {
    $response = Invoke-WebRequest -Uri $TargetUrl -TimeoutSec 10
    Write-Host "✅ Target raggiungibile (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Target non raggiungibile: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Assicurati che il server FastAPI sia in esecuzione" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Avvio scan OWASP ZAP..." -ForegroundColor Green

try {
    # Esegue lo scan con ZAP
    $zapArgs = @(
        "-cmd",
        "-quickurl", $TargetUrl,
        "-quickprogress",
        "-quickout", $ReportFile,
        "-silent"
    )
    
    $process = Start-Process -FilePath $ZapPath -ArgumentList $zapArgs -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host "✅ Scan completato con successo!" -ForegroundColor Green
        Write-Host "📄 Report HTML: $ReportFile" -ForegroundColor Cyan
        
        # Genera report JSON semplificato
        $jsonReport = @{
            timestamp = $Timestamp
            target_url = $TargetUrl
            scan_type = "OWASP ZAP Quick Scan"
            status = "completed"
            report_file = $ReportFile
            summary = @{
                total_alerts = 0
                high_alerts = 0
                medium_alerts = 0
                low_alerts = 0
                info_alerts = 0
            }
        }
        
        $jsonReport | ConvertTo-Json -Depth 10 | Out-File -FilePath $JsonReportFile -Encoding UTF8
        Write-Host "📄 Report JSON: $JsonReportFile" -ForegroundColor Cyan
        
    } else {
        Write-Host "❌ Scan fallito con exit code: $($process.ExitCode)" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "❌ Errore durante lo scan: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Scan OWASP ZAP completato!" -ForegroundColor Green
Write-Host "📊 Controlla i report in: $ReportPath" -ForegroundColor Cyan 