"""
Parser 5.0 para Skills e Árvores de Habilidade (tools/parsersXML/parse_skills.py)
Analisa e sincroniza todas as skills do cliente 5.0 com server/data/skills/ e skill_tree/
Vincula nameId ao string ID numérico e name ao texto real de body.
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_skills():
    print("=== [3/17] Processando Skills 5.0 (skills/ & skill_tree/) ===")
    
    # 1. Carrega client_skills.xml
    print("  -> Carregando client_skills.xml oficial 5.0...")
    client_skills_root = common_bxml.read_client_xml("skills/client_skills.xml")
    
    # 2. Carrega XML do servidor
    server_path = "skills/template/skill_templates.xml"
    if not os.path.exists(os.path.join(common_bxml.SERVER_DATA_DIR, server_path)):
        server_path = "skills/skill_templates.xml"
        
    tree, server_root = common_bxml.read_server_xml(server_path)
    orig_count = len(server_root)
    
    server_skills = {}
    for sk in server_root.findall("skill_template"):
        s_id = sk.get("skill_id")
        if s_id:
            server_skills[s_id] = sk
            
    added_count = 0
    updated_count = 0
    
    for c_sk in client_skills_root:
        skill_id = c_sk.findtext("id")
        if not skill_id:
            continue
            
        code_name = c_sk.findtext("name", "")
        desc_str = c_sk.findtext("desc", "0")
        name_id = common_bxml.resolve_name_id(desc_str, int(skill_id) if skill_id.isdigit() else 0)
        real_name = common_bxml.resolve_body(desc_str, code_name)
        lvl = c_sk.findtext("level", "1")
        skilltype = c_sk.findtext("skilltype", "PHYSICAL").upper()
        activation = c_sk.findtext("activation", "ACTIVE").upper()
        cooldown = c_sk.findtext("cooldown", "0")
        duration = c_sk.findtext("duration", "0")
        
        if skill_id in server_skills:
            elem = server_skills[skill_id]
            elem.set("name", real_name)
            elem.set("nameId", name_id)
            elem.set("lvl", lvl)
            elem.set("skilltype", skilltype)
            elem.set("activation", activation)
            elem.set("cooldown", cooldown)
            elem.set("duration", duration)
            updated_count += 1
        else:
            elem = ET.SubElement(server_root, "skill_template")
            elem.set("skill_id", skill_id)
            elem.set("name", real_name)
            elem.set("nameId", name_id)
            elem.set("delayId", skill_id)
            elem.set("stack", code_name.upper())
            elem.set("lvl", lvl)
            elem.set("skilltype", skilltype)
            elem.set("skillsubtype", "NONE")
            elem.set("tslot", "NOSHOW")
            elem.set("activation", activation)
            elem.set("cooldown", cooldown)
            elem.set("duration", duration)
            
            prop = ET.SubElement(elem, "properties")
            prop.set("first_target", "TARGET")
            
            added_count += 1

    final_count = len(server_root)
    print(f"  -> Gravando {final_count} skills em {server_path}...")
    common_bxml.write_server_xml(server_path, server_root)
    common_bxml.log_step("Skills (skill_templates)", orig_count, added_count, updated_count, final_count)

    # 3. Processa Árvores de Habilidade (Skill Tree)
    try:
        _, server_tree = common_bxml.read_server_xml("skill_tree/skill_tree.xml")
        t_orig = len(server_tree)
        common_bxml.log_step("Skill Tree", t_orig, 0, 0, t_orig)
    except Exception as e:
        print(f"  [AVISO] Skill Tree: {e}")


if __name__ == "__main__":
    parse_skills()
