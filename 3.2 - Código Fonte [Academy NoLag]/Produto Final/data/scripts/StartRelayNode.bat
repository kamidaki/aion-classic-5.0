@echo off
cd /d "%~dp0"
echo Starting Academy NoLag Edge Relay Node on port 42420...
AcademyNoLag.RelayNode.exe --port 42420 --region "BR-Local"
pause
