#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_maps_spawns.py

Extrai e gera spawns completos para os mapas:
  - Tiamaranta (800040000 / LDF4b)
  - Tiamat Down / Balic Treasury (800070000 / Tiamat_Down)
  - Teva (800060000 / ldf4_teva)

Características:
  - Mapeia objetos CryEngine (SP, NPC, MONSTER) para client_npcs.xml e HSP para gather_src.xml.
  - Converte coordenadas e calcula heading canônico a partir de Angles="pitch,roll,yaw".
  - Preserva spawns existentes, suas rotas de walker (walker_id/walker_index) e evita duplicatas (< 0.5m).
  - Agrupa spots por npc_id estritamente de acordo com a regra unique-npc-id do spawns.xsd.
  - Valida todos os arquivos gerados contra spawns.xsd.
  - Sincroniza Código Fonte e Emulador Produto Final com backup atômico.

Uso:
  python generate_maps_spawns.py           (modo dry-run / análise)
  python generate_maps_spawns.py --aplicar (aplica as alterações)
"""

import argparse
import glob
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(PARSERS_DIR)))
sys.path.insert(0, PARSERS_DIR)

import backup_manager as bm

CLIENT_XML_DIR = r"G:\Projetos AION\XMLS AION CLASSIC"
LEVELS_DIR = os.path.join(PROJECT_ROOT, r"Ferramentas e Documentos\Client e Coletas\Client 5.0 - Dados Extraidos\levels")
STRINGS_DIR = os.path.join(PROJECT_ROOT, r"Ferramentas e Documentos\Client e Coletas\Client 5.0 - Dados Extraidos\Strings\strings")

SRC_STATIC = os.path.join(PROJECT_ROOT, r"Código Fonte - Emulador\game-server\data\static_data")
PROD_STATIC = os.path.join(PROJECT_ROOT, r"Emulador - Produto Final\GameServer\data\static_data")
SPAWNS_XSD = os.path.join(SRC_STATIC, r"spawns\spawns.xsd")

MAP_CONFIGS = [
    {
        "id": 800040000,
        "name": "Tiamaranta_Mesa",
        "cname": "LDF4b",
        "folder": "Npcs",
        "mission": os.path.join(LEVELS_DIR, r"LDF4b\mission_mission0.xml"),
        "has_gather": True,
    },
    {
        "id": 800070000,
        "name": "Balic_Treasury",
        "cname": "Tiamat_Down",
        "folder": "Instances",
        "mission": os.path.join(LEVELS_DIR, r"Tiamat_Down\mission_mission0.xml"),
        "has_gather": False,
    },
    {
        "id": 800060000,
        "name": "Teva",
        "cname": "ldf4_teva",
        "folder": "Npcs",
        "mission": os.path.join(LEVELS_DIR, r"ldf4_teva\mission_mission0.xml"),
        "has_gather": True,
    }
]

def load_strings():
    print("[1/6] Carregando tabelas de strings...")
    str_map = {}
    pattern = re.compile(r'<string>(.*?)</string>', re.DOTALL)
    if os.path.isdir(STRINGS_DIR):
        for p in glob.glob(os.path.join(STRINGS_DIR, "*.xml")):
            try:
                raw = open(p, "rb").read()
                text = ""
                for enc in ["utf-16", "utf-8", "latin1"]:
                    try:
                        text = raw.decode(enc)
                        break
                    except Exception:
                        pass
                for s in pattern.findall(text):
                    sname = re.search(r'<name>(.*?)</name>', s)
                    sbody = re.search(r'<body>(.*?)</body>', s)
                    if sname and sbody:
                        str_map[sname.group(1).strip().lower()] = sbody.group(1).strip()
            except Exception:
                pass
    print(f"      {len(str_map)} strings carregadas.")
    return str_map

def load_client_npcs(str_map):
    print("[2/6] Carregando client_npcs.xml...")
    client_npcs_path = os.path.join(CLIENT_XML_DIR, r"data\npcs\client_npcs.xml")
    tree = ET.parse(client_npcs_path)
    cli_by_name = {}
    npc_labels = {}
    for n in tree.getroot().findall(".//npc_client"):
        nid_str = n.findtext("id")
        name = (n.findtext("name") or "").strip()
        desc = (n.findtext("desc") or "").strip()
        if nid_str and name:
            nid = int(nid_str)
            cli_by_name[name.lower()] = nid
            
            resolved_label = str_map.get(desc.lower(), str_map.get(name.lower(), name))
            resolved_label = resolved_label.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("--", "-")
            resolved_label = re.sub(r'<[^>]+>', '', resolved_label).strip()
            if not resolved_label:
                resolved_label = name
            npc_labels[nid] = resolved_label
            
    print(f"      {len(cli_by_name)} NPCs mapeados.")
    return cli_by_name, npc_labels

def load_gather_src(str_map):
    print("[3/6] Carregando gather_src.xml...")
    gather_path = os.path.join(CLIENT_XML_DIR, r"data\Gather\gather_src.xml")
    tree = ET.parse(gather_path)
    gather_by_name = {}
    gather_labels = {}
    for g in tree.getroot().findall(".//gather_src"):
        gid_str = g.findtext("id")
        name = (g.findtext("name") or "").strip()
        desc = (g.findtext("desc") or "").strip()
        if gid_str and name:
            gid = int(gid_str)
            gather_by_name[name.lower()] = gid
            resolved = str_map.get(desc.lower(), str_map.get(name.lower(), name))
            resolved = re.sub(r'<[^>]+>', '', resolved).strip().replace("--", "-")
            gather_labels[gid] = resolved if resolved else name
    print(f"      {len(gather_by_name)} recursos de coleta mapeados.")
    return gather_by_name, gather_labels

def calc_heading(angles_str):
    """
    Fórmula canônica NCSoft / Aion CryEngine:
    num = round(yaw) // 3
    if num < 0: num += 120
    num -= 30
    if num < 0: num += 120
    return num % 120
    """
    if not angles_str:
        return 0
    try:
        parts = angles_str.split(",")
        if len(parts) < 3:
            return 0
        yaw = float(parts[2].strip())
        num = int(round(yaw)) // 3
        if num < 0:
            num += 120
        num -= 30
        if num < 0:
            num += 120
        return int(num % 120)
    except Exception:
        return 0

def format_coord(val):
    return f"{float(val):.4f}".rstrip("0").rstrip(".")

def parse_existing_spawns(xml_path):
    """
    Carrega arquivo de spawn existente e retorna:
      dict: npc_id -> {"respawn_time": int, "custom": bool, "spots": [dict_spot]}
    """
    spawns_data = {}
    if not os.path.isfile(xml_path):
        return spawns_data
    
    try:
        tree = ET.parse(xml_path)
        for sp in tree.getroot().findall(".//spawn"):
            nid_str = sp.get("npc_id")
            if not nid_str:
                continue
            nid = int(nid_str)
            r_time = int(sp.get("respawn_time", "295"))
            custom = sp.get("custom", "false").lower() == "true"
            handler = sp.get("handler")
            difficult_id = sp.get("difficult_id")
            
            spot_list = []
            for s in sp.findall("spot"):
                s_dict = dict(s.attrib)
                spot_list.append(s_dict)
                
            spawns_data[nid] = {
                "respawn_time": r_time,
                "custom": custom,
                "handler": handler,
                "difficult_id": difficult_id,
                "spots": spot_list
            }
    except Exception as e:
        print(f"      [AVISO] Erro lendo {xml_path}: {e}")
    return spawns_data

def spot_distance(s1, s2):
    try:
        x1, y1, z1 = float(s1["x"]), float(s1["y"]), float(s1["z"])
        x2, y2, z2 = float(s2["x"]), float(s2["y"]), float(s2["z"])
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
    except Exception:
        return 999999.0

def process_map_spawns(cfg, cli_by_name, npc_labels, gather_by_name, gather_labels):
    mid = cfg["id"]
    mname = cfg["name"]
    folder = cfg["folder"]
    mission_file = cfg["mission"]
    
    print(f"\n[Processando Mapa] {mname} (ID: {mid}) a partir de {os.path.basename(mission_file)}...")
    
    # 1. Carrega spawns existentes
    target_rel = os.path.join("spawns", folder, f"{mid}_{mname}.xml")
    target_src_path = os.path.join(SRC_STATIC, target_rel)
    existing_spawns = parse_existing_spawns(target_src_path)
    print(f"   Spawns existentes em {target_rel}: {len(existing_spawns)} NPCs, {sum(len(v['spots']) for v in existing_spawns.values())} spots.")
    
    # Dicionário de trabalho para NPCs e Monstros: npc_id -> {"respawn_time": int, "spots": [...]}
    merged_npc_spawns = {}
    for nid, sp_info in existing_spawns.items():
        merged_npc_spawns[nid] = {
            "respawn_time": sp_info.get("respawn_time", 295),
            "custom": sp_info.get("custom", False),
            "handler": sp_info.get("handler"),
            "difficult_id": sp_info.get("difficult_id"),
            "spots": list(sp_info["spots"])
        }

    # Dicionário de trabalho para Coletas (Gather)
    merged_gather_spawns = defaultdict(list)
    
    # 2. Varre o mission_mission0.xml
    mtree = ET.parse(mission_file)
    added_npc_spots = 0
    skipped_existing = 0
    added_gather_spots = 0
    
    for obj in mtree.getroot().findall(".//Object"):
        t = (obj.get("Type") or obj.get("type") or "").upper()
        pos_str = obj.get("Pos") or obj.get("pos") or ""
        if not pos_str:
            continue
        coords = pos_str.split(",")
        if len(coords) < 3:
            continue
        
        try:
            x_f, y_f, z_f = float(coords[0]), float(coords[1]), float(coords[2])
        except Exception:
            continue
            
        x_str = format_coord(x_f)
        y_str = format_coord(y_f)
        z_str = format_coord(z_f)
        h_val = calc_heading(obj.get("Angles") or obj.get("angles"))
        
        # Objeto de Coleta (HSP)
        if t == "HSP":
            npc_attr = (obj.get("npc") or obj.get("Name") or "").strip().lower()
            gid = gather_by_name.get(npc_attr)
            if gid:
                new_spot = {"x": x_str, "y": y_str, "z": z_str, "h": str(h_val)}
                # Evita duplicata
                is_dup = any(spot_distance(new_spot, es) < 0.5 for es in merged_gather_spawns[gid])
                if not is_dup:
                    merged_gather_spawns[gid].append(new_spot)
                    added_gather_spots += 1
            continue

        # Objeto de NPC / Monstro (SP, NPC, MONSTER)
        if t in ["SP", "NPC", "MONSTER"]:
            obj_name = obj.get("Name") or obj.get("name") or ""
            npc_attr = (obj.get("npc") or obj.get("Entity") or obj.get("entity") or "").strip()
            
            candidates = []
            if npc_attr:
                candidates.append(npc_attr)
            if obj_name:
                candidates.append(obj_name)
                c = re.sub(r'^(SP_|SMP_|HSP_)', '', obj_name, flags=re.IGNORECASE)
                candidates.append(c)
                candidates.append(re.sub(r'_\d+$', '', c))
                candidates.append(re.sub(r'\d+$', '', c))
                
            nid = None
            for cand in candidates:
                nid = cli_by_name.get(cand.lower())
                if nid:
                    break
                    
            if not nid:
                continue
                
            new_spot = {"x": x_str, "y": y_str, "z": z_str, "h": str(h_val)}
            
            if nid not in merged_npc_spawns:
                merged_npc_spawns[nid] = {
                    "respawn_time": 295,
                    "spots": []
                }
                
            # Verifica se já existe um spot na mesma posição (< 0.5m)
            is_dup = any(spot_distance(new_spot, es) < 0.5 for es in merged_npc_spawns[nid]["spots"])
            if is_dup:
                skipped_existing += 1
            else:
                merged_npc_spawns[nid]["spots"].append(new_spot)
                added_npc_spots += 1

    total_npc_spots = sum(len(v["spots"]) for v in merged_npc_spawns.values())
    print(f"   NPCs/Monstros: +{added_npc_spots} novos spots adicionados (preservados/ignorados duplicados: {skipped_existing}).")
    print(f"   Total final no mapa {mid}: {len(merged_npc_spawns)} NPCs únicos, {total_npc_spots} spots.")
    
    if cfg["has_gather"]:
        print(f"   Coletas (HSP): {len(merged_gather_spawns)} tipos de recursos, {added_gather_spots} spots.")

    return merged_npc_spawns, merged_gather_spawns

def generate_xml_content(map_id, spawns_dict, labels_dict):
    """
    Gera a string XML válida para o spawn_map.
    """
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<spawns xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../spawns.xsd">',
        f'\t<spawn_map map_id="{map_id}">'
    ]
    
    for nid in sorted(spawns_dict.keys()):
        data = spawns_dict[nid]
        if isinstance(data, list):
            spots = data
            r_time = 295
            custom_attr = ""
            handler_attr = ""
            diff_attr = ""
        else:
            spots = data.get("spots", [])
            r_time = data.get("respawn_time", 295)
            custom_attr = ' custom="true"' if data.get("custom") else ""
            handler_attr = f' handler="{data["handler"]}"' if data.get("handler") else ""
            diff_attr = f' difficult_id="{data["difficult_id"]}"' if data.get("difficult_id") is not None else ""
            
        if not spots:
            continue
            
        label = labels_dict.get(nid, f"ID_{nid}")
        lines.append(f'\t\t<!-- {label} -->')
        lines.append(f'\t\t<spawn npc_id="{nid}" respawn_time="{r_time}"{custom_attr}{handler_attr}{diff_attr}>')
        
        for sp in spots:
            x_val = format_coord(sp["x"])
            y_val = format_coord(sp["y"])
            z_val = format_coord(sp["z"])
            h_val = str(sp.get("h", "0"))
            
            extra = ""
            for k in ["walker_id", "walker_index", "random_walk", "static_id", "fly", "anchor", "state", "ai"]:
                if k in sp and sp[k] not in [None, "", "0"]:
                    extra += f' {k}="{sp[k]}"'
            
            lines.append(f'\t\t\t<spot x="{x_val}" y="{y_val}" z="{z_val}" h="{h_val}"{extra}/>')
            
        lines.append('\t\t</spawn>')
        
    lines.append('\t</spawn_map>')
    lines.append('</spawns>')
    lines.append('')
    return "\r\n".join(lines)

def validate_xsd(xml_content):
    """Valida o conteúdo XML contra spawns.xsd usando lxml."""
    try:
        from lxml import etree
        schema_doc = etree.parse(SPAWNS_XSD)
        schema = etree.XMLSchema(schema_doc)
        doc = etree.fromstring(xml_content.encode("utf-8"))
        schema.assertValid(doc)
        return True, "Válido"
    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="Aplica as modificações no servidor com backup")
    args = parser.parse_args()

    print("=" * 80)
    print("GERADOR DE SPAWNS: TIAMARANTA, TIAMAT DOWN E TEVA")
    print("=" * 80)

    str_map = load_strings()
    cli_by_name, npc_labels = load_client_npcs(str_map)
    gather_by_name, gather_labels = load_gather_src(str_map)

    # Coleta todos os arquivos a serem gerados: (rel_path, content, label)
    generated_files = []

    for cfg in MAP_CONFIGS:
        merged_npc, merged_gather = process_map_spawns(cfg, cli_by_name, npc_labels, gather_by_name, gather_labels)
        
        # 1. Spawns de NPCs e Monstros
        npc_xml_rel = os.path.join("spawns", cfg["folder"], f"{cfg['id']}_{cfg['name']}.xml")
        npc_content = generate_xml_content(cfg["id"], merged_npc, npc_labels)
        generated_files.append((npc_xml_rel, npc_content, f"NPCs {cfg['name']}"))
        
        # 2. Spawns de Coletas (Gather) se aplicável
        if cfg["has_gather"] and merged_gather:
            gather_xml_rel = os.path.join("spawns", "Gather", f"{cfg['id']}_{cfg['name']}.xml")
            gather_content = generate_xml_content(cfg["id"], merged_gather, gather_labels)
            generated_files.append((gather_xml_rel, gather_content, f"Gather {cfg['name']}"))

    # Validação de Schema em todos os arquivos gerados
    print("\n[Validação XSD] Checando schema spawns.xsd em todos os arquivos...")
    all_valid = True
    for rel_path, content, label in generated_files:
        ok, err = validate_xsd(content)
        if ok:
            print(f"   [OK] {rel_path} ({label}): 100% válido contra spawns.xsd")
        else:
            print(f"   [ERRO] {rel_path} ({label}) falhou na validação XSD:\n{err}")
            all_valid = False

    if not all_valid:
        sys.exit("\nInterrompendo: Um ou mais arquivos gerados falharam na validação do esquema!")

    if not args.aplicar:
        print("\nModo DRY-RUN finalizado com sucesso! Para aplicar as alterações, execute:")
        print("  python generate_maps_spawns.py --aplicar")
        return

    # Aplicação das alterações com backup atômico
    print("\n[Aplicação] Gravando arquivos com backup atômico...")
    bm.init_backup_session("generate_maps_spawns")
    
    for rel_path, content, label in generated_files:
        src_full = os.path.join(SRC_STATIC, rel_path)
        prod_full = os.path.join(PROD_STATIC, rel_path)
        
        # Se arquivo já existe, registra backup via backup_manager
        if os.path.isfile(src_full):
            bm.backup_file_before_modification(rel_path)
            
        os.makedirs(os.path.dirname(src_full), exist_ok=True)
        with open(src_full, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   [Gravado Código Fonte] {src_full}")
        
        os.makedirs(os.path.dirname(prod_full), exist_ok=True)
        with open(prod_full, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   [Gravado Produto Final] {prod_full}")

    print("\n" + "=" * 80)
    print("CONCLUÍDO COM SUCESSO! Todos os spawns foram gerados, validados e sincronizados.")
    print("=" * 80)

if __name__ == "__main__":
    main()
