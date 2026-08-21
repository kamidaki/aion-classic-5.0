# Sobe o emulador inteiro e abre o cliente.
#
# Le config.txt, confere o que precisa estar no lugar, e so entao inicia -- porque quase toda
# falha aqui produz o mesmo sintoma no cliente ("nao consigo conectar"), e o servidor certo
# rodando com a configuracao errada e indistinguivel de servidor quebrado.

$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $aqui

function Erro($msg) {
    Write-Host ""
    Write-Host "  ERRO: $msg" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Corrija o config.txt e rode de novo." -ForegroundColor Yellow
    Write-Host ""
    try { Read-Host "  Enter para fechar" | Out-Null } catch { }
    exit 1
}

function Aviso($msg) { Write-Host "  ! $msg" -ForegroundColor Yellow }
function Ok($msg)    { Write-Host "  + $msg" -ForegroundColor Green }

Write-Host ""
Write-Host "  Aion Classic 4.5 - servidor local" -ForegroundColor Cyan
Write-Host "  ---------------------------------"
Write-Host ""

# --- configuracao -----------------------------------------------------------

if (-not (Test-Path "config.txt")) { Erro "nao achei o config.txt aqui do lado." }

$cfg = @{}
foreach ($linha in Get-Content "config.txt") {
    $t = $linha.Trim()
    if ($t -eq "" -or $t.StartsWith("#")) { continue }
    $i = $t.IndexOf("=")
    if ($i -lt 1) { continue }
    $cfg[$t.Substring(0, $i).Trim().ToUpper()] = $t.Substring($i + 1).Trim()
}

$cliente = $cfg["CLIENTE"]
$ip      = $cfg["IP"]
$dados   = $cfg["DADOS"]
$usuario = $cfg["USUARIO"]
if ([string]::IsNullOrWhiteSpace($usuario)) { $usuario = "durak" }

# --- o cliente do jogo ------------------------------------------------------

if ([string]::IsNullOrWhiteSpace($cliente)) {
    Erro "CLIENTE nao esta preenchido no config.txt. Aponte para o aion.bin da sua instalacao."
}
if (-not (Test-Path $cliente)) {
    Erro "nao achei o cliente em '$cliente'. Confira o caminho em CLIENTE no config.txt."
}
Ok "cliente: $cliente"

# --- o IP anunciado ---------------------------------------------------------
#
# O cliente 4.5 DESCARTA entradas de loopback na lista de servidores, antes de tentar conectar.
# Com 127.0.0.1 nao sai nem um pacote, e a mensagem na tela e a mesma de servidor fora do ar.

if ([string]::IsNullOrWhiteSpace($ip)) {
    $candidato = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object {
            $_.IPAddress -notlike "127.*" -and
            $_.IPAddress -notlike "169.254.*" -and
            $_.InterfaceAlias -notlike "*Loopback*"
        } |
        Select-Object -First 1 -ExpandProperty IPAddress
    if (-not $candidato) { Erro "nao consegui descobrir o IP da sua rede. Preencha IP no config.txt." }
    $ip = $candidato
    Ok "IP da rede (detectado): $ip"
} else {
    Ok "IP da rede (config.txt): $ip"
}

if ($ip -like "127.*") {
    Erro "IP nao pode ser loopback. O cliente 4.5 descarta essas entradas sem nem tentar conectar."
}

# --- dados do cliente (opcional) --------------------------------------------

if (-not [string]::IsNullOrWhiteSpace($dados)) {
    if (Test-Path $dados) { Ok "dados do cliente: $dados" }
    else { Aviso "DADOS aponta para '$dados', que nao existe. Seguindo sem o catalogo de NPCs e itens." }
} else {
    Aviso "sem DADOS configurado. O servidor roda igual; so nao resolve nome de NPC e item nos logs."
}

# --- o launcher oficial nao pode estar aberto -------------------------------
#
# O gfclient.exe cria o mesmo named pipe que o nosso launcher, e o cliente conecta no dele.
# O sintoma e o cliente cair no formulario de login manual, sem nenhum erro do nosso lado.

$gf = Get-Process -Name gfclient -ErrorAction SilentlyContinue
if ($gf) {
    Aviso "o launcher oficial (gfclient.exe) esta aberto e sequestra a conexao. Fechando."
    $gf | Stop-Process -Force -Confirm:$false
    Start-Sleep -Seconds 2
}

# --- limpa sobras de execucoes anteriores -----------------------------------

$sobras = Get-Process -Name auth-server, sts-server, game-server, launcher, Aion.bin -ErrorAction SilentlyContinue
if ($sobras) {
    Aviso "fechando processos de uma execucao anterior."
    $sobras | Stop-Process -Force -Confirm:$false
    Start-Sleep -Seconds 2
}

# --- sobe os tres servidores ------------------------------------------------

Write-Host ""
Write-Host "  Subindo os servidores..." -ForegroundColor Cyan

$env:AION_GAME_IP = $ip
$env:AION_CLIENT = $cliente
if (-not [string]::IsNullOrWhiteSpace($dados)) { $env:AION_DATA_DIR = $dados }

Start-Process -FilePath ".\auth-server.exe" -WorkingDirectory $aqui
Start-Process -FilePath ".\sts-server.exe"  -WorkingDirectory $aqui
Start-Process -FilePath ".\game-server.exe" -WorkingDirectory $aqui

# Espera as portas abrirem em vez de dormir um tempo fixo: em maquina lenta o cliente chegava
# antes do servidor estar ouvindo.
$portas = @(13001, 6600, 7777)
$limite = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $limite) {
    $abertas = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $portas -contains $_.LocalPort } |
        Select-Object -ExpandProperty LocalPort -Unique)
    if ($abertas.Count -eq $portas.Count) { break }
    Start-Sleep -Milliseconds 500
}

$abertas = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $portas -contains $_.LocalPort } |
    Select-Object -ExpandProperty LocalPort -Unique)
$faltando = $portas | Where-Object { $abertas -notcontains $_ }

if ($faltando) {
    Erro "estas portas nao abriram: $($faltando -join ', '). Veja as janelas dos servidores."
}
Ok "auth (13001), STS (6600) e game (7777) no ar"

# --- abre o cliente ---------------------------------------------------------

Write-Host ""
Write-Host "  Abrindo o cliente como '$usuario'..." -ForegroundColor Cyan
Start-Process -FilePath ".\launcher.exe" -ArgumentList "--auto", $usuario -WorkingDirectory $aqui

Write-Host ""
Write-Host "  Pronto. O cliente demora um pouco para abrir." -ForegroundColor Green
Write-Host ""
Write-Host "  O que esperar: termos -> lista de servidores -> personagem -> Pandaemonium."
Write-Host "  Se pedir PIN, confirme qualquer valor."
Write-Host ""
Write-Host "  Para fechar tudo depois, rode o PARAR.bat."
Write-Host ""
# Segura a janela aberta para a mensagem acima ser lida. Falha em terminal nao-interativo, e
# nesse caso nao ha janela para segurar.
try { Read-Host "  Enter para fechar esta janela (os servidores continuam rodando)" | Out-Null } catch { }
