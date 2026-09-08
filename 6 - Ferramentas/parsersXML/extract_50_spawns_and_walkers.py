#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Extração e Integração de Spawns e Rotas do Classic 5.0
1. Carrega todas as strings do cliente e resolve os nomes reais de todos os NPCs.
2. Carrega todas as rotas de waypoint.csv, calcula os hashes SHA-1 e atualiza npc_walker.xml.
3. Para cada mapa do 5.0 e instâncias faltantes, extrai os spawns de client_world_*.xml.
4. Agrupa os spots por npc_id, insere comentários <!-- Nome do NPC --> e vincula walker_id aos NPCs móveis.
5. Grava os arquivos em game-server/data/static_data e publica em EMULADOR FINAL.
"""

import os
import sys
import glob
import re
import hashlib
import xml.etree.ElementTree as ET
from collections import defaultdict

# Ajusta encoding da saída do console
sys.stdout.reconfigure(encoding='utf-8')

# Caminhos base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_TOOLS = os.path.join(BASE_DIR, "6 - Ferramentas")
CLIENT_DATA_DIR = os.path.join(BASE_DIR, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
STRINGS_DIR = os.path.join(CLIENT_DATA_DIR, "Strings", "strings")
CLIENT_NPCS_PATH = os.path.join(CLIENT_DATA_DIR, "data", "npcs", "client_npcs.xml")
CLIENT_WORLD_DIR = os.path.join(CLIENT_DATA_DIR, "data", "world")
WAYPOINT_CSV_PATH = os.path.join(CLIENT_WORLD_DIR, "waypoint.csv")

GAME_SERVER_STATIC = os.path.join(BASE_DIR, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data")
EMULADOR_FINAL_STATIC = os.path.join(BASE_DIR, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data")

sys.path.insert(0, BASE_TOOLS)
import aion_bxml

# -----------------------------------------------------------------------------
# 1. Carregamento de Strings e Nomes de NPCs
# -----------------------------------------------------------------------------
def load_client_strings():
    print("[1/5] Carregando tabelas de strings do cliente...")
    str_map = {}
    pattern = re.compile(r'<string>(.*?)</string>', re.DOTALL)
    
    xml_files = glob.glob(os.path.join(STRINGS_DIR, "*.xml"))
    for p in xml_files:
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

    print(f"      {len(str_map)} strings localizadas carregadas.")
    return str_map


def load_npc_names(str_map):
    print("[2/5] Carregando nomes de NPCs de client_npcs.xml...")
    raw = open(CLIENT_NPCS_PATH, "rb").read()
    xml_str = aion_bxml.decodifica(raw)
    root = ET.fromstring(xml_str)
    
    npc_name_map = {}
    for npc in root.findall("npc_client"):
        nid_str = npc.findtext("id")
        if not nid_str or not nid_str.isdigit():
            continue
        nid = int(nid_str)
        name_val = (npc.findtext("name") or "").strip()
        desc_val = (npc.findtext("desc") or "").strip()
        
        resolved = str_map.get(desc_val.lower(),
                   str_map.get(name_val.lower(),
                   str_map.get(str(nid), name_val)))
        
        # Limpeza de caracteres especiais
        resolved = resolved.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("’", "'")
        # Remove tags HTML se houver
        resolved = re.sub(r'<[^>]+>', '', resolved).strip()
        if not resolved:
            resolved = name_val if name_val else f"NPC_{nid}"
        npc_name_map[nid] = resolved

    print(f"      {len(npc_name_map)} nomes de NPCs mapeados com sucesso.")
    return npc_name_map


# -----------------------------------------------------------------------------
# 2. Carregamento e Atualização de Rotas de Caminhada (npc_walker.xml)
# -----------------------------------------------------------------------------
def load_waypoint_routes():
    print("[3/5] Carregando rotas de waypoint.csv...")
    routes = {}
    with open(WAYPOINT_CSV_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 5 and parts[1].isdigit():
                wname = parts[0].strip()
                num = int(parts[1].strip())
                rid = hashlib.sha1(wname.encode('utf-8')).hexdigest().upper()
                steps = []
                for i in range(num):
                    idx = 2 + i * 3
                    if idx + 2 < len(parts):
                        try:
                            steps.append((float(parts[idx]), float(parts[idx + 1]), float(parts[idx + 2])))
                        except Exception:
                            pass
                if steps:
                    routes[rid] = {
                        "name": wname,
                        "steps": steps,
                        "prefix": wname.split("_")[0].lower()
                    }
    print(f"      {len(routes)} rotas carregadas de waypoint.csv.")
    return routes


def update_npc_walker(routes):
    print("      Verificando rotas faltantes em npc_walker.xml...")
    walker_file = os.path.join(GAME_SERVER_STATIC, "npc_walker", "npc_walker.xml")
    tree = ET.parse(walker_file)
    root = tree.getroot()
    
    existing_rids = set(wt.attrib.get("route_id") for wt in root.findall("walker_template"))
    
    added_count = 0
    for rid, rdata in routes.items():
        if rid not in existing_rids:
            wt_elem = ET.Element("walker_template", {"route_id": rid})
            for sx, sy, sz in rdata["steps"]:
                ET.SubElement(wt_elem, "routestep", {
                    "x": f"{sx:.4f}".rstrip("0").rstrip("."),
                    "y": f"{sy:.4f}".rstrip("0").rstrip("."),
                    "z": f"{sz:.4f}".rstrip("0").rstrip(".")
                })
            root.append(wt_elem)
            existing_rids.add(rid)
            added_count += 1
            
    print(f"      +{added_count} rotas adicionadas a npc_walker.xml.")
    
    # Indenta e grava nos dois diretórios
    ET.indent(root, space="\t")
    
    for base_dir in [GAME_SERVER_STATIC, EMULADOR_FINAL_STATIC]:
        dst_path = os.path.join(base_dir, "npc_walker", "npc_walker.xml")
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        tree.write(dst_path, encoding="utf-8", xml_declaration=True)
        print(f"      Gravado: {dst_path}")


# -----------------------------------------------------------------------------
# 3. Definição dos Mapas 5.0 e Extração de Spawns
# -----------------------------------------------------------------------------
MAPS_TO_GENERATE = [
    # Mapas Normais / World Maps (pasta: Npcs)
    {"id": 800010000, "name": "Apheta_Beluslan", "cname": "LDF3_01", "folder": "Npcs"},
    {"id": 800020000, "name": "LDF4a", "cname": "LDF4a", "folder": "Npcs"},
    {"id": 800030000, "name": "Laphsaran", "cname": "LDF10", "folder": "Npcs"},
    {"id": 800040000, "name": "Tiamaranta_Mesa", "cname": "LDF4b", "folder": "Npcs"},
    {"id": 800060000, "name": "Teva", "cname": "LDF4_Teva", "folder": "Npcs"},
    {"id": 110030000, "name": "Sanctum_Gate", "cname": "LC1a", "folder": "Npcs"},
    {"id": 110040000, "name": "Griffoen", "cname": "LC1Space", "folder": "Npcs"},
    {"id": 120030000, "name": "Pandaemonium_Entrance", "cname": "DC1a", "folder": "Npcs"},
    {"id": 120040000, "name": "Habrok", "cname": "DC1Space", "folder": "Npcs"},
    {"id": 390000000, "name": "Land_of_Shadows", "cname": "IDTutorialQ", "folder": "Npcs"},

    # Mapas Instância / Campos de Batalha (pasta: Instances)
    {"id": 300650000, "name": "Dranium_Battlefield", "cname": "IDDranamine_War", "folder": "Instances"},
    {"id": 300660000, "name": "Burning_Blood_Fortress", "cname": "IDDragon_Twin", "folder": "Instances"},
    {"id": 300670000, "name": "Dokkaebi_Realm", "cname": "IDDokkaebi", "folder": "Instances"},
    {"id": 300680000, "name": "Sonsara", "cname": "IDSunshara_Isle_War", "folder": "Instances"},
    {"id": 300690000, "name": "Sunayakas_Treasure_Chamber", "cname": "IDEvent_01", "folder": "Instances"},
    {"id": 300710000, "name": "Vindachinerks_Infinity_Cube", "cname": "IDCubeQ", "folder": "Instances"},
    {"id": 300720000, "name": "Secret_of_the_Cube_Trial", "cname": "IDCubeM", "folder": "Instances"},
    {"id": 300900000, "name": "Beast_Rival_War", "cname": "IDEvent_04", "folder": "Instances"},
    {"id": 301000000, "name": "Tiamats_Sanctuary", "cname": "IDDragonlord", "folder": "Instances"},
    {"id": 330010000, "name": "Jakunerk_Game", "cname": "IDPogusgame", "folder": "Instances"},
    {"id": 330020000, "name": "Punishing_Aster", "cname": "IDFist", "folder": "Instances"},
    {"id": 330030000, "name": "Bloody_Aster", "cname": "IDFist_01", "folder": "Instances"},
    {"id": 330040000, "name": "IDEvent_Damage_01", "cname": "IDEvent_damage_01", "folder": "Instances"},
    {"id": 800050000, "name": "Sunshara_Isle_Lobby", "cname": "Sunshara_Isle_Lobby", "folder": "Instances"},
    {"id": 800070000, "name": "Balic_Treasury", "cname": "Tiamat_Down", "folder": "Instances"},
    {"id": 800080000, "name": "Dragon_Lords_Library", "cname": "Tiamat_Reward", "folder": "Instances"},
    {"id": 800090000, "name": "Balic_Treasury_of_Torment", "cname": "Tiamat_Down_R", "folder": "Instances"},
    {"id": 300300000, "name": "Empyrean_Crucible", "cname": "IDArena", "folder": "Instances"},
    {"id": 300320000, "name": "Crucible_Challenge", "cname": "IDArena_Solo", "folder": "Instances"},
    {"id": 300470000, "name": "Arena_of_Glory", "cname": "IDArena_Glory", "folder": "Instances"},
    {"id": 300490000, "name": "Liberated_Beshmundir_Temple", "cname": "IDCatacombs_Hell", "folder": "Instances"},
    {"id": 300500000, "name": "Tempus", "cname": "IDF4Re_Solo", "folder": "Instances"},
    {"id": 300530000, "name": "IDArena_Team01_T", "cname": "IDArena_Team01_T", "folder": "Instances"},
    {"id": 300580000, "name": "Phaestos_Disc", "cname": "IDPHAISTOS_DISC", "folder": "Instances"},
    {"id": 300151000, "name": "Udas_Temple_Q", "cname": "IDTemple_UpQ", "folder": "Instances"},
    {"id": 300161000, "name": "Lower_Udas_Temple_Q", "cname": "IDTemple_LowQ", "folder": "Instances"},
]


def find_walker_route(nx, ny, nz, map_routes):
    """Localiza a rota mais próxima para o NPC móvel."""
    best_dist = 999999
    best_rid = None
    best_idx = 0
    
    for rid, rdata in map_routes.items():
        for idx, (sx, sy, sz) in enumerate(rdata["steps"]):
            d = ((nx - sx)**2 + (ny - sy)**2 + (nz - sz)**2)**0.5
            if d < best_dist:
                best_dist = d
                best_rid = rid
                best_idx = idx
                
    if best_dist <= 50.0:
        return best_rid, best_idx + 1
    return None, None


def generate_map_spawns(map_info, npc_name_map, all_routes):
    mid = map_info["id"]
    mname = map_info["name"]
    cname = map_info["cname"]
    folder = map_info["folder"]
    
    cworld_file = os.path.join(CLIENT_WORLD_DIR, f"client_world_{cname.lower()}.xml")
    
    # Filtra rotas potenciais deste mapa pelo cname
    cname_clean = cname.lower().replace("_", "")
    map_routes = {}
    for rid, rdata in all_routes.items():
        rp = rdata["name"].lower().replace("_", "")
        if cname_clean in rp or rp in cname_clean:
            map_routes[rid] = rdata
    if not map_routes:
        # Tenta pelo prefixo ou palavras-chave
        prefix = cname.split("_")[0].lower()
        for rid, rdata in all_routes.items():
            if rdata["prefix"] == prefix or prefix in rdata["name"].lower():
                map_routes[rid] = rdata
                
    # Lê os npc_infos
    npc_spots = defaultdict(list)
    total_spots = 0
    walker_assigned = 0
    
    if os.path.exists(cworld_file):
        try:
            raw = open(cworld_file, "rb").read()
            if aion_bxml.e_bxml(cworld_file):
                xml_str = aion_bxml.decodifica(raw)
                root = ET.fromstring(xml_str)
                for ni in root.findall(".//npc_info"):
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
                    except Exception:
                        continue
                        
                    is_moving = (ni.findtext("movetype") or "").lower() == "true"
                    spot_data = {"x": x, "y": y, "z": z, "h": 0}
                    
                    if is_moving and map_routes:
                        rid, sidx = find_walker_route(x, y, z, map_routes)
                        if rid:
                            spot_data["walker_id"] = rid
                            spot_data["walker_index"] = sidx
                            walker_assigned += 1
                            
                    npc_spots[nid].append(spot_data)
                    total_spots += 1
        except Exception as e:
            print(f"      [AVISO] Erro lendo {cworld_file}: {e}")

    # Monta o XML de spawns com comentários
    xml_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<spawns xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../spawns.xsd">',
        f'\t<spawn_map map_id="{mid}">'
    ]
    
    for nid in sorted(npc_spots.keys()):
        npc_name = npc_name_map.get(nid, f"NPC_{nid}")
        # Escapa comentário XML
        npc_name_comment = npc_name.replace("--", "-")
        xml_lines.append(f'\t\t<!-- {npc_name_comment} -->')
        xml_lines.append(f'\t\t<spawn npc_id="{nid}" respawn_time="295">')
        for sp in npc_spots[nid]:
            x_str = f"{sp['x']:.4f}".rstrip("0").rstrip(".")
            y_str = f"{sp['y']:.4f}".rstrip("0").rstrip(".")
            z_str = f"{sp['z']:.4f}".rstrip("0").rstrip(".")
            h_str = str(sp.get("h", 0))
            
            walker_attr = ""
            if "walker_id" in sp:
                walker_attr = f' walker_id="{sp["walker_id"]}" walker_index="{sp["walker_index"]}"'
                
            xml_lines.append(f'\t\t\t<spot x="{x_str}" y="{y_str}" z="{z_str}" h="{h_str}"{walker_attr}/>')
        xml_lines.append('\t\t</spawn>')
        
    xml_lines.append('\t</spawn_map>')
    xml_lines.append('</spawns>')
    xml_lines.append('')
    
    content = "\n".join(xml_lines)
    
    filename = f"{mid}_{mname}.xml"
    for base_dir in [GAME_SERVER_STATIC, EMULADOR_FINAL_STATIC]:
        target_path = os.path.join(base_dir, "spawns", folder, filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    print(f"  [OK] Mapa {mid} ({mname}): {len(npc_spots)} tipos de NPC, {total_spots} spots, {walker_assigned} walkers -> spawns/{folder}/{filename}")


def main():
    print("=" * 80)
    print("EXTRAÇÃO E GERAÇÃO DE SPAWNS E ROTAS DO AION CLASSIC 5.0")
    print("=" * 80)
    
    # 1. Carrega Strings e Nomes
    str_map = load_client_strings()
    npc_names = load_npc_names(str_map)
    
    # 2. Carrega Rotas e Atualiza npc_walker.xml
    routes = load_waypoint_routes()
    update_npc_walker(routes)
    
    # 3. Processa e Gera cada Mapa
    print(f"[4/5] Gerando XMLs de spawn para {len(MAPS_TO_GENERATE)} mapas...")
    for minfo in MAPS_TO_GENERATE:
        generate_map_spawns(minfo, npc_names, routes)
        
    print("\n[5/5] Extração e publicação concluídas com sucesso!")
    print("=" * 80)


if __name__ == "__main__":
    main()
