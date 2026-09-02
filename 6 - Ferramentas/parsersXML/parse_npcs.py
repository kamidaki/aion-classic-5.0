"""
Parser 5.0 para NPCs e Entidades (tools/parsersXML/parse_npcs.py)
Analisa e sincroniza todos os NPCs do cliente 5.0 com server/data/npcs/
Vincula name_id/title_id às strings do cliente, name ao texto real de body,
e inclui bound_radius, talk_info, equipment e stats de combate.
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_npcs():
    print("=== [2/17] Processando NPCs e Entidades 5.0 (npcs/ & npc_factions/) ===")
    
    print("  -> Carregando client_npcs.xml oficial 5.0...")
    client_npcs_root = common_bxml.read_client_xml("npcs/client_npcs.xml")
    
    server_path = "npcs/npc_templates.xml"
    if not os.path.exists(os.path.join(common_bxml.SERVER_DATA_DIR, server_path)):
        server_path = "npcs/npcs.xml"
        
    orig_root = ET.Element("npc_templates", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "npcs.xsd"
    })
    
    n_count = 0
    for c_npc in client_npcs_root:
        npc_id = c_npc.findtext("id")
        if not npc_id:
            continue
            
        code_name = c_npc.findtext("name", "")
        desc_str = c_npc.findtext("desc", "")
        name_id = common_bxml.resolve_name_id(desc_str, 0)
        real_name = common_bxml.resolve_body(desc_str, code_name)
        
        title_str = c_npc.findtext("npc_title", "")
        title_id = common_bxml.resolve_name_id(title_str, 0) if title_str else "0"
        
        level = c_npc.findtext("level", "1")
        npc_type = c_npc.findtext("npc_type", "MONSTER").upper()
        rank = c_npc.findtext("rank", "NORMAL").upper()
        rating = c_npc.findtext("rating", "NORMAL").upper()
        tribe = c_npc.findtext("tribe", "GENERAL").upper()
        ai = c_npc.findtext("ai_name", "aggressive")
        if not ai or ai == "none":
            ai = "aggressive"
        sensory_range = c_npc.findtext("sensory_range", "15")
        height = c_npc.findtext("height", "1.5")
        ammo_speed = c_npc.findtext("ammo_speed")
        hpgauge_level = c_npc.findtext("hpgauge_level")
        attack_delay = c_npc.findtext("attack_delay")
        attack_range = c_npc.findtext("attack_range")
        attack_rate = c_npc.findtext("attack_rate")
        float_corpse = c_npc.findtext("float_corpse")
        save_trade_count = c_npc.findtext("save_trade_count")

        elem = ET.SubElement(orig_root, "npc_template")
        elem.set("npc_id", npc_id)
        elem.set("level", level)
        elem.set("name_id", name_id)
        if title_id and title_id != "0":
            elem.set("title_id", title_id)
        elem.set("name", real_name)
        elem.set("height", height)
        elem.set("npc_type", npc_type)
        elem.set("rank", rank)
        elem.set("rating", rating)
        elem.set("tribe", tribe)
        elem.set("ai", ai)
        elem.set("sensory_range", sensory_range)
        if ammo_speed:
            elem.set("ammo_speed", ammo_speed)
        if hpgauge_level:
            elem.set("hpgauge_level", hpgauge_level)
        if attack_delay:
            elem.set("attack_delay", attack_delay)
        if attack_range:
            elem.set("attack_range", attack_range)
        if attack_rate:
            elem.set("attack_rate", attack_rate)
        if float_corpse and float_corpse != "0":
            elem.set("floatcorpse", "true")
        if save_trade_count and save_trade_count != "0":
            elem.set("savetradecount", "true")

        # 1. Stats
        stats = ET.SubElement(elem, "stats")
        stats.set("max_hp", c_npc.findtext("hp", "1000"))
        stats.set("max_mp", c_npc.findtext("mp", "1000"))
        stats.set("pdef", c_npc.findtext("pdef", "100"))
        stats.set("mdef", c_npc.findtext("mdef", "100"))
        stats.set("run_speed", c_npc.findtext("run_speed", "6.0"))

        # 2. Equipment
        ve = c_npc.find("visible_equipments")
        if ve is not None and len(ve) > 0:
            equip_elem = ET.SubElement(elem, "equipment")
            for sub in ve:
                eq_name = sub.text.strip().lower() if sub.text else ""
                eq_id = common_bxml.get_item_id_by_name(eq_name)
                if eq_id:
                    it_elem = ET.SubElement(equip_elem, "item")
                    it_elem.text = eq_id

        # 3. Bound Radius
        br = c_npc.find("bound_radius")
        if br is not None and len(br) > 0:
            br_front = br.findtext("front", "1.0")
            br_side = br.findtext("side", "1.0")
            br_upper = br.findtext("upper", "2.0")
            br_elem = ET.SubElement(elem, "bound_radius")
            br_elem.set("front", br_front)
            br_elem.set("side", br_side)
            br_elem.set("upper", br_upper)

        # 4. Talk Info
        talk_dist = c_npc.findtext("talking_distance")
        talk_delay = c_npc.findtext("talk_delay_time")
        if talk_dist or talk_delay:
            talk_elem = ET.SubElement(elem, "talk_info")
            if talk_dist:
                talk_elem.set("distance", talk_dist)
            if talk_delay:
                talk_elem.set("delay", talk_delay)
            talk_elem.set("is_dialog", "true")

        n_count += 1

    print(f"  -> Gravando {n_count} NPCs em {server_path}...")
    common_bxml.write_server_xml(server_path, orig_root)
    common_bxml.log_step("NPCs (npc_templates)", 0, n_count, 0, n_count)

    # Facções
    try:
        c_factions = common_bxml.read_client_xml("faction/NpcFactions.xml")
        base_fac = "npc_factions/npc_factions.xml"
        _, root_fac = common_bxml.read_server_xml(base_fac)
        existing_f = {el.get("id") for el in root_fac.findall("npc_faction")}
        f_added = 0
        for fac in c_factions:
            f_id = fac.findtext("id")
            if f_id and f_id not in existing_f:
                elem = ET.SubElement(root_fac, "npc_faction")
                elem.set("id", f_id)
                c_name = fac.findtext("name", "")
                d_str = fac.findtext("desc", "")
                elem.set("name", common_bxml.resolve_body(d_str, c_name))
                elem.set("category", fac.findtext("category", "GENERAL"))
                f_added += 1
        common_bxml.write_server_xml(base_fac, root_fac)
        common_bxml.log_step("NPC Factions", len(existing_f), f_added, 0, len(root_fac))
    except Exception as e:
        print(f"  [AVISO] Factions: {e}")


if __name__ == "__main__":
    parse_npcs()
