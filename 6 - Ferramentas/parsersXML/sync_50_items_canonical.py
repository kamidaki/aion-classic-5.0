#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_50_items_canonical.py
Sincroniza e preenche o catálogo item_templates.xml do servidor com 100% dos dados
oficiais decodificados do cliente Aion Classic 5.0 (client_items.xml, 220 MB).
"""

import os
import sys
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = r"g:/Projetos AION/Classic"
CLIENT_ITEMS_XML = r"g:/Projetos AION/XMLS AION CLASSIC/data/items/client_items.xml"
CLIENT_STRINGS_DIR = r"g:/Projetos AION/XMLS AION CLASSIC/Strings/strings"
SERVER_XML_SRC = os.path.join(PROJECT_ROOT, r"1 - Código Fonte [Emulador]/game-server/data/static_data/items/item_templates.xml")
SERVER_XML_PROD = os.path.join(PROJECT_ROOT, r"2 - Emulador [Produto Final]/GameServer/data/static_data/items/item_templates.xml")

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
    'seed': 24576,
    'wing': 32768,                          # WINGS (32768)
    'waist': 65536,                         # WAIST (65536)
    'torso glove foot shoulder leg': 6200,  # Full body suit (8|16|32|2048|4096)
    'torso leg': 4104,                      # 8 | 4096
}

WEAPON_MAP = {
    '1h_sword': 'SWORD',
    '2h_sword': 'GREATSWORD',
    '1h_dagger': 'DAGGER',
    '1h_mace': 'MACE',
    '2h_staff': 'STAFF',
    '2h_polearm': 'POLEARM',
    'bow': 'BOW',
    '2h_book': 'SPELLBOOK',
    '2h_orb': 'ORB',
    '1h_gun': 'GUN',
    '2h_cannon': 'CANNON',
    '2h_harp': 'HARP',
    'keyblade': 'KEYBLADE',
    '2h_blade': 'CHAINBLADE',
    '1h_gauntlet': 'GAUNTLET',
    '2h_dimensionsword': 'DIMENSIONSWORD',
    '2h_runesword': 'RUNESWORD',
    'toolrods': 'TOOLRODS',
    'toolhoes': 'TOOLHOES',
    'toolpicks': 'TOOLPICKS',
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
    'abyss': 'ABYSS',
    'draconic': 'DRACONIC',
    'devanion': 'DEVANION',
    'normal': 'NORMAL',
}

RACE_MAP = {
    'pc_light pc_dark': 'PC_ALL',
    'pc_light': 'ELYOS',
    'pc_dark': 'ASMODIANS',
    'all': 'PC_ALL',
}


def load_strings():
    print("1. Carregando strings do cliente 5.0...")
    n2id = {}
    n2b = {}
    pattern = re.compile(r'<string>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>(?:\s*<body>([^<]*)</body>)?', re.DOTALL)
    
    if os.path.exists(CLIENT_STRINGS_DIR):
        for f in os.listdir(CLIENT_STRINGS_DIR):
            if f.endswith('.xml'):
                p = os.path.join(CLIENT_STRINGS_DIR, f)
                raw = open(p, 'rb').read()
                try:
                    if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
                        text = raw.decode('utf-16', errors='ignore')
                    else:
                        text = raw.decode('utf-8', errors='ignore')
                except Exception:
                    text = raw.decode('latin-1', errors='ignore')
                for s_id, s_name, s_body in pattern.findall(text):
                    sn = s_name.strip()
                    s_id_int = int(s_id)
                    n2id[sn] = s_id_int
                    n2id[sn.upper()] = s_id_int
                    if s_body:
                        sb = s_body.strip()
                        n2b[sn] = sb
                        n2b[sn.upper()] = sb
    print(f"   Strings carregadas: {len(n2id)} IDs, {len(n2b)} corpos de texto.")
    return n2id, n2b


def resolve_item_group(ci: dict) -> str:
    wt = (ci.get("weapon_type") or "").lower()
    if wt in WEAPON_MAP:
        return WEAPON_MAP[wt]

    at = (ci.get("armor_type") or "").lower()
    es = (ci.get("equipment_slots") or "").lower()

    if at == "shield":
        return "SHIELD"
    if es == "sub" and at == "clothes":
        return "CL_SHIELD"
    if es in ("torso glove foot shoulder leg", "torso leg"):
        return "CL_MULTISLOT"

    if es == "torso":
        if at == "robe": return "RB_TORSO"
        if at == "leather": return "LT_TORSO"
        if at == "chain": return "CH_TORSO"
        if at == "plate": return "PL_TORSO"
        if at == "clothes": return "CL_TORSO"
        return "TORSO"
    if es == "glove":
        if at == "robe": return "RB_GLOVE"
        if at == "leather": return "LT_GLOVE"
        if at == "chain": return "CH_GLOVE"
        if at == "plate": return "PL_GLOVE"
        if at == "clothes": return "CL_GLOVE"
        return "GLOVE"
    if es == "foot":
        if at == "robe": return "RB_SHOES"
        if at == "leather": return "LT_SHOES"
        if at == "chain": return "CH_SHOES"
        if at == "plate": return "PL_SHOES"
        if at == "clothes": return "CL_SHOES"
        return "SHOES"
    if es == "leg":
        if at == "robe": return "RB_PANTS"
        if at == "leather": return "LT_PANTS"
        if at == "chain": return "CH_PANTS"
        if at == "plate": return "PL_PANTS"
        if at == "clothes": return "CL_PANTS"
        return "PANTS"
    if es == "shoulder":
        if at == "robe": return "RB_SHOULDER"
        if at == "leather": return "LT_SHOULDER"
        if at == "chain": return "CH_SHOULDER"
        if at == "plate": return "PL_SHOULDER"
        if at == "clothes": return "CL_SHOULDER"
        return "SHOULDER"
    if es == "head":
        if at == "leather": return "LT_HEADS"
        if at == "clothes": return "CL_HEADS"
        return "HEAD"
    if es == "right_or_left_ear":
        return "EARRING"
    if es == "right_or_left_finger":
        return "RING"
    if es == "neck":
        return "NECKLACE"
    if es == "waist":
        return "BELT"
    if es == "wing":
        return "WING"
    if es in ("right_or_left_battery", "seed"):
        return "POWER_SHARDS"

    mt = (ci.get("mgrouptag") or "")
    if "I_Stigma_All" in mt: return "STIGMA"
    if "I_Recipe_All" in mt: return "RECIPE"
    if "I_Enchant_All" in mt: return "ENCHANTMENT"
    if "I_Option_All" in mt:
        if "special" in (ci.get("name") or "").lower(): return "SPECIAL_MANASTONE"
        return "MANASTONE"
    if "I_Proc_All" in mt: return "GODSTONE"
    if "I_BATTERY_All" in mt: return "POWER_SHARDS"
    if "I_Harvest_Out_All" in mt: return "GATHERABLE"
    if "I_dr_material" in mt: return "BALIC_MATERIAL"
    if "I_Soulstone_All" in mt or "I_RESURRECT" in mt: return "SOULSTONE"
    if "I_Coin_All" in mt or "I_Badge_All" in mt: return "COINS"
    if "I_Medal_All" in mt: return "MEDALS"
    if "I_Q_F4_Request_All" in mt or "I_raid_check_coin" in mt: return "QUEST"
    if any(k in mt for k in ("I_Scroll_", "I_Potion_", "I_Food_", "I_Drink_", "I_Candy_", "I_Jelly_", "I_Cure_")):
        return "PACK_SCROLL"

    return None


def calculate_item_mask(ci: dict) -> int:
    mask = 0
    if ci.get('lore', '').lower() == 'true':
        mask |= 1   # LIMIT_ONE
    if ci.get('can_exchange', '').lower() == 'true':
        mask |= 2   # TRADEABLE
    if ci.get('can_sell_to_npc', '').lower() == 'true':
        mask |= 4   # SELLABLE
    if ci.get('can_deposit_to_character_warehouse', '').lower() == 'true':
        mask |= 8   # STORABLE_IN_WH
    if ci.get('can_deposit_to_account_warehouse', '').lower() == 'true':
        mask |= 16  # STORABLE_IN_AWH
    if ci.get('can_deposit_to_guild_warehouse', '').lower() == 'true':
        mask |= 32  # STORABLE_IN_LWH
    if ci.get('breakable', '').lower() == 'true':
        mask |= 64  # BREAKABLE
    if ci.get('soul_bind', '').lower() == 'true':
        mask |= 128 # SOUL_BOUND
    if ci.get('remove_when_logout', '').lower() == 'true':
        mask |= 256 # REMOVE_LOGOUT
    if ci.get('no_enchant', '').lower() == 'true':
        mask |= 512 # NO_ENCHANT
    if ci.get('can_proc_enchant', '').lower() == 'true':
        mask |= 1024 # CAN_PROC_ENCHANT
    if ci.get('can_composite_weapon', '').lower() == 'true':
        mask |= 2048 # CAN_COMPOSITE_WEAPON
    if ci.get('cannot_changeskin', '0') not in ('1', 'true', 'TRUE'):
        mask |= 4096 # REMODELABLE
    if ci.get('can_split', '').lower() == 'true':
        mask |= 8192 # CAN_SPLIT
    if ci.get('item_drop_permitted', '').lower() == 'true':
        mask |= 16384 # DELETABLE
    if ci.get('dyeable', '').lower() == 'true':
        mask |= 32768 # DYEABLE
    if ci.get('can_ap_extract', '').lower() == 'true':
        mask |= 65536 # CAN_AP_EXTRACT
    if ci.get('can_polish', '').lower() == 'true':
        mask |= 131072 # CAN_POLISH
    if ci.get('can_deposit_to_guild_warehouse', '').lower() == 'true':
        mask |= 262144 # LEGION_TRADEABLE
    return mask


def main():
    start_time = time.time()
    print("=" * 75)
    print(" Sincronização Canônica de Itens Classic 5.0 (client_items.xml -> item_templates.xml)")
    print("=" * 75)

    n2id, n2b = load_strings()

    print("\n2. Parseando client_items.xml do Classic 5.0 (streaming iterparse)...")
    client_items = {}
    context = ET.iterparse(CLIENT_ITEMS_XML, events=('end',))
    
    count_cli = 0
    for event, elem in context:
        if elem.tag == 'client_item':
            count_cli += 1
            iid_str = elem.findtext('id')
            if iid_str and iid_str.isdigit():
                iid = int(iid_str)
                d = {}
                for child in elem:
                    if child.text:
                        d[child.tag] = child.text.strip()
                client_items[iid] = d
            elem.clear()
            if count_cli % 20000 == 0:
                print(f"   Processados {count_cli} client_items...")

    print(f"   Total de itens lidos do cliente 5.0: {len(client_items)}")

    print(f"\n3. Carregando e atualizando o XML do servidor ({SERVER_XML_SRC})...")
    tree = ET.parse(SERVER_XML_SRC)
    root = tree.getroot()
    server_items = {}
    for item in root.findall('item_template'):
        sid_str = item.get('id')
        if sid_str and sid_str.isdigit():
            server_items[int(sid_str)] = item

    print(f"   Itens existentes no item_templates.xml: {len(server_items)}")

    updated_items = 0
    added_items = 0

    for iid, ci in client_items.items():
        cname = ci.get('name', '')
        desc_raw = ci.get('desc', '')
        
        # Name e Desc
        name_val = n2b.get(desc_raw) or n2b.get(cname) or cname
        desc_id = n2id.get(desc_raw) or 0
        
        quality_raw = (ci.get('quality') or 'common').lower()
        quality = QUALITY_MAP.get(quality_raw, 'COMMON')
        level = ci.get('level', '1')
        price = ci.get('price', '0')
        max_stack = ci.get('max_stack_count', '1')
        
        race_raw = (ci.get('race_permitted') or 'all').lower()
        race = RACE_MAP.get(race_raw, 'PC_ALL')
        
        item_type_raw = (ci.get('item_type') or 'normal').lower()
        item_type = ITEM_TYPE_MAP.get(item_type_raw, 'NORMAL')
        
        item_group = resolve_item_group(ci)
        mask = calculate_item_mask(ci)
        
        is_weapon = (ci.get('weapon_type') and ci.get('weapon_type').lower() != 'none')
        is_armor = (ci.get('armor_type') and ci.get('armor_type').lower() != 'none')
        
        no_enchant = (ci.get('no_enchant', '').lower() == 'true')
        max_enchant = 0
        if not no_enchant and (is_weapon or is_armor):
            enc_val = ci.get('max_enchant_value')
            if enc_val and enc_val.isdigit():
                max_enchant = int(enc_val)
            elif quality in ('LEGENDARY', 'UNIQUE', 'EPIC', 'MYTHIC'):
                max_enchant = 15
            else:
                max_enchant = 10
        
        atk_type = ci.get('attack_type', '').strip().upper() if is_weapon else None
        
        elem = server_items.get(iid)
        if elem is None:
            elem = ET.SubElement(root, 'item_template')
            elem.set('id', str(iid))
            server_items[iid] = elem
            added_items += 1
        else:
            updated_items += 1

        # Limpar atributos inválidos se existirem
        for invalid_attr in ('category', 'weapon_type', 'equipment_type'):
            if invalid_attr in elem.attrib:
                del elem.attrib[invalid_attr]

        # Atualizar atributos canônicos
        if name_val:
            elem.set('name', name_val)
        if cname:
            elem.set('cName', cname)
        if desc_id > 0:
            elem.set('desc', str(desc_id))
        elem.set('level', str(level))
        elem.set('quality', quality)
        elem.set('price', str(price))
        elem.set('max_stack_count', str(max_stack))
        elem.set('race', race)
        elem.set('item_type', item_type)
        elem.set('mask', str(mask))
        if item_group:
            elem.set('item_group', item_group)
        if max_enchant > 0:
            elem.set('max_enchant', str(max_enchant))
        elif 'max_enchant' in elem.attrib and no_enchant:
            del elem.attrib['max_enchant']
            
        if atk_type:
            elem.set('attack_type', atk_type)

        # Slots
        eq_slots_raw = (ci.get('equipment_slots') or '').lower()
        s_mask = SLOT_MAP.get(eq_slots_raw, 0)
        TWO_HAND_GROUPS = {
            'POLEARM', 'GREATSWORD', 'BOW', 'STAFF', 'SPELLBOOK', 'ORB',
            'CANNON', 'HARP', 'KEYBLADE', 'CHAINBLADE', 'DIMENSIONSWORD',
            'RUNESWORD', 'TOOLRODS', 'TOOLPICKS', 'NOWEAPON'
        }
        if item_group in TWO_HAND_GROUPS:
            s_mask = 3
        elif s_mask == 0 and is_weapon:
            s_mask = 1

        if s_mask > 0:
            elem.set('slot', str(s_mask))
            
        opt_slots = ci.get('option_slot_bonus')
        if opt_slots and opt_slots.isdigit() and int(opt_slots) > 0:
            elem.set('option_slot_bonus', opt_slots)
        spec_slots = ci.get('special_slot')
        if spec_slots and spec_slots.isdigit() and int(spec_slots) > 0:
            elem.set('s_slots', spec_slots)

        # weapon_stats para armas ou escudos
        if is_weapon or (item_group and 'SHIELD' in item_group):
            ws_elem = elem.find('weapon_stats')
            if ws_elem is None:
                ws_elem = ET.Element('weapon_stats')
                # Encontrar a posição correta de inserção respeitando a ordem do schema XSD:
                # modifiers, actions, godstone, stigma, weapon_stats, tradein_list, acquisition, disposition, improve, uselimits, inventory, idian
                insert_idx = len(elem)
                for i, ch in enumerate(elem):
                    if ch.tag in ('tradein_list', 'acquisition', 'disposition', 'improve', 'uselimits', 'inventory', 'idian'):
                        insert_idx = i
                        break
                elem.insert(insert_idx, ws_elem)

            min_dmg = ci.get('min_damage')
            max_dmg = ci.get('max_damage')
            atk_delay = ci.get('attack_delay')
            crit = ci.get('critical')
            acc = ci.get('hit_accuracy')
            parry = ci.get('parry')
            m_acc = ci.get('magical_hit_accuracy')
            m_bst = ci.get('magical_skill_boost')
            atk_range = ci.get('attack_range')
            hit_cnt = ci.get('hit_count')
            red_max = ci.get('reduce_max')

            if min_dmg and min_dmg.isdigit(): ws_elem.set('min_damage', min_dmg)
            if max_dmg and max_dmg.isdigit(): ws_elem.set('max_damage', max_dmg)
            if atk_delay and atk_delay.isdigit(): ws_elem.set('attack_speed', atk_delay)
            if crit and crit.isdigit(): ws_elem.set('critical', crit)
            if acc and acc.isdigit(): ws_elem.set('physical_accuracy', acc)
            if parry and parry.isdigit(): ws_elem.set('parry', parry)
            if m_acc and m_acc.isdigit(): ws_elem.set('magical_accuracy', m_acc)
            if m_bst and m_bst.isdigit(): ws_elem.set('boost_magical_skill', m_bst)
            if atk_range:
                try:
                    rng = int(round(float(atk_range) * 1000))
                    ws_elem.set('attack_range', str(rng))
                except:
                    pass
            if hit_cnt and hit_cnt.isdigit(): ws_elem.set('hit_count', hit_cnt)
            if red_max and red_max.isdigit() and int(red_max) > 0: ws_elem.set('reduce_max', red_max)

    print(f"\n4. Resumo das Modificações:")
    print(f"   Itens atualizados: {updated_items}")
    print(f"   Itens novos adicionados: {added_items}")
    print(f"   Total final de itens no catálogo: {len(root)}")

    print("\n5. Gravando os arquivos estáticos...")
    tree.write(SERVER_XML_SRC, encoding='utf-8', xml_declaration=True)
    tree.write(SERVER_XML_PROD, encoding='utf-8', xml_declaration=True)
    print(f"   Gravado com sucesso em: {SERVER_XML_SRC}")
    print(f"   Gravado com sucesso em: {SERVER_XML_PROD}")
    print(f"   Tempo total decorrido: {time.time() - start_time:.2f}s")
    print("=" * 75)


if __name__ == '__main__':
    main()
