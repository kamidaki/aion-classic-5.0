import struct
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

cap = r'Docs-Refs/Wireshark - Oficial Classic 5.0/03_Tutorial/Elyos/01_Soul_Reaper/03_Tutorial_Elyos_01_Soul_Reaper_2026-08-27_12-31-54_00001_20260827123154.pcapng'

todos = aion_pcap.fluxos(cap, 7777, com_tempo=True)
dados, _ = todos[list(todos.keys())[0]] if list(todos.keys())[0][1] == 7777 else todos[list(todos.keys())[1]]
seed = struct.unpack_from("<I", dados, 7)[0]
cifra = aion_pcap.Cifra(seed)
off = 11

op_counter = Counter()
packets = []

while off + 2 <= len(dados):
    plen = struct.unpack_from("<H", dados, off)[0]
    if plen < 5 or off + plen > len(dados):
        break
    body = dados[off+2 : off+plen]
    dec = cifra.decrypt(body)
    op_raw = struct.unpack_from("<H", dec, 0)[0]
    op = aion_pcap.opcode_servidor(op_raw)
    payload = dec[5:] if len(dec) >= 5 else b""
    op_counter[op] += 1
    packets.append((op, payload))
    off += plen

print(f"Total decoded packets: {len(packets)}")
print("\nTop 25 Opcodes in Tutorial:")
for op, cnt in op_counter.most_common(25):
    print(f"  Opcode 0x{op:04X} ({op:5d}): {cnt:5d} times")

# Let's inspect Quest packets, Cutscene packets, NPC dialogues, Map loads
# Common Aion Opcodes:
# 0x000F: SM_WORLD (Map Spawn)
# 0x000E: SM_PUT_NPC (NPC Spawn)
# 0x002C: SM_ADD_SKILL
# 0x001A: SM_INVENTORY_INFO
# 0x002B: SM_DELETE_ITEM / SM_UPDATE_ITEM
# 0x003A: SM_PLAY_MOVIE (Cutscene)
# 0x0041: SM_QUEST_ACTION
# 0x0042: SM_DIALOG_WINDOW
# 0x0045: SM_LEVEL_UPDATE
# 0x008E: SM_EMOTION

print("\n--- Searching for SM_WORLD (0x000F) ---")
for i, (op, p) in enumerate(packets):
    if op == 0x000F or len(p) == 42:
        print(f"  Pkt {i:04d} (0x{op:04X}) len={len(p)}: {p.hex()}")

print("\n--- Searching for SM_PLAY_MOVIE / Cutscenes ---")
for i, (op, p) in enumerate(packets):
    # Cutscene packet usually has movie id (u32 or u16)
    if len(p) in (4, 6, 8, 12, 16) and any(m in p for m in [b"\x01\x00", b"\x02\x00", b"\x03\x00"]):
        pass
