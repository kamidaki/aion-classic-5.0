# Academy NoLag — Technical Roadmap & Future Milestones

This document outlines planned capabilities, future network architectural evolutions, and long-term milestones for **Academy NoLag**.

---

## Phase 1: Foundation & Aion Classic 5.0 (Completed ✅)

- [x] High-performance .NET 9 solution with 12 modular projects
- [x] Dynamic process and socket detection via Win32 IP Helper API (`GetExtendedTcpTable`)
- [x] Aion Classic 5.0 profile with dynamic server endpoint classification (Ports 2106, 7777, 10241)
- [x] Multi-protocol network prober (ICMP, non-blocking TCP SYN-ACK connect latency, UDP, DNS)
- [x] Sub-millisecond RFC 3550 Jitter algorithm and rolling percentile statistics
- [x] Formal Route Quality Scoring Engine ($Q$) with configurable weights
- [x] Hysteresis switching controller preventing route flapping
- [x] Failsafe degradation monitor with automatic fallback to default route
- [x] Custom binary wire protocol (`AcademyRelay` / `ACNL`) with IEEE 802.3 CRC-32
- [x] Standalone Edge Relay Node Server daemon (`AcademyNoLag.RelayNode.exe`)
- [x] Hardware-accelerated WPF dark gaming dashboard with 60 FPS real-time vector graphs
- [x] Windows System Tray integration with background execution
- [x] 21 automated unit and integration tests passing with 100% success rate
- [x] Comprehensive 10-document technical documentation suite

---

## Phase 2: Distributed Cloud Node Mesh & Multipath Routing (Upcoming 🚀)

- [ ] **Multipath Packet Forwarding (Packet Duplication)**:
  Simultaneously send critical gameplay packets across two distinct physical paths (Direct Route + Relay Node), discarding duplicates at the receiver. Guarantees 0% effective packet loss during momentary ISP drops.
- [ ] **Global Anycast Node Discovery**:
  Dynamic geo-DNS resolution routing clients to the topologically nearest Academy NoLag edge node.
- [ ] **UDP-Based QUIC Tunnel**:
  Introduce a QUIC/HTTP3 transport tunnel option between client and relay node with 0-RTT connection resumption and native multiplexing.

---

## Phase 3: Kernel Callout Driver & Hardware Offload

- [ ] **Custom Windows Filtering Platform (WFP) Kernel Callout Driver**:
  Transition socket redirection from user-mode transparent proxying to in-kernel WFP stream inspection, reducing context switches to absolute zero.
- [ ] **Network Interface Card (NIC) Tuning Suite**:
  Automated tuning for Windows network adapters:
  - Disabling Nagle's algorithm (`TcpAckFrequency = 1`, `TCPNoDelay = 1`)
  - Receive Side Scaling (RSS) queue alignment
  - Interrupt Moderation optimization for competitive gaming
