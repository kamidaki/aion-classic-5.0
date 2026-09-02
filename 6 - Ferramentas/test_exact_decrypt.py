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
        print(f"Server stream len: {len(dados)}, seed: 0x{seed:08X}")
        cifra = aion_pcap.Cifra(seed)
        off = 11
        pkt_idx = 0
        valid_cnt = 0
        while off + 2 <= len(dados):
            plen = struct.unpack_from("<H", dados, off)[0]
            if plen < 5 or off + plen > len(dados):
                break
            body = dados[off+2 : off+plen]
            dec = cifra.decrypt(body)
            op = struct.unpack_from("<H", dec, 0)[0]
            op_serv = aion_pcap.opcode_servidor(op)
            chk = struct.unpack_from("<H", dec, 3)[0]
            expected_chk = (~op) & 0xFFFF
            is_valid = (chk == expected_chk)
            if is_valid:
                valid_cnt += 1
            print(f"Pkt {pkt_idx:03d} | off={off:6d} len={plen:4d} | op_raw=0x{op:04X} op_serv=0x{op_serv:04X} | valid={is_valid} | dec_hex={dec[:20].hex()}")
            off += plen
            pkt_idx += 1
            if pkt_idx >= 35:
                break
        print(f"Total valid packets in first 35: {valid_cnt}")
