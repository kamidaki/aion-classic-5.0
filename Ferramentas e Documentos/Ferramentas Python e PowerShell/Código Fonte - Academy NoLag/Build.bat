@echo off
cd /d "%~dp0"
echo ====================================================
echo     Academy NoLag Automated Build System (.NET 9)
echo ====================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build.ps1" -Configuration Release
if '%errorlevel%' NEQ '0' (
    echo [ERROR] Build failed with exit code %errorlevel%.
    pause
    exit /b %errorlevel%
)
echo [SUCCESS] Build completed. Deliverables ready in 'build/' and 'dist/'.
pause
