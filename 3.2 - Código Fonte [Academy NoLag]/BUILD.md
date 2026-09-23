# Academy NoLag — Build & Compilation Guide

This document describes the prerequisites, toolchain specifications, and step-by-step instructions to compile and package **Academy NoLag** from source code.

---

## 1. Prerequisites

- **Operating System**: Windows 10 (Version 19041+) or Windows 11 (x64)
- **Runtime & SDK**: .NET 9.0 SDK (version `9.0.300` or higher) with `Microsoft.WindowsDesktop.App`
- **Language**: C# 13.0
- **Optional**: Visual Studio 2022 (v17.12+) or Visual Studio Code with C# Dev Kit extension

---

## 2. Solution Structure

```text
AcademyNoLag.sln
├── src/
│   ├── AcademyNoLag.Core/           # Models, algorithms, and interfaces
│   ├── AcademyNoLag.Network/        # Win32 IP Helper interop & probers
│   ├── AcademyNoLag.Detection/      # Process monitor & endpoint discovery
│   ├── AcademyNoLag.Routing/        # Routing engine, failsafe & analyzer
│   ├── AcademyNoLag.Relay/          # Binary wire protocol & client
│   ├── AcademyNoLag.Redirection/    # Socket proxy & WFP dynamic session
│   ├── AcademyNoLag.Persistence/    # JSON/SQLite configuration stores
│   ├── AcademyNoLag.Diagnostics/    # Logging, benchmark runner, telemetry
│   ├── AcademyNoLag.RelayNode/      # Standalone edge server executable
│   ├── AcademyNoLag.Service/        # Privileged Windows background service
│   ├── AcademyNoLag.App/            # Hardware-accelerated WPF desktop GUI
│   └── AcademyNoLag.Tests/          # Automated xUnit test suite
├── build/                           # Raw compiler publish output
├── dist/                            # Packaged production distribution
├── Build.ps1                        # Master automated PowerShell build script
└── Build.bat                        # One-click command line build launcher
```

---

## 3. Automated One-Click Build

To build the entire solution, run all 21 automated tests, publish release binaries, and generate the final distribution folder, simply run:

```cmd
Build.bat
```

Or via PowerShell:

```powershell
.\Build.ps1 -Configuration Release
```

---

## 4. Manual Compilation Steps

### 4.1 Restore Dependencies
```powershell
dotnet restore AcademyNoLag.sln
```

### 4.2 Run Test Suite
```powershell
dotnet test src\AcademyNoLag.Tests\AcademyNoLag.Tests.csproj -c Release
```

### 4.3 Publish Desktop UI Executable
```powershell
dotnet publish src\AcademyNoLag.App\AcademyNoLag.App.csproj -c Release -r win-x64 --self-contained false -o build\
```

### 4.4 Publish Relay Node Server
```powershell
dotnet publish src\AcademyNoLag.RelayNode\AcademyNoLag.RelayNode.csproj -c Release -r win-x64 --self-contained false -o build\
```

### 4.5 Publish Windows Privileged Service
```powershell
dotnet publish src\AcademyNoLag.Service\AcademyNoLag.Service.csproj -c Release -r win-x64 --self-contained false -o build\
```

---

## 5. Output Verification

Upon successful compilation, the following executables and artifacts will be created in `dist/`:

- `dist\AcademyNoLag.exe` — Desktop GUI Launcher
- `dist\AcademyNoLag.RelayNode.exe` — Relay Server Daemon
- `dist\AcademyNoLag.Service.exe` — Background Service
- `dist\config\profiles.json` — Pre-configured Game Profiles
- `dist\config\nodes.json` — Edge Server Registry
- `dist\config\settings.json` — User Preferences
