#!/usr/bin/env python3
r"""
AION CLASSIC 5.0 - COLETOR DE SPAWNS EM TEMPO REAL (LIVE WIRE & MEMORY COLLECTOR)
Monitora o cliente oficial em D:\GameForge\aionclassic e captura os spawns de NPCs/monstros
em tempo real conforme o jogador se desloca pelos mapas do jogo.
Salva automaticamente os dados em CSV e XML oficial na pasta do mapa selecionado.
"""

import os
import sys
import time
import struct
import subprocess
import ctypes
from ctypes import wintypes
import xml.etree.ElementTree as ET
from collections import defaultdict

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

import aion_pcap
from extract_spawns_from_pcap import load_world_maps, load_npc_templates, deduplicate_spawns, export_spawns

PROCESS_ALL_ACCESS = 0x1F0FFF

class MemoryInspector:
    def __init__(self):
        self.pid = None
        self.handle = None
        self.k32 = ctypes.windll.kernel32

    def find_process(self, process_name="Aion.bin"):
        try:
            out = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {process_name}" /FO CSV /NH', shell=True).decode('latin1', errors='ignore')
            for line in out.strip().splitlines():
                parts = [p.strip(' "') for p in line.split(',')]
                if len(parts) >= 2 and parts[0].lower() == process_name.lower():
                    self.pid = int(parts[1])
                    self.handle = self.k32.OpenProcess(PROCESS_ALL_ACCESS, False, self.pid)
                    return self.pid
        except Exception:
            pass
        return None

    def is_connected(self):
        return self.handle is not None

    def close(self):
        if self.handle:
            self.k32.CloseHandle(self.handle)
            self.handle = None

def main():
    print("=" * 80)
    print("      AION CLASSIC 5.0 - MONITOR E COLETOR DE SPAWNS AO VIVO (CLIENTE 5.0)     ")
    print("=" * 80)

    # Carregar Mapas e Templates
    maps_xml = os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data", "world_maps.xml")
    id_to_name, name_to_id = load_world_maps(maps_xml)

    npcs_xml = os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data", "npcs", "npc_templates.xml")
    print("[*] Carregando templates de monstros e NPCs...")
    npc_name_map = load_npc_templates(npcs_xml)
    print(f"[*] Templates prontos: {len(npc_name_map)} cadastrados.")

    # Conectar ao Processo Aion.bin
    inspector = MemoryInspector()
    pid = inspector.find_process("Aion.bin")
    if pid:
        print(f"[+] Processo do jogo detectado: Aion.bin (PID={pid})")
    else:
        print("[-] Aion.bin nao foi detectado no momento (inicie o jogo caso queira inspecao de memoria).")

    # Selecionar Mapa para Salvar
    print("\nSELECAO DO MAPA PARA SALVAR OS SPAWNS:")
    print("------------------------------------------------------------------------------")
    user_map = input("Digite o nome ou ID do mapa (ex: Sanctum, Poeta, Inggison, 210010000): ").strip()
    
    selected_mid = None
    selected_mname = None

    if user_map.isdigit():
        mid = int(user_map)
        if mid in id_to_name:
            selected_mid = mid
            selected_mname = id_to_name[mid]
    else:
        q = user_map.lower()
        matches = [(mid, name) for mid, name in id_to_name.items() if q in name.lower()]
        if len(matches) == 1:
            selected_mid, selected_mname = matches[0]
        elif len(matches) > 1:
            print("\nMapas encontrados:")
            for i, (mid, name) in enumerate(matches[:10], 1):
                print(f" [{i}] {name} (ID: {mid})")
            choice = input(f"Selecione (1-{min(10, len(matches))}) [Padrao: 1]: ").strip()
            idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(matches) else 0
            selected_mid, selected_mname = matches[idx]

    if not selected_mid:
        selected_mid = 210010000
        selected_mname = "Poeta"

    save_dir = os.path.join(PROJECT_ROOT, "5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0", "08_Spawns_Mapas", selected_mname)
    os.makedirs(save_dir, exist_ok=True)

    print(f"\n[OK] Mapa Ativo: {selected_mname} (ID: {selected_mid})")
    print(f"[OK] Pasta de Destino: {save_dir}")
    print("\nIniciando captura com Wireshark/dumpcap em segundo plano...")

    # Localizar dumpcap
    wireshark_paths = [
        r"E:\Programas instalados - Leves\Wireshark\dumpcap.exe",
        r"C:\Program Files\Wireshark\dumpcap.exe",
        r"C:\Program Files (x86)\Wireshark\dumpcap.exe"
    ]
    dumpcap_exe = None
    for p in wireshark_paths:
        if os.path.exists(p):
            dumpcap_exe = p
            break

    if not dumpcap_exe:
        print("[ERRO] dumpcap.exe nao foi encontrado.")
        sys.exit(1)

    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    temp_pcap = os.path.join(save_dir, f"live_{selected_mname}_{ts}.pcapng")

    # Iniciar dumpcap
    cmd = [
        dumpcap_exe,
        "-i", "4",
        "-f", "tcp and port 7777",
        "-w", temp_pcap
    ]
    
    print(f"[NET] Gravador ativo em: {temp_pcap}")
    print("==============================================================================")
    print("  >>> NAVEGUE LIVREMENTE PELO MAPA NO JOGO. <<<")
    print("  >>> Todos os NPCs/mobs que entrarem no seu raio de visao serao capturados. <<<")
    print("  >>> Pressione [CTRL + C] quando terminar de explorar para consolidar os dados. <<<")
    print("==============================================================================")

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        while True:
            time.sleep(2)
            if not os.path.exists(temp_pcap):
                continue
            # Estatisticas do arquivo
            size_kb = os.path.getsize(temp_pcap) // 1024
            sys.stdout.write(f"\r[*] Gravando trafego... Tamanho do arquivo: {size_kb} KB")
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\n[*] Finalizando gravador e processando spawns...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass

    # Processar pcap com o extrator
    print("\n[*] Processando o trafego capturado para extrair coordenadas e IDs...")
    from extract_spawns_from_pcap import process_pcap
    mid, raw_spawns = process_pcap(temp_pcap, default_map_id=selected_mid)
    
    if not raw_spawns:
        print("[AVISO] Nenhum pacote 0x000E foi decifrado.")
        print("Lembrete: Inicie a ferramenta ANTES de carregar o mapa ou relogue para gravar o handshake.")
        return

    grouped = deduplicate_spawns(raw_spawns)
    csv_p, xml_p, total_spots = export_spawns(selected_mid, selected_mname, grouped, npc_name_map, save_dir)

    print("\n" + "=" * 80)
    print(f"[SUCESSO] Spawns do mapa '{selected_mname}' consolidados com sucesso!")
    print(f"  * Total de Monstros/NPCs Coletados: {total_spots} (em {len(grouped)} tipos)")
    print(f"  * CSV Salvo: {csv_p}")
    print(f"  * XML Salvo: {xml_p}")
    print("=" * 80)

if __name__ == "__main__":
    main()
