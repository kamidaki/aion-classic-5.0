"""
Parser 5.0 para Missões e Scripts de Quests (tools/parsersXML/parse_quests.py)
Analisa e sincroniza todas as missões do cliente 5.0 com server/data/quest_data/ e quest_script_data/
Vincula nameId ao string ID numérico e name ao texto real de body.
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_quests():
    print("=== [4/17] Processando Missões 5.0 (quest_data/ & quest_script_data/) ===")
    
    # 1. Carrega Quest/quest.xml
    print("  -> Carregando Quest/quest.xml oficial 5.0...")
    client_quests_root = common_bxml.read_client_xml("Quest/quest.xml")
    
    # 2. Carrega XML do servidor
    tree, server_root = common_bxml.read_server_xml("quest_data/quest_data.xml")
    orig_count = len(server_root)
    
    server_quests = {}
    for q in server_root.findall("quest"):
        q_id = q.get("id")
        if q_id:
            server_quests[q_id] = q
            
    added_count = 0
    updated_count = 0
    
    for c_q in client_quests_root:
        quest_id = c_q.findtext("id")
        if not quest_id:
            continue
            
        code_name = c_q.findtext("name", "")
        desc_str = c_q.findtext("desc", "0")
        name_id = common_bxml.resolve_name_id(desc_str, int(quest_id) if quest_id.isdigit() else 0)
        real_name = common_bxml.resolve_body(desc_str, code_name)
        min_lvl = c_q.findtext("minlevel_permitted", "1")
        max_lvl = c_q.findtext("maxlevel_permitted", "85")
        repeat_count = c_q.findtext("max_repeat_count", "1")
        f_mission = c_q.findtext("f_mission", "0")
        category = "MISSION" if f_mission == "1" else c_q.findtext("category1", "QUEST").upper()
        
        name_low = code_name.lower()
        race = "ELYOS" if ("elyos" in name_low or "light" in name_low) else ("ASMODIANS" if ("asmo" in name_low or "dark" in name_low) else "PC_ALL")
        
        if quest_id in server_quests:
            elem = server_quests[quest_id]
            elem.set("name", real_name)
            elem.set("nameId", name_id)
            elem.set("minlevel_permitted", min_lvl)
            elem.set("maxlevel_permitted", max_lvl)
            elem.set("max_repeat_count", repeat_count)
            elem.set("category", category)
            updated_count += 1
        else:
            elem = ET.SubElement(server_root, "quest")
            elem.set("id", quest_id)
            elem.set("name", real_name)
            elem.set("nameId", name_id)
            elem.set("minlevel_permitted", min_lvl)
            elem.set("maxlevel_permitted", max_lvl)
            elem.set("max_repeat_count", repeat_count)
            elem.set("race_permitted", race)
            elem.set("cannot_share", "false")
            elem.set("cannot_giveup", "false")
            elem.set("category", category)
            added_count += 1

    final_count = len(server_root)
    print(f"  -> Gravando {final_count} missões em quest_data/quest_data.xml...")
    common_bxml.write_server_xml("quest_data/quest_data.xml", server_root)
    common_bxml.log_step("Missões (quest_data)", orig_count, added_count, updated_count, final_count)


if __name__ == "__main__":
    parse_quests()
