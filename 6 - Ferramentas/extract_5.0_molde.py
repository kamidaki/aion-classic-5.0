import sys
import os
import struct
sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

pcap_50 = r'Docs-Refs/Wireshark - Oficial Classic 5.0/01_Login_World/Elyos/01_Login_World_Elyos_2026-08-27_10-03-03_00001_20260827100304.pcapng'
r50 = aion_pcap.abre(pcap_50)

rec50 = None
for op, p, _ in r50['servidor']:
    if op == 0x0C7 and len(p) > 50:
        rec50 = bytearray(p[11:11+766])
        break

print(f"rec50 size: {len(rec50)} bytes")
# Create a template by zeroing ID and Name
rec_template = bytearray(rec50)
rec_template[0:56] = b'\x00' * 56

print("Generated 766-byte template hex:")
formatted = []
for i in range(0, len(rec_template), 16):
    chunk = rec_template[i:i+16]
    hex_str = ", ".join(f"0x{b:02X}" for b in chunk)
    formatted.append(f"    {hex_str},")

print("\n".join(formatted))
