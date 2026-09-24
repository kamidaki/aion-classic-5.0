"""
Parser 5.0 para Receitas de Fabricação (tools/parsersXML/parse_recipes.py)
Analisa e sincroniza todas as receitas de artesanato, culinária, alquimia e ferraria com server/data/recipe/recipe_templates.xml
Vincula nameid ao string ID numérico e name ao texto real de body.
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_recipes():
    print("=== [9/17] Processando Receitas de Crafting 5.0 (recipe/recipe_templates.xml) ===")
    
    print("  -> Carregando items/client_combine_recipe.xml oficial 5.0...")
    c_recipes_root = common_bxml.read_client_xml("items/client_combine_recipe.xml")
    
    tree, r_root = common_bxml.read_server_xml("recipe/recipe_templates.xml")
    r_orig = len(r_root)
    existing = {r.get("id"): r for r in r_root.findall("recipe_template")}
    
    skill_map = {
        "cooking": "40001",
        "weaponsmithing": "40002",
        "armorsmithing": "40003",
        "tailoring": "40004",
        "alchemy": "40007",
        "handicrafting": "40008",
        "convert": "40009",
        "magical_crafting": "40010"
    }
    
    added = 0
    updated = 0
    for c_r in c_recipes_root:
        r_id = c_r.findtext("id")
        if not r_id:
            continue
            
        code_name = c_r.findtext("name", "")
        desc_str = c_r.findtext("desc", "")
        name_id = common_bxml.resolve_name_id(desc_str, 0)
        real_name = common_bxml.resolve_body(desc_str, code_name)
        cskill = c_r.findtext("combineskill", "convert").lower()
        skill_id = skill_map.get(cskill, "40009")
        q_race = c_r.findtext("qualification_race", "pc_all").lower()
        race = "ELYOS" if "light" in q_race else ("ASMODIANS" if "dark" in q_race else "PC_ALL")
        skillpoint = c_r.findtext("required_skillpoint", "1")
        autolearn = c_r.findtext("auto_learn", "0")
        product = c_r.findtext("product", "0")
        product_qty = c_r.findtext("product_quantity", "1")

        if r_id in existing:
            elem = existing[r_id]
            elem.set("name", real_name)
            elem.set("nameid", name_id)
            updated += 1
        else:
            elem = ET.SubElement(r_root, "recipe_template")
            elem.set("id", r_id)
            elem.set("name", real_name)
            elem.set("nameid", name_id)
            elem.set("skillid", skill_id)
            elem.set("race", race)
            elem.set("skillpoint", skillpoint)
            if autolearn == "1":
                elem.set("autolearn", "1")
            elem.set("productid", product if product.isdigit() else "152000401")
            elem.set("quantity", product_qty)
            added += 1

    common_bxml.write_server_xml("recipe/recipe_templates.xml", r_root)
    common_bxml.log_step("Receitas (recipe_templates)", r_orig, added, updated, len(r_root))


if __name__ == "__main__":
    parse_recipes()
