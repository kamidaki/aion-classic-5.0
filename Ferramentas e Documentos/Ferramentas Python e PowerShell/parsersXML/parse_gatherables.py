"""
Parser 5.0 para Fontes de Coleta (tools/parsersXML/parse_gatherables.py)
Analisa e sincroniza todas as fontes de coleta com server/data/gatherables/gatherable_templates.xml
Vincula nameId ao string ID numérico e name ao texto real de body.
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_gatherables():
    print("=== [11/17] Processando Fontes de Coleta 5.0 (gatherables/gatherable_templates.xml) ===")
    
    print("  -> Carregando Gather/gather_src.xml oficial 5.0...")
    c_gather_root = common_bxml.read_client_xml("Gather/gather_src.xml")
    
    tree, s_gather_root = common_bxml.read_server_xml("gatherables/gatherable_templates.xml")
    orig_count = len(s_gather_root)
    
    s_gathers = {}
    for g in s_gather_root.findall("gatherable_template"):
        g_id = g.get("id")
        if g_id:
            s_gathers[g_id] = g
            
    added_count = 0
    updated_count = 0
    
    # Carrega mapa de itens para resolver materiais textuais do cliente para item_id numérico
    print("  -> Indexando itens para resolução de materiais de coleta...")
    _, s_items_root = common_bxml.read_server_xml("items/item_templates.xml")
    item_lookup = {}
    for it in s_items_root.findall("item_template"):
        it_id = it.get("id")
        it_name = it.get("name")
        it_cname = it.get("cName")
        if it_name:
            item_lookup[it_name.lower()] = it_id
        if it_cname:
            item_lookup[it_cname.lower()] = it_id

    for c_g in c_gather_root:
        g_id = c_g.findtext("id")
        if not g_id:
            continue
            
        code_name = c_g.findtext("name", "")
        desc_str = c_g.findtext("desc", "0")
        name_id = common_bxml.resolve_name_id(desc_str, 0)
        real_name = common_bxml.resolve_body(desc_str, code_name)
        source_type = c_g.findtext("source_type", "VEGETABLE").upper()
        skill_level = c_g.findtext("skill_level", "1")
        harvest_skill_raw = (c_g.findtext("harvestskill") or "").strip().lower()
        if harvest_skill_raw.isdigit():
            harvest_skill = harvest_skill_raw
        elif harvest_skill_raw == "gathering_a":
            harvest_skill = "30001"
        elif harvest_skill_raw in ["aerial_gathering", "extract_aether", "aether"]:
            harvest_skill = "30003"
        else:
            harvest_skill = "30002" # Essencetapping (gathering_b, gathering, etc.)
        harvest_count = c_g.findtext("harvest_count", "3")
        
        if g_id in s_gathers:
            elem = s_gathers[g_id]
            elem.set("name", real_name)
            elem.set("nameId", name_id)
            elem.set("sourceType", source_type)
            elem.set("skillLevel", skill_level)
            elem.set("harvestSkill", harvest_skill)
            elem.set("harvestCount", harvest_count)
            # Corrige materiais existentes se tiverem IDs textuais
            for mat_elem in elem.findall(".//material"):
                cur_iid = mat_elem.get("itemid", "")
                if cur_iid and not cur_iid.isdigit():
                    res = item_lookup.get(cur_iid.lower())
                    if res:
                        mat_elem.set("itemid", res)
            updated_count += 1
        else:
            elem = ET.SubElement(s_gather_root, "gatherable_template")
            elem.set("id", g_id)
            elem.set("name", real_name)
            elem.set("nameId", name_id)
            elem.set("sourceType", source_type)
            elem.set("harvestCount", harvest_count)
            elem.set("skillLevel", skill_level)
            elem.set("harvestSkill", harvest_skill)
            elem.set("successAdj", "100")
            elem.set("failureAdj", "100")
            elem.set("aerialAdj", "100")
            
            materials = ET.SubElement(elem, "materials")
            for i in range(1, 5):
                mat_id = c_g.findtext(f"material{i}")
                rate = c_g.findtext(f"normal_rate{i}", "100")
                if mat_id and mat_id != "0":
                    res_id = mat_id if mat_id.isdigit() else item_lookup.get(mat_id.lower(), mat_id)
                    mat_elem = ET.SubElement(materials, "material")
                    mat_elem.set("itemid", res_id)
                    mat_elem.set("name", f"mat_{res_id}")
                    mat_elem.set("rate", rate)
                    
            added_count += 1

    final_count = len(s_gather_root)
    print(f"  -> Gravando {final_count} fontes de coleta em gatherables/gatherable_templates.xml...")
    common_bxml.write_server_xml("gatherables/gatherable_templates.xml", s_gather_root)
    common_bxml.log_step("Coleta (gatherable_templates)", orig_count, added_count, updated_count, final_count)


if __name__ == "__main__":
    parse_gatherables()
