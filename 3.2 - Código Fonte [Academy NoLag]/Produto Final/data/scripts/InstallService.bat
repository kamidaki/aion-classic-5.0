@echo off
:: Academy NoLag — Windows Service Installer (Elevated)
cd /d "%~dp0"
echo ===================================================
echo     Academy NoLag Privileged Service Installer
echo ===================================================

openfiles >nul 2>&1
if '%errorlevel%' NEQ '0' (
    echo [ERROR] This installer requires Administrator privileges.
    echo Please right-click InstallService.bat and choose 'Run as administrator'.
    pause
    exit /b 1
)

set SERVICE_NAME=AcademyNoLagService
set BINARY_PATH="%~dp0AcademyNoLag.Service.exe"

echo Stopping existing service if running...
sc stop %SERVICE_NAME% >nul 2>&1
sc delete %SERVICE_NAME% >nul 2>&1

echo Creating Windows Service '%SERVICE_NAME%'...
sc create %SERVICE_NAME% binPath= %BINARY_PATH% start= auto DisplayName= "Academy NoLag Network Service"

if '%errorlevel%' EQU '0' (
    echo [SUCCESS] Service registered successfully.
    echo Starting service...
    sc start %SERVICE_NAME%
    echo [OK] Academy NoLag Privileged Service is now running in background.
) else (
    echo [ERROR] Failed to register service. Error code: %errorlevel%
)

pause
