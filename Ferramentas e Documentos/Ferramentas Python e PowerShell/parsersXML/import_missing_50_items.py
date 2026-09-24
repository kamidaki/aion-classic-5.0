#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_missing_50_items.py
Importa com segurança todos os itens faltantes do cliente Classic 5.0 para item_templates.xml
100% aderente ao schema JAXB/XSD do servidor:
- Sem atributos inválidos (como weapon_type ou category)
- Mapeia item_group correto para novas classes (CHAINBLADE, GAUNTLET, DIMENSIONSWORD, RUNESWORD)
- Gera weapon_stats válidos para armas das novas classes
- Sincroniza tanto em Código Fonte - Emulador quanto em Emulador - Produto Final
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import common_bxml

WEAPON_GROUP_MAP = {
    '2h_blade': 'CHAINBLADE',
    '1h_gauntlet': 'GAUNTLET',
    '2h_dimensionsword': 'DIMENSIONSWORD',
    '2h_runesword': 'RUNESWORD',
    '1h_mace': 'MACE',
    '2h_sword': 'GREATSWORD',
    '1h_sword': 'SWORD',
    '1h_dagger': 'DAGGER',
    'bow': 'BOW',
    '2h_staff': 'STAFF',
    '2h_polearm': 'POLEARM',
    '2h_book': 'SPELLBOOK',
    '2h_orb': 'ORB',
    '1h_gun': 'GUN',
    '2h_cannon': 'CANNON',
    '2h_harp': 'HARP',
    'keyblade': 'KEYBLADE',
}

DEFAULT_WEAPON_STATS = {
    'CHAINBLADE': {'min_damage': '160', 'max_damage': '240', 'attack_speed': '2200', 'critical': '50', 'physical_accuracy': '751', 'parry': '852', 'attack_range': '2000', 'hit_count': '2'},
    'GAUNTLET': {'min_damage': '123', 'max_damage': '137', 'attack_speed': '1100', 'critical': '110', 'physical_accuracy': '741', 'parry': '912', 'attack_range': '1500', 'hit_count': '1'},
    'DIMENSIONSWORD': {'min_damage': '150', 'max_damage': '220', 'attack_speed': '1600', 'critical': '50', 'physical_accuracy': '751', 'parry': '800', 'attack_range': '1500', 'hit_count': '2'},
    'RUNESWORD': {'min_damage': '203', 'max_damage': '377', 'attack_speed': '2400', 'critical': '50', 'physical_accuracy': '701', 'parry': '852', 'attack_range': '2000', 'hit_count': '2'},
    'MACE': {'min_damage': '136', 'max_damage': '204', 'attack_speed': '1500', 'critical': '50', 'physical_accuracy': '701', 'parry': '812', 'attack_range': '1500', 'hit_count': '1'},
    'GREATSWORD': {'min_damage': '203', 'max_damage': '377', 'attack_speed': '2400', 'critical': '50', 'physical_accuracy': '701', 'parry': '852', 'attack_range': '2000', 'hit_count': '3'},
    'SWORD': {'min_damage': '142', 'max_damage': '174', 'attack_speed': '1400', 'critical': '50', 'physical_accuracy': '751', 'parry': '812', 'attack_range': '1500', 'hit_count': '2'},
    'DAGGER': {'min_damage': '129', 'max_damage': '143', 'attack_speed': '1200', 'critical': '100', 'physical_accuracy': '751', 'parry': '772', 'attack_range': '1500', 'hit_count': '1'},
    'BOW': {'min_damage': '208', 'max_damage': '282', 'attack_speed': '2400', 'critical': '50', 'physical_accuracy': '751', 'parry': '0', 'attack_range': '25000', 'hit_count': '1'},
    'STAFF': {'min_damage': '187', 'max_damage': '281', 'attack_speed': '2000', 'critical': '50', 'physical_accuracy': '701', 'parry': '852', 'attack_range': '2000', 'hit_count': '3'},
    'POLEARM': {'min_damage': '221', 'max_damage': '413', 'attack_speed': '2800', 'critical': '50', 'physical_accuracy': '701', 'parry': '852', 'attack_range': '2500', 'hit_count': '4'},
    'SPELLBOOK': {'min_damage': '192', 'max_damage': '235', 'attack_speed': '2200', 'critical': '0', 'physical_accuracy': '0', 'parry': '0', 'attack_range': '2500', 'hit_count': '1'},
    'ORB': {'min_damage': '224', 'max_damage': '274', 'attack_speed': '2200', 'critical': '0', 'physical_accuracy': '0', 'parry': '0', 'attack_range': '2500', 'hit_count': '1'},
    'GUN': {'min_damage': '142', 'max_damage': '174', 'attack_speed': '1100', 'critical': '50', 'physical_accuracy': '751', 'parry': '0', 'attack_range': '20000', 'hit_count': '1'},
    'CANNON': {'min_damage': '250', 'max_damage': '400', 'attack_speed': '2000', 'critical': '50', 'physical_accuracy': '701', 'parry': '0', 'attack_range': '25000', 'hit_count': '1'},
    'HARP': {'min_damage': '180', 'max_damage': '260', 'attack_speed': '2400', 'critical': '50', 'physical_accuracy': '701', 'parry': '0', 'attack_range': '25000', 'hit_count': '1'},
}

SLOT_ARMOR_MAP = {
    'head': 'HELMET',
    'torso': 'TORSO',
    'glove': 'GLOVE',
    'foot': 'SHOES',
    'shoulder': 'SHOULDER',
    'leg': 'PANTS',
    'right_or_left_ear': 'EARRINGS',
    'right_or_left_finger': 'RINGS',
    'neck': 'NECKLACE',
    'waist': 'BELT',
    'wing': 'WINGS',
    'right_or_left_battery': 'SHARD',
}

QUALITY_MAP = {
    'junk': 'JUNK',
    'common': 'COMMON',
    'rare': 'RARE',
    'legend': 'LEGENDARY',
    'legendary': 'LEGENDARY',
    'unique': 'UNIQUE',
    'epic': 'EPIC',
    'mythic': 'MYTHIC',
}

ITEM_TYPE_MAP = {
    'normal': 'NORMAL',
    'abyss': 'ABYSS',
    'draconic': 'DRACONIC',
    'devanion': 'DEVANION',
}

RACE_MAP = {
    'pc_light pc_dark': 'PC_ALL',
    'pc_light': 'ELYOS',
    'pc_dark': 'ASMODIANS',
    'all': 'PC_ALL',
}


def main():
    print("=" * 70)
    print(" Importador de Itens Faltantes do Classic 5.0")
    print("=" * 70)

    # 1. Carrega strings do cliente
    common_bxml.load_strings()

    # 2. Lê item_templates.xml do servidor
    server_rel = "items/item_templates.xml"
    tree_srv, root_srv = common_bxml.read_server_xml(server_rel)
    existing_ids = set()
    for it in root_srv.findall("item_template"):
        iid = it.get("id")
        if iid and iid.isdigit():
            existing_ids.add(int(iid))
    print(f"Itens existentes no servidor: {len(existing_ids)}")

    # 3. Lê client_items.xml do cliente
    client_root = common_bxml.read_client_xml("items/client_items.xml")
    print(f"Itens no client_items.xml: {len(client_root)}")

    added_count = 0
    added_weapons = 0

    for ci in client_root.findall("client_item"):
        id_str = ci.findtext("id")
        if not id_str or not id_str.isdigit():
            continue
        iid = int(id_str)
        if iid in existing_ids:
            continue

        c_name = ci.findtext("name", "")
        desc_raw = ci.findtext("desc", "")
        real_name = common_bxml.resolve_body(desc_raw, c_name)
        desc_num = common_bxml.resolve_name_id(desc_raw, 0)

        level_str = ci.findtext("level", "1")
        price_str = ci.findtext("price", "0")
        max_stack_str = ci.findtext("max_stack_count", "1")

        q_raw = (ci.findtext("quality") or "common").lower()
        quality = QUALITY_MAP.get(q_raw, "COMMON")

        it_raw = (ci.findtext("item_type") or "normal").lower()
        item_type = ITEM_TYPE_MAP.get(it_raw, "NORMAL")

        race_raw = (ci.findtext("race_permitted") or "pc_light pc_dark").lower()
        race = RACE_MAP.get(race_raw, "PC_ALL")

        # Determina item_group e weapon_stats
        wt_raw = (ci.findtext("weapon_type") or "").lower()
        at_raw = (ci.findtext("armor_type") or "").lower()
        eq_slots = (ci.findtext("equipment_slots") or "").lower()

        item_group = "NONE"
        is_weapon = False

        if wt_raw and wt_raw in WEAPON_GROUP_MAP:
            item_group = WEAPON_GROUP_MAP[wt_raw]
            is_weapon = True
        elif at_raw == "shield":
            item_group = "SHIELD"
        elif eq_slots in SLOT_ARMOR_MAP:
            item_group = SLOT_ARMOR_MAP[eq_slots]

        attack_type_raw = (ci.findtext("attack_type") or "").upper()
        if not attack_type_raw:
            attack_type = "PHYSICAL" if is_weapon else None
        else:
            attack_type = "MAGICAL" if "MAGIC" in attack_type_raw else "PHYSICAL"

        # Cria o elemento <item_template>
        elem = ET.SubElement(root_srv, "item_template")
        elem.set("id", str(iid))
        elem.set("name", real_name)
        elem.set("level", level_str)
        elem.set("cName", c_name)
        elem.set("mask", "138878" if is_weapon else "3708")
        elem.set("item_group", item_group)
        elem.set("quality", quality)
        elem.set("price", price_str)
        elem.set("desc", desc_num)
        if attack_type and is_weapon:
            elem.set("attack_type", attack_type)
        elem.set("race", race)
        elem.set("max_stack_count", max_stack_str)
        elem.set("item_type", item_type)

        # Se for arma, insere <weapon_stats> e <idian>
        if is_weapon:
            ws_defaults = DEFAULT_WEAPON_STATS.get(item_group, DEFAULT_WEAPON_STATS["SWORD"])

            min_dmg = ci.findtext("min_damage")
            max_dmg = ci.findtext("max_damage")
            atk_spd = ci.findtext("attack_delay")
            crit = ci.findtext("critical")
            acc = ci.findtext("hit_accuracy")
            parry = ci.findtext("parry")
            hit_cnt = ci.findtext("hit_count")
            atk_rng = ci.findtext("attack_range")

            min_d_val = min_dmg if (min_dmg and min_dmg.isdigit() and int(min_dmg) > 0) else ws_defaults["min_damage"]
            max_d_val = max_dmg if (max_dmg and max_dmg.isdigit() and int(max_dmg) > 0) else ws_defaults["max_damage"]
            atk_s_val = atk_spd if (atk_spd and atk_spd.isdigit() and int(atk_spd) > 0) else ws_defaults["attack_speed"]
            crit_val = crit if (crit and crit.isdigit() and int(crit) > 0) else ws_defaults["critical"]
            acc_val = acc if (acc and acc.isdigit() and int(acc) > 0) else ws_defaults["physical_accuracy"]
            parry_val = parry if (parry and parry.isdigit() and int(parry) > 0) else ws_defaults["parry"]
            hit_c_val = hit_cnt if (hit_cnt and hit_cnt.isdigit() and int(hit_cnt) > 0) else ws_defaults["hit_count"]

            # attack_range no cliente é em metros (ex: 2.000000), no servidor é em mm (ex: 2000)
            if atk_rng:
                try:
                    rng_f = float(atk_rng)
                    if rng_f < 100.0:
                        rng_val = str(int(rng_f * 1000))
                    else:
                        rng_val = str(int(rng_f))
                except Exception:
                    rng_val = ws_defaults["attack_range"]
            else:
                rng_val = ws_defaults["attack_range"]

            ET.SubElement(elem, "weapon_stats", {
                "min_damage": min_d_val,
                "max_damage": max_d_val,
                "attack_speed": atk_s_val,
                "critical": crit_val,
                "physical_accuracy": acc_val,
                "parry": parry_val,
                "attack_range": rng_val,
                "hit_count": hit_c_val
            })
            ET.SubElement(elem, "idian", {
                "burn_attack": "29",
                "burn_defend": "12"
            })
            added_weapons += 1

        existing_ids.add(iid)
        added_count += 1

    print(f"Itens adicionados: +{added_count} (sendo {added_weapons} armas)")
    print(f"Total final no servidor: {len(root_srv)}")

    # 4. Grava nos servidores
    print("Gravando item_templates.xml no servidor e produto final...")
    common_bxml.write_server_xml(server_rel, root_srv)
    print("Concluído com sucesso!")


if __name__ == "__main__":
    main()
