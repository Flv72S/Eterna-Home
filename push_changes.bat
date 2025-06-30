@echo off
echo ========================================
echo PUSH CAMBIAMENTI ETERNA HOME
echo ========================================
echo.

echo 1. Verificando stato repository...
git status

echo.
echo 2. Aggiungendo tutti i file...
git add .

echo.
echo 3. Creando commit...
git commit -m "feat: Sistema di monitoraggio e pentest completo - Endpoint /health, /ready, /metrics - Scanner OWASP ZAP e Nikto PowerShell - Test automatici (5/5 struttura superati) - Logging multi-tenant - Ready per produzione"

echo.
echo 4. Facendo push su GitHub...
git push origin main

echo.
echo ========================================
echo PUSH COMPLETATO!
echo ========================================
echo.
echo Repository: https://github.com/Flv72S/Eterna-Home.git
echo.
pause 