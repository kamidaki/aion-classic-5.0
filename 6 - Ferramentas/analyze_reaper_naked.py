import sys
import os
import struct

sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

pcap_naked = r'Docs-Refs/Wireshark - Oficial Classic 5.0/03_Tutorial/Elyos/01_Soul_Reaper/03_Tutorial_Elyos_01_Soul_Reaper_2026-08-27_12-59-34_00001_20260827125934.pcapng'

r = aion_pcap.abre(pcap_naked)
print(f"=== NAKED SOUL REAPER (15.9 KB) ===")
print("Total pacotes servidor:", len(r['servidor']))
print("Total pacotes cliente:", len(r['cliente']))

for i, (op, payload, fecha) in enumerate(r['servidor']):
    print(f"S[{i:03d}] Opcode: 0x{op:04X} ({op:3d}) | Len: {len(payload):4d} | Hex: {payload[:32].hex()}")
    if op == 0x0001: # SM_STATS_INFO
        print("  -> SM_STATS_INFO payload:")
        print("    " + payload.hex())
    elif op == 0x001A: # SM_INVENTORY_INFO
        print("  -> SM_INVENTORY_INFO payload len:", len(payload))
    elif op == 0x000F: # SM_WORLD
        print("  -> SM_WORLD payload:", payload.hex())

print("\n=== CLIENT PACKETS ===")
for i, (op, payload, fecha) in enumerate(r['cliente']):
    print(f"C[{i:03d}] Opcode: 0x{op:04X} ({op:3d}) | Len: {len(payload):4d} | Hex: {payload[:32].hex()}")
