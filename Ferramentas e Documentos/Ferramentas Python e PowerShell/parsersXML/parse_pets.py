"""
Parser 5.0 para Pets e Mascotes (tools/parsersXML/parse_pets.py)
Analisa e sincroniza todos os pets com server/data/pets/
Vincula nameid ao string ID numérico e name ao texto real de body.
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_pets():
    print("=== [12/17] Processando Pets e Mascotes 5.0 (pets/pets.xml) ===")
    
    print("  -> Carregando func_pet/toypets.xml oficial 5.0...")
    c_pets_root = common_bxml.read_client_xml("func_pet/toypets.xml")
    
    tree, s_pets_root = common_bxml.read_server_xml("pets/pets.xml")
    orig_count = len(s_pets_root)
    existing_p = {p.get("id"): p for p in s_pets_root.findall("pet")}
    
    added_count = 0
    updated_count = 0
    
    for c_p in c_pets_root:
        pet_id = c_p.findtext("id")
        if not pet_id:
            continue
            
        code_name = c_p.findtext("name", "")
        desc_str = c_p.findtext("desc", "0")
        name_id = common_bxml.resolve_name_id(desc_str, 0)
        real_name = common_bxml.resolve_body(desc_str, code_name)
        cond_reward = c_p.findtext("pet_condition_reward", "0")
        
        if pet_id in existing_p:
            elem = existing_p[pet_id]
            elem.set("name", real_name)
            elem.set("nameid", name_id)
            if cond_reward and cond_reward != "0":
                elem.set("condition_reward", cond_reward)
            updated_count += 1
        else:
            elem = ET.SubElement(s_pets_root, "pet")
            elem.set("id", pet_id)
            elem.set("name", real_name)
            elem.set("nameid", name_id)
            if cond_reward and cond_reward != "0":
                elem.set("condition_reward", cond_reward)
            added_count += 1

    common_bxml.write_server_xml("pets/pets.xml", s_pets_root)
    common_bxml.log_step("Pets (pets.xml)", orig_count, added_count, updated_count, len(s_pets_root))


if __name__ == "__main__":
    parse_pets()
