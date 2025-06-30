#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Nikto Security Scan for Eterna Home
.DESCRIPTION
    Esegue uno scan di sicurezza con Nikto contro l'applicazione Eterna Home
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
$NiktoPath = "nikto.exe"  # Assumiamo che sia nel PATH
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportFile = "$ReportPath\nikto_report_$Timestamp.txt"
$JsonReportFile = "$ReportPath\nikto_report_$Timestamp.json"

Write-Host "🔍 Nikto Security Scan - Eterna Home" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Target URL: $TargetUrl" -ForegroundColor Yellow
Write-Host "Report Path: $ReportPath" -ForegroundColor Yellow
Write-Host "Timestamp: $Timestamp" -ForegroundColor Yellow

# Verifica che Nikto sia disponibile
try {
    $null = Get-Command $NiktoPath -ErrorAction Stop
    Write-Host "✅ Nikto trovato nel PATH" -ForegroundColor Green
} catch {
    Write-Host "❌ Nikto non trovato nel PATH" -ForegroundColor Red
    Write-Host "📥 Installa Nikto o aggiungilo al PATH" -ForegroundColor Yellow
    Write-Host "💡 Per Windows: https://github.com/sullo/nikto" -ForegroundColor Yellow
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

Write-Host "🚀 Avvio scan Nikto..." -ForegroundColor Green

try {
    # Esegue lo scan con Nikto
    $niktoArgs = @(
        "-h", $TargetUrl,
        "-o", $ReportFile,
        "-Format", "txt",
        "-Tuning", "1,2,3,4,5,6,7,8,9,0,a,b,c",
        "-timeout", "10"
    )
    
    $process = Start-Process -FilePath $NiktoPath -ArgumentList $niktoArgs -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0 -or $process.ExitCode -eq 1) {
        Write-Host "✅ Scan completato!" -ForegroundColor Green
        Write-Host "📄 Report: $ReportFile" -ForegroundColor Cyan
        
        # Genera report JSON semplificato
        $jsonReport = @{
            timestamp = $Timestamp
            target_url = $TargetUrl
            scan_type = "Nikto Web Scanner"
            status = "completed"
            report_file = $ReportFile
            summary = @{
                total_issues = 0
                high_issues = 0
                medium_issues = 0
                low_issues = 0
                info_issues = 0
            }
        }
        
        # Legge il report per estrarre statistiche
        if (Test-Path $ReportFile) {
            $reportContent = Get-Content $ReportFile -Raw
            $jsonReport.summary.total_issues = ($reportContent -split "`n" | Where-Object { $_ -match "^\+\s" }).Count
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

Write-Host "🎉 Scan Nikto completato!" -ForegroundColor Green
Write-Host "📊 Controlla i report in: $ReportPath" -ForegroundColor Cyan 