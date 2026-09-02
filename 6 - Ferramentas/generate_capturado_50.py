import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

pcap_50 = r'Docs-Refs/Wireshark - Oficial Classic 5.0/01_Login_World/Elyos/01_Login_World_Elyos_2026-08-27_10-03-03_00001_20260827100304.pcapng'
r50 = aion_pcap.abre(pcap_50)

p1 = None
p2 = None
for op, p, _ in r50['servidor']:
    if op == 0x0C7:
        if len(p) == 11 and p1 is None:
            p1 = p
        elif len(p) > 50 and p2 is None:
            p2 = p

print(f"p1 len: {len(p1) if p1 else None}")
print(f"p2 len: {len(p2) if p2 else None}")

def format_rust_array(data):
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_s = ", ".join(f"0x{b:02X}" for b in chunk)
        lines.append(f"    {hex_s},")
    return "\n".join(lines)

if p1:
    print("pub const CHARACTER_LIST_1: [u8; %d] = [\n%s\n];" % (len(p1), format_rust_array(p1)))
if p2:
    print("pub const CHARACTER_LIST_2: [u8; %d] = [\n%s\n];" % (len(p2), format_rust_array(p2)))
