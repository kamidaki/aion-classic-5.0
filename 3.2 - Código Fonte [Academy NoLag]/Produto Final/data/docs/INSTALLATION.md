# Academy NoLag — Installation & Deployment Guide

This guide covers deployment instructions for the desktop client, edge relay nodes, and optional privileged Windows Service registration.

---

## 1. System Requirements

- **Operating System**: Windows 10 (Build 19041+) or Windows 11 (64-bit).
- **Architecture**: x64 (AMD64 / Intel 64).
- **Runtime**: .NET 9.0 Desktop Runtime (`Microsoft.WindowsDesktop.App 9.0+`).
- **Network Interface**: Ethernet, 802.11 Wi-Fi, or cellular network adapter.
- **Privileges**:
  - The desktop client (`AcademyNoLag.exe`) runs as a standard user without requiring elevation.
  - Optional: The background network service requires Administrator rights during registration.

---

## 2. Standard Client Installation

1. Copy the contents of the `dist/` directory to your desired location, for example:
   ```text
   C:\Program Files\Academy NoLag\
   ```
2. Launch `AcademyNoLag.exe`.
3. The application will start in the notification area and display the main dashboard.
4. (Optional) Check "Start with Windows" in the Settings tab to launch on system boot.

---

## 3. Registering the Background Windows Service (Optional)

For environments where strict user-space privilege separation is required:

1. Open PowerShell or Command Prompt as **Administrator**.
2. Navigate to the installation directory.
3. Run `InstallService.bat`:
   ```cmd
   InstallService.bat
   ```
4. This executes:
   ```cmd
   sc create AcademyNoLagService binPath= "C:\Program Files\Academy NoLag\AcademyNoLag.Service.exe" start= auto DisplayName= "Academy NoLag Network Service"
   sc start AcademyNoLagService
   ```
5. To remove the service at any time:
   ```cmd
   UninstallService.bat
   ```

---

## 4. Deploying an Optimization Relay Node (VPS / Cloud Server)

To deploy your own edge relay server on an external cloud instance (e.g., AWS, Linode, Hetzner, Oracle Cloud):

### 4.1 On Windows Server:
```cmd
AcademyNoLag.RelayNode.exe --port 42420 --region "EU-Frankfurt"
```

### 4.2 Firewall Rule:
Ensure TCP and UDP port `42420` (or chosen port) is open in the server firewall:
```powershell
New-NetFirewallRule -DisplayName "AcademyNoLag Relay" -Direction Inbound -Protocol TCP -LocalPort 42420 -Action Allow
```

### 4.3 Adding the Node to Academy NoLag:
Edit `dist\config\nodes.json` on the client PC:
```json
{
  "Id": "node_my_custom",
  "Name": "My Frankfurt Cloud VPS",
  "Region": "Frankfurt",
  "CountryCode": "DE",
  "Host": "YOUR_SERVER_IP",
  "Port": 42420
}
```
Restart Academy NoLag or click "Refresh Latencies" in the Relay Nodes tab.
