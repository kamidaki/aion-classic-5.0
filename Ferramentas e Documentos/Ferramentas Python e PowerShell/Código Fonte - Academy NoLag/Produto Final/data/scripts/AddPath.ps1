# AddPath.ps1 - Permanently registers Academy NoLag in User and System PATH
[CmdletBinding()]
param()

$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if (-not $scriptDir) {
    $scriptDir = (Get-Location).Path
}

# Resolve the Produto Final directory containing Academy - NoLag.exe
if (Test-Path -LiteralPath (Join-Path $scriptDir "Academy - NoLag.exe")) {
    $target = (Get-Item -LiteralPath $scriptDir).FullName
} elseif (Test-Path -LiteralPath (Join-Path $scriptDir "Produto Final")) {
    $target = (Get-Item -LiteralPath (Join-Path $scriptDir "Produto Final")).FullName
} elseif (Test-Path -LiteralPath (Join-Path (Split-Path -Parent (Split-Path -Parent $scriptDir)) "Produto Final")) {
    $target = (Get-Item -LiteralPath (Join-Path (Split-Path -Parent (Split-Path -Parent $scriptDir)) "Produto Final")).FullName
} else {
    $target = (Get-Item -LiteralPath (Join-Path $scriptDir "Produto Final")).FullName
}

Write-Host "Configuring Windows PATH for: $target"

# 1. User PATH: Remove non-existent or corrupted paths and add the valid target path
$rawUser = [Environment]::GetEnvironmentVariable("PATH", "User")
$userList = @()
if ($rawUser) {
    $userList = $rawUser -split ";" | Where-Object {
        $_.Trim() -and (Test-Path -LiteralPath $_ -ErrorAction SilentlyContinue) -and ($_ -ne $target)
    }
}
$userList += $target
$newUserPath = ($userList | Select-Object -Unique) -join ";"
[Environment]::SetEnvironmentVariable("PATH", $newUserPath, "User")
Write-Host "[OK] Added to User PATH successfully: $target"

# 2. Machine (System) PATH: Clean up and add (requires elevation, best-effort)
try {
    $rawMach = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $machList = @()
    if ($rawMach) {
        $machList = $rawMach -split ";" | Where-Object {
            $_.Trim() -and (Test-Path -LiteralPath $_ -ErrorAction SilentlyContinue) -and ($_ -ne $target)
        }
    }
    $machList += $target
    $newMachPath = ($machList | Select-Object -Unique) -join ";"
    [Environment]::SetEnvironmentVariable("PATH", $newMachPath, "Machine")
    Write-Host "[OK] Added to Machine (System) PATH successfully: $target"
} catch {
    Write-Host "[INFO] Machine PATH requires administrator elevation. User PATH is active."
}

# Refresh current session PATH
$env:PATH = "$env:PATH;$target"
Write-Host "[DONE] Path registration complete."
