import struct
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

cap = r'Docs-Refs/Wireshark - Oficial Classic 5.0/03_Tutorial/Elyos/01_Soul_Reaper/03_Tutorial_Elyos_01_Soul_Reaper_2026-08-27_12-31-54_00001_20260827123154.pcapng'

# Let's inspect all raw packets in this capture
from scapy.all import rdpcap, TCP, Raw

pkts = rdpcap(cap)
print(f"Total packets in 1.9MB tutorial: {len(pkts)}")

# Find SYN, S_KEY, etc.
for i, p in enumerate(pkts[:50]):
    if TCP in p:
        tcp = p[TCP]
        flags = tcp.flags
        raw_len = len(p[Raw].load) if Raw in p else 0
        if tcp.sport == 7777 or tcp.dport == 7777:
            print(f"Pkt {i:03d} | {tcp.sport} -> {tcp.dport} | Flags: {flags} | Raw len: {raw_len}")
            if raw_len > 0 and tcp.sport == 7777:
                load = p[Raw].load
                print(f"   Payload: {load[:16].hex()}")
