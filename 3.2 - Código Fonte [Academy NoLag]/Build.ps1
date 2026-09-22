# Academy NoLag - Production Automated Build & Packaging Engine (.NET 9)
param(
    [string]$Configuration = "Release"
)

$BaseDir = $PSScriptRoot
Set-Location -LiteralPath $BaseDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   ACADEMY NOLAG - AUTOMATED PRODUCTION BUILD ENGINE      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$BuildDir = Join-Path $BaseDir "build"
$DistDir = Join-Path $BaseDir "dist"
$FinalDir = Join-Path $BaseDir "Produto Final"
$TempAppPublish = Join-Path $BuildDir "app_publish"
$TempNodePublish = Join-Path $BuildDir "node_publish"
$TempServicePublish = Join-Path $BuildDir "service_publish"

# 0. Terminate any running Academy NoLag instances to prevent file lock contention
Write-Host "[0/5] Ensuring no previous Academy NoLag processes are running..." -ForegroundColor Cyan
@("Academy - NoLag", "AcademyNoLag", "AcademyNoLag.RelayNode", "AcademyNoLag.Service") | ForEach-Object {
    Get-Process -Name $_ -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            Stop-Process -Id $_.Id -Force -ErrorAction Stop
            Write-Host "  Terminated running instance: $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Yellow
        }
        catch { }
    }
}
Start-Sleep -Milliseconds 600

# 1. Clean previous build artifacts and intermediate compiler/XAML cache
Write-Host "Cleaning build, dist, and intermediate obj/bin cache..." -ForegroundColor Cyan
if (Test-Path -LiteralPath $BuildDir) { Remove-Item -Recurse -Force -LiteralPath $BuildDir }
if (Test-Path -LiteralPath $DistDir) { Remove-Item -Recurse -Force -LiteralPath $DistDir }
if (Test-Path -LiteralPath $FinalDir) { Remove-Item -Recurse -Force -LiteralPath $FinalDir }

Get-ChildItem -LiteralPath (Join-Path $BaseDir "src") -Recurse -Directory | Where-Object { $_.Name -in @("bin", "obj") } | ForEach-Object {
    try { Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
    catch { }
}

# Setup clean folder hierarchy for Produto Final
$FinalModules = Join-Path $FinalDir "modules"
$FinalBin = Join-Path $FinalDir "bin"
$FinalData = Join-Path $FinalDir "data"
$FinalConfig = Join-Path $FinalData "config"
$FinalDocs = Join-Path $FinalData "docs"
$FinalScripts = Join-Path $FinalData "scripts"
$FinalLogs = Join-Path $FinalDir "logs"

[System.IO.Directory]::CreateDirectory($FinalDir) | Out-Null
[System.IO.Directory]::CreateDirectory($FinalModules) | Out-Null
[System.IO.Directory]::CreateDirectory($FinalBin) | Out-Null
[System.IO.Directory]::CreateDirectory($FinalConfig) | Out-Null
[System.IO.Directory]::CreateDirectory($FinalDocs) | Out-Null
[System.IO.Directory]::CreateDirectory($FinalScripts) | Out-Null
[System.IO.Directory]::CreateDirectory($FinalLogs) | Out-Null

Write-Host "[1/5] Running Automated Test Suite..." -ForegroundColor Yellow
dotnet test "src\AcademyNoLag.Tests\AcademyNoLag.Tests.csproj" -c $Configuration --verbosity normal
if ($LASTEXITCODE -ne 0) {
    Write-Error "Test suite failed! Aborting build."
    exit 1
}
Write-Host "[OK] All tests passed successfully!" -ForegroundColor Green

Write-Host "[2/5] Publishing Standalone Single-File Desktop Application (Academy - NoLag.exe)..." -ForegroundColor Yellow
dotnet publish "src\AcademyNoLag.App\AcademyNoLag.App.csproj" -c $Configuration -r win-x64 --self-contained false -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o $TempAppPublish
if ($LASTEXITCODE -ne 0) {
    Write-Error "Publishing App failed."
    exit 1
}

# Copy standalone executable to the root of Produto Final
$publishedExe = Join-Path $TempAppPublish "Academy - NoLag.exe"
if (-not (Test-Path -LiteralPath $publishedExe)) {
    Write-Error "Published executable not found at $publishedExe!"
    exit 1
}
Copy-Item -LiteralPath $publishedExe -Destination (Join-Path $FinalDir "Academy - NoLag.exe") -Force

# Copy application icon to root
$iconPath = Join-Path $BaseDir "src\AcademyNoLag.App\app.ico"
if (Test-Path -LiteralPath $iconPath) {
    Copy-Item -LiteralPath $iconPath -Destination (Join-Path $FinalDir "app.ico") -Force
}

Write-Host "[3/5] Publishing Secondary Execution Modules (RelayNode & Service) to 'modules/' and 'bin/'..." -ForegroundColor Yellow
dotnet publish "src\AcademyNoLag.RelayNode\AcademyNoLag.RelayNode.csproj" -c $Configuration -r win-x64 --self-contained false -o $TempNodePublish
if ($LASTEXITCODE -ne 0) {
    Write-Error "Publishing RelayNode failed."
    exit 1
}
dotnet publish "src\AcademyNoLag.Service\AcademyNoLag.Service.csproj" -c $Configuration -r win-x64 --self-contained false -o $TempServicePublish
if ($LASTEXITCODE -ne 0) {
    Write-Error "Publishing Service failed."
    exit 1
}

# Copy modules & supporting DLLs into modules/ and bin/ (dual compatibility)
Get-ChildItem -LiteralPath $TempNodePublish | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $FinalModules $_.Name) -Recurse -Force
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $FinalBin $_.Name) -Recurse -Force
}
Get-ChildItem -LiteralPath $TempServicePublish | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $FinalModules $_.Name) -Recurse -Force
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $FinalBin $_.Name) -Recurse -Force
}

Write-Host "[4/5] Packaging Configurations, Docs, and Scripts into 'data/'..." -ForegroundColor Yellow

# Copy configs into data/config
$configSrc = Join-Path $BaseDir "config"
if (Test-Path -LiteralPath $configSrc) {
    Get-ChildItem -LiteralPath $configSrc -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $FinalConfig $_.Name) -Force
    }
}

# Copy docs into data/docs
Get-ChildItem -LiteralPath $BaseDir -Filter "*.md" | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $FinalDocs $_.Name) -Force
}

# Copy scripts into data/scripts
@("AddPath.ps1", "InstallService.bat", "UninstallService.bat", "StartRelayNode.bat") | ForEach-Object {
    $src = Join-Path $BaseDir $_
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $FinalScripts $_) -Force
    }
}

# Also ensure AddPath.ps1 exists in Produto Final root for instant user convenience
Copy-Item -LiteralPath (Join-Path $BaseDir "AddPath.ps1") -Destination (Join-Path $FinalDir "AddPath.ps1") -Force

# Hygiene: Remove PDB debug symbols and intermediate localization artifacts from release output
Get-ChildItem -LiteralPath $FinalDir -Recurse -Filter "*.pdb" | ForEach-Object {
    try { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue } catch { }
}

Write-Host "[5/5] Mirroring distribution to 'dist/'..." -ForegroundColor Yellow
[System.IO.Directory]::CreateDirectory($DistDir) | Out-Null
Copy-Item -LiteralPath (Join-Path $FinalDir "*") -Destination $DistDir -Recurse -Force

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   BUILD & PACKAGING SUCCEEDED!                           " -ForegroundColor Green
Write-Host "   - Root Executable:  $FinalDir\Academy - NoLag.exe      " -ForegroundColor White
Write-Host "   - Root Icon:        $FinalDir\app.ico                  " -ForegroundColor White
Write-Host "   - Modules Folder:   $FinalDir\modules\                 " -ForegroundColor White
Write-Host "   - Data/Configs:     $FinalDir\data\config\             " -ForegroundColor White
Write-Host "   - Docs:             $FinalDir\data\docs\               " -ForegroundColor White
Write-Host "   - Scripts:          $FinalDir\data\scripts\            " -ForegroundColor White
Write-Host "   - Logs:             $FinalDir\logs\                    " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
