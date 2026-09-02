import sys
import os
import struct
sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

pcap_elyos = r'Docs-Refs/Wireshark - Oficial Classic 5.0/01_Login_World/Elyos/01_Login_World_Elyos_2026-08-27_10-03-03_00001_20260827100304.pcapng'
pcap_asmo = r'Docs-Refs/Wireshark - Oficial Classic 5.0/01_Login_World/Asmodians/01_Login_World_Asmodians_2026-08-27_10-08-12_00001_20260827100812.pcapng'

for label, pcap in [('ELYOS', pcap_elyos), ('ASMODIANS', pcap_asmo)]:
    print(f"============================== {label} ==============================")
    r = aion_pcap.abre(pcap)
    for op, payload, fecha in r['servidor']:
        if op == 0x0C7 and len(payload) > 50:
            marca = payload[0]
            session_key = struct.unpack_from('<I', payload, 1)[0]
            zeros = payload[5:10]
            count = payload[10]
            print(f"Header: marca=0x{marca:02X}, session_key=0x{session_key:08X}, zeros={zeros.hex()}, count={count}")
            body = payload[11:]
            rec_len = len(body) // count
            print(f"Total characters: {count}, total body: {len(body)} bytes, record_len = {rec_len} bytes (rem={len(body)%count})")
            
            for i in range(count):
                rec = body[i*rec_len : (i+1)*rec_len]
                char_id = struct.unpack_from('<I', rec, 0)[0]
                name_bytes = rec[4:56]
                name = name_bytes.split(b'\x00\x00')[0].decode('utf-16-le', errors='ignore').rstrip('\x00')
                gender = struct.unpack_from('<I', rec, 56)[0]
                race = struct.unpack_from('<I', rec, 60)[0]
                class_id = struct.unpack_from('<I', rec, 64)[0]
                redundancy = struct.unpack_from('<I', rec, 144)[0]
                map_id = struct.unpack_from('<I', rec, 148)[0]
                x, y, z = struct.unpack_from('<fff', rec, 152)
                heading = struct.unpack_from('<I', rec, 164)[0]
                level = struct.unpack_from('<H', rec, 168)[0]
                print("  Char [%d]: ID=%d (0x%08X), Name=%r, Gender=%d, Race=%d, Class=%d" % (i, char_id, char_id, name, gender, race, class_id))
                print("      Redundancy=%d (expected %d), Map=%d, Pos=(%.2f, %.2f, %.2f), Heading=%d, Level=%d" % (redundancy, 100000 + race*2 + gender, map_id, x, y, z, heading, level))
                print("      Trailing bytes (last 16 bytes): %s" % rec[-16:].hex())
