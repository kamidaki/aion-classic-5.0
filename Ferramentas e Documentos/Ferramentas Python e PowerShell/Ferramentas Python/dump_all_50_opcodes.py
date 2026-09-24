import sys
import os
import struct
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

pcap_elyos = r'Docs-Refs/Wireshark - Oficial Classic 5.0/01_Login_World/Elyos/01_Login_World_Elyos_2026-08-27_10-03-03_00001_20260827100304.pcapng'
pcap_asmo = r'Docs-Refs/Wireshark - Oficial Classic 5.0/01_Login_World/Asmodians/01_Login_World_Asmodians_2026-08-27_10-08-12_00001_20260827100812.pcapng'

for label, pcap in [('ELYOS', pcap_elyos), ('ASMODIANS', pcap_asmo)]:
    print(f"============================== {label} ==============================")
    r = aion_pcap.abre(pcap)
    
    server_opcodes = defaultdict(list)
    client_opcodes = defaultdict(list)
    
    for op, payload, fecha in r['servidor']:
        server_opcodes[op].append(payload)
        
    for op, payload, fecha in r['cliente']:
        client_opcodes[op].append(payload)
        
    print("\n--- SERVER OPCODES RECIBIDOS (Total distintos: %d) ---" % len(server_opcodes))
    for op in sorted(server_opcodes.keys()):
        payloads = server_opcodes[op]
        lens = sorted(list(set(len(p) for p in payloads)))
        print(f"  Opcode 0x{op:04X} ({op:3d}): {len(payloads):2d}x, lens: {lens}")
        
    print("\n--- CLIENT OPCODES ENVIADOS (Total distintos: %d) ---" % len(client_opcodes))
    for op in sorted(client_opcodes.keys()):
        payloads = client_opcodes[op]
        lens = sorted(list(set(len(p) for p in payloads)))
        print(f"  Opcode 0x{op:04X} ({op:3d}): {len(payloads):2d}x, lens: {lens}")
