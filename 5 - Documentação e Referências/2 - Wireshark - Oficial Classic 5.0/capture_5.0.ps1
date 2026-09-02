# ==============================================================================
# Aion Classic 5.0 - Suite Automatizada de Captura de Trafego de Rede (Wireshark)
# ==============================================================================
param(
    [string]$TargetSubDir = "",
    [string]$Filter = "tcp and (port 2106 or port 7777 or port 10241 or port 13001 or port 6600 or portrange 7770-7790)",
    [int]$MaxFileMB = 100,
    [switch]$TestOnly
)

try {
    $Host.UI.RawUI.WindowTitle = "Aion Classic 5.0 - Gravador de Trafego de Rede (Wireshark)"
} catch {}

function Write-Header {
    try { Clear-Host } catch {}
    Write-Host "==============================================================================" -ForegroundColor Cyan
    Write-Host "       AION CLASSIC 5.0 - SUITE DE CAPTURA DE REDE (OFICIAL GAMEFORGE)        " -ForegroundColor Yellow -BackgroundColor Black
    Write-Host "==============================================================================" -ForegroundColor Cyan
    Write-Host ""
}

Write-Header

# 1. Localizar dumpcap / tshark
$wiresharkPaths = @(
    "E:\Programas instalados - Leves\Wireshark\dumpcap.exe",
    "C:\Program Files\Wireshark\dumpcap.exe",
    "C:\Program Files (x86)\Wireshark\dumpcap.exe"
)

$dumpcapExe = $null
foreach ($path in $wiresharkPaths) {
    if (Test-Path $path) {
        $dumpcapExe = $path
        break
    }
}

if (-not $dumpcapExe) {
    $cmd = Get-Command dumpcap.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        $dumpcapExe = $cmd.Path
    }
}

if (-not $dumpcapExe) {
    Write-Host "[ERRO] Executavel do dumpcap/Wireshark nao encontrado!" -ForegroundColor Red
    Write-Host "Verifique se o Wireshark esta instalado em 'E:\Programas instalados - Leves\Wireshark' ou no PATH." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Pressione [ENTER] para fechar..."
    exit 1
}

Write-Host "[*] Dumpcap localizado: $dumpcapExe" -ForegroundColor Green

# 2. Localizar Interface de Rede Ativa
$baseDir = $PSScriptRoot
if (-not (Test-Path $baseDir)) {
    New-Item -ItemType Directory -Path $baseDir -Force | Out-Null
}

$interfaceIndex = "4" # Padrao Ethernet identificado
$interfaceOutput = & $dumpcapExe -D 2>&1
$ethernetLine = $interfaceOutput | Where-Object { $_ -match "Ethernet" -or $_ -match "Intel" -or $_ -match "Realtek" } | Select-Object -First 1

if ($ethernetLine -and ($ethernetLine -match "^(\d+)\.")) {
    $interfaceIndex = $matches[1]
    Write-Host "[*] Interface de captura selecionada: $ethernetLine" -ForegroundColor Green
} else {
    Write-Host "[*] Usando interface padrao ID: $interfaceIndex" -ForegroundColor Green
}

if ($TestOnly) {
    Write-Host "[OK] Teste de ambiente concluido com sucesso!" -ForegroundColor Green
    exit 0
}

# 3. Menu Interativo de Modulos (caso nao tenha passado por parametro)
if ([string]::IsNullOrWhiteSpace($TargetSubDir)) {
    while ($true) {
        Write-Header
        Write-Host "SELECIONE A CATEGORIA DE CAPTURA QUE DESEJA GRAVAR:" -ForegroundColor White
        Write-Host "------------------------------------------------------------------------------" -ForegroundColor DarkGray
        Write-Host " [1]  01_Login_World              - Login e Entrada no Mundo (Elyos / Asmodians)" -ForegroundColor Cyan
        Write-Host " [2]  02_Character_Creation       - Criacao de Personagem (Classes / Aparência)" -ForegroundColor White
        Write-Host " [3]  03_Tutorial - ELYOS         - Tutorial Inicial Elyos (13 Classes + Deslogue)" -ForegroundColor Yellow
        Write-Host " [4]  03_Tutorial - ASMODIANS     - Tutorial Inicial Asmodians (13 Classes + Deslogue)" -ForegroundColor Yellow
        Write-Host " [5]  04_Realizando_Missoes       - Campanhas, Quests, Locate/Teleport e NPCs" -ForegroundColor Blue
        Write-Host " [6]  05_Combate_Skills           - Rotacoes, Habilidades e Combate" -ForegroundColor Magenta
        Write-Host " [7]  06_Sistemas_Novos_5.0       - Instancias, Daeva Pass e Sistemas 5.0" -ForegroundColor Green
        Write-Host " [8]  07_Deletar_Char_Voltar_Lobby- Deletar Personagem e Voltar pra Tela de Servidores" -ForegroundColor Red
        Write-Host " [9]  Digitar Nome / Pasta Personalizada" -ForegroundColor DarkYellow
        Write-Host " [0]  Sair" -ForegroundColor Red
        Write-Host "------------------------------------------------------------------------------" -ForegroundColor DarkGray

        $catChoice = Read-Host "Digite a categoria desejada (0-9) [Padrao: 3]"
        if ([string]::IsNullOrWhiteSpace($catChoice)) { $catChoice = "3" }

        if ($catChoice -eq "0") {
            Write-Host "Operacao cancelada pelo usuario." -ForegroundColor Yellow
            exit 0
        }

        if ($catChoice -eq "1") {
            Write-Header
            Write-Host "01_Login_World - Selecione a Raca:" -ForegroundColor White
            Write-Host " [1] Elyos" -ForegroundColor Cyan
            Write-Host " [2] Asmodians" -ForegroundColor Cyan
            Write-Host " [0] Voltar" -ForegroundColor Red
            $sub = Read-Host "Opcao (1-2) [Padrao: 1]"
            if ($sub -eq "2") { $TargetSubDir = "01_Login_World\Asmodians"; break }
            elseif ($sub -eq "0") { continue }
            else { $TargetSubDir = "01_Login_World\Elyos"; break }
        }

        if ($catChoice -eq "2") {
            Write-Header
            Write-Host "02_Character_Creation - Selecione a Raca:" -ForegroundColor White
            Write-Host " [1] Elyos" -ForegroundColor White
            Write-Host " [2] Asmodians" -ForegroundColor White
            Write-Host " [0] Voltar" -ForegroundColor Red
            $sub = Read-Host "Opcao (1-2) [Padrao: 1]"
            if ($sub -eq "2") { $TargetSubDir = "02_Character_Creation\Asmodians"; break }
            elseif ($sub -eq "0") { continue }
            else { $TargetSubDir = "02_Character_Creation\Elyos"; break }
        }

        if ($catChoice -eq "3" -or $catChoice -eq "4") {
            $race = if ($catChoice -eq "3") { "Elyos" } else { "Asmodians" }
            Write-Header
            Write-Host "03_Tutorial - $race - SELECIONE A CLASSE:" -ForegroundColor Yellow
            Write-Host "------------------------------------------------------------------------------" -ForegroundColor DarkGray
            Write-Host " [1]  01_Soul_Reaper           - Soul Reaper (Male / Female)" -ForegroundColor Cyan
            Write-Host " [2]  02_Phoenix               - Phoenix (Male / Female)" -ForegroundColor Cyan
            Write-Host " [3]  03_Gladiator             - Gladiator (Male / Female)" -ForegroundColor White
            Write-Host " [4]  04_Templar               - Templar (Male / Female)" -ForegroundColor White
            Write-Host " [5]  05_Assassin              - Assassin (Male / Female)" -ForegroundColor White
            Write-Host " [6]  06_Ranger                - Ranger (Male / Female)" -ForegroundColor White
            Write-Host " [7]  07_Sorcerer              - Sorcerer (Male / Female)" -ForegroundColor White
            Write-Host " [8]  08_SpiritMaster          - SpiritMaster (Male / Female)" -ForegroundColor White
            Write-Host " [9]  09_Cleric                - Cleric (Male / Female)" -ForegroundColor White
            Write-Host " [10] 10_Chanter               - Chanter (Male / Female)" -ForegroundColor White
            Write-Host " [11] 11_Revenant              - Revenant (Male / Female)" -ForegroundColor Cyan
            Write-Host " [12] 12_Brawler               - Brawler (Male / Female)" -ForegroundColor Cyan
            Write-Host " [13] 13_Luminess              - Luminess (Female only)" -ForegroundColor Magenta
            Write-Host " [14] Deslogue_Intermediario   - Retorno ao mapa intermediario no meio do tutorial" -ForegroundColor DarkYellow
            Write-Host " [0]  Voltar" -ForegroundColor Red
            Write-Host "------------------------------------------------------------------------------" -ForegroundColor DarkGray

            $classChoice = Read-Host "Selecione a Classe (1-14) [Padrao: 1]"
            if ([string]::IsNullOrWhiteSpace($classChoice)) { $classChoice = "1" }

            $classFolder = switch ($classChoice) {
                "1"  { "01_Soul_Reaper" }
                "2"  { "02_Phoenix" }
                "3"  { "03_Gladiator" }
                "4"  { "04_Templar" }
                "5"  { "05_Assassin" }
                "6"  { "06_Ranger" }
                "7"  { "07_Sorcerer" }
                "8"  { "08_SpiritMaster" }
                "9"  { "09_Cleric" }
                "10" { "10_Chanter" }
                "11" { "11_Revenant" }
                "12" { "12_Brawler" }
                "13" { "13_Luminess" }
                "14" { "Deslogue_Intermediario" }
                "0"  { "BACK" }
                default { "01_Soul_Reaper" }
            }

            if ($classFolder -eq "BACK") { continue }
            $TargetSubDir = "03_Tutorial\$race\$classFolder"
            break
        }

        if ($catChoice -eq "5") {
            Write-Header
            Write-Host "04_Realizando_Missoes - Selecione o Modulo:" -ForegroundColor Blue
            Write-Host " [1] Elyos - Campanha Poeta" -ForegroundColor Cyan
            Write-Host " [2] Elyos - Campanha Verteron" -ForegroundColor Cyan
            Write-Host " [3] Elyos - Campanha Sanctum" -ForegroundColor Cyan
            Write-Host " [4] Elyos - Quests Normais" -ForegroundColor Cyan
            Write-Host " [5] Elyos - Teleport / Locate NPCs" -ForegroundColor Cyan
            Write-Host " [6] Asmodians - Campanha Ishalgen" -ForegroundColor White
            Write-Host " [7] Asmodians - Campanha Altgard" -ForegroundColor White
            Write-Host " [8] Asmodians - Campanha Pandaemonium" -ForegroundColor White
            Write-Host " [9] Asmodians - Quests Normais" -ForegroundColor White
            Write-Host " [10] Asmodians - Teleport / Locate NPCs" -ForegroundColor White
            Write-Host " [0] Voltar" -ForegroundColor Red

            $qChoice = Read-Host "Opcao (1-10) [Padrao: 1]"
            if ([string]::IsNullOrWhiteSpace($qChoice)) { $qChoice = "1" }

            $TargetSubDir = switch ($qChoice) {
                "1" { "04_Realizando_Missoes\Elyos\Campanha_Poeta" }
                "2" { "04_Realizando_Missoes\Elyos\Campanha_Verteron" }
                "3" { "04_Realizando_Missoes\Elyos\Campanha_Sanctum" }
                "4" { "04_Realizando_Missoes\Elyos\Quests_Normais" }
                "5" { "04_Realizando_Missoes\Elyos\Teleport_Locate_NPCs" }
                "6" { "04_Realizando_Missoes\Asmodians\Campanha_Ishalgen" }
                "7" { "04_Realizando_Missoes\Asmodians\Campanha_Altgard" }
                "8" { "04_Realizando_Missoes\Asmodians\Campanha_Pandaemonium" }
                "9" { "04_Realizando_Missoes\Asmodians\Quests_Normais" }
                "10" { "04_Realizando_Missoes\Asmodians\Teleport_Locate_NPCs" }
                "0" { "BACK" }
                default { "04_Realizando_Missoes\Elyos\Campanha_Poeta" }
            }

            if ($TargetSubDir -eq "BACK") { continue }
            break
        }

        if ($catChoice -eq "6") {
            Write-Header
            Write-Host "05_Combate_Skills - Selecione a Raca:" -ForegroundColor Magenta
            Write-Host " [1] Elyos" -ForegroundColor Cyan
            Write-Host " [2] Asmodians" -ForegroundColor Cyan
            Write-Host " [0] Voltar" -ForegroundColor Red
            $sub = Read-Host "Opcao (1-2) [Padrao: 1]"
            if ($sub -eq "2") { $TargetSubDir = "05_Combate_Skills\Asmodians"; break }
            elseif ($sub -eq "0") { continue }
            else { $TargetSubDir = "05_Combate_Skills\Elyos"; break }
        }

        if ($catChoice -eq "7") {
            $TargetSubDir = "06_Sistemas_Novos_5.0"
            break
        }

        if ($catChoice -eq "8") {
            Write-Header
            Write-Host "07_Deletar_Personagem_Voltar_Servidores - Selecione a Raca:" -ForegroundColor Red
            Write-Host " [1] Elyos" -ForegroundColor Cyan
            Write-Host " [2] Asmodians" -ForegroundColor Cyan
            Write-Host " [0] Voltar" -ForegroundColor Red
            $sub = Read-Host "Opcao (1-2) [Padrao: 1]"
            if ($sub -eq "2") { $TargetSubDir = "07_Deletar_Personagem_Voltar_Servidores\Asmodians"; break }
            elseif ($sub -eq "0") { continue }
            else { $TargetSubDir = "07_Deletar_Personagem_Voltar_Servidores\Elyos"; break }
        }

        if ($catChoice -eq "9") {
            $custom = Read-Host "Digite o caminho relativo da pasta (ex: 03_Tutorial\Elyos\01_Soul_Reaper)"
            if ([string]::IsNullOrWhiteSpace($custom)) { $custom = "Outros" }
            $TargetSubDir = $custom
            break
        }
    }
}

# 4. Preparar Diretorio e Nome de Arquivo
$fullSaveDir = Join-Path $baseDir $TargetSubDir
if (-not (Test-Path $fullSaveDir)) {
    New-Item -ItemType Directory -Path $fullSaveDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$prefix = ($TargetSubDir -replace '[\\]', '_')
$pcapFileName = "${prefix}_${timestamp}.pcapng"
$pcapFullPath = Join-Path $fullSaveDir $pcapFileName
$filesizeKB = $MaxFileMB * 1024

Write-Header
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "                   CONFIGURACAO DA SESSAO DE GRAVACAO                         " -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "  * Modulo Selecionado : $TargetSubDir" -ForegroundColor Cyan
Write-Host "  * Pasta de Gravacao  : $fullSaveDir" -ForegroundColor Cyan
Write-Host "  * Prefixo do Arquivo : $pcapFileName" -ForegroundColor Cyan
Write-Host "  * Divisao de Arquivo : Maximo de ${MaxFileMB} MB por chunk (.pcapng)" -ForegroundColor Yellow
Write-Host "  * Filtro BPF         : $Filter" -ForegroundColor Gray
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  >>> [o] GRAVANDO TRAFEGO DE REDE EM TEMPO REAL... <<<" -ForegroundColor Yellow -BackgroundColor Black
Write-Host "  >>> Abra o Aion Classic 5.0 oficial e jogue normalmente. <<<" -ForegroundColor White
Write-Host "  >>> Para FINALIZAR a gravacao, pressione [Ctrl + C] nesta janela. <<<" -ForegroundColor Red -BackgroundColor Black
Write-Host ""

# 5. Executar dumpcap
try {
    & $dumpcapExe -i $interfaceIndex -f $Filter -b filesize:$filesizeKB -w $pcapFullPath
} catch {
    Write-Host "`n[!] Finalizando dumpcap..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "                         COLETA FINALIZADA COM SUCESSO                        " -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "Arquivos salvos em: $fullSaveDir" -ForegroundColor Cyan
Write-Host ""

$generatedFiles = Get-ChildItem -Path $fullSaveDir -Filter "*.pcapng" | Sort-Object LastWriteTime -Descending | Select-Object -First 5
if ($generatedFiles) {
    foreach ($file in $generatedFiles) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Host "  [OK] $($file.Name) ($sizeMB MB)" -ForegroundColor Green
    }
} else {
    Write-Host "  [AVISO] Nenhum pacote foi capturado nos filtros especificados durante esta sessao." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Dica de Analise: Para decodificar e listar os opcodes desta captura:" -ForegroundColor White
if ($generatedFiles -and $generatedFiles.Count -gt 0) {
    $latest = $generatedFiles[0].FullName
    Write-Host "  python ""6 - Ferramentas\aion_pcap.py"" ""$latest"" --opcodes" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Pressione [ENTER] para encerrar..."
