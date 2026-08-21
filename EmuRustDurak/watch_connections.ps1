# Aguarda o processo Aion.bin iniciar, depois monitora todas as conexões TCP que ele abre
# (excluindo as portas já conhecidas do auth e STS)
$knownPorts = @(13001, 6600, 80, 443, 135, 49152, 49153, 49154)

Write-Host "Aguardando Aion.bin..." -ForegroundColor Cyan

$proc = $null
while (-not $proc) {
    $proc = Get-Process -Name "aion" -ErrorAction SilentlyContinue | Select-Object -First 1
    Start-Sleep -Milliseconds 100
}
Write-Host "Aion PID: $($proc.Id)  -- monitorando conexoes TCP..." -ForegroundColor Green

$seen = @{}
while ($true) {
    try {
        $conns = Get-NetTCPConnection -OwningProcess $proc.Id -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            $key = "$($c.LocalPort)->$($c.RemoteAddress):$($c.RemotePort) [$($c.State)]"
            if (-not $seen[$key]) {
                $seen[$key] = $true
                if ($c.RemotePort -notin $knownPorts) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss.fff')] NOVO:  $key" -ForegroundColor Yellow
                } else {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss.fff')] auth/sts: $key" -ForegroundColor DarkGray
                }
            }
        }
    } catch {}

    if (-not (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) {
        Write-Host "Aion.bin encerrou." -ForegroundColor Red
        break
    }
    Start-Sleep -Milliseconds 50
}

Write-Host ""
Write-Host "Todas as conexoes observadas:" -ForegroundColor Cyan
$seen.Keys | Sort-Object
