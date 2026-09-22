# Academy NoLag — Low-Level Windows Networking Internals

This document details the low-level Windows networking mechanics, native Win32 APIs, socket tables, multi-protocol probing methods, and route analysis techniques used in **Academy NoLag**.

---

## 1. Native Windows Network Inspection (`iphlpapi.dll`)

### 1.1 Enumerating Active TCP Sockets (`GetExtendedTcpTable`)
To correlate game network traffic with running processes, Academy NoLag queries the Windows IP Helper API:

```csharp
[DllImport("iphlpapi.dll", SetLastError = true)]
public static extern uint GetExtendedTcpTable(
    IntPtr pTcpTable,
    ref int pdwSize,
    bool bOrder,
    uint ulAf,
    TCP_TABLE_CLASS tableClass,
    uint reserved = 0);
```

- **Table Class**: `TCP_TABLE_OWNER_PID_ALL` returns all listening and established TCP connections mapped directly to the owning Process ID (`owningPid`).
- **Memory Optimization**: Memory is allocated via `Marshal.AllocHGlobal` and walked sequentially with pointer arithmetic (`IntPtr.Add`), avoiding array reallocations on every scan cycle.
- **Filtering**: Local loopback sockets (`127.0.0.1`, `::1`) and wildcard listening sockets (`0.0.0.0:*`) are separated from active remote game endpoints.

### 1.2 Enumerating UDP Endpoints (`GetExtendedUdpTable`)
Online FPS and MOBA games frequently use UDP for gameplay packets. Academy NoLag enumerates UDP listeners using:

```csharp
[DllImport("iphlpapi.dll", SetLastError = true)]
public static extern uint GetExtendedUdpTable(
    IntPtr pUdpTable,
    ref int pdwSize,
    bool bOrder,
    uint ulAf,
    UDP_TABLE_CLASS tableClass,
    uint reserved = 0);
```

Using `UDP_TABLE_OWNER_PID`, the system captures the local port bound by the game process.

### 1.3 Best Route & Interface Discovery (`GetBestRoute2`, `GetAdaptersAddresses`)
Academy NoLag identifies the operating system's routing table to inspect:
- Default Gateway IP (IPv4 and IPv6)
- Interface type (Ethernet, 802.11 Wi-Fi, VPN, Loopback)
- Link speed (negotiated bits per second)
- Maximum Transmission Unit (MTU) to avoid fragmentation

---

## 2. Multi-Protocol Network Probing Subsystem

### 2.1 Why ICMP Alone Is Insufficient
A critical flaw in simplistic network tools is relying entirely on ICMP Echo (ping):
1. **Firewall Filtering**: Many gaming edge servers, CDN shields (Cloudflare Spectrum, AWS Global Accelerator), and DDoS mitigation appliances explicitly drop ICMP packets.
2. **QoS Prioritization**: Many transit ISPs assign ICMP to low-priority queues (`Best Effort`), causing artificial jitter that does not reflect actual game packet performance.
3. **Protocol Divergence**: TCP and UDP packets often take different ECMP (Equal-Cost Multi-Path) routes through carrier backbones than ICMP.

### 2.2 Non-Blocking TCP Handshake Prober (`TcpConnectProber`)
To measure the true application-level round-trip latency of TCP game servers (such as Aion Classic 5.0, World of Warcraft, FFXIV):
1. A non-blocking TCP socket is initialized:
   ```csharp
   var socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp)
   {
       NoDelay = true,
       Blocking = false,
       LingerState = new LingerOption(true, 0) // Fast RST teardown
   };
   ```
2. High-resolution timestamps are captured via `Stopwatch.GetTimestamp()` immediately before initiating `socket.ConnectAsync()`.
3. As soon as the operating system receives the server's `SYN/ACK` packet, the socket completes the handshake and the elapsed time is recorded.
4. Setting `LingerState(true, 0)` causes the socket close to immediately send a `RST` packet rather than entering the `TIME_WAIT` state, ensuring zero socket resource exhaustion on either the client PC or the game server.

### 2.3 Sub-Millisecond Precision Timers
Standard .NET `DateTime.UtcNow` resolution on Windows is limited to 15.6 milliseconds (the default OS timer interrupt period). Academy NoLag measures latency exclusively using hardware QueryPerformanceCounter through `Stopwatch.GetTimestamp()` and `Stopwatch.GetElapsedTime()`, achieving sub-microsecond precision:

$$\Delta t = \frac{\text{StopwatchTicks} \times 1000.0}{\text{Stopwatch.Frequency}}$$

---

## 3. Route Discovery & Intermediate Hop Tracing

### 3.1 TTL Stepping Algorithm
To discover how packets travel from the user to the game server:
1. ICMP Echo packets are transmitted with an initial `TTL = 1` using `System.Net.NetworkInformation.PingOptions(ttl, true)`.
2. The first router (user's home gateway) decrements TTL to 0 and returns an ICMP `TTL Expired in Transit` message (`IPStatus.TtlExpired`), identifying Hop 1.
3. The probe loop increments TTL from 1 up to `maxHops` (30), discovering each transit router and measuring its intermediate RTT and packet loss percentage.
4. Reverse DNS lookups (`Dns.GetHostEntryAsync`) resolve router hostnames to identify carrier ASNs, internet exchange points (IXPs), and transit providers (e.g., Telia/Arelion, Lumen, Cogent, GTT).

### 3.2 Gateway Latency Isolation
Academy NoLag continuously probes the default gateway (Hop 1) in a dedicated background monitor. This allows the system to definitively distinguish between:
- **Local Congestion**: High ping caused by domestic Wi-Fi interference, family bandwidth saturation, or cable modem issues.
- **Carrier / Peering Congestion**: Good local gateway ping (e.g., < 2 ms) combined with latency spikes occurring at peering exchange points.
