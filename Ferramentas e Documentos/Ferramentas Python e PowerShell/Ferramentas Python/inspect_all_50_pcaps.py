import os
import sys
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(TOOLS_DIR)))
import os
import pyshark
import struct

PCAP_DIR = os.path.join(PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Wireshark - Oficial Classic 5.0")

def inspect_pcap(filepath):
    print("=" * 80)
    print(f"Inspecting: {filepath}")
    print("=" * 80)
    cap = pyshark.FileCapture(filepath, display_filter="tcp.port in {2106, 7777, 10241}")
    
    packet_count = 0
    streams = {}
    for pkt in cap:
        packet_count += 1
        try:
            tcp = pkt.tcp
            srcport = int(tcp.srcport)
            dstport = int(tcp.dstport)
            payload_hex = getattr(tcp, 'payload', None)
            if payload_hex:
                raw_bytes = bytes.fromhex(payload_hex.replace(':', ''))
                stream_id = tcp.stream
                if stream_id not in streams:
                    streams[stream_id] = []
                streams[stream_id].append((srcport, dstport, raw_bytes))
        except Exception as e:
            continue
    cap.close()
    
    print(f"Total packets with payload: {packet_count}, Streams: {len(streams)}")
    return streams

for root, dirs, files in os.walk(PCAP_DIR):
    for f in files:
        if f.endswith('.pcapng'):
            inspect_pcap(os.path.join(root, f))
