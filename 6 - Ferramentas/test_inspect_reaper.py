import struct
import os

def decrypt_game_packet(data, key):
    # Standard Aion Game Packet decrypter
    # First 2 bytes are length (little-endian, includes 2 bytes length, packet length = len - 2)
    # 3rd byte: opcode XOR key
    # etc.
    pass

# Let's inspect raw opcodes and payloads using aion_pcap logic
import pcapng
from scapy.all import rdpcap, TCP, Raw

pcap_path = r"D:\AION CLASSIC 5.0 - EMULADOR\5 - Documentação e Referências\2 - Wireshark - Oficial Classic 5.0\03_Tutorial\Elyos\01_Soul_Reaper\03_Tutorial_Elyos_01_Soul_Reaper_2026-08-27_12-59-34_00001_20260827125934.pcapng"

packets = rdpcap(pcap_path)
print(f"Total raw packets: {len(packets)}")

# Extract TCP stream on port 7777
stream_s2c = bytearray()
stream_c2s = bytearray()

for p in packets:
    if TCP in p and Raw in p:
        tcp = p[TCP]
        raw = p[Raw].load
        if tcp.sport == 7777: # Server -> Client
            stream_s2c.extend(raw)
        elif tcp.dport == 7777: # Client -> Server
            stream_c2s.extend(raw)

print(f"S->C payload: {len(stream_s2c)} bytes")
print(f"C->S payload: {len(stream_c2s)} bytes")
