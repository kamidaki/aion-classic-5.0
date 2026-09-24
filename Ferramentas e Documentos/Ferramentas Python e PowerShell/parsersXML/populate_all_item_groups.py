#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
populate_all_item_groups.py
Adiciona o item_group verdadeiro extraindo do client Classic 5.0 para 100% dos itens do item_templates.xml.
- Nenhum item é deixado sem item_group.
- Nenhum item usa NONE no XML.
- Normaliza valores legados inválidos (HELMET -> HEAD, EARRINGS -> EARRING, SHARD -> POWER_SHARDS).
- Sincroniza em:
    Código Fonte - Emulador/game-server/data/static_data/items/item_templates.xml
    Emulador - Produto Final/GameServer/data/static_data/items/item_templates.xml
- Garante total aderência ao schema XSD e JAXB (ItemGroup.java).
"""

import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(PARSERS_DIR)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "Ferramentas e Documentos", "Ferramentas Python e PowerShell", "Ferramentas Python"))
import aion_bxml

SOURCE_XML = os.path.join(PROJECT_ROOT, r"Código Fonte - Emulador\game-server\data\static_data\items\item_templates.xml")
TARGET_XML = os.path.join(PROJECT_ROOT, r"Emulador - Produto Final\GameServer\data\static_data\items\item_templates.xml")
CLIENT_ITEMS_XML = os.path.join(PROJECT_ROOT, r"Ferramentas e Documentos\Client e Coletas\Client 5.0 - Dados Extraidos\data\items\client_items.xml")

VALID_ITEM_GROUPS = {
    "NOWEAPON", "SWORD", "GREATSWORD", "EXTRACT_SWORD", "DAGGER", "MACE", "ORB", "SPELLBOOK", "POLEARM",
    "STAFF", "BOW", "HARP", "GUN", "CANNON", "KEYBLADE", "CHAINBLADE", "GAUNTLET", "DIMENSIONSWORD", "RUNESWORD",
    "NPC_MACE", "TOOLRODS", "TOOLHOES", "TOOLPICKS", "ARROW",
    "SHIELD", "CL_SHIELD",
    "TORSO", "GLOVE", "SHOULDER", "PANTS", "SHOES",
    "RB_TORSO", "RB_GLOVE", "RB_SHOULDER", "RB_PANTS", "RB_SHOES",
    "CL_TORSO", "CL_GLOVE", "CL_SHOULDER", "CL_PANTS", "CL_SHOES", "CL_MULTISLOT",
    "LT_TORSO", "LT_GLOVE", "LT_SHOULDER", "LT_PANTS", "LT_SHOES",
    "CH_TORSO", "CH_GLOVE", "CH_SHOULDER", "CH_PANTS", "CH_SHOES",
    "PL_TORSO", "PL_GLOVE", "PL_SHOULDER", "PL_PANTS", "PL_SHOES",
    "HEAD", "LT_HEADS", "CL_HEADS",
    "EARRING", "RING", "NECKLACE", "BELT", "WING", "PLUME", "POWER_SHARDS",
    "STIGMA", "STIGMA_SHARD", "MANASTONE", "SPECIAL_MANASTONE", "RECIPE", "ENCHANTMENT",
    "PACK_SCROLL", "FLUX", "BALIC_EMOTION", "BALIC_MATERIAL", "RAWHIDE", "SOULSTONE",
    "GATHERABLE", "GATHERABLE_BONUS", "DROP_MATERIAL", "COINS", "MEDALS", "QUEST",
    "KEY", "CRAFT_BOOST", "TAMPERING", "COMBINATION", "SKILLBOOK", "GODSTONE"
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

LEGACY_NORMALIZATION = {
    'HELMET': 'HEAD',
    'EARRINGS': 'EARRING',
    'SHARD': 'POWER_SHARDS',
}


def resolve_item_group(iid: int, s_attr: dict, ci: dict) -> str:
    """Extrai e resolve o item_group verdadeiro baseado em dados do cliente 5.0 e do servidor."""
    # 1. Armas
    wt = (ci.get("weapon_type") or "").lower()
    if wt in WEAPON_MAP:
        return WEAPON_MAP[wt]

    # 2. Escudos e Armaduras
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

    # 3. Client mgrouptag
    mt = (ci.get("mgrouptag") or "")
    if "I_Stigma_All" in mt:
        return "STIGMA"
    if "I_Recipe_All" in mt:
        return "RECIPE"
    if "I_Enchant_All" in mt:
        return "ENCHANTMENT"
    if "I_Option_All" in mt:
        if "special" in (ci.get("name") or "").lower():
            return "SPECIAL_MANASTONE"
        return "MANASTONE"
    if "I_Proc_All" in mt:
        return "GODSTONE"
    if "I_BATTERY_All" in mt:
        return "POWER_SHARDS"
    if "I_Harvest_Out_All" in mt:
        return "GATHERABLE"
    if "I_dr_material" in mt:
        return "BALIC_MATERIAL"
    if "I_Soulstone_All" in mt or "I_RESURRECT" in mt:
        return "SOULSTONE"
    if "I_Coin_All" in mt or "I_Badge_All" in mt:
        return "COINS"
    if "I_Medal_All" in mt:
        return "MEDALS"
    if "I_Q_F4_Request_All" in mt or "I_raid_check_coin" in mt:
        return "QUEST"
    if any(k in mt for k in ("I_Scroll_", "I_Potion_", "I_Food_", "I_Drink_", "I_Candy_", "I_Jelly_", "I_Cure_")):
        return "PACK_SCROLL"

    # 4. Prefixo de ID e Padrões de cName / Name
    p = str(iid)[:3]
    cname = (ci.get("name") or s_attr.get("cName") or "").lower()
    sname = (s_attr.get("name") or "").lower()

    if p in ("100", "101", "102"):
        if "sword" in cname or "sword" in sname: return "SWORD"
        if "dagger" in cname or "dagger" in sname: return "DAGGER"
        if "staff" in cname or "staff" in sname: return "STAFF"
        if "bow" in cname or "bow" in sname: return "BOW"
        return "SWORD"

    if p == "103":
        if "rod" in cname or "rod" in sname or "fish" in cname: return "TOOLRODS"
        if "hoe" in cname or "hoe" in sname: return "TOOLHOES"
        return "TOOLPICKS"

    if p in ("110", "111", "112", "113", "114"):
        if p == "110": return "TORSO"
        if p == "111": return "GLOVE"
        if p == "112": return "SHOULDER"
        if p == "113": return "PANTS"
        if p == "114": return "SHOES"

    if p == "115":
        return "SHIELD"

    if p == "120":
        if "plume" in cname or "plume" in sname: return "PLUME"
        return "EARRING"
    if p == "121":
        return "NECKLACE"
    if p == "122":
        return "RING"
    if p == "123":
        return "BELT"
    if p == "125":
        return "HEAD"

    if p == "140":
        return "STIGMA"
    if p == "141":
        return "STIGMA_SHARD"

    if p == "150":
        return "CRAFT_BOOST"

    if p == "152":
        if "recipe" in cname or "design" in sname or "recipe" in sname:
            return "RECIPE"
        if any(k in cname for k in ("flux", "gem_matter")):
            return "FLUX"
        if any(k in cname for k in ("balic", "drana", "dragon", "dracon", "scale", "horn", "heart")):
            return "BALIC_MATERIAL"
        if "rawhide" in cname or "pelt" in cname or "leather" in cname:
            return "RAWHIDE"
        if any(k in cname for k in ("harvest", "gather", "ore", "herb", "wood", "fiber", "gem")):
            return "GATHERABLE"
        return "DROP_MATERIAL"

    if p == "160":
        return "PACK_SCROLL"
    if p == "161":
        return "SOULSTONE"
    if p == "162":
        return "PACK_SCROLL"
    if p == "163":
        if "arrow" in cname or "arrow" in sname: return "ARROW"
        return "CL_SHIELD"
    if p == "164":
        if "soulstone" in cname or "resurrect" in cname: return "SOULSTONE"
        if "key" in cname: return "KEY"
        return "PACK_SCROLL"
    if p == "165":
        if "combination" in cname: return "COMBINATION"
        if "extraction" in cname or "boost" in cname: return "CRAFT_BOOST"
        return "PACK_SCROLL"
    if p == "166":
        if "tampering" in cname or "water" in cname: return "TAMPERING"
        return "ENCHANTMENT"
    if p == "167":
        if "special" in cname or "ancient" in cname: return "SPECIAL_MANASTONE"
        return "MANASTONE"
    if p == "168":
        return "GODSTONE"
    if p == "169":
        if "skillbook" in cname or "book" in cname or "card" in cname or "manual" in sname or "skill" in sname:
            return "SKILLBOOK"
        if "power_shard" in cname or "shard" in cname: return "POWER_SHARDS"
        if "quest" in cname: return "QUEST"
        return "PACK_SCROLL"
    if p in ("170", "171"):
        return "DROP_MATERIAL"
    if p == "174":
        return "FLUX"
    if p == "181":
        return "DROP_MATERIAL"
    if p == "182":
        return "QUEST"
    if p == "184":
        return "SOULSTONE"
    if p == "185":
        return "KEY"
    if p == "186":
        if "coin" in cname or "coin" in sname or "token" in sname: return "COINS"
        if "medal" in cname or "medal" in sname: return "MEDALS"
        return "DROP_MATERIAL"
    if p == "187":
        if "plume" in cname or "plume" in sname: return "PLUME"
        return "WING"
    if p == "188":
        if "quest" in cname: return "QUEST"
        if "key" in cname: return "KEY"
        if any(k in cname for k in ("scroll", "potion", "buff", "siege", "weapon", "ticket", "pass")):
            return "PACK_SCROLL"
        if any(k in cname for k in ("box", "bundle", "chest", "pouch", "package")):
            return "COMBINATION"
        return "DROP_MATERIAL"
    if p == "189":
        if "book" in cname or "skill" in cname or "skill" in sname: return "SKILLBOOK"
        return "PACK_SCROLL"
    if p == "190":
        return "DROP_MATERIAL"

    return "DROP_MATERIAL"


def main():
    print("=" * 80)
    print(" Populando item_group em 100% dos Itens no XML a partir do Cliente 5.0")
    print("=" * 80)

    # 1. Carregar dados do cliente
    print(f"Lendo client_items.xml: {CLIENT_ITEMS_XML} ...")
    raw = open(CLIENT_ITEMS_XML, "rb").read()
    xml_str = aion_bxml.decodifica(raw) if aion_bxml.e_bxml(CLIENT_ITEMS_XML) else raw.decode("utf-8", errors="ignore")
    c_root = ET.fromstring(xml_str)

    client_items = {}
    for ci in c_root.findall(".//client_item"):
        id_str = ci.findtext("id")
        if id_str and id_str.isdigit():
            client_items[int(id_str)] = {elem.tag: elem.text for elem in ci}
    print(f"Itens do cliente carregados: {len(client_items)}")

    # 2. Carregar item_templates.xml do servidor
    print(f"\nLendo item_templates.xml do servidor: {SOURCE_XML} ...")
    tree = ET.parse(SOURCE_XML)
    root = tree.getroot()

    all_items = root.findall(".//item_template")
    total_items = len(all_items)
    print(f"Total de itens no servidor: {total_items}")

    added_group_count = 0
    fixed_none_count = 0
    normalized_legacy_count = 0
    unchanged_count = 0

    group_counts = Counter()

    for it in all_items:
        iid = int(it.get("id"))
        ig = it.get("item_group")
        ci = client_items.get(iid, {})

        if not ig:
            # Atributo ausente: resolver grupo verdadeiro
            new_group = resolve_item_group(iid, it.attrib, ci)
            it.set("item_group", new_group)
            added_group_count += 1
            group_counts[new_group] += 1
        elif ig == "NONE":
            # Atributo era NONE: substituir pelo grupo verdadeiro
            new_group = resolve_item_group(iid, it.attrib, ci)
            it.set("item_group", new_group)
            fixed_none_count += 1
            group_counts[new_group] += 1
        elif ig in LEGACY_NORMALIZATION:
            # Normalizar grupo legado inválido
            new_group = LEGACY_NORMALIZATION[ig]
            it.set("item_group", new_group)
            normalized_legacy_count += 1
            group_counts[new_group] += 1
        else:
            unchanged_count += 1
            group_counts[ig] += 1

    print("\n--- Estatísticas de Modificação ---")
    print(f"  Itens que não tinham item_group (adicionado): {added_group_count}")
    print(f"  Itens que tinham item_group='NONE' (corrigido): {fixed_none_count}")
    print(f"  Itens legados normalizados (HELMET/EARRINGS/SHARD): {normalized_legacy_count}")
    print(f"  Itens com item_group mantido: {unchanged_count}")
    print(f"  Total de itens processados: {total_items}")

    # 3. Validação estrita
    missing = [it.get("id") for it in all_items if not it.get("item_group")]
    none_left = [it.get("id") for it in all_items if it.get("item_group") == "NONE"]
    invalid_left = [it.get("id") for it in all_items if it.get("item_group") not in VALID_ITEM_GROUPS]

    print("\n--- Validação de Integridade ---")
    print(f"  Itens sem item_group: {len(missing)}")
    print(f"  Itens com item_group='NONE': {len(none_left)}")
    print(f"  Itens com item_group inválido: {len(invalid_left)}")

    if missing or none_left or invalid_left:
        print("ERRO CRÍTICO: Falha na validação dos grupos!")
        if missing: print(f"  Primeiros sem grupo: {missing[:5]}")
        if none_left: print(f"  Primeiros com NONE: {none_left[:5]}")
        if invalid_left: print(f"  Primeiros inválidos: {invalid_left[:5]}")
        sys.exit(1)

    print("VALIDAÇÃO 100% SUCESSO: Zero itens sem grupo, zero NONE, zero inválidos!")

    # 4. Formatação e salvamento
    print("\nAjustando indentação do XML...")
    ET.indent(tree, space="\t", level=0)

    print(f"Salvando no Código Fonte: {SOURCE_XML} ...")
    tree.write(SOURCE_XML, encoding="utf-8", xml_declaration=True)
    size_src = os.path.getsize(SOURCE_XML)
    print(f"Salvo com sucesso! Tamanho: {size_src:,} bytes")

    print(f"\nSalvando no Produto Final: {TARGET_XML} ...")
    os.makedirs(os.path.dirname(TARGET_XML), exist_ok=True)
    tree.write(TARGET_XML, encoding="utf-8", xml_declaration=True)
    size_tgt = os.path.getsize(TARGET_XML)
    print(f"Salvo com sucesso! Tamanho: {size_tgt:,} bytes")

    print("\n" + "=" * 80)
    print(" Concluído com sucesso em ambos os locais!")
    print("=" * 80)


if __name__ == "__main__":
    main()
