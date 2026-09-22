# Academy NoLag — Troubleshooting & Diagnostics Guide

This document provides step-by-step diagnostic workflows for identifying and resolving networking issues, game detection conflicts, and route optimization errors.

---

## 1. Quick Diagnostic Checklist

| Symptom | Probable Cause | Recommended Action |
| :--- | :--- | :--- |
| **Game not detected** | Process name mismatch or game launched with elevated privileges | Launch Academy NoLag as Administrator or add custom profile in Game Profiles tab. |
| **Optimization not engaging** | Default ISP route is already faster than candidate nodes (Zero-Fake Guarantee) | Verify telemetry comparison in Dashboard. Optimization only switches when sustained improvement $\ge 7\%$ and $\ge 4\text{ms}$. |
| **High packet loss reported** | Wi-Fi channel interference or local LAN congestion | Check the Default Gateway ping. If gateway ping has jitter or loss, troubleshoot local home network. |
| **Relay Node showing Offline** | Firewall blocking outbound TCP port 42420 | Verify outbound firewall rules; test connectivity via Benchmark tab. |

---

## 2. In-Depth Diagnostic Workflows

### 2.1 Game Detection Troubleshooting (Aion Classic 5.0)
1. **Verify Executable Name**:
   Aion Classic can run as `Aion.bin`, `aion.bin`, `aionclassic.bin`, or `Aion.exe`.
2. **Inspect Process Elevation**:
   If Aion Classic is launched from a batch script or launcher running as Administrator, Windows security policy prevents non-elevated processes from reading the process memory table or opening socket queries. Run `AcademyNoLag.exe` as Administrator in this scenario.
3. **Check Dynamic Sockets**:
   In the Academy NoLag dashboard, look at the "Active Game Network Endpoints" table. Verify that the login connection (`*:2106`) or game world connection (`*:7777`) appears with state `ESTABLISHED`.

### 2.2 Isolating Local Jitter vs Transit Latency
1. Open the **Diagnostics & Logs** tab in Academy NoLag.
2. Note the **Gateway IPv4** address of your primary interface (e.g., `192.168.1.1`).
3. Switch to the **Benchmark** tab and enter your gateway IP.
4. Run the benchmark:
   - **Normal Local Result**: Mean $< 1.0\text{ ms}$, Jitter $< 0.5\text{ ms}$, Loss $= 0\%$.
   - **Congested Local Result**: Mean $> 15\text{ ms}$, Jitter $> 10\text{ ms}$, Loss $> 1\%$.
   - *Fix*: Connect via physical Cat6 Ethernet cable instead of 2.4GHz Wi-Fi.

### 2.3 Emergency Network State Restoration
Academy NoLag uses dynamic WFP sessions (`FWPM_SESSION_FLAG_DYNAMIC`), which means the Windows kernel automatically purges all filters when the process closes. However, if your network remains in an unexpected state after an abnormal system shutdown:

Run the following in an elevated PowerShell prompt:
```powershell
# Reset Windows TCP/IP stack to default factory state
netsh int ip reset
netsh winsock reset
ipconfig /flushdns
```
Then restart your computer.
