import struct
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

cap = r'Docs-Refs/Wireshark - Oficial Classic 5.0/03_Tutorial/Elyos/01_Soul_Reaper/03_Tutorial_Elyos_01_Soul_Reaper_2026-08-27_12-31-54_00001_20260827123154.pcapng'

todos = aion_pcap.fluxos(cap, 7777, com_tempo=True)
for k, (dados, marcos) in todos.items():
    src, sport, dst, dport = k
    if sport == 7777:
        seed = struct.unpack_from("<I", dados, 7)[0]
        cifra = aion_pcap.Cifra(seed)
        off = 11
        pkt_idx = 0
        pkts = []
        while off + 2 <= len(dados):
            plen = struct.unpack_from("<H", dados, off)[0]
            if plen < 5 or off + plen > len(dados):
                break
            body = dados[off+2 : off+plen]
            dec = cifra.decrypt(body)
            op_raw = struct.unpack_from("<H", dec, 0)[0]
            op = aion_pcap.opcode_servidor(op_raw)
            seq_b = dec[2] if len(dec) > 2 else 0
            chk = struct.unpack_from("<H", dec, 3)[0] if len(dec) >= 5 else 0
            payload = dec[5:] if len(dec) >= 5 else b""
            pkts.append((op, payload, seq_b, chk))
            off += plen
            pkt_idx += 1
            
        print(f"Decoded {len(pkts)} server packets!")
        for i, (op, payload, seq_b, chk) in enumerate(pkts[:30]):
            print(f"  S[{i:03d}] Opcode: 0x{op:04X} ({op:4d}) | Len: {len(payload):4d} | Seq: 0x{seq_b:02X} | Payload: {payload[:24].hex()}")

