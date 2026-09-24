import sys
import os
import struct

sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

cap = r'Docs-Refs/Wireshark - Oficial Classic 5.0/03_Tutorial/Elyos/01_Soul_Reaper/03_Tutorial_Elyos_01_Soul_Reaper_2026-08-27_12-31-54_00001_20260827123154.pcapng'

todos = aion_pcap.fluxos(cap, 7777, com_tempo=True)
print(f"Fluxos encontrados no pcap de 1.9MB: {len(todos)}")
for k, (dados, marcos) in todos.items():
    src, sport, dst, dport = k
    print(f"Fluxo {sport} -> {dport}: {len(dados)} bytes, {len(marcos)} segmentos")
    if sport == 7777 and len(dados) >= 11:
        ln = struct.unpack_from("<H", dados, 0)[0]
        seed = struct.unpack_from("<I", dados, 7)[0]
        print(f"  Handshake: len={ln}, seed=0x{seed:08X}, raw={dados[:16].hex()}")
        # Let's try decrypting the first 10 packets manually step by step
        cifra = aion_pcap.Cifra(seed)
        off = 11
        for pnum in range(20):
            if off + 2 > len(dados):
                break
            plen = struct.unpack_from("<H", dados, off)[0]
            if plen < 7 or off + plen > len(dados):
                print(f"  [Pkt {pnum}] Invalid plen={plen} at off={off}")
                break
            body_cifrado = dados[off+2 : off+plen]
            body_dec = cifra.decrypt(body_cifrado)
            op = struct.unpack_from("<H", body_dec, 0)[0]
            chk = struct.unpack_from("<H", body_dec, 3)[0]
            op_serv = aion_pcap.opcode_servidor(op)
            valido = (chk == ((~op) & 0xFFFF))
            print(f"  [Pkt {pnum:02d}] off={off:5d} len={plen:4d} op_raw=0x{op:04X} op_serv=0x{op_serv:04X} chk_ok={valido} hex={body_dec[:16].hex()}")
            off += plen
