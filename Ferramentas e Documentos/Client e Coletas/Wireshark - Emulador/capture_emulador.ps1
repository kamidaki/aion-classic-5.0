# ==============================================================================
# Aion Classic 5.0 - Captura do trafego do NOSSO emulador (nao do oficial)
# ==============================================================================
# Cliente e emulador na mesma maquina: o Windows entrega esse trafego pela interface de loopback, mesmo quando o cliente conecta
# no IP da rede local (192.168.x.x). O capture_5.0.ps1 escolhe a placa Ethernet e nao ve nada disso.
# As capturas ficam nesta pasta, separadas das oficiais, para nunca serem confundidas com prova do oficial.
param(
    [string]$Assunto = "",
    # portas do cliente: login 2106, jogo 7777, chat 10241 (9014/9021 sao internas entre os servidores do emulador)
    [string]$Filter = "tcp and (port 2106 or port 7777 or port 10241)",
    [int]$MaxFileMB = 100
)

try { $Host.UI.RawUI.WindowTitle = "Aion Classic 5.0 - Captura do Emulador (loopback)" } catch {}

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "        AION CLASSIC 5.0 - CAPTURA DO EMULADOR LOCAL (INTERFACE LOOPBACK)      " -ForegroundColor Yellow -BackgroundColor Black
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. dumpcap
$dumpcapExe = $null
foreach ($path in @("C:\Program Files\Wireshark\dumpcap.exe", "C:\Program Files (x86)\Wireshark\dumpcap.exe", "E:\Programas instalados - Leves\Wireshark\dumpcap.exe")) {
    if (Test-Path -LiteralPath $path) { $dumpcapExe = $path; break }
}
if (-not $dumpcapExe) {
    $cmd = Get-Command dumpcap.exe -ErrorAction SilentlyContinue
    if ($cmd) { $dumpcapExe = $cmd.Path }
}
if (-not $dumpcapExe) {
    Write-Host "[ERRO] dumpcap.exe (Wireshark) nao encontrado." -ForegroundColor Red
    Read-Host "Pressione [ENTER] para fechar..."
    exit 1
}
Write-Host "[*] Dumpcap: $dumpcapExe" -ForegroundColor Green

# 2. Interface de loopback do Npcap (pelo nome, nao pelo numero, que muda entre maquinas)
$loopback = & $dumpcapExe -D 2>&1 | Where-Object { $_ -match "NPF_Loopback" -or $_ -match "loopback traffic" } | Select-Object -First 1
if (-not ($loopback -and ($loopback -match "^(\d+)\."))) {
    Write-Host "[ERRO] Interface de loopback do Npcap nao encontrada." -ForegroundColor Red
    Write-Host "Reinstale o Npcap marcando 'Support loopback traffic' (vem junto com o Wireshark)." -ForegroundColor Yellow
    Read-Host "Pressione [ENTER] para fechar..."
    exit 1
}
$interfaceIndex = $matches[1]
Write-Host "[*] Interface: $loopback" -ForegroundColor Green

# 3. Nome da captura
if ([string]::IsNullOrWhiteSpace($Assunto)) {
    Write-Host ""
    $Assunto = Read-Host "Assunto da captura (ex: aionlook, quest_poeta) [Padrao: emulador]"
    if ([string]::IsNullOrWhiteSpace($Assunto)) { $Assunto = "emulador" }
}
$Assunto = ($Assunto -replace '[^A-Za-z0-9_\-]', '_')

$saveDir = $PSScriptRoot
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$pcapFullPath = Join-Path $saveDir "emulador_${Assunto}_${timestamp}.pcapng"
$filesizeKB = $MaxFileMB * 1024

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "  * Arquivo : $pcapFullPath" -ForegroundColor Cyan
Write-Host "  * Filtro  : $Filter" -ForegroundColor Gray
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  >>> GRAVANDO. Abra o cliente e entre no emulador DEPOIS de iniciar esta janela, <<<" -ForegroundColor Yellow -BackgroundColor Black
Write-Host "  >>> para a captura pegar o S_KEY do login e conseguir decifrar a sessao.        <<<" -ForegroundColor Yellow -BackgroundColor Black
Write-Host "  >>> Para FINALIZAR, pressione [Ctrl + C] nesta janela.                         <<<" -ForegroundColor Red -BackgroundColor Black
Write-Host ""

# 4. Captura
try {
    & $dumpcapExe -i $interfaceIndex -f $Filter -b filesize:$filesizeKB -w $pcapFullPath
} catch {
    Write-Host "`n[!] Finalizando dumpcap..." -ForegroundColor Yellow
}

Write-Host ""
$generated = Get-ChildItem -LiteralPath $saveDir -Filter "emulador_${Assunto}_${timestamp}*.pcapng" | Sort-Object Name
if ($generated) {
    foreach ($file in $generated) {
        Write-Host "  [OK] $($file.Name) ($([math]::Round($file.Length / 1MB, 2)) MB)" -ForegroundColor Green
    }
    $decoder = Join-Path (Split-Path (Split-Path $saveDir -Parent) -Parent) "Ferramentas Python e PowerShell\Ferramentas Python\aion_pcap.py"
    Write-Host ""
    Write-Host "Para listar os opcodes desta captura:" -ForegroundColor White
    Write-Host "  python ""$decoder"" ""$($generated[0].FullName)"" --opcodes" -ForegroundColor Yellow
} else {
    Write-Host "  [AVISO] Nenhum pacote capturado. O emulador estava rodando e o cliente conectou nele?" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Pressione [ENTER] para encerrar..."
