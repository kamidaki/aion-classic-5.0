<#
.SYNOPSIS
    Reseta a senha do root do MariaDB local. PRECISA de PowerShell como Administrador.

.DESCRIPTION
    Procedimento padrao de recuperacao documentado pela MariaDB:
      1. para o servico MariaDB
      2. sobe um mysqld temporario com --skip-grant-tables
      3. redefine a senha do root
      4. derruba o temporario e religa o servico
      5. confere que a senha nova funciona

    A janela sem autenticacao e o ponto delicado, entao o mysqld temporario sobe numa porta
    separada (3307) presa em 127.0.0.1 -- fora do alcance da rede e sem colidir com nada que
    esperasse encontrar o servidor normal na 3306. Se qualquer passo falhar, o bloco catch
    derruba o temporario e religa o servico, para nao deixar o banco fora do ar.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\reset_mariadb_root.ps1
    powershell -ExecutionPolicy Bypass -File scripts\reset_mariadb_root.ps1 -NewPassword 'outra'
#>
param(
    [string]$NewPassword = '88437295d*',
    [string]$MariaDbHome = 'C:\Program Files\MariaDB 10.6',
    [int]$TempPort = 3307,
    [string]$ServiceName = 'MariaDB'
)

$ErrorActionPreference = 'Stop'

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Este script precisa ser executado como Administrador." -ForegroundColor Red
    exit 1
}

$mysqld     = Join-Path $MariaDbHome 'bin\mysqld.exe'
$mysql      = Join-Path $MariaDbHome 'bin\mysql.exe'
$mysqladmin = Join-Path $MariaDbHome 'bin\mysqladmin.exe'
foreach ($exe in @($mysqld, $mysql, $mysqladmin)) {
    if (-not (Test-Path $exe)) { Write-Host "Nao encontrei: $exe" -ForegroundColor Red; exit 1 }
}

$temp = $null
try {
    Write-Host "[1/5] parando o servico $ServiceName..." -ForegroundColor Cyan
    Stop-Service $ServiceName
    (Get-Service $ServiceName).WaitForStatus('Stopped', '00:00:30')

    Write-Host "[2/5] subindo mysqld temporario sem autenticacao (127.0.0.1:$TempPort)..." -ForegroundColor Cyan
    $temp = Start-Process -FilePath $mysqld -PassThru -WindowStyle Hidden -ArgumentList @(
        '--skip-grant-tables', '--bind-address=127.0.0.1', "--port=$TempPort"
    )

    $pronto = $false
    foreach ($i in 1..30) {
        Start-Sleep -Milliseconds 500
        & $mysql '-u' 'root' '-h' '127.0.0.1' '-P' "$TempPort" '-e' 'SELECT 1;' *> $null
        if ($LASTEXITCODE -eq 0) { $pronto = $true; break }
    }
    if (-not $pronto) { throw "o mysqld temporario nao respondeu em 15s" }

    Write-Host "[3/5] estado atual do root:" -ForegroundColor Cyan
    & $mysql '-u' 'root' '-h' '127.0.0.1' '-P' "$TempPort" '-e' `
        "SELECT user, host, plugin FROM mysql.user WHERE user='root';"

    # FLUSH PRIVILEGES antes: com --skip-grant-tables o sistema de permissoes esta desligado e o
    # ALTER USER seria recusado. O IDENTIFIED VIA garante autenticacao por senha, caso o root
    # esteja num plugin de socket -- que seria, por si so, uma explicacao para a senha nao pegar.
    Write-Host "[4/5] redefinindo a senha..." -ForegroundColor Cyan
    $sql = @"
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('$NewPassword');
FLUSH PRIVILEGES;
"@
    $sql | & $mysql '-u' 'root' '-h' '127.0.0.1' '-P' "$TempPort"
    if ($LASTEXITCODE -ne 0) { throw "ALTER USER falhou" }

    Write-Host "[5/5] derrubando o temporario e religando o servico..." -ForegroundColor Cyan
    & $mysqladmin '-u' 'root' '-h' '127.0.0.1' '-P' "$TempPort" 'shutdown' *> $null
    if ($temp) { $temp.WaitForExit(20000) | Out-Null }
    $temp = $null

    Start-Service $ServiceName
    (Get-Service $ServiceName).WaitForStatus('Running', '00:00:30')

    $env:MYSQL_PWD = $NewPassword
    & $mysql '-u' 'root' '-e' 'SELECT VERSION();' *> $null
    $ok = ($LASTEXITCODE -eq 0)
    $env:MYSQL_PWD = $null

    if ($ok) {
        Write-Host "`nsenha redefinida e conferida. o servico esta no ar." -ForegroundColor Green
    } else {
        Write-Host "`nsenha trocada, mas a conferencia falhou -- veja o plugin listado no passo 3." -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Host "`nFALHOU: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "religando o servico para nao deixar o banco fora do ar..." -ForegroundColor Yellow
    if ($temp -and -not $temp.HasExited) {
        & $mysqladmin '-u' 'root' '-h' '127.0.0.1' '-P' "$TempPort" 'shutdown' *> $null
        Start-Sleep -Seconds 2
        if (-not $temp.HasExited) { Stop-Process -Id $temp.Id -Force }
    }
    try { Start-Service $ServiceName } catch { Write-Host "religue o servico manualmente: net start $ServiceName" -ForegroundColor Red }
    exit 1
}
