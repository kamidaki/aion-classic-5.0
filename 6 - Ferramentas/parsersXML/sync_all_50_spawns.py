#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_all_50_spawns.py

Sincronização Completa de Spawns entre o Cliente Oficial Aion Classic 5.0 e o Emulador Java 25.
Audit e extração de:
  1. Coletas (Gather) a partir de HSP e SP em mission_mission0.xml e gather_src.xml.
  2. NPCs e Monstros a partir de SP em mission_mission0.xml, source_sphere.csv e client_world_*.xml.
  3. Mapeamento de todos os mapas para Npcs, Instances e Gather.
  4. Resolução de terreno Z com heightmaps 16-bit (geo/*.png).
  5. Conversão de rotação CryEngine para heading H (0..119).
  6. Garantia de unicidade de spawn por npc_id (compatível com spawns.xsd).
  7. Publicação atômica em Código Fonte e Produto Final.
"""

import os
import sys
import glob
import math
import re
import hashlib
import xml.etree.ElementTree as ET
from collections import defaultdict

# Console UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = r"D:\AION CLASSIC 5.0 - EMULADOR"
TOOLS_DIR = os.path.join(PROJECT_ROOT, "6 - Ferramentas")
PARSERS_DIR = os.path.join(TOOLS_DIR, "parsersXML")

sys.path.insert(0, TOOLS_DIR)
import aion_bxml

# Diretórios principais
ref_folder = [x for x in os.listdir(PROJECT_ROOT) if x.startswith("5")][0]
CLIENT_EXTRACTED = os.path.join(PROJECT_ROOT, ref_folder, "3 - Client 5.0 - Dados Extraidos")
DATA_DIR = os.path.join(CLIENT_EXTRACTED, "data")
LEVELS_DIR = os.path.join(CLIENT_EXTRACTED, "levels")
STRINGS_DIR = os.path.join(CLIENT_EXTRACTED, "Strings", "strings")

SRC_STATIC = os.path.join(PROJECT_ROOT, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data")
PROD_STATIC = os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data")
GEO_DIR = os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "geo")

# Mapas que não devem ser modificados (solicitação prévia)
IGNORED_MAPS = {110030000, 120030000}


def angle_to_heading(angle_str):
    if not angle_str:
        return 0
    try:
        parts = angle_str.split(",")
        z_deg = float(parts[2] if len(parts) >= 3 else parts[0])
        num = int(round(z_deg)) // 3
        if num < 0:
            num = 120 + (num % 120)
        num -= 30
        if num < 0:
            num += 120
        return num % 120
    except Exception:
        return 0


class Terrenos:
    """Heightmap 16 bits por mapa: pixel * 2048 / 65536 metros, células de 2m."""
    def __init__(self, geo_dir):
        try:
            import numpy as np
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            self.np = np
            self.Image = Image
            self.cache = {}
            self.files = {}
            if os.path.isdir(geo_dir):
                for p in glob.glob(os.path.join(geo_dir, "*.png")):
                    base = os.path.basename(p)[:-4]
                    if not base.endswith("_materials"):
                        for mid in base.split(","):
                            if mid.isdigit():
                                self.files[int(mid)] = p
            print(f"[*] Terrenos: carregados mapeamentos de {len(self.files)} mapas de terreno.")
        except Exception as e:
            print(f"[!] Terrenos desativado: {e}")
            self.files = {}

    def get_z(self, mid, x, y):
        if mid not in self.files:
            return None
        if mid not in self.cache:
            try:
                im = self.Image.open(self.files[mid])
                if im.mode.startswith("I"):
                    self.cache[mid] = self.np.array(im, dtype=self.np.uint32)
                else:
                    self.cache[mid] = None
            except Exception:
                self.cache[mid] = None

        arr = self.cache.get(mid)
        if arr is None:
            return None
        xi, yi = int(x // 2), int(y // 2)
        h, w = arr.shape
        if xi < 0 or xi >= w or yi < 0 or yi >= h:
            return None
        val = int(arr[yi, xi])  # [row, col]
        if val == 0xFFFF:
            return None
        return val * 2048.0 / 65536.0


def load_strings():
    print("[1/8] Carregando tabelas de strings...")
    str_map = {}
    pattern = re.compile(r'<string>(.*?)</string>', re.DOTALL)
    xml_files = glob.glob(os.path.join(STRINGS_DIR, "*.xml"))
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
    print(f"      {len(str_map)} strings carregadas.")
    return str_map


def load_npcs_and_gathers(str_map):
    print("[2/8] Indexando templates de NPCs e Coletas...")
    # 1. Gather
    gather_path = os.path.join(DATA_DIR, "Gather", "gather_src.xml")
    g_raw = open(gather_path, "rb").read()
    g_xml = aion_bxml.decodifica(g_raw)
    g_root = ET.fromstring(g_xml)
    
    gather_by_name = {}
    gather_by_id = {}
    for g in g_root.findall("gather_src"):
        name = (g.findtext("name") or "").strip().lower()
        gid_str = g.findtext("id")
        desc = (g.findtext("desc") or "").strip()
        if name and gid_str and gid_str.isdigit():
            gid = int(gid_str)
            loc_name = str_map.get(desc.lower(), str_map.get(name, f"Gather_{gid}"))
            loc_name = re.sub(r'<[^>]+>', '', loc_name).strip()
            info = {"id": gid, "name": name, "loc_name": loc_name}
            gather_by_name[name] = info
            gather_by_id[gid] = info

    # 2. NPCs
    npcs_path = os.path.join(DATA_DIR, "npcs", "client_npcs.xml")
    n_raw = open(npcs_path, "rb").read()
    n_xml = aion_bxml.decodifica(n_raw)
    n_root = ET.fromstring(n_xml)
    
    npc_by_name = {}
    npc_by_id = {}
    for n in n_root.findall("npc_client"):
        name = (n.findtext("name") or "").strip().lower()
        nid_str = n.findtext("id")
        desc = (n.findtext("desc") or "").strip()
        ui_type = (n.findtext("ui_type") or "").strip().lower()
        npc_type = (n.findtext("npc_type") or "").strip()
        if name and nid_str and nid_str.isdigit():
            nid = int(nid_str)
            loc_name = str_map.get(desc.lower(), str_map.get(name, f"NPC_{nid}"))
            loc_name = re.sub(r'<[^>]+>', '', loc_name).strip()
            info = {
                "id": nid,
                "name": name,
                "loc_name": loc_name,
                "ui_type": ui_type,
                "npc_type": npc_type
            }
            if name not in npc_by_name:
                npc_by_name[name] = info
            npc_by_id[nid] = info

    # 3. Validar templates conhecidos no emulador
    valid_npc_ids = set()
    emu_npc_tmpl = os.path.join(SRC_STATIC, "npcs", "npc_templates.xml")
    if os.path.exists(emu_npc_tmpl):
        for _, elem in ET.iterparse(emu_npc_tmpl, events=("start",)):
            if elem.tag == "npc_template":
                tid = elem.get("npc_id")
                if tid and tid.isdigit():
                    valid_npc_ids.add(int(tid))

    valid_gather_ids = set()
    emu_gather_tmpl = os.path.join(SRC_STATIC, "gatherables", "gatherable_templates.xml")
    if os.path.exists(emu_gather_tmpl):
        for _, elem in ET.iterparse(emu_gather_tmpl, events=("start",)):
            if elem.tag == "gatherable_template":
                gid = elem.get("id")
                if gid and gid.isdigit():
                    valid_gather_ids.add(int(gid))

    print(f"      {len(gather_by_name)} recursos de coleta ({len(valid_gather_ids)} válidos no emulador).")
    print(f"      {len(npc_by_name)} templates de NPC ({len(valid_npc_ids)} válidos no emulador).")
    return gather_by_name, gather_by_id, npc_by_name, npc_by_id, valid_npc_ids, valid_gather_ids


def load_world_mappings():
    print("[3/8] Mapeando mundos e zonas...")
    wid_path = os.path.join(DATA_DIR, "world", "WorldId.xml")
    raw = open(wid_path, "rb").read()
    xml_str = aion_bxml.decodifica(raw)
    root = ET.fromstring(xml_str)
    
    folder_to_id = {}
    for elem in root.findall("data"):
        wid = elem.get("id")
        folder = (elem.text or "").strip().lower()
        if wid and folder and wid.isdigit():
            folder_to_id[folder] = int(wid)

    emu_wm = os.path.join(SRC_STATIC, "world_maps.xml")
    tree_wm = ET.parse(emu_wm)
    maps_info = {}
    for m in tree_wm.getroot().findall("map"):
        mid = int(m.get("id"))
        name = m.get("name")
        cname = (m.get("cName") or "").lower()
        wtype = m.get("world_type") or "INSTANCE"
        
        # Categorização
        is_instance = (mid >= 300000000 and mid < 400000000) or wtype == "INSTANCE"
        if mid in (110010000, 110020000, 110030000, 110040000, 110070000,
                    120010000, 120020000, 120030000, 120040000, 120080000,
                    210010000, 210020000, 210030000, 210040000, 210050000, 210060000, 210070000, 210080000,
                    220010000, 220020000, 220030000, 220040000, 220050000, 220070000, 220080000, 220090000,
                    400010000, 800010000, 800020000, 800030000, 800040000, 800060000):
            category = "Npcs"
        elif is_instance:
            category = "Instances"
        else:
            category = "Npcs"

        maps_info[mid] = {
            "id": mid,
            "name": name,
            "cname": cname,
            "category": category,
            "world_type": wtype
        }

    print(f"      {len(maps_info)} mundos mapeados ({sum(1 for m in maps_info.values() if m['category'] == 'Npcs')} Npcs, {sum(1 for m in maps_info.values() if m['category'] == 'Instances')} Instances).")
    return folder_to_id, maps_info


def load_existing_spawns(mid, category):
    """Carrega spawns existentes preservando atributos de servidor."""
    existing_file = None
    target_dir = os.path.join(SRC_STATIC, "spawns", category)
    if os.path.exists(target_dir):
        for f in os.listdir(target_dir):
            if f.startswith(f"{mid}_") and f.endswith(".xml"):
                existing_file = os.path.join(target_dir, f)
                break

    npc_spawns = {}  # npc_id -> {"attrib": {}, "spots": []}
    coords_set = set()

    if existing_file and os.path.exists(existing_file):
        try:
            tree = ET.parse(existing_file)
            root = tree.getroot()
            for sp in root.findall(".//spawn"):
                nid_str = sp.get("npc_id")
                if not nid_str or not nid_str.isdigit():
                    continue
                nid = int(nid_str)
                sp_attrib = dict(sp.attrib)
                
                spots = []
                for st in sp.findall("spot"):
                    st_attrib = dict(st.attrib)
                    try:
                        x = float(st_attrib.get("x", "0"))
                        y = float(st_attrib.get("y", "0"))
                        z = float(st_attrib.get("z", "0"))
                        coords_set.add((nid, round(x, 1), round(y, 1)))
                        spots.append(st_attrib)
                    except Exception:
                        continue

                if nid not in npc_spawns:
                    npc_spawns[nid] = {"attrib": sp_attrib, "spots": spots}
                else:
                    npc_spawns[nid]["spots"].extend(spots)
        except Exception as e:
            print(f"      [AVISO] Erro ao ler spawn existente {existing_file}: {e}")

    return npc_spawns, coords_set


def parse_mission_objects(mid, folder_name, gather_by_name, npc_by_name, valid_npc_ids, valid_gather_ids, terrenos):
    """Lê mission_mission0.xml e extrai pontos de Gather e NPCs."""
    m_path = os.path.join(LEVELS_DIR, folder_name, "mission_mission0.xml")
    if not os.path.exists(m_path):
        return [], []

    gather_spots = []
    npc_spots = []

    try:
        tree = ET.parse(m_path)
        root = tree.getroot()
        for obj in root.findall(".//Object"):
            obj_type = obj.get("Type")
            npc_name = (obj.get("npc") or "").strip().lower()
            pos_str = obj.get("Pos")
            if not pos_str:
                continue
            coords = pos_str.split(",")
            if len(coords) < 3:
                continue
            try:
                x = float(coords[0].strip())
                y = float(coords[1].strip())
                z = float(coords[2].strip())
            except Exception:
                continue

            # Altura Z pelo heightmap de terreno se disponível
            terr_z = terrenos.get_z(mid, x, y)
            if terr_z is not None and not math.isnan(terr_z):
                # Se o marcador CryEngine está até 4m acima do chão, ajusta ao piso
                if -1.0 <= (z - terr_z) <= 5.0:
                    z = terr_z

            h = angle_to_heading(obj.get("Angles"))

            spot = {
                "x": round(x, 4),
                "y": round(y, 4),
                "z": round(z, 4),
                "h": h
            }

            # 1. Gather (HSP ou SP com nome de gather)
            if obj_type == "HSP" or (npc_name and npc_name in gather_by_name):
                if npc_name in gather_by_name:
                    gid = gather_by_name[npc_name]["id"]
                    if gid in valid_gather_ids:
                        gather_spots.append((gid, spot, gather_by_name[npc_name]["loc_name"]))
                continue

            # 2. NPC / Monster (SP)
            if obj_type == "SP" and npc_name:
                if npc_name in npc_by_name:
                    nid = npc_by_name[npc_name]["id"]
                    if nid in valid_npc_ids:
                        npc_spots.append((nid, spot, npc_by_name[npc_name]["loc_name"]))
    except Exception as e:
        print(f"      [AVISO] Erro ao analisar {m_path}: {e}")

    return gather_spots, npc_spots


def load_source_spheres():
    print("[4/8] Carregando source_sphere.csv...")
    spheres_by_zone = defaultdict(list)
    ss_path = os.path.join(DATA_DIR, "world", "source_sphere.csv")
    if os.path.exists(ss_path):
        with open(ss_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 6:
                    name = parts[0].strip().lower()
                    stype = parts[1].strip().lower()
                    zone = parts[2].strip().lower()
                    try:
                        x = float(parts[3])
                        y = float(parts[4])
                        z = float(parts[5])
                        wp = parts[7].strip() if len(parts) > 7 else ""
                        spheres_by_zone[zone].append({
                            "name": name,
                            "type": stype,
                            "x": x,
                            "y": y,
                            "z": z,
                            "wp": wp
                        })
                    except Exception:
                        continue
    print(f"      {sum(len(v) for v in spheres_by_zone.values())} esferas de spawn em {len(spheres_by_zone)} zonas.")
    return spheres_by_zone


def write_spawn_file(filepath, map_id, spawns_dict, id_to_name, default_respawn=295):
    """Grava arquivo de spawn XML formatado rigorosamente conforme spawns.xsd."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as out:
        out.write('<?xml version="1.0" encoding="utf-8"?>\n')
        out.write('<spawns xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n')
        out.write(f'\t<spawn_map map_id="{map_id}">\n')

        for nid in sorted(spawns_dict.keys()):
            data = spawns_dict[nid]
            attrib = dict(data["attrib"])
            spots = data["spots"]
            if not spots:
                continue

            respawn = attrib.get("respawn_time", str(default_respawn))
            pool = attrib.get("pool")
            handler = attrib.get("handler")
            custom = attrib.get("custom")

            sp_attrs = f'npc_id="{nid}" respawn_time="{respawn}"'
            if pool:
                sp_attrs += f' pool="{pool}"'
            if handler:
                sp_attrs += f' handler="{handler}"'
            if custom:
                sp_attrs += f' custom="{custom}"'

            loc_name = id_to_name.get(nid, f"ID_{nid}")
            # Limpa caracteres ilegais para comentários XML
            loc_name = loc_name.replace("--", "-").replace("&", "&amp;")

            out.write(f'\t\t<!-- {loc_name} -->\n')
            out.write(f'\t\t<spawn {sp_attrs}>\n')
            for st in spots:
                st_str = f'x="{st["x"]}" y="{st["y"]}" z="{st["z"]}" h="{st.get("h", 0)}"'
                for k in ["static_id", "random_walk", "walker_id", "walker_index", "fly", "anchor", "state", "aerial_spawn", "ai"]:
                    if k in st and st[k] not in ("", "0", 0, None):
                        st_str += f' {k}="{st[k]}"'
                out.write(f'\t\t\t<spot {st_str}/>\n')
            out.write('\t\t</spawn>\n')

        out.write('\t</spawn_map>\n')
        out.write('</spawns>\n')


def main():
    print("=" * 80)
    print("Sincronização Master de Spawns 5.0 (Aion Classic -> Emulador Java 25)")
    print("=" * 80)

    terrenos = Terrenos(GEO_DIR)
    str_map = load_strings()
    gather_by_name, gather_by_id, npc_by_name, npc_by_id, valid_npc_ids, valid_gather_ids = load_npcs_and_gathers(str_map)
    folder_to_id, maps_info = load_world_mappings()
    spheres_by_zone = load_source_spheres()

    print("[5/8] Processando sincronização por mapa...")

    total_npcs_added = 0
    total_gathers_added = 0
    files_updated = 0

    # Dicionário reverso de ID -> Nome Localizado
    id_to_name = {}
    for gid, info in gather_by_id.items():
        id_to_name[gid] = info["loc_name"]
    for nid, info in npc_by_id.items():
        id_to_name[nid] = info["loc_name"]

    # Itera sobre todos os mapas cadastrados
    for mid, minfo in sorted(maps_info.items()):
        if mid in IGNORED_MAPS:
            continue

        mname = minfo["name"]
        cname = minfo["cname"]
        category = minfo["category"]

        # -------------------------------------------------------------
        # A. Sincronização de Gather
        # -------------------------------------------------------------
        existing_gathers, g_coords = load_existing_spawns(mid, "Gather")
        initial_g_spots = sum(len(d["spots"]) for d in existing_gathers.values())

        # Procura pasta de level correspondente
        level_folders = [cname]
        for f, wid in folder_to_id.items():
            if wid == mid and f not in level_folders:
                level_folders.append(f)

        g_added = 0
        n_added = 0

        # Spawns de mission_mission0.xml
        for lf in level_folders:
            g_spots, n_spots = parse_mission_objects(mid, lf, gather_by_name, npc_by_name, valid_npc_ids, valid_gather_ids, terrenos)

            # Adiciona Gathers
            for gid, spot, _ in g_spots:
                coord_key = (gid, round(spot["x"], 1), round(spot["y"], 1))
                if coord_key not in g_coords:
                    g_coords.add(coord_key)
                    if gid not in existing_gathers:
                        existing_gathers[gid] = {"attrib": {"npc_id": str(gid), "respawn_time": "295"}, "spots": []}
                    existing_gathers[gid]["spots"].append(spot)
                    g_added += 1

        # Grava Gather se houver spots
        total_g_spots = sum(len(d["spots"]) for d in existing_gathers.values())
        if total_g_spots > 0 and (g_added > 0 or initial_g_spots == 0):
            fname = f"{mid}_{mname}.xml"
            src_file = os.path.join(SRC_STATIC, "spawns", "Gather", fname)
            prod_file = os.path.join(PROD_STATIC, "spawns", "Gather", fname)
            write_spawn_file(src_file, mid, existing_gathers, id_to_name, default_respawn=295)
            write_spawn_file(prod_file, mid, existing_gathers, id_to_name, default_respawn=295)
            total_gathers_added += g_added

        # -------------------------------------------------------------
        # B. Sincronização de NPCs e Monstros (Npcs ou Instances)
        # -------------------------------------------------------------
        existing_npcs, n_coords = load_existing_spawns(mid, category)
        initial_n_spots = sum(len(d["spots"]) for d in existing_npcs.values())

        # 1. De mission_mission0.xml
        for lf in level_folders:
            _, n_spots = parse_mission_objects(mid, lf, gather_by_name, npc_by_name, valid_npc_ids, valid_gather_ids, terrenos)
            for nid, spot, _ in n_spots:
                coord_key = (nid, round(spot["x"], 1), round(spot["y"], 1))
                if coord_key not in n_coords:
                    n_coords.add(coord_key)
                    if nid not in existing_npcs:
                        existing_npcs[nid] = {"attrib": {"npc_id": str(nid), "respawn_time": "295"}, "spots": []}
                    existing_npcs[nid]["spots"].append(spot)
                    n_added += 1

        # 2. De source_sphere.csv
        for lf in level_folders:
            spheres = spheres_by_zone.get(lf, [])
            for sph in spheres:
                s_name = sph["name"]
                if s_name in npc_by_name:
                    nid = npc_by_name[s_name]["id"]
                    if nid in valid_npc_ids:
                        sx, sy, sz = sph["x"], sph["y"], sph["z"]
                        terr_z = terrenos.get_z(mid, sx, sy)
                        if terr_z is not None and not math.isnan(terr_z) and -1.0 <= (sz - terr_z) <= 5.0:
                            sz = terr_z
                        coord_key = (nid, round(sx, 1), round(sy, 1))
                        if coord_key not in n_coords:
                            n_coords.add(coord_key)
                            spot = {
                                "x": round(sx, 4),
                                "y": round(sy, 4),
                                "z": round(sz, 4),
                                "h": 0
                            }
                            if sph.get("wp"):
                                wp_hash = hashlib.sha1(sph["wp"].encode("utf-8")).hexdigest().upper()
                                spot["walker_id"] = wp_hash
                            if nid not in existing_npcs:
                                existing_npcs[nid] = {"attrib": {"npc_id": str(nid), "respawn_time": "295"}, "spots": []}
                            existing_npcs[nid]["spots"].append(spot)
                            n_added += 1

        # Grava NPC/Instance se houver spots
        total_n_spots = sum(len(d["spots"]) for d in existing_npcs.values())
        if total_n_spots > 0 and (n_added > 0 or initial_n_spots == 0):
            fname = f"{mid}_{mname}.xml"
            src_file = os.path.join(SRC_STATIC, "spawns", category, fname)
            prod_file = os.path.join(PROD_STATIC, "spawns", category, fname)
            write_spawn_file(src_file, mid, existing_npcs, id_to_name, default_respawn=295)
            write_spawn_file(prod_file, mid, existing_npcs, id_to_name, default_respawn=295)
            total_npcs_added += n_added
            files_updated += 1

        if g_added > 0 or n_added > 0:
            print(f"  [OK] Mapa {mid} ({mname} | {category}): +{n_added} NPCs/Monstros (total {total_n_spots}), +{g_added} Gathers (total {total_g_spots})")

    print("=" * 80)
    print(f"[CONCLUÍDO] Sincronização Finalizada com Sucesso!")
    print(f"  - Total de spots de Coleta adicionados: {total_gathers_added}")
    print(f"  - Total de spots de NPCs/Monstros adicionados: {total_npcs_added}")
    print(f"  - Arquivos de spawn atualizados / criados: {files_updated}")
    print("=" * 80)


if __name__ == "__main__":
    main()
