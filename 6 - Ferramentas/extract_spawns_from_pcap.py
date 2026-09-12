#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AION CLASSIC 5.0 - EXTRATOR DE SPAWNS DE NPCS/MOBS A PARTIR DE CAPTURAS PCAP (WIRESHARK)
Decifra as capturas de rede (.pcapng), localiza os pacotes 0x000E (SM_NPC_INFO) e 0x000F (SM_WORLD),
resolve os nomes dos NPCs a partir dos dados do cliente e gera arquivos oficiais em XML e CSV.
"""

import os
import sys
import glob
import re
import struct
import csv
import argparse
import xml.etree.ElementTree as ET
from collections import defaultdict

# Ajustar path para importar aion_pcap
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

try:
    import aion_pcap
except ImportError:
    print("[ERRO] Nao foi possivel importar 'aion_pcap.py'. Verifique se esta em '6 - Ferramentas'.")
    sys.exit(1)

def load_world_maps(maps_xml_path):
    """Carrega mapa id -> nome e nome -> id a partir de world_maps.xml"""
    id_to_name = {}
    name_to_id = {}
    if not os.path.exists(maps_xml_path):
        return id_to_name, name_to_id

    try:
        tree = ET.parse(maps_xml_path)
        for m in tree.getroot().findall("map"):
            mid = int(m.get("id"))
            name = m.get("name")
            if name:
                id_to_name[mid] = name
                if name not in name_to_id:
                    name_to_id[name.lower()] = mid
    except Exception as e:
        print(f"[AVISO] Falha ao carregar world_maps.xml: {e}")
    return id_to_name, name_to_id

def load_client_strings(strings_dir):
    """Carrega dicionarios de strings do cliente 5.0"""
    str_map = {}
    if not os.path.exists(strings_dir):
        return str_map

    pattern = re.compile(r'<string>(.*?)</string>', re.DOTALL)
    xml_files = glob.glob(os.path.join(strings_dir, "*.xml"))
    for p in xml_files:
        content = None
        for enc in ["utf-16", "utf-8", "latin1"]:
            try:
                with open(p, "r", encoding=enc) as f:
                    content = f.read()
                break
            except Exception:
                continue
        if not content:
            continue

        for s in pattern.findall(content):
            sid = re.search(r'<id>(.*?)</id>', s)
            sname = re.search(r'<name>(.*?)</name>', s)
            sbody = re.search(r'<body>(.*?)</body>', s)
            if sname and sbody:
                str_map[sname.group(1).strip().lower()] = sbody.group(1).strip()
            if sid and sbody:
                str_map[sid.group(1).strip()] = sbody.group(1).strip()

    return str_map

def load_npc_templates(npc_templates_path):
    """Carrega npc_templates.xml do GameServer e mapeia npc_id -> Nome Real do Monstro/NPC"""
    npc_name_map = {}
    if not os.path.exists(npc_templates_path):
        return npc_name_map

    try:
        tree = ET.parse(npc_templates_path)
        for n in tree.getroot().findall("npc_template"):
            nid_str = n.attrib.get("npc_id")
            name = n.attrib.get("name")
            if nid_str and nid_str.isdigit() and name:
                npc_name_map[int(nid_str)] = name.strip()
    except Exception as e:
        print(f"[AVISO] Falha ao carregar npc_templates.xml: {e}")

    return npc_name_map

def process_pcap(pcap_path, default_map_id=None):
    """
    Decodifica o pcap e extrai os spawns.
    Retorna: (detected_map_id, list_of_spawns)
    """
    print(f"[*] Analisando captura: {pcap_path}")
    try:
        r = aion_pcap.abre(pcap_path)
    except Exception as e:
        print(f"[ERRO] Falha ao abrir captura {pcap_path}: {e}")
        return default_map_id, []

    server_packets = r.get("servidor", [])
    if not server_packets:
        print("[AVISO] Nenhum pacote de servidor decifrado nesta captura.")
        return default_map_id, []

    detected_map_id = default_map_id
    raw_spawns = []

    for op, payload, _ in server_packets:
        # 1. Detectar Mapa (SM_WORLD 0x000F)
        if op == 0x000F and len(payload) >= 4:
            mid1 = struct.unpack_from("<I", payload, 0)[0]
            if mid1 > 100000000:
                detected_map_id = mid1

        # 2. Detectar Spawn de NPC (SM_NPC_INFO 0x000E)
        if op == 0x000E and len(payload) >= 28:
            try:
                x, y, z, obj_id, npc_id = struct.unpack_from("<fffII", payload, 0)
                heading = struct.unpack_from("<B", payload, 27)[0]
                # Validar coordenadas e IDs
                if 0 < npc_id < 2000000 and (-20000 <= x <= 20000) and (-20000 <= y <= 20000):
                    raw_spawns.append({
                        "npc_id": npc_id,
                        "obj_id": obj_id,
                        "x": round(x, 2),
                        "y": round(y, 2),
                        "z": round(z, 2),
                        "h": heading
                    })
            except Exception:
                continue

    return detected_map_id, raw_spawns

def deduplicate_spawns(raw_spawns, tolerance=1.5):
    """
    Remove duplicatas do mesmo NPC na mesma posicao aproximada (tolerancia em metros).
    """
    grouped = defaultdict(list)
    for sp in raw_spawns:
        npc_id = sp["npc_id"]
        spot = (sp["x"], sp["y"], sp["z"], sp["h"])
        
        # Verificar se ja existe spot similar
        exists = False
        for ex_x, ex_y, ex_z, ex_h in grouped[npc_id]:
            dist_sq = (sp["x"] - ex_x)**2 + (sp["y"] - ex_y)**2 + (sp["z"] - ex_z)**2
            if dist_sq <= (tolerance ** 2):
                exists = True
                break
        if not exists:
            grouped[npc_id].append(spot)

    return grouped

def export_spawns(map_id, map_name, grouped_spawns, npc_name_map, out_dir):
    """
    Gera arquivos CSV e XML formatados para o emulador.
    """
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Exportar CSV
    csv_filename = f"{map_name}_spawns.csv"
    csv_path = os.path.join(out_dir, csv_filename)
    total_spots = 0
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["map_id", "map_name", "npc_id", "npc_name", "x", "y", "z", "h"])
        for npc_id in sorted(grouped_spawns.keys()):
            npc_name = npc_name_map.get(npc_id, f"NPC_{npc_id}")
            for x, y, z, h in grouped_spawns[npc_id]:
                writer.writerow([map_id, map_name, npc_id, npc_name, f"{x:.2f}", f"{y:.2f}", f"{z:.2f}", h])
                total_spots += 1

    # 2. Exportar XML (Formato padrao do Emulador)
    xml_filename = f"{map_id}_{map_name}.xml"
    xml_path = os.path.join(out_dir, xml_filename)
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(f'<!--\n  Aion Classic 5.0 - Spawns Capturados Oficial Gameforge\n')
        f.write(f'  Mapa: {map_name} (ID: {map_id})\n')
        f.write(f'  Total de NPCs: {len(grouped_spawns)} tipos | Total de Spawns: {total_spots}\n-->\n')
        f.write('<spawns>\n')
        f.write(f'    <spawn_map map_id="{map_id}">\n')

        for npc_id in sorted(grouped_spawns.keys()):
            npc_name = npc_name_map.get(npc_id, f"NPC_{npc_id}")
            f.write(f'        <!-- {npc_name} -->\n')
            f.write(f'        <spawn npc_id="{npc_id}" respawn_time="60">\n')
            for x, y, z, h in grouped_spawns[npc_id]:
                f.write(f'            <spot x="{x:.2f}" y="{y:.2f}" z="{z:.2f}" h="{h}"/>\n')
            f.write('        </spawn>\n')

        f.write('    </spawn_map>\n')
        f.write('</spawns>\n')

    return csv_path, xml_path, total_spots

def main():
    parser = argparse.ArgumentParser(description="Aion Classic 5.0 - Extrator de Spawns PCAP")
    parser.add_argument("target", help="Caminho do arquivo .pcapng ou da pasta contendo capturas")
    parser.add_argument("--map-id", type=int, help="Forcar Map ID especifico (caso nao haja SM_WORLD na captura)")
    parser.add_argument("--map-name", help="Forcar Nome do Mapa")
    parser.add_argument("--out-dir", help="Pasta de saida para salvar CSV e XML (padrao: pasta da captura)")
    args = parser.parse_args()

    print("=" * 80)
    print("        AION CLASSIC 5.0 - EXTRATOR DE SPAWNS DE MONSTROS E NPCS (PCAP)       ")
    print("=" * 80)

    # Carregar Mapas e Nomes
    maps_xml = os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data", "world_maps.xml")
    id_to_name, name_to_id = load_world_maps(maps_xml)

    # Carregar Templates de NPCs
    npcs_xml = os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data", "npcs", "npc_templates.xml")
    print("[*] Carregando templates oficiais de NPCs do GameServer...")
    npc_name_map = load_npc_templates(npcs_xml)
    print(f"[*] Templates carregados: {len(npc_name_map)} monstros/NPCs catalogados.")

    # Localizar arquivos PCAP
    pcaps_to_process = []
    if os.path.isfile(args.target):
        pcaps_to_process.append(args.target)
        target_dir = os.path.dirname(os.path.abspath(args.target))
    elif os.path.isdir(args.target):
        pcaps_to_process = glob.glob(os.path.join(args.target, "**", "*.pcapng"), recursive=True)
        target_dir = os.path.abspath(args.target)
    else:
        print(f"[ERRO] Alvo nao encontrado: {args.target}")
        sys.exit(1)

    if not pcaps_to_process:
        print(f"[AVISO] Nenhum arquivo .pcapng encontrado em: {args.target}")
        sys.exit(0)

    # Processar cada pcap
    all_raw_spawns = []
    final_map_id = args.map_id

    for p in pcaps_to_process:
        mid, spawns = process_pcap(p, default_map_id=final_map_id)
        if mid and not final_map_id:
            final_map_id = mid
        all_raw_spawns.extend(spawns)

    # Determinar Mapa
    if not final_map_id and args.map_name:
        final_map_id = name_to_id.get(args.map_name.lower())

    if not final_map_id:
        # Tentar deduzir pelo nome da pasta pai
        folder_name = os.path.basename(target_dir)
        if folder_name.lower() in name_to_id:
            final_map_id = name_to_id[folder_name.lower()]

    map_name = args.map_name
    if not map_name and final_map_id in id_to_name:
        map_name = id_to_name[final_map_id]
    if not map_name:
        map_name = os.path.basename(target_dir)
    if not final_map_id:
        final_map_id = 999999999

    print(f"[*] Mapa Vinculado : {map_name} (ID: {final_map_id})")
    print(f"[*] Total de Pacotes 0x000E Identificados: {len(all_raw_spawns)}")

    if not all_raw_spawns:
        print("[AVISO] Nenhum spawn foi detectado nestas capturas.")
        print("DICA: Certifique-se de que a captura foi iniciada ANTES de logar no mundo ou re-logue para capturar o handshake S_KEY.")
        sys.exit(0)

    # Desduplicar
    grouped = deduplicate_spawns(all_raw_spawns)
    out_dir = args.out_dir if args.out_dir else target_dir

    csv_path, xml_path, total_spots = export_spawns(final_map_id, map_name, grouped, npc_name_map, out_dir)

    print("\n" + "=" * 80)
    print("                   RELATORIO DE EXTRACAO DE SPAWNS CONCLUIDO                   ")
    print("=" * 80)
    print(f"  * Tipos de Monstros / NPCs Distintos : {len(grouped)}")
    print(f"  * Total de Spawns Unicos Coletados   : {total_spots}")
    print(f"  * Arquivo CSV Gerado                 : {csv_path}")
    print(f"  * Arquivo XML Oficial Gerado         : {xml_path}")
    print("=" * 80)

    # Exibir previa dos 10 primeiros NPCs capturados
    print("\nPrevia dos Spawns Coletados:")
    print("-" * 80)
    print(f"{'NPC ID':<10} {'Nome do Monstro/NPC':<35} {'Qtd Spawns':<12} {'Exemplo (X, Y, Z)'}")
    print("-" * 80)
    for npc_id in sorted(grouped.keys())[:15]:
        name = npc_name_map.get(npc_id, f"NPC_{npc_id}")[:33]
        spots = grouped[npc_id]
        ex_x, ex_y, ex_z, _ = spots[0]
        print(f"{npc_id:<10} {name:<35} {len(spots):<12} ({ex_x:.1f}, {ex_y:.1f}, {ex_z:.1f})")
    if len(grouped) > 15:
        print(f"... e mais {len(grouped) - 15} monstros distintos.")
    print("-" * 80)

if __name__ == "__main__":
    main()
