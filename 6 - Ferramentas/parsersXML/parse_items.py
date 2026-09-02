import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PARSERS_DIR))
"""
Parser 5.0 para Itens (tools/parsersXML/parse_items.py)
Analisa e sincroniza todos os itens do cliente 5.0 com server/data/items/ e cosmetic_items/
Vincula desc a string IDs numéricos e name a textos reais de body.
Extrai equipment_slots oficial e mapeia slot bitmask e equipment_type.
Garante weapon_stats em 100% das armas alinhados com o cliente 5.0 e fallbacks tabelados.
"""

import os
import sys
import shutil
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml

SLOT_MAP = {
    'main': 1,                              # MAIN_HAND (1)
    'sub': 2,                               # SUB_HAND (2)
    'main_or_sub': 3,                       # MAIN_OR_SUB (1 | 2)
    'head': 4,                              # HELMET (4)
    'torso': 8,                             # TORSO (8)
    'glove': 16,                            # GLOVES (16)
    'foot': 32,                             # BOOTS (32)
    'right_or_left_ear': 192,               # EARRING_RIGHT_OR_LEFT (64 | 128)
    'right_or_left_finger': 768,            # RING_RIGHT_OR_LEFT (256 | 512)
    'neck': 1024,                           # NECKLACE (1024)
    'shoulder': 2048,                       # SHOULDER (2048)
    'leg': 4096,                            # PANTS (4096)
    'right_or_left_battery': 24576,         # SHARD_RIGHT_OR_LEFT (8192 | 16384)
    'wing': 32768,                          # WINGS (32768)
    'waist': 65536,                         # WAIST (65536)
    'torso glove foot shoulder leg': 6200,  # Full body suit (8|16|32|2048|4096)
}

ACCESSORY_SLOT_CATEGORIES = {
    'neck': ('NECKLACE', 'ARMOR'),
    'waist': ('BELT', 'ARMOR'),
    'right_or_left_ear': ('EARRINGS', 'ARMOR'),
    'right_or_left_finger': ('RINGS', 'ARMOR'),
    'wing': ('WINGS', 'ARMOR'),
    'head': ('HELMET', 'ARMOR'),
    'right_or_left_battery': ('SHARD', 'ARMOR'),
}

DEFAULT_WEAPON_STATS = {
    '1H_DAGGER': {'min_damage': 129, 'max_damage': 143, 'attack_speed': 1200, 'physical_critical': 100, 'physical_accuracy': 751, 'parry': 772, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 1500, 'hit_count': 1, 'reduce_max': 0},
    'DAGGER_1H': {'min_damage': 129, 'max_damage': 143, 'attack_speed': 1200, 'physical_critical': 100, 'physical_accuracy': 751, 'parry': 772, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 1500, 'hit_count': 1, 'reduce_max': 0},
    '1H_SWORD': {'min_damage': 142, 'max_damage': 174, 'attack_speed': 1400, 'physical_critical': 50, 'physical_accuracy': 751, 'parry': 812, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 1500, 'hit_count': 2, 'reduce_max': 0},
    'SWORD_1H': {'min_damage': 142, 'max_damage': 174, 'attack_speed': 1400, 'physical_critical': 50, 'physical_accuracy': 751, 'parry': 812, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 1500, 'hit_count': 2, 'reduce_max': 0},
    '1H_MACE': {'min_damage': 136, 'max_damage': 204, 'attack_speed': 1500, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 812, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 1500, 'hit_count': 1, 'reduce_max': 0},
    'MACE_1H': {'min_damage': 136, 'max_damage': 204, 'attack_speed': 1500, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 812, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 1500, 'hit_count': 1, 'reduce_max': 0},
    '1H_GUN': {'min_damage': 142, 'max_damage': 174, 'attack_speed': 1100, 'physical_critical': 50, 'physical_accuracy': 751, 'parry': 0, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 20000, 'hit_count': 1, 'reduce_max': 0},
    'GUN_1H': {'min_damage': 142, 'max_damage': 174, 'attack_speed': 1100, 'physical_critical': 50, 'physical_accuracy': 751, 'parry': 0, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 20000, 'hit_count': 1, 'reduce_max': 0},
    '1H_GAUNTLET': {'min_damage': 123, 'max_damage': 137, 'attack_speed': 1100, 'physical_critical': 110, 'physical_accuracy': 741, 'parry': 912, 'magical_accuracy': 180, 'boost_magical_skill': 0, 'attack_range': 1500, 'hit_count': 1, 'reduce_max': 0},
    '2H_SWORD': {'min_damage': 203, 'max_damage': 377, 'attack_speed': 2400, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 852, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 2000, 'hit_count': 3, 'reduce_max': 0},
    'SWORD_2H': {'min_damage': 203, 'max_damage': 377, 'attack_speed': 2400, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 852, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 2000, 'hit_count': 3, 'reduce_max': 0},
    '2H_POLEARM': {'min_damage': 221, 'max_damage': 413, 'attack_speed': 2800, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 852, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 2500, 'hit_count': 4, 'reduce_max': 0},
    'POLEARM_2H': {'min_damage': 221, 'max_damage': 413, 'attack_speed': 2800, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 852, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 2500, 'hit_count': 4, 'reduce_max': 0},
    '2H_STAFF': {'min_damage': 187, 'max_damage': 281, 'attack_speed': 2000, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 852, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 2000, 'hit_count': 3, 'reduce_max': 0},
    'STAFF_2H': {'min_damage': 187, 'max_damage': 281, 'attack_speed': 2000, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 852, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 2000, 'hit_count': 3, 'reduce_max': 0},
    'BOW': {'min_damage': 208, 'max_damage': 282, 'attack_speed': 2400, 'physical_critical': 50, 'physical_accuracy': 751, 'parry': 0, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 25000, 'hit_count': 1, 'reduce_max': 0},
    '2H_BOOK': {'min_damage': 192, 'max_damage': 235, 'attack_speed': 2200, 'physical_critical': 0, 'physical_accuracy': 0, 'parry': 0, 'magical_accuracy': 320, 'boost_magical_skill': 720, 'attack_range': 2500, 'hit_count': 1, 'reduce_max': 0},
    'BOOK_2H': {'min_damage': 192, 'max_damage': 235, 'attack_speed': 2200, 'physical_critical': 0, 'physical_accuracy': 0, 'parry': 0, 'magical_accuracy': 320, 'boost_magical_skill': 720, 'attack_range': 2500, 'hit_count': 1, 'reduce_max': 0},
    '2H_ORB': {'min_damage': 224, 'max_damage': 274, 'attack_speed': 2200, 'physical_critical': 0, 'physical_accuracy': 0, 'parry': 0, 'magical_accuracy': 320, 'boost_magical_skill': 720, 'attack_range': 2500, 'hit_count': 1, 'reduce_max': 0},
    'ORB_2H': {'min_damage': 224, 'max_damage': 274, 'attack_speed': 2200, 'physical_critical': 0, 'physical_accuracy': 0, 'parry': 0, 'magical_accuracy': 320, 'boost_magical_skill': 720, 'attack_range': 2500, 'hit_count': 1, 'reduce_max': 0},
    '2H_BLADE': {'min_damage': 160, 'max_damage': 240, 'attack_speed': 2200, 'physical_critical': 50, 'physical_accuracy': 751, 'parry': 852, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 2000, 'hit_count': 2, 'reduce_max': 0},
    'BLADE_2H': {'min_damage': 160, 'max_damage': 240, 'attack_speed': 2200, 'physical_critical': 50, 'physical_accuracy': 751, 'parry': 852, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 2000, 'hit_count': 2, 'reduce_max': 0},
    '2H_RUNESWORD': {'min_damage': 203, 'max_damage': 377, 'attack_speed': 2400, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 852, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 2000, 'hit_count': 2, 'reduce_max': 0},
    '2H_DIMENSIONSWORD': {'min_damage': 150, 'max_damage': 220, 'attack_speed': 1600, 'physical_critical': 50, 'physical_accuracy': 751, 'parry': 800, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 1500, 'hit_count': 2, 'reduce_max': 0},
    '2H_CANNON': {'min_damage': 250, 'max_damage': 400, 'attack_speed': 2000, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 0, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 25000, 'hit_count': 1, 'reduce_max': 0},
    '2H_HARP': {'min_damage': 180, 'max_damage': 260, 'attack_speed': 2400, 'physical_critical': 50, 'physical_accuracy': 701, 'parry': 0, 'magical_accuracy': 240, 'boost_magical_skill': 0, 'attack_range': 25000, 'hit_count': 1, 'reduce_max': 0},
}


def map_equipment_type(item_type: str, weapon_type: str, armor_type: str, eq_slot: str) -> tuple[str, str]:
    """Determina category e equipment_type para o schema do servidor."""
    if weapon_type and weapon_type != "NONE":
        return weapon_type, "WEAPON"
    if armor_type and armor_type != "NONE":
        return armor_type, "ARMOR"
    if eq_slot in ACCESSORY_SLOT_CATEGORIES:
        return ACCESSORY_SLOT_CATEGORIES[eq_slot]
    return "NONE", "NONE"


def apply_weapon_stats(elem, c_item, weapon_type):
    """Insere ou atualiza <weapon_stats> de acordo com os dados do cliente oficial e schema XSD."""
    is_weapon = (elem.get("equipment_type") == "WEAPON")
    is_shield = (elem.get("armor_type") == "SHIELD" or (c_item is not None and c_item.findtext("armor_type", "").upper() == "SHIELD"))
    
    if not is_weapon and not is_shield:
        return

    min_dmg = c_item.findtext("min_damage") if c_item is not None else None
    max_dmg = c_item.findtext("max_damage") if c_item is not None else None
    atk_delay = c_item.findtext("attack_delay") if c_item is not None else None
    atk_range = c_item.findtext("attack_range") if c_item is not None else None
    hit_cnt = c_item.findtext("hit_count") if c_item is not None else None
    crit = c_item.findtext("critical") if c_item is not None else None
    acc = c_item.findtext("hit_accuracy") if c_item is not None else None
    parry = c_item.findtext("parry") if c_item is not None else None
    m_acc = c_item.findtext("magical_hit_accuracy") if c_item is not None else None
    m_bst = c_item.findtext("magical_skill_boost") if c_item is not None else None
    red_max = c_item.findtext("reduce_max") if c_item is not None else None

    fallback = DEFAULT_WEAPON_STATS.get(weapon_type, DEFAULT_WEAPON_STATS['1H_SWORD'])

    ws_elem = elem.find("weapon_stats")
    if ws_elem is None:
        ws_elem = ET.Element("weapon_stats")
        # Inserção respeitando a sequência estrita do schema XSD:
        # sequence: modifiers, actions, godstone, stigma, weapon_stats, tradein_list, acquisition, uselimits, purchable, inventory, improve
        insert_idx = len(elem)
        for i, child in enumerate(elem):
            if child.tag in ('tradein_list', 'acquisition', 'uselimits', 'purchable', 'inventory', 'improve'):
                insert_idx = i
                break
        elem.insert(insert_idx, ws_elem)

    if is_weapon:
        min_d = int(min_dmg) if min_dmg and min_dmg.isdigit() else fallback['min_damage']
        max_d = int(max_dmg) if max_dmg and max_dmg.isdigit() else fallback['max_damage']
        spd = int(atk_delay) if atk_delay and atk_delay.isdigit() else fallback['attack_speed']
        rng = int(float(atk_range) * 1000) if atk_range else fallback['attack_range']
        hits = int(hit_cnt) if hit_cnt and hit_cnt.isdigit() else fallback['hit_count']
        c_crit = int(crit) if crit and crit.isdigit() else fallback['physical_critical']
        p_acc = int(acc) if acc and acc.isdigit() else fallback['physical_accuracy']
        p_parry = int(parry) if parry and parry.isdigit() else fallback['parry']
        m_acc_val = int(m_acc) if m_acc and m_acc.isdigit() else fallback['magical_accuracy']
        m_bst_val = int(m_bst) if m_bst and m_bst.isdigit() else fallback['boost_magical_skill']

        ws_elem.set("min_damage", str(min_d))
        ws_elem.set("max_damage", str(max_d))
        ws_elem.set("attack_speed", str(spd))
        ws_elem.set("physical_critical", str(c_crit))
        ws_elem.set("physical_accuracy", str(p_acc))
        ws_elem.set("parry", str(p_parry))
        ws_elem.set("magical_accuracy", str(m_acc_val))
        ws_elem.set("boost_magical_skill", str(m_bst_val))
        ws_elem.set("attack_range", str(rng))
        ws_elem.set("hit_count", str(hits))

    if red_max and red_max.isdigit() and int(red_max) > 0:
        ws_elem.set("reduce_max", red_max)


def parse_items():
    print("=== [1/17] Processando Itens 5.0 (items/ & cosmetic_items/) ===")
    
    # 1. Carrega dados do cliente 5.0
    print("  -> Carregando client_items.xml oficial 5.0...")
    client_items_root = common_bxml.read_client_xml("items/client_items.xml")
    if client_items_root is None:
        print("  [ERRO] Nao foi possivel carregar items/client_items.xml do cliente!")
        return

    # 2. Carrega item_templates.xml do servidor
    server_path = "items/item/item_templates.xml"
    _, server_root = common_bxml.read_server_xml(server_path)
    orig_count = len(server_root)
    
    # Indexa itens existentes por ID
    server_items = {}
    for item in server_root.findall("item_template"):
        i_id = item.get("id")
        if i_id:
            server_items[i_id] = item
            
    added_count = 0
    updated_count = 0
    
    for c_item in client_items_root:
        item_id = c_item.findtext("id")
        if not item_id:
            continue
            
        code_name = c_item.findtext("name", "")
        desc_str = c_item.findtext("desc", "0")
        name_id = common_bxml.resolve_name_id(desc_str, 0)
        real_name = common_bxml.resolve_body(desc_str, code_name)
        level = c_item.findtext("level", "1")
        price = c_item.findtext("price", "0")
        quality = c_item.findtext("quality", "COMMON").upper()
        item_type = c_item.findtext("item_type", "NORMAL").upper()
        weapon_type = c_item.findtext("weapon_type", "NONE").upper()
        armor_type = c_item.findtext("armor_type", "NONE").upper()
        max_stack = c_item.findtext("max_stack_count", "1")
        race = c_item.findtext("race", "PC_ALL").upper()
        eq_slots_raw = c_item.findtext("equipment_slots", "none").strip().lower()
        slot_mask = SLOT_MAP.get(eq_slots_raw, 0)
        
        category, equip_type = map_equipment_type(item_type, weapon_type, armor_type, eq_slots_raw)
        if slot_mask == 0:
            if equip_type == "WEAPON":
                slot_mask = 1
            elif equip_type == "ARMOR" and armor_type == "SHIELD":
                slot_mask = 2
        
        if item_id in server_items:
            elem = server_items[item_id]
            elem.set("name", real_name)
            elem.set("desc", name_id)
            elem.set("level", level)
            elem.set("price", price)
            elem.set("quality", quality)
            elem.set("item_type", item_type)
            if weapon_type != "NONE":
                elem.set("weapon_type", weapon_type)
                elem.set("equipment_type", "WEAPON")
            if armor_type != "NONE":
                elem.set("equipment_type", "ARMOR")
            if equip_type != "NONE" and elem.get("equipment_type") in (None, "NONE"):
                elem.set("equipment_type", equip_type)
            if category != "NONE" and elem.get("category") in (None, "NONE"):
                elem.set("category", category)
            if slot_mask > 0:
                elem.set("slot", str(slot_mask))
            
            # Aplica weapon_stats
            apply_weapon_stats(elem, c_item, weapon_type)
            updated_count += 1
        else:
            elem = ET.SubElement(server_root, "item_template")
            elem.set("id", item_id)
            elem.set("name", real_name)
            elem.set("level", level)
            elem.set("mask", "3708")
            elem.set("category", category)
            if weapon_type != "NONE":
                elem.set("weapon_type", weapon_type)
            elem.set("item_type", item_type)
            elem.set("quality", quality)
            elem.set("price", price)
            elem.set("race", race)
            elem.set("max_stack_count", max_stack)
            elem.set("desc", name_id)
            elem.set("equipment_type", equip_type)
            if slot_mask > 0:
                elem.set("slot", str(slot_mask))
            
            # Aplica weapon_stats
            apply_weapon_stats(elem, c_item, weapon_type)
            added_count += 1

    # Garante que 100% dos itens WEAPON existentes no servidor tenham <weapon_stats>
    missing_ws_count = 0
    for item in server_root.findall("item_template"):
        if item.get("equipment_type") == "WEAPON" and item.find("weapon_stats") is None:
            w_type = item.get("weapon_type", "1H_SWORD")
            apply_weapon_stats(item, None, w_type)
            missing_ws_count += 1

    if missing_ws_count > 0:
        print(f"  -> Injetados weapon_stats padrão em {missing_ws_count} armas restantes.")
        updated_count += missing_ws_count

    final_count = len(server_root)
    print(f"  -> Gravando {final_count} itens em {server_path}...")
    common_bxml.write_server_xml(server_path, server_root)
    common_bxml.log_step("Itens (item_templates)", orig_count, added_count, updated_count, final_count)

    # Sincroniza diretamente com o PRODUTO FINAL
    produto_final_xml = os.path.join(os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data", "items\item\item_templates.xml"))
    if os.path.exists(os.path.dirname(produto_final_xml)):
        source_xml = os.path.join(common_bxml.SERVER_DATA_DIR, server_path)
        shutil.copy2(source_xml, produto_final_xml)
        print(f"  -> Sincronizado com PRODUTO FINAL: {produto_final_xml}")

    # 3. Processa Cosmetic Items
    try:
        cosmetics_root = common_bxml.read_client_xml("items/client_item_skin.xml")
        _, server_cosmetics = common_bxml.read_server_xml("cosmetic_items/cosmetic_items.xml")
        c_orig = len(server_cosmetics)
        c_added = 0
        c_existing = {el.get("id") for el in server_cosmetics.findall("cosmetic_item")}
        for elem in cosmetics_root:
            skin_id = elem.findtext("id")
            if skin_id and skin_id not in c_existing:
                c_name = elem.findtext("name", "")
                c_skin_name = elem.findtext("skin_name", "")
                ne = ET.SubElement(server_cosmetics, "cosmetic_item")
                ne.set("id", skin_id)
                ne.set("name", common_bxml.resolve_body(c_name, c_name))
                ne.set("cosmetic_name", c_skin_name)
                c_added += 1
        common_bxml.write_server_xml("cosmetic_items/cosmetic_items.xml", server_cosmetics)
        common_bxml.log_step("Cosmetic Items", c_orig, c_added, 0, len(server_cosmetics))
    except Exception as e:
        print(f"  [AVISO] Cosmetic items: {e}")


if __name__ == "__main__":
    parse_items()
