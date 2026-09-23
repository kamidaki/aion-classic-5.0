@echo off
cd /d "%~dp0"
echo Starting Academy NoLag Edge Relay Node on port 42420...
if exist "modules\AcademyNoLag.RelayNode.exe" (
    "modules\AcademyNoLag.RelayNode.exe" --port 42420 --region "BR-Local"
) else if exist "..\..\modules\AcademyNoLag.RelayNode.exe" (
    "..\..\modules\AcademyNoLag.RelayNode.exe" --port 42420 --region "BR-Local"
) else (
    AcademyNoLag.RelayNode.exe --port 42420 --region "BR-Local"
)
pause
