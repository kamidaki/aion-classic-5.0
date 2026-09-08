# -*- coding: utf-8 -*-
"""
merge_city_spawns.py
Mescla spawns do cliente 5.0 (client_world_lc1.xml e client_world_dc1.xml)
em 110010000_Sanctum.xml e 120010000_Pandaemonium.xml sem perder spawns existentes.
"""

import os
import sys
import glob
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

# Ajusta encoding da saída do console
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_TOOLS = os.path.join(BASE_DIR, "6 - Ferramentas")
CLIENT_DATA_DIR = os.path.join(BASE_DIR, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
STRINGS_DIR = os.path.join(CLIENT_DATA_DIR, "Strings", "strings")
CLIENT_NPCS_PATH = os.path.join(CLIENT_DATA_DIR, "data", "npcs", "client_npcs.xml")
CLIENT_WORLD_DIR = os.path.join(CLIENT_DATA_DIR, "data", "world")

GAME_SERVER_STATIC = os.path.join(BASE_DIR, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data")
EMULADOR_FINAL_STATIC = os.path.join(BASE_DIR, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data")

sys.path.insert(0, BASE_TOOLS)
import aion_bxml

def load_npc_names():
    print("[1/3] Carregando nomes dos NPCs do cliente...")
    str_map = {}
    pattern = re.compile(r'<string>(.*?)</string>', re.DOTALL)
    for p in glob.glob(os.path.join(STRINGS_DIR, "*.xml")):
        raw = open(p, "rb").read()
        text = ""
        for enc in ["utf-16", "utf-8", "latin1"]:
            try:
                text = raw.decode(enc)
                break
            except Exception:
                continue
        for s in pattern.findall(text):
            sid = re.search(r'<id>(.*?)</id>', s)
            sname = re.search(r'<name>(.*?)</name>', s)
            sbody = re.search(r'<body>(.*?)</body>', s)
            if sname and sbody:
                str_map[sname.group(1).strip().lower()] = sbody.group(1).strip()
            if sid and sbody:
                str_map[sid.group(1).strip()] = sbody.group(1).strip()

    raw = open(CLIENT_NPCS_PATH, "rb").read()
    xml_str = aion_bxml.decodifica(raw)
    root = ET.fromstring(xml_str)
    
    npc_name_map = {}
    for nc in root.findall(".//npc_client"):
        nid_str = nc.findtext("id")
        if not nid_str or not nid_str.isdigit():
            continue
        nid = int(nid_str)
        desc = nc.findtext("desc")
        name = nc.findtext("name")
        resolved = None
        if desc:
            resolved = str_map.get(desc.strip().lower())
        if not resolved and name:
            resolved = str_map.get(name.strip().lower()) or name
        npc_name_map[nid] = resolved or f"NPC_{nid}"
    print(f"      {len(npc_name_map)} nomes de NPCs mapeados.")
    return npc_name_map

def merge_map(mid, mname, cname, npc_names):
    print(f"[2/3] Processando {mname} ({mid})...")
    cworld_file = os.path.join(CLIENT_WORLD_DIR, f"client_world_{cname.lower()}.xml")
    if not os.path.exists(cworld_file):
        print(f"      [ERRO] Arquivo cliente {cworld_file} não encontrado!")
        return

    # Lê cliente
    raw = open(cworld_file, "rb").read()
    xml_str = aion_bxml.decodifica(raw)
    c_root = ET.fromstring(xml_str)

    client_spots = []
    for ni in c_root.findall(".//npc_info"):
        nid_str = ni.findtext("nameid")
        if not nid_str or not nid_str.isdigit():
            continue
        nid = int(nid_str)
        pos = ni.find("pos")
        if pos is None:
            continue
        try:
            x = float(pos.findtext("x"))
            y = float(pos.findtext("y"))
            z = float(pos.findtext("z"))
            h_str = pos.findtext("h") or "0"
            h = int(float(h_str))
        except Exception:
            continue
        client_spots.append({"nid": nid, "x": x, "y": y, "z": z, "h": h})

    print(f"      Cliente possui {len(client_spots)} spots.")

    # Lê arquivo existente do servidor
    server_file = os.path.join(GAME_SERVER_STATIC, "spawns", "Npcs", f"{mid}_{mname}.xml")
    if not os.path.exists(server_file):
        print(f"      [ERRO] Arquivo servidor {server_file} não encontrado!")
        return

    s_tree = ET.parse(server_file)
    s_root = s_tree.getroot()
    spawn_map = s_root.find(".//spawn_map")
    if spawn_map is None:
        spawn_map = s_root

    # Indexa spots existentes: (nid, round(x, 0), round(y, 0))
    existing_coords = set()
    existing_spawns_by_nid = {}
    for sp in spawn_map.findall("spawn"):
        nid = int(sp.attrib["npc_id"])
        if nid not in existing_spawns_by_nid:
            existing_spawns_by_nid[nid] = sp
        for spot in sp.findall("spot"):
            try:
                sx = round(float(spot.attrib["x"]), 0)
                sy = round(float(spot.attrib["y"]), 0)
                existing_coords.add((nid, sx, sy))
            except Exception:
                pass

    added_spots = 0
    added_spawns = 0

    for cs in client_spots:
        nid = cs["nid"]
        cx = round(cs["x"], 0)
        cy = round(cs["y"], 0)
        
        # Verifica se já existe próximo (tolerância de 2m)
        found = False
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if (nid, cx + dx, cy + dy) in existing_coords:
                    found = True
                    break
            if found:
                break
        if found:
            continue

        # Precisa adicionar
        x_str = f"{cs['x']:.4f}".rstrip("0").rstrip(".")
        y_str = f"{cs['y']:.4f}".rstrip("0").rstrip(".")
        z_str = f"{cs['z']:.4f}".rstrip("0").rstrip(".")
        h_str = str(cs["h"])

        if nid in existing_spawns_by_nid:
            sp_elem = existing_spawns_by_nid[nid]
            ET.SubElement(sp_elem, "spot", {"x": x_str, "y": y_str, "z": z_str, "h": h_str})
            added_spots += 1
        else:
            # Cria novo spawn
            npc_name = npc_names.get(nid, f"NPC_{nid}").replace("--", "-")
            comment = ET.Comment(f" {npc_name} ")
            spawn_map.append(comment)
            new_sp = ET.SubElement(spawn_map, "spawn", {"npc_id": str(nid), "respawn_time": "295"})
            ET.SubElement(new_sp, "spot", {"x": x_str, "y": y_str, "z": z_str, "h": h_str})
            existing_spawns_by_nid[nid] = new_sp
            added_spawns += 1
            added_spots += 1

        existing_coords.add((nid, cx, cy))

    print(f"      +{added_spots} novos spots adicionados (+{added_spawns} novos NPCs).")

    # Indenta e salva nos dois destinos
    ET.indent(s_root, space="\t")
    for base_dir in [GAME_SERVER_STATIC, EMULADOR_FINAL_STATIC]:
        dst = os.path.join(base_dir, "spawns", "Npcs", f"{mid}_{mname}.xml")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        s_tree.write(dst, encoding="utf-8", xml_declaration=True)
        print(f"      Salvo em: {dst}")

def main():
    npc_names = load_npc_names()
    merge_map(110010000, "Sanctum", "lc1", npc_names)
    merge_map(120010000, "Pandaemonium", "dc1", npc_names)
    print("[3/3] Concluído com sucesso!")

if __name__ == "__main__":
    main()
