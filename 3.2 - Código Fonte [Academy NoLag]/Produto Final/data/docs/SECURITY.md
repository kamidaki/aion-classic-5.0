# Academy NoLag — Security Architecture & Threat Model

Network optimization software operates at privileged networking boundaries. Academy NoLag was designed from inception with strict defense-in-depth principles.

---

## 1. Principle of Least Privilege

- **Unprivileged Desktop Client**:
  The primary user interface (`AcademyNoLag.exe`) executes with standard user privileges (`requestedExecutionLevel level="asInvoker"`). It does not require permanent administrative access for telemetry, real-time graph rendering, or standard process detection.
- **Isolated Privileged Operations**:
  Kernel-level Windows Filtering Platform (WFP) operations are strictly isolated to the background service worker (`AcademyNoLag.Service.exe`). Communication occurs over authenticated Windows Named Pipes restricted to the interactive user's security identifier (SID).

---

## 2. Prevention of Broken Networking States

A common hazard with poorly designed routing tools is leaving users disconnected from the internet if the application crashes or freezes.

Academy NoLag mitigates this entirely through:
1. **WFP Dynamic Sessions (`FWPM_SESSION_FLAG_DYNAMIC`)**:
   Every filter rule created in the Windows Filtering Platform is associated with an active dynamic handle. The Windows kernel itself automatically drops and cleans all registered callouts and filters if the process handle closes or crashes.
2. **Watchdog Heartbeat**:
   The background service continuously checks for liveness heartbeats from the client application. If heartbeats stop for $> 5$ seconds, the service automatically deactivates all proxy rules and restores default routing.

---

## 3. Wire Protocol & Cryptographic Integrity

The custom wire protocol (`AcademyRelay` / `ACNL`) protects against packet tampering, bit rot, and malformed buffer exploits:

1. **Protocol Magic & Version Validation**:
   Packets must match the 4-byte signature `0x41434E4C` ("ACNL") and supported version number.
2. **IEEE 802.3 CRC-32 Checksumming**:
   Every transmitted packet contains a 32-bit CRC calculated across the entire payload. Packets with checksum mismatches are immediately discarded without allocation.
3. **Bounded Memory Allocations**:
   The maximum allowed payload length in any single frame is constrained to 65,536 bytes, preventing memory exhaustion or heap blowup attacks.
4. **No Remote Code Execution**:
   The relay protocol only forwards raw transport layer payloads (`TCP`/`UDP`). It does not interpret or evaluate commands, scripts, or executable code from remote endpoints.
