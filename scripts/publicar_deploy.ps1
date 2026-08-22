# =========================================================================
#  AION CLASSIC 4.5 RUST EMULATOR - SCRIPT DE PUBLICAÇÃO DE DEPLOY
# =========================================================================

$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$raiz = Split-Path -Parent $aqui
$rust = Join-Path $raiz "Emulador-Rust"
$deploy = Join-Path $raiz "deploy"

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "  PUBLICANDO PACOTE DE DEPLOY LIMPO (PRODUÇÃO)                           " -ForegroundColor White
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Compilar em modo Release
Write-Host "[1/3] Compilando executáveis em modo release (cargo build --release)..." -ForegroundColor Yellow
Push-Location $rust
try {
    cmd.exe /c "`"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat`" && cargo build --release"
    if ($LASTEXITCODE -ne 0) { throw "Falha na compilação do Cargo." }
} finally {
    Pop-Location
}

# 2. Criar diretório de Deploy se não existir
if (-not (Test-Path $deploy)) {
    New-Item -ItemType Directory -Path $deploy -Force | Out-Null
}

# 3. Copiar Executáveis
Write-Host "[2/3] Copiando binários de produção para a pasta deploy..." -ForegroundColor Yellow
$binarios = @("auth-server.exe", "sts-server.exe", "game-server.exe", "launcher.exe")
foreach ($bin in $binarios) {
    $origem = Join-Path $rust "target\release\$bin"
    if (Test-Path $origem) {
        Copy-Item -Path $origem -Destination (Join-Path $deploy $bin) -Force
        Write-Host "  + $bin copiado com sucesso." -ForegroundColor Green
    } else {
        Write-Warning "Binário $origem não encontrado."
    }
}

# 4. Copiar Dados Estáticos (Data)
Write-Host "[3/3] Sincronizando dados estáticos de jogo (data/)..." -ForegroundColor Yellow
$origemData = Join-Path $rust "data"
$destinoData = Join-Path $deploy "data"
if (-not (Test-Path $destinoData)) {
    New-Item -ItemType Directory -Path $destinoData -Force | Out-Null
}

if (Test-Path $origemData) {
    Get-ChildItem -Path $origemData -Recurse -File | Where-Object {
        $_.Name -notlike "Cargo.toml" -and $_.FullName -notmatch '\\src\\'
    } | ForEach-Object {
        $rel = $_.FullName.Substring($origemData.Length + 1)
        $dest = Join-Path $destinoData $rel
        $parent = Split-Path -Parent $dest
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        Copy-Item -Path $_.FullName -Destination $dest -Force
    }
    Write-Host "  + Dados estáticos copiados para deploy/data." -ForegroundColor Green
}

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host "  PUBLICAÇÃO CONCLUÍDA COM SUCESSO!                                      " -ForegroundColor White
Write-Host "  A pasta 'deploy/' está pronta para execução de produção.               " -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host ""
