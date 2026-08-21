# Monta o pacote que vai para outra pessoa: compila, junta o que e necessario, e zipa.
#
# O criterio do que entra e "roda sem o repositorio". Codigo, capturas e ferramentas de analise
# ficam de fora; o que sobra e o que o cliente precisa encontrar rodando.

$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$raiz = Split-Path -Parent $aqui
$rust = Join-Path $raiz "EmuRustDurak"
$saida = Join-Path $raiz "dist\aion-emulador"

Write-Host ""
Write-Host "  Empacotando o servidor local de Aion" -ForegroundColor Cyan
Write-Host ""

# --- compila ----------------------------------------------------------------

$rodando = Get-Process -Name auth-server, sts-server, game-server, launcher -ErrorAction SilentlyContinue
if ($rodando) {
    Write-Host "  ! fechando servidores em execucao (senao o cargo nao substitui o .exe)" -ForegroundColor Yellow
    $rodando | Stop-Process -Force -Confirm:$false
    Start-Sleep -Seconds 2
}

Write-Host "  compilando em modo release..."
Push-Location $rust
# O cargo escreve os warnings no stderr, e com ErrorActionPreference=Stop o PowerShell 5.1 trata
# saida de stderr de executavel nativo como erro terminante. Quem decide se deu certo e o codigo
# de saida, entao afrouxamos so aqui.
$antes = $ErrorActionPreference
$ErrorActionPreference = "Continue"
cargo build --release --offline
$codigo = $LASTEXITCODE
$ErrorActionPreference = $antes
Pop-Location
if ($codigo -ne 0) { throw "cargo build falhou (codigo $codigo)" }

# --- junta ------------------------------------------------------------------

if (Test-Path $saida) { Remove-Item $saida -Recurse -Force }
New-Item -ItemType Directory -Path $saida -Force | Out-Null

$exes = @("auth-server.exe", "sts-server.exe", "game-server.exe", "launcher.exe")
foreach ($exe in $exes) {
    Copy-Item (Join-Path $rust "target\release\$exe") $saida
}

# O replay completa o mundo enquanto os pacotes nao estao implementados. Sem ele o cliente chega
# na tela de personagem e nao entra no jogo.
$replay = Join-Path $rust "replay.bin"
if (-not (Test-Path $replay)) {
    throw "replay.bin nao existe. Gere com: python tools/export_replay.py build/capture/gf-login.pcapng EmuRustDurak/replay.bin"
}
Copy-Item $replay $saida

foreach ($arquivo in @("INICIAR.bat", "PARAR.bat", "config.txt", "LEIA-ME.txt")) {
    Copy-Item (Join-Path $aqui $arquivo) $saida
}
Copy-Item (Join-Path $aqui "iniciar.ps1") $saida

# --- confere ----------------------------------------------------------------
#
# O nome da conta que aparecia nos bytes capturados e trocado por um neutro na geracao do
# replay.bin. Se um replay antigo entrar no pacote, ele vai junto -- entao conferimos aqui.
$bytes = [System.IO.File]::ReadAllBytes((Join-Path $saida "replay.bin"))
$texto = [System.Text.Encoding]::Unicode.GetString($bytes)
if ($texto.Contains("niZZin")) {
    Write-Host ""
    Write-Host "  ! o replay.bin ainda tem o nome da conta capturada." -ForegroundColor Yellow
    Write-Host "    Regenere com: python tools/export_replay.py build/capture/gf-login.pcapng EmuRustDurak/replay.bin" -ForegroundColor Yellow
    Write-Host ""
}

# --- zipa -------------------------------------------------------------------

$zip = Join-Path $raiz "dist\aion-emulador.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path "$saida\*" -DestinationPath $zip

$tamanho = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host ""
Write-Host "  Pronto." -ForegroundColor Green
Write-Host "    pasta: $saida"
Write-Host "    zip:   $zip  ($tamanho MB)"
Write-Host ""
Write-Host "  Quem receber precisa preencher o CLIENTE no config.txt e rodar o INICIAR.bat."
Write-Host ""
