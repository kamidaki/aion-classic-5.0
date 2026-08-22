# =========================================================================
#  AION CLASSIC 4.5 RUST EMULATOR - INICIALIZADOR DE PRODUÇÃO (1-CLIQUE)
# =========================================================================

$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $aqui

function Escrever-Erro($msg) {
    Write-Host ""
    Write-Host "  [ERRO] $msg" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Verifique o arquivo config.txt antes de prosseguir." -ForegroundColor Yellow
    Write-Host ""
    try { Read-Host "  Pressione Enter para fechar" | Out-Null } catch { }
    exit 1
}

function Escrever-Aviso($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Escrever-Ok($msg)    { Write-Host "  [+] $msg" -ForegroundColor Green }
function Escrever-Info($msg)  { Write-Host "  [*] $msg" -ForegroundColor Cyan }

Clear-Host
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "  AION CLASSIC 4.5 - EMULADOR RUST DE ALTA PERFORMANCE                   " -ForegroundColor White
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Carregar Configuração
if (-not (Test-Path "config.txt")) {
    Escrever-Erro "Arquivo config.txt não encontrado no diretório $aqui."
}

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

# 2. Descobrir / Validar IP
if ([string]::IsNullOrWhiteSpace($ip)) {
    $candidato = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object {
            $_.IPAddress -notlike "127.*" -and
            $_.IPAddress -notlike "169.254.*" -and
            $_.InterfaceAlias -notlike "*Loopback*"
        } |
        Select-Object -First 1 -ExpandProperty IPAddress
    if (-not $candidato) { Escrever-Erro "Não foi possível detectar o IP da rede local. Defina 'IP =' no config.txt." }
    $ip = $candidato
    Escrever-Ok "IP detectado automaticamente: $ip"
} else {
    Escrever-Ok "IP configurado: $ip"
}

if ($ip -like "127.*") {
    Escrever-Erro "O IP anunciado não pode ser 127.0.0.1 (Loopback). O cliente Aion 4.5 descarta essas conexões."
}

# 3. Finalizar instâncias antigas para evitar conflito de portas
Escrever-Info "Verificando processos em execução..."
$antigos = Get-Process -Name sts-server, auth-server, game-server, launcher -ErrorAction SilentlyContinue
if ($antigos) {
    Escrever-Aviso "Encerrando instâncias antigas do servidor..."
    $antigos | Stop-Process -Force -Confirm:$false
    Start-Sleep -Milliseconds 800
}

# Fechar gfclient oficial se estiver aberto
$gf = Get-Process -Name gfclient -ErrorAction SilentlyContinue
if ($gf) {
    Escrever-Aviso "O launcher oficial (gfclient.exe) foi detectado aberto. Encerrando para liberar o Named Pipe..."
    $gf | Stop-Process -Force -Confirm:$false
    Start-Sleep -Milliseconds 500
}

# 4. Validar Executáveis
$exes = @("sts-server.exe", "auth-server.exe", "game-server.exe")
foreach ($exe in $exes) {
    if (-not (Test-Path $exe)) {
        Escrever-Erro "Executável obrigatório '$exe' não encontrado. Compile o projeto ou rode scripts/publicar_deploy.ps1."
    }
}

# 5. Iniciar os Serviços do Servidor
Write-Host ""
Escrever-Info "Inicializando serviços do servidor..."

# 5.1 STS Server
Start-Process -FilePath ".\sts-server.exe" -WindowStyle Normal
Start-Sleep -Milliseconds 600
Escrever-Ok "STS Server iniciado na porta 10241."

# 5.2 Auth Server
Start-Process -FilePath ".\auth-server.exe" -ArgumentList $ip -WindowStyle Normal
Start-Sleep -Milliseconds 600
Escrever-Ok "Auth Server iniciado na porta 2106 (IP anunciado: $ip)."

# 5.3 Game Server
Start-Process -FilePath ".\game-server.exe" -ArgumentList $ip -WindowStyle Normal
Start-Sleep -Milliseconds 1000
Escrever-Ok "Game Server iniciado na porta 7777 (IP anunciado: $ip)."

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host "  SERVIDOR ONLINE COM SUCESSO!                                          " -ForegroundColor White
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Pressione 'L' para abrir o Launcher e iniciar o Cliente do jogo." -ForegroundColor Yellow
Write-Host "  Pressione 'Q' ou feche esta janela para manter os servidores rodando." -ForegroundColor Gray
Write-Host ""

$tecla = Read-Host "  Opção"
if ($tecla -eq "L" -or $tecla -eq "l") {
    if (Test-Path ".\launcher.exe") {
        if (-not [string]::IsNullOrWhiteSpace($cliente) -and (Test-Path $cliente)) {
            Escrever-Info "Iniciando Launcher e cliente: $cliente..."
            Start-Process -FilePath ".\launcher.exe" -ArgumentList "`"$cliente`"", "`"$usuario`""
        } else {
            Escrever-Aviso "Caminho do cliente não encontrado em config.txt. Abrindo launcher..."
            Start-Process -FilePath ".\launcher.exe"
        }
    }
}
