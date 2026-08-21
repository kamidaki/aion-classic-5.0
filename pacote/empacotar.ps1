# Monta o pacote que vai para outra pessoa: compila, junta o que e necessario, e zipa.
#
# Sao dois pacotes, para dois usos que nao se misturam:
#
#   (padrao)   so os executaveis. Quem recebe roda; nao precisa de Rust nem do repositorio.
#   -Fonte     o codigo. Quem recebe compila e altera.
#
# O criterio do padrao e "roda sem o repositorio". O do -Fonte e "o que o git rastreia, mais o
# replay.bin" -- que nao esta no git e nao da para regenerar sem a captura original.

param([switch]$Fonte)

$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$raiz = Split-Path -Parent $aqui
$rust = Join-Path $raiz "EmuRustDurak"
$saida = Join-Path $raiz "dist\aion-emulador"

Write-Host ""
Write-Host "  Empacotando o servidor local de Aion" -ForegroundColor Cyan
Write-Host ""

# --- pacote de codigo-fonte -------------------------------------------------
#
# A lista de arquivos sai do proprio git: e a definicao mais confiavel de "o que e fonte" que
# existe no repositorio, e ja exclui target/, capturas e o resto do que o .gitignore cobre.
if ($Fonte) {
    $saidaFonte = Join-Path $raiz "dist\aion-emulador-fonte"
    if (Test-Path $saidaFonte) { Remove-Item $saidaFonte -Recurse -Force }
    New-Item -ItemType Directory -Path $saidaFonte -Force | Out-Null

    Push-Location $raiz
    # A base Java sao 359 MB de referencia que nao executa -- fica de fora, e o LEIA-ME-FONTE
    # explica onde encontra-la.
    $arquivos = git ls-files EmuRustDurak docs tools pacote RELATORIO.txt |
        Where-Object { $_ -notlike "EmuRustDurak/aion.db*" }
    Pop-Location

    foreach ($rel in $arquivos) {
        $origem = Join-Path $raiz $rel
        if (-not (Test-Path $origem)) { continue }
        $destino = Join-Path $saidaFonte $rel
        New-Item -ItemType Directory -Path (Split-Path -Parent $destino) -Force | Out-Null
        Copy-Item $origem $destino
    }

    # O replay.bin nao esta no git (deriva da captura), e sem ele o cliente nao entra no mundo.
    Copy-Item (Join-Path $raiz "EmuRustDurak\replay.bin") (Join-Path $saidaFonte "EmuRustDurak")
    Copy-Item (Join-Path $aqui "LEIA-ME-FONTE.txt") (Join-Path $saidaFonte "LEIA-ME.txt")

    $zipFonte = Join-Path $raiz "dist\aion-emulador-fonte.zip"
    if (Test-Path $zipFonte) { Remove-Item $zipFonte -Force }
    Compress-Archive -Path "$saidaFonte\*" -DestinationPath $zipFonte

    $mb = [math]::Round((Get-Item $zipFonte).Length / 1MB, 1)
    Write-Host "  Pronto (codigo-fonte)." -ForegroundColor Green
    Write-Host "    $($arquivos.Count) arquivos rastreados, mais o replay.bin"
    Write-Host "    zip: $zipFonte  ($mb MB)"
    Write-Host ""
    Write-Host "  Quem receber precisa de Rust. O LEIA-ME.txt de dentro explica."
    Write-Host ""
    exit 0
}

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
