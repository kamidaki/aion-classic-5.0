import os
import sys
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(TOOLS_DIR)))
#!/usr/bin/env python3
"""
Aion Client 4.5 NPC Spawn Generator & Localized Name Resolver
Extracts and consolidates NPC spawns across all maps, resolves real localized NPC names
from Client 4.5 Strings (client_strings_*.xml and client_npcs.xml), and generates
authoritative XML spawn files under data/server/data/spawns/{map_id}.xml.
"""

import os
import sys
import glob
import re
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict

def load_client_strings(strings_dir):
    """
    Loads all localized string mappings from Client 4.5 Strings XMLs (UTF-16 and UTF-8).
    Returns: dict mapping lowercase identifier/id -> localized string body
    """
    str_map = {}
    pattern = re.compile(r'<string>(.*?)</string>', re.DOTALL)
    
    if not os.path.exists(strings_dir):
        print(f"WARN: Strings directory not found at {strings_dir}")
        return str_map

    xml_files = glob.glob(os.path.join(strings_dir, "*.xml"))
    print(f"[*] Loading localized strings from {len(xml_files)} files...")

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

        strings = pattern.findall(content)
        for s in strings:
            sid = re.search(r'<id>(.*?)</id>', s)
            sname = re.search(r'<name>(.*?)</name>', s)
            sbody = re.search(r'<body>(.*?)</body>', s)
            if sname and sbody:
                name_k = sname.group(1).strip().lower()
                body_v = sbody.group(1).strip()
                str_map[name_k] = body_v
            if sid and sbody:
                id_k = sid.group(1).strip()
                body_v = sbody.group(1).strip()
                str_map[id_k] = body_v

    print(f"[*] Loaded {len(str_map)} localized string entries.")
    return str_map

def load_npc_templates(npcs_xml_path, str_map):
    """
    Loads NPC templates from client_npcs.xml and resolves real names for each NPC ID.
    Returns: dict mapping npc_id (int) -> resolved NPC name (str)
    """
    npc_name_map = {}
    if not os.path.exists(npcs_xml_path):
        print(f"WARN: client_npcs.xml not found at {npcs_xml_path}")
        return npc_name_map

    content = None
    for enc in ["utf-8", "utf-16", "latin1"]:
        try:
            with open(npcs_xml_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except Exception:
            continue

    if not content:
        return npc_name_map

    npc_pattern = re.compile(r'<npc_client>(.*?)</npc_client>', re.DOTALL)
    npcs = npc_pattern.findall(content)
    print(f"[*] Loading {len(npcs)} NPC templates from client_npcs.xml...")

    for npc_block in npcs:
        nid = re.search(r'<id>(.*?)</id>', npc_block)
        nname = re.search(r'<name>(.*?)</name>', npc_block)
        ndesc = re.search(r'<desc>(.*?)</desc>', npc_block)

        if not nid:
            continue

        try:
            npc_id = int(nid.group(1).strip())
        except ValueError:
            continue

        name_val = nname.group(1).strip() if nname else ""
        desc_val = ndesc.group(1).strip() if ndesc else ""

        # Resolve name through str_map priority: desc -> name -> id -> raw name
        resolved = str_map.get(desc_val.lower(),
                    str_map.get(name_val.lower(),
                    str_map.get(str(npc_id), name_val)))
        
        # Clean HTML/XML entities if present
        resolved = resolved.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        if not resolved:
            resolved = name_val if name_val else f"NPC_{npc_id}"

        npc_name_map[npc_id] = resolved

    print(f"[*] Resolved {len(npc_name_map)} NPC template names.")
    return npc_name_map

def load_java_spawns(java_spawns_dir):
    """
    Loads all spawn points from Java emulator static_data/spawns.
    Returns: dict mapping map_id (int) -> list of spawn dicts
    """
    map_spawns = defaultdict(list)
    if not os.path.exists(java_spawns_dir):
        print(f"WARN: Java spawns dir not found at {java_spawns_dir}")
        return map_spawns

    for root, dirs, files in os.walk(java_spawns_dir):
        for f in files:
            if f.endswith(".xml") and not f.startswith("spawns"):
                p = os.path.join(root, f)
                try:
                    tree = ET.parse(p)
                    for smap in tree.getroot().findall(".//spawn_map"):
                        mid_str = smap.get("map_id")
                        if not mid_str or not mid_str.isdigit():
                            continue
                        mid = int(mid_str)
                        for sp in smap.findall(".//spawn"):
                            npc_id_str = sp.get("npc_id")
                            if not npc_id_str or not npc_id_str.isdigit():
                                continue
                            npc_id = int(npc_id_str)
                            respawn = int(sp.get("respawn_time", "60"))
                            spots = []
                            for spot in sp.findall(".//spot"):
                                try:
                                    x = float(spot.get("x", "0"))
                                    y = float(spot.get("y", "0"))
                                    z = float(spot.get("z", "0"))
                                    h = int(spot.get("h", "0"))
                                    spots.append({"x": x, "y": y, "z": z, "h": h})
                                except Exception:
                                    continue
                            if spots:
                                map_spawns[mid].append({
                                    "npc_id": npc_id,
                                    "respawn_time": respawn,
                                    "spots": spots
                                })
                except Exception:
                    continue

    return map_spawns

def load_csv_spawns(csv_path):
    """
    Loads spawns from spawns.csv packet capture.
    Returns: dict mapping map_id (int) -> list of spawn dicts
    """
    map_spawns = defaultdict(list)
    if not os.path.exists(csv_path):
        return map_spawns

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f)
        header = next(r, None)
        for row in r:
            if not row or row[0].startswith("#") or not row[0].strip().isdigit():
                continue
            try:
                mid = int(row[0].strip())
                npc_id = int(row[1].strip())
                x = float(row[3].strip())
                y = float(row[4].strip())
                z = float(row[5].strip())
                h = 0
                payload = row[6].strip() if len(row) > 6 else ""
                map_spawns[mid].append({
                    "npc_id": npc_id,
                    "respawn_time": 295,
                    "spots": [{"x": x, "y": y, "z": z, "h": h}],
                    "payload": payload
                })
            except Exception:
                continue

    return map_spawns

def main():
    print("=" * 70)
    print("Aion Client 4.5 NPC Spawn Generation & String Resolution Pipeline")
    print("=" * 70)

    base_dir = PROJECT_ROOT
    strings_dir = os.path.join(base_dir, "Produto Final", "data", "client", "Strings", "strings")
    npcs_xml_path = os.path.join(base_dir, "Produto Final", "data", "client", "data", "npcs", "client_npcs.xml")
    java_spawns_dir = os.path.join(base_dir, "Docs-Refs", "JAVA EMU - 2.8 CLASSIC CHS", "GameServer", "data", "static_data", "spawns")
    csv_spawns_path = os.path.join(base_dir, "Produto Final", "data", "spawns.csv")
    output_spawns_dir = os.path.join(base_dir, "Produto Final", "data", "server", "data", "spawns")

    # 1. Load Strings
    str_map = load_client_strings(strings_dir)

    # 2. Load NPC Templates
    npc_name_map = load_npc_templates(npcs_xml_path, str_map)

    # 3. Load Spawns
    java_spawns = load_java_spawns(java_spawns_dir)
    csv_spawns = load_csv_spawns(csv_spawns_path)

    # Merge spawns per map
    all_maps = set(java_spawns.keys()) | set(csv_spawns.keys())
    print(f"[*] Total unique maps with spawn data: {len(all_maps)}")

    os.makedirs(output_spawns_dir, exist_ok=True)
    total_generated_spawns = 0

    for mid in sorted(all_maps):
        spawns_list = java_spawns.get(mid, [])
        
        # Avoid duplicate spawns from CSV if already present in Java spawns
        existing_coords = set()
        for sp in spawns_list:
            for st in sp["spots"]:
                existing_coords.add((sp["npc_id"], round(st["x"], 1), round(st["y"], 1)))

        csv_list = csv_spawns.get(mid, [])
        added_from_csv = 0
        for csp in csv_list:
            for st in csp["spots"]:
                key = (csp["npc_id"], round(st["x"], 1), round(st["y"], 1))
                if key not in existing_coords:
                    spawns_list.append(csp)
                    existing_coords.add(key)
                    added_from_csv += 1

        if not spawns_list:
            continue

        # Sort spawns by npc_id
        spawns_list.sort(key=lambda s: s["npc_id"])

        out_xml_path = os.path.join(output_spawns_dir, f"{mid}.xml")
        with open(out_xml_path, "w", encoding="utf-8") as out:
            out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            out.write(f'<!--\n  Aion 4.5 Server Spawns for Map ID: {mid}\n  Total Spawns: {len(spawns_list)}\n-->\n')
            out.write('<spawns>\n')
            out.write(f'    <spawn_map map_id="{mid}">\n')

            for sp in spawns_list:
                npc_id = sp["npc_id"]
                npc_name = npc_name_map.get(npc_id, f"NPC_{npc_id}")
                respawn = sp.get("respawn_time", 60)
                payload = sp.get("payload", "")

                out.write(f'        <!-- {npc_name} -->\n')
                payload_attr = f' payload="{payload}"' if payload else ""
                out.write(f'        <spawn npc_id="{npc_id}" respawn_time="{respawn}"{payload_attr}>\n')
                for st in sp["spots"]:
                    x = st["x"]
                    y = st["y"]
                    z = st["z"]
                    h = st.get("h", 0)
                    out.write(f'            <spot x="{x:.2f}" y="{y:.2f}" z="{z:.2f}" h="{h}"/>\n')
                out.write('        </spawn>\n')

            out.write('    </spawn_map>\n')
            out.write('</spawns>\n')

        total_generated_spawns += len(spawns_list)
        print(f"  [OK] Generated {out_xml_path} ({len(spawns_list)} spawns, +{added_from_csv} from packet capture)")

    print("=" * 70)
    print(f"[COMPLETE] Generated {len(all_maps)} map spawn files ({total_generated_spawns} total spawns) in {output_spawns_dir}")
    print("=" * 70)

if __name__ == "__main__":
    main()
