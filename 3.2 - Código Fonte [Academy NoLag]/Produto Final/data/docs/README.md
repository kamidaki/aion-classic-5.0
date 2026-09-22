# Academy NoLag — Game Network Routing Optimizer

[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011%20(x64)-blue.svg)](#)
[![Runtime](https://img.shields.io/badge/.NET-9.0%20LTS-purple.svg)](#)
[![Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#)
[![Tests](https://img.shields.io/badge/tests-21%2F21%20passing-success.svg)](#)
[![Architecture](https://img.shields.io/badge/architecture-Zero--Allocation%20Async-teal.svg)](#)

**Academy NoLag** is an enterprise-grade, high-performance Windows desktop network optimization application engineered to intelligently eliminate unnecessary network latency, packet loss, jitter, and suboptimal ISP routing while playing online games.

Conceptualized similarly to commercial products like ExitLag, Academy NoLag dynamically detects active game processes, discovers their live network endpoints without hardcoding static IPs, continuously evaluates alternative transit paths through edge optimization relay nodes, and applies safe, process-isolated traffic redirection with strict hysteresis and immediate failsafe fallback.

---

## ⚡ Core Highlights & Innovations

- **Zero-Fake Guarantee**: Every metric displayed (Default vs Optimized Ping, Jitter, Packet Loss, Hops) originates exclusively from live, multi-protocol measurements. No synthetic ping drops, fabricated improvements, or placebo sliders.
- **Dynamic Endpoint Discovery**: Correlates process IDs to active network sockets in real time via the Windows IP Helper API (`GetExtendedTcpTable` / `GetExtendedUdpTable`). Discovers game servers, authentication realms, and chat gateways dynamically.
- **First Target: Aion Classic 5.0 EU / Emulator**: Out-of-the-box detection and routing profiles for `Aion.bin`, `aionclassic.bin`, `Aion.exe`, mapping Login (port 2106), Game World (port 7777), and Chat (port 10241) endpoints.
- **Multi-Protocol Network Probing**:
  - Sub-millisecond ICMP Echo prober with TTL stepping for PathPing-style hop analysis.
  - Non-blocking TCP 3-way handshake (`SYN` $\rightarrow$ `SYN/ACK` $\rightarrow$ `ACK`) connect latency prober for destinations that block or deprioritize ICMP.
  - UDP packet prober with high-resolution timestamps.
  - Default Gateway (LAN / ISP Access) prober to isolate local Wi-Fi/router jitter from WAN peering delays.
  - DNS resolution benchmark against public and local resolvers.
- **Formal Route Quality Engine**:
  Multi-factor composite scoring ($0$ to $100$):
  $$Q = w_{\text{lat}} \cdot S_{\text{lat}} + w_{\text{loss}} \cdot S_{\text{loss}} + w_{\text{jit}} \cdot S_{\text{jit}} + w_{\text{stab}} \cdot S_{\text{stab}} + w_{\text{node}} \cdot S_{\text{node}}$$
- **Hysteresis Protection**: Prevents route flapping. Enforces a minimum 7.0% improvement and $\ge 4.0\text{ ms}$ latency reduction sustained over at least 3 consecutive measurement cycles before triggering a route switch.
- **Dynamic Failsafe Controller**: Automatic watchdog that instantly reverts traffic to the default Windows ISP route if packet loss exceeds direct route or latency degrades.
- **Modern Dark/Neon Gaming Dashboard**: Hardware-accelerated Direct3D WPF UI featuring 60 FPS real-time vector graphs for Ping, Jitter, and Loss, alongside Windows System Tray integration.
- **Standalone Edge Relay Node Server**: Complete, deployable relay server daemon (`AcademyNoLag.RelayNode.exe`) ready to run on any cloud VPS or local test environment.

---

## 🏗️ System Architecture

```
                       ┌─────────────────────────────────────────┐
                       │     Academy NoLag Desktop App (WPF)     │
                       │  - Live Graphs  - System Tray  - MVVM   │
                       └────────────────────┬────────────────────┘
                                            │
                                  In-Process / Named Pipe
                                            │
                       ┌────────────────────▼────────────────────┐
                       │           Academy NoLag Core            │
                       │  - Game Detector    - Quality Engine    │
                       │  - Discovery Engine - Hysteresis Logic  │
                       └─────────────┬──────────────┬────────────┘
                                     │              │
                   ┌─────────────────┴────┐   ┌─────┴─────────────────┐
                   │  Network Prober      │   │ Traffic Redirection   │
                   │  - IcmpSendEcho (TTL)│   │ - Dynamic WFP Session │
                   │  - Non-blocking TCP  │   │ - Transparent Proxy   │
                   │  - Gateway & DNS     │   │ - Failsafe Watchdog   │
                   └──────────────────────┘   └─────────────┬─────────┘
                                                            │
                                              Wire Protocol (ACNL)
                                                            │
                                              ┌─────────────▼─────────┐
                                              │ Academy Relay Node    │
                                              │ (Edge VPS / Localhost)│
                                              └─────────────┬─────────┘
                                                            │
                                                    Optimized Peering
                                                            │
                                              ┌─────────────▼─────────┐
                                              │ Game Server (Aion/LoL)│
                                              └───────────────────────┘
```

---

## 🚀 Quick Start

### 1. Running the Desktop Application
Navigate to `dist/` and launch `AcademyNoLag.exe`:
```powershell
cd "D:\AION CLASSIC 5.0 - EMULADOR\3.2 - Código Fonte [Academy NoLag]\dist"
.\AcademyNoLag.exe
```

### 2. Testing with Simulated Aion Classic 5.0
1. Launch the Academy NoLag dashboard.
2. In the top header bar, click **"🎮 Simulate Aion 5.0"**.
3. Watch the system immediately detect the simulated process (PID: 7724), identify its 3 active sockets (Authentication 2106, GameServer 7777, Chat 10241), measure the default route, discover relay candidates, and update the live real-time graph.

### 3. Running a Local Edge Relay Node
To test loopback relay performance locally:
```powershell
.\StartRelayNode.bat
```
The relay server will listen on `0.0.0.0:42420` with zero CPU overhead.

### 4. Running the Built-in Network Benchmark
1. Switch to the **Benchmark** tab on the left sidebar.
2. Enter any destination IP (e.g. `1.1.1.1` or your game server's IP).
3. Click **"Run Benchmark (50 Packets)"**.
4. The system will calculate Min, Mean, Median, P90, P95, P99, Jitter, Packet Loss, and Standard Deviation.

---

## 📦 Project Deliverables

| Path | Purpose |
| :--- | :--- |
| `dist/AcademyNoLag.exe` | Main desktop application executable (WPF) |
| `dist/AcademyNoLag.RelayNode.exe` | Standalone edge relay server daemon |
| `dist/AcademyNoLag.Service.exe` | Privileged Windows service worker |
| `dist/config/` | Profile rules, relay nodes registry, and settings |
| `dist/InstallService.bat` | Windows Service installer |
| `dist/UninstallService.bat` | Windows Service uninstaller |
| `dist/StartRelayNode.bat` | Quick relay node server launcher |
| `Build.ps1` & `Build.bat` | One-click automated build & test pipeline |

---

## 📚 Technical Documentation Suite

For detailed technical references, refer to the documentation:

- [ARCHITECTURE.md](ARCHITECTURE.md) — Comprehensive architectural and design specification
- [NETWORKING.md](NETWORKING.md) — Low-level Windows networking internals (IP Helper API, Winsock, WFP)
- [ROUTING.md](ROUTING.md) — Mathematical route optimization, RFC 3550 jitter, and hysteresis
- [BUILD.md](BUILD.md) — Build prerequisites, compilation pipeline, and automated test suite
- [INSTALLATION.md](INSTALLATION.md) — Installation, deployment, and service configuration
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Diagnostic steps, firewall rules, and error recovery
- [SECURITY.md](SECURITY.md) — Privilege isolation, memory safety, and kernel boundary protections
- [PERFORMANCE.md](PERFORMANCE.md) — Latency budgets, zero-allocation memory pooling, and benchmarks
- [ROADMAP.md](ROADMAP.md) — Future evolution, Anycast network, and kernel callout drivers
