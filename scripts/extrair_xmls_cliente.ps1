# =========================================================================
#  AION CLASSIC 4.5 - SCRIPT DE EXTRAÇÃO AUTOMÁTICA DE XMLS DO CLIENTE
# =========================================================================

$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$raiz = Split-Path -Parent $aqui
$rust = Join-Path $raiz "Emulador-Rust"
$deploy = Join-Path $raiz "deploy"
$clientData = Join-Path $raiz "Cliente\GFAion\aionclassic\data"

$rawOut = Join-Path $rust "data\client_raw"
$clientOut = Join-Path $rust "data\client"
$deployClientOut = Join-Path $deploy "data\client"

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "  EXTRAINDO DADOS XML DIRETAMENTE DO CLIENTE AION CLASSIC 4.5            " -ForegroundColor White
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "  Origem: $clientData" -ForegroundColor Gray
Write-Host "  Destino: $clientOut e $deployClientOut" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $clientData)) {
    Write-Error "Pasta de dados do cliente não encontrada em: $clientData"
    exit 1
}

# 1. Compilar os utilitários pak e bxml em Release
Write-Host "[1/4] Compilando ferramentas de extração (pak e bxml)..." -ForegroundColor Yellow
Push-Location $rust
try {
    cmd.exe /c "`"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat`" && cargo build --release -p pak -p bxml"
    if ($LASTEXITCODE -ne 0) { throw "Falha na compilação das ferramentas pak / bxml." }
} finally {
    Pop-Location
}

$pakExe = Join-Path $rust "target\release\pak.exe"
$bxmlExe = Join-Path $rust "target\release\bxml.exe"

# 2. Criar diretórios de saída
if (-not (Test-Path $rawOut)) { New-Item -ItemType Directory -Path $rawOut -Force | Out-Null }
if (-not (Test-Path $clientOut)) { New-Item -ItemType Directory -Path $clientOut -Force | Out-Null }
if (-not (Test-Path $deployClientOut)) { New-Item -ItemType Directory -Path $deployClientOut -Force | Out-Null }

# 3. Executar o PAK extractor para descompactar todos os .pak
Write-Host "[2/4] Descompactando arquivos .pak do cliente..." -ForegroundColor Yellow
& $pakExe $clientData $rawOut

# 4. Executar o BXML decoder para converter os XMLs binários em texto puro
Write-Host "[3/4] Convertendo Binary XML (BXML) em XMLs legíveis..." -ForegroundColor Yellow
& $bxmlExe $rawOut $clientOut

# 5. Sincronizar com deploy/data/client
Write-Host "[4/4] Sincronizando catálogo completo com deploy/data/client..." -ForegroundColor Yellow
Copy-Item -Path "$clientOut\*" -Destination $deployClientOut -Recurse -Force

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host "  EXTRAÇÃO E DECODIFICAÇÃO DE XMLS CONCLUÍDAS COM SUCESSO!               " -ForegroundColor White
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host ""
