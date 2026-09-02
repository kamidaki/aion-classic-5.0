import sys
import os
import struct

sys.path.insert(0, os.path.dirname(__file__))
import aion_pcap

captures = [
    r'Docs-Refs/Wireshark - Oficial Classic 5.0/03_Tutorial/Elyos/01_Soul_Reaper/03_Tutorial_Elyos_01_Soul_Reaper_2026-08-27_12-31-54_00001_20260827123154.pcapng',
    r'Docs-Refs/Wireshark - Oficial Classic 5.0/03_Tutorial/Elyos/01_Soul_Reaper/03_Tutorial_Elyos_01_Soul_Reaper_2026-08-27_12-59-34_00001_20260827125934.pcapng',
    r'Docs-Refs/Wireshark - Oficial Classic 5.0/07_Deletar_Personagem_Voltar_Servidores/Elyos_Asmodians/07_Deletar_Personagem_Voltar_Servidores_Elyos_2026-08-27_12-22-45_00001_20260827122245.pcapng'
]

for cap in captures:
    print(f"\n=======================================================")
    print(f"File: {os.path.basename(cap)} ({os.path.getsize(cap)/1024:.1f} KB)")
    sessoes = aion_pcap.abre_todas(cap)
    print(f"Total sessoes encontradas: {len(sessoes)}")
    for i, s in enumerate(sessoes):
        s_pkts = [p for p in s['servidor'] if p[2]] # checksum_fecha == True
        c_pkts = [p for p in s['cliente'] if p[2]]
        print(f"  Sessao {i}: Seed=0x{s['seed']:08X} | Servidor={len(s_pkts)} pacotes validos | Cliente={len(c_pkts)} pacotes validos")
