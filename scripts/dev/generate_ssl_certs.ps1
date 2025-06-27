# 🔒 SSL Certificate Generator for Eterna Home Development (PowerShell)
# Genera certificati SSL self-signed per sviluppo locale

param(
    [string]$Country = "IT",
    [string]$State = "Italy", 
    [string]$City = "Rome",
    [string]$Org = "Eterna Home",
    [string]$OrgUnit = "Development",
    [string]$CommonName = "localhost",
    [int]$ValidDays = 365
)

# Colori per output
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

Write-Host "🔒 GENERATORE CERTIFICATI SSL - ETERNA HOME" -ForegroundColor $Blue
Write-Host "==========================================" -ForegroundColor $Blue
Write-Host ""

# Directory per i certificati
$CertDir = "certs"
if (!(Test-Path $CertDir)) {
    New-Item -ItemType Directory -Path $CertDir | Out-Null
}

Write-Host "📋 Configurazione certificati:" -ForegroundColor $Yellow
Write-Host "  - Paese: $Country"
Write-Host "  - Stato: $State"
Write-Host "  - Città: $City"
Write-Host "  - Organizzazione: $Org"
Write-Host "  - Unità: $OrgUnit"
Write-Host "  - Nome comune: $CommonName"
Write-Host "  - Validità: $ValidDays giorni"
Write-Host ""

# Funzione per generare certificato
function New-Certificate {
    param(
        [string]$ServiceName,
        [string]$PrivateKeyPath,
        [string]$CertPath
    )
    
    Write-Host "🔑 Generazione chiave privata $ServiceName..." -ForegroundColor $Yellow
    
    # Genera chiave privata
    $PrivateKeyParams = @{
        Path = $PrivateKeyPath
        KeyAlgorithm = "RSA"
        KeyLength = 2048
        KeyExportPolicy = "Exportable"
        KeyUsage = "KeyEncipherment"
        Provider = "Microsoft Enhanced RSA and AES Cryptographic Provider"
    }
    
    $PrivateKey = New-SelfSignedCertificate @PrivateKeyParams
    
    # Esporta chiave privata
    $PrivateKeyBytes = $PrivateKey.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Pkcs12)
    [System.IO.File]::WriteAllBytes($PrivateKeyPath, $PrivateKeyBytes)
    
    Write-Host "✅ Chiave privata $ServiceName generata: $PrivateKeyPath" -ForegroundColor $Green
    
    # Genera certificato
    Write-Host "📜 Generazione certificato $ServiceName..." -ForegroundColor $Yellow
    
    $CertParams = @{
        Subject = "CN=$CommonName, OU=$OrgUnit, O=$Org, L=$City, S=$State, C=$Country"
        CertStoreLocation = "Cert:\CurrentUser\My"
        NotAfter = (Get-Date).AddDays($ValidDays)
        KeyAlgorithm = "RSA"
        KeyLength = 2048
        KeyExportPolicy = "Exportable"
        KeyUsage = "KeyEncipherment"
        TextExtension = @("2.5.29.37={text}1.3.6.1.5.5.7.3.1")
        Provider = "Microsoft Enhanced RSA and AES Cryptographic Provider"
    }
    
    $Certificate = New-SelfSignedCertificate @CertParams
    
    # Esporta certificato
    $CertBytes = $Certificate.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
    [System.IO.File]::WriteAllBytes($CertPath, $CertBytes)
    
    Write-Host "✅ Certificato $ServiceName generato: $CertPath" -ForegroundColor $Green
    
    # Pulisci certificato dal store
    Remove-Item "Cert:\CurrentUser\My\$($Certificate.Thumbprint)" -Force
}

# 1. Genera certificati per MinIO
New-Certificate -ServiceName "MinIO" -PrivateKeyPath "$CertDir\minio-private.pfx" -CertPath "$CertDir\minio-cert.pem"

# 2. Genera certificati per PostgreSQL
New-Certificate -ServiceName "PostgreSQL" -PrivateKeyPath "$CertDir\postgresql-private.pfx" -CertPath "$CertDir\postgresql-cert.pem"

# 3. Genera certificati per Redis
New-Certificate -ServiceName "Redis" -PrivateKeyPath "$CertDir\redis-private.pfx" -CertPath "$CertDir\redis-cert.pem"

# 4. Crea file di configurazione per i servizi
Write-Host "📝 Creazione file di configurazione..." -ForegroundColor $Yellow

# MinIO configuration
$MinioConfig = @"
# MinIO SSL Configuration
MINIO_CERT_FILE=./certs/minio-cert.pem
MINIO_KEY_FILE=./certs/minio-private.pfx
MINIO_USE_SSL=true
MINIO_VERIFY_SSL=true
"@
$MinioConfig | Out-File -FilePath "$CertDir\minio-config.env" -Encoding UTF8

# PostgreSQL configuration
$PostgresConfig = @"
# PostgreSQL SSL Configuration
ssl = on
ssl_cert_file = './certs/postgresql-cert.pem'
ssl_key_file = './certs/postgresql-private.pfx'
ssl_ca_file = './certs/postgresql-cert.pem'
"@
$PostgresConfig | Out-File -FilePath "$CertDir\postgresql-ssl.conf" -Encoding UTF8

# Redis configuration
$RedisConfig = @"
# Redis SSL Configuration
tls-port 6380
tls-cert-file ./certs/redis-cert.pem
tls-key-file ./certs/redis-private.pfx
tls-ca-cert-file ./certs/redis-cert.pem
"@
$RedisConfig | Out-File -FilePath "$CertDir\redis-ssl.conf" -Encoding UTF8

Write-Host "✅ File di configurazione creati" -ForegroundColor $Green

# 5. Riepilogo finale
Write-Host ""
Write-Host "📊 RIEPILOGO CERTIFICATI GENERATI" -ForegroundColor $Blue
Write-Host "================================" -ForegroundColor $Blue
Write-Host ""
Write-Host "✅ MinIO:" -ForegroundColor $Green
Write-Host "  - Chiave: $CertDir\minio-private.pfx"
Write-Host "  - Certificato: $CertDir\minio-cert.pem"
Write-Host "  - Config: $CertDir\minio-config.env"
Write-Host ""
Write-Host "✅ PostgreSQL:" -ForegroundColor $Green
Write-Host "  - Chiave: $CertDir\postgresql-private.pfx"
Write-Host "  - Certificato: $CertDir\postgresql-cert.pem"
Write-Host "  - Config: $CertDir\postgresql-ssl.conf"
Write-Host ""
Write-Host "✅ Redis:" -ForegroundColor $Green
Write-Host "  - Chiave: $CertDir\redis-private.pfx"
Write-Host "  - Certificato: $CertDir\redis-cert.pem"
Write-Host "  - Config: $CertDir\redis-ssl.conf"
Write-Host ""

# 6. Istruzioni per l'uso
Write-Host "📋 ISTRUZIONI PER L'USO:" -ForegroundColor $Yellow
Write-Host ""
Write-Host "1. **MinIO SSL:**"
Write-Host "   - Copia i file in $CertDir\minio-cert.pem e $CertDir\minio-private.pfx"
Write-Host "   - Avvia MinIO con: minio server --certs-dir ./certs"
Write-Host ""
Write-Host "2. **PostgreSQL SSL:**"
Write-Host "   - Aggiungi al postgresql.conf:"
Write-Host "     ssl = on"
Write-Host "     ssl_cert_file = './certs/postgresql-cert.pem'"
Write-Host "     ssl_key_file = './certs/postgresql-private.pfx'"
Write-Host ""
Write-Host "3. **Redis SSL:**"
Write-Host "   - Avvia Redis con: redis-server --tls-port 6380 --tls-cert-file ./certs/redis-cert.pem --tls-key-file ./certs/redis-private.pfx"
Write-Host ""
Write-Host "4. **Environment Variables:**"
Write-Host "   - Aggiorna il file .env con:"
Write-Host "     MINIO_USE_SSL=true"
Write-Host "     DATABASE_SSL_MODE=require"
Write-Host "     REDIS_SSL=true"
Write-Host ""

Write-Host "🎉 Certificati SSL generati con successo!" -ForegroundColor $Green
Write-Host "⚠️  RICORDA: Questi sono certificati self-signed per sviluppo." -ForegroundColor $Yellow
Write-Host "   In produzione usa certificati firmati da una CA autorizzata." -ForegroundColor $Yellow 