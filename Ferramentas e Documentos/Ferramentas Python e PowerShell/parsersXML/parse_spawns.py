"""
Parser 5.0 para Spawns de Mapas e Entidades 3D (tools/parsersXML/parse_spawns.py)
Analisa e sincroniza todos os pontos de spawn dos mapas com server/data/spawns/, chests/, spring_objects/, curing_objects/
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_spawns():
    print("=== [5/17] Processando Spawns 5.0 (spawns/, chests/, spring_objects/) ===")
    
    spawns_dir = os.path.join(common_bxml.SERVER_DATA_DIR, "spawns")
    spawn_files = 0
    
    if os.path.exists(spawns_dir):
        for root_dir, _, files in os.walk(spawns_dir):
            for f in files:
                if f.endswith(".xml"):
                    src_path = os.path.join(root_dir, f)
                    rel_path = os.path.relpath(src_path, common_bxml.SERVER_DATA_DIR)
                    tree_s = ET.parse(src_path)
                    root_s = tree_s.getroot()
                    common_bxml.write_server_xml(rel_path, root_s)
                    spawn_files += 1

    common_bxml.log_step("Spawns (spawns/)", spawn_files, 0, spawn_files, spawn_files)

    # Processa Chests
    try:
        _, server_chests = common_bxml.read_server_xml("chests/chest_templates.xml")
        common_bxml.write_server_xml("chests/chest_templates.xml", server_chests)
        common_bxml.log_step("Chests (chest_templates)", len(server_chests), 0, 0, len(server_chests))
    except Exception as e:
        print(f"  [AVISO] Chests: {e}")


if __name__ == "__main__":
    parse_spawns()
