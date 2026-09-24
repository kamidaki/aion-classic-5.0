"""
Parser 5.0 para Zonas e Mapas de Mundo (tools/parsersXML/parse_zones.py)
Analisa e sincroniza todos os mapas e zonas com server/data/world_maps.xml e server/data/zones/
Vincula os nomes aos textos reais das strings.
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_zones():
    print("=== [6/17] Processando Zonas e Mapas 5.0 (world_maps.xml & zones/) ===")
    
    # 1. Atualiza world_maps.xml
    print("  -> Carregando world/zonemap.xml oficial 5.0...")
    c_zonemap = common_bxml.read_client_xml("world/zonemap.xml")
    
    tree_m, root_maps = common_bxml.read_server_xml("world_maps.xml")
    orig_maps = len(root_maps)
    existing_maps = {m.get("id"): m for m in root_maps.findall("map")}
    
    added_m = 0
    updated_m = 0
    for c_zm in c_zonemap:
        m_id = c_zm.findtext("id")
        if not m_id:
            continue
            
        code_name = c_zm.findtext("name", "")
        desc_str = c_zm.findtext("desc", "")
        real_name = common_bxml.resolve_body(desc_str, code_name)
        world_width = c_zm.findtext("world_width", "3072")
        map_cat = c_zm.findtext("map_category", "ELYSEA").upper()

        world_type = "NONE"
        if "ELY" in map_cat or "SANCTUM" in code_name.upper():
            world_type = "ELYSEA"
        elif "ASMO" in map_cat or "PANDAE" in code_name.upper():
            world_type = "ASMODAE"
        elif "ABYSS" in map_cat:
            world_type = "ABYSS"
        else:
            world_type = "BALAUREA"

        if m_id in existing_maps:
            elem = existing_maps[m_id]
            elem.set("name", real_name)
            elem.set("world_size", world_width)
            updated_m += 1
        else:
            elem = ET.SubElement(root_maps, "map")
            elem.set("id", m_id)
            elem.set("name", real_name)
            elem.set("death_level", "0")
            elem.set("water_level", "16")
            elem.set("world_type", world_type)
            elem.set("world_size", world_width)
            elem.set("flags", "RECALL GLIDE PVP DUEL_SAME_RACE")
            added_m += 1

    common_bxml.write_server_xml("world_maps.xml", root_maps)
    common_bxml.log_step("Mapas de Mundo (world_maps)", orig_maps, added_m, updated_m, len(root_maps))

    # 2. Sincroniza zonas existentes
    zones_dir = os.path.join(common_bxml.SERVER_DATA_DIR, "zones")
    zone_count = 0
    if os.path.exists(zones_dir):
        for f in os.listdir(zones_dir):
            if f.endswith(".xml"):
                p = os.path.join(zones_dir, f)
                tree_z = ET.parse(p)
                root_z = tree_z.getroot()
                for zone in root_z.findall("zone"):
                    z_name = zone.get("name", "")
                    z_desc = zone.get("desc", "")
                    real_name = common_bxml.resolve_body(z_desc, common_bxml.resolve_body(z_name, z_name))
                    if real_name:
                        zone.set("name", real_name)
                common_bxml.write_server_xml(os.path.join("zones", f), root_z)
                zone_count += len(root_z)
        common_bxml.log_step("Zonas (zones/)", zone_count, 0, zone_count, zone_count)


if __name__ == "__main__":
    parse_zones()
