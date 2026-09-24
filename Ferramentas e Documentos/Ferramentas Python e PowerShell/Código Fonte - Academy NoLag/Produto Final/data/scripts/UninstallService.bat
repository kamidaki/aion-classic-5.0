@echo off
:: Academy NoLag — Windows Service Uninstaller (Elevated)
cd /d "%~dp0"
echo ===================================================
echo    Academy NoLag Privileged Service Uninstaller
echo ===================================================

openfiles >nul 2>&1
if '%errorlevel%' NEQ '0' (
    echo [ERROR] This uninstaller requires Administrator privileges.
    echo Please right-click UninstallService.bat and choose 'Run as administrator'.
    pause
    exit /b 1
)

set SERVICE_NAME=AcademyNoLagService

echo Stopping service '%SERVICE_NAME%'...
sc stop %SERVICE_NAME% >nul 2>&1

echo Deleting service '%SERVICE_NAME%'...
sc delete %SERVICE_NAME%

echo [OK] Academy NoLag service uninstalled. Default Windows networking restored.
pause
