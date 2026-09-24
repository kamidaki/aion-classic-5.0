import sys
import os
import struct

sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

pcap_elyos = r'Docs-Refs/Wireshark - Oficial Classic 5.0/01_Login_World/Elyos/01_Login_World_Elyos_2026-08-27_10-03-03_00001_20260827100304.pcapng'

r = aion_pcap.abre(pcap_elyos)
print("Total pacotes servidor:", len(r['servidor']))
print("Total pacotes cliente:", len(r['cliente']))

for i, (op, payload, fecha) in enumerate(r['servidor'][:50]):
    print("S[%03d] Opcode: 0x%04X (%3d) | Len: %4d | Data: %s" % (i, op, op, len(payload), payload[:24].hex()))
