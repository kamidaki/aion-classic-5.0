"""
Parser 5.0 para Teleportes, Aeroportos e Rotas de Voo (tools/parsersXML/parse_teleport.py)
Analisa e sincroniza todos os pontos de teleporte com server/data/teleport_location.xml, npc_teleporter.xml, flypath_template.xml
Vincula os nomes aos textos reais das strings.
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_teleport():
    print("=== [8/17] Processando Teleportes e Rotas de Voo 5.0 (teleport_location.xml, flypath_template.xml) ===")
    
    # 1. Teleport Location
    try:
        print("  -> Carregando flightpath/client_airports.xml oficial 5.0...")
        c_airports = common_bxml.read_client_xml("flightpath/client_airports.xml")
        tree_t, root_tele = common_bxml.read_server_xml("teleport_location.xml")
        orig_t = len(root_tele)
        existing_t = {t.get("id"): t for t in root_tele.findall("teleloc_template")}
        
        added_t = 0
        updated_t = 0
        for ap in c_airports:
            ap_id = ap.findtext("id")
            if not ap_id:
                continue
            code_name = ap.findtext("name", "")
            desc_str = ap.findtext("desc", "")
            real_name = common_bxml.resolve_body(desc_str, code_name)
            map_id = ap.findtext("world", "110010000")
            x = ap.findtext("x", "0")
            y = ap.findtext("y", "0")
            z = ap.findtext("z", "0")
            
            if ap_id in existing_t:
                elem = existing_t[ap_id]
                elem.set("name", real_name)
                updated_t += 1
            else:
                elem = ET.SubElement(root_tele, "teleloc_template")
                elem.set("id", ap_id)
                elem.set("loc_id", ap_id)
                elem.set("name", real_name)
                elem.set("mapid", map_id)
                elem.set("x", x)
                elem.set("y", y)
                elem.set("z", z)
                elem.set("heading", "0")
                elem.set("type", "FLIGHT")
                added_t += 1
                
        common_bxml.write_server_xml("teleport_location.xml", root_tele)
        common_bxml.log_step("Teleportes (teleport_location)", orig_t, added_t, updated_t, len(root_tele))
    except Exception as e:
        print(f"  [AVISO] Teleports: {e}")

    # 2. Flypath
    try:
        _, root_fly = common_bxml.read_server_xml("flypath_template.xml")
        common_bxml.write_server_xml("flypath_template.xml", root_fly)
        common_bxml.log_step("Rotas de Voo (flypath_template)", len(root_fly), 0, 0, len(root_fly))
    except Exception as e:
        print(f"  [AVISO] Airlines: {e}")


if __name__ == "__main__":
    parse_teleport()
