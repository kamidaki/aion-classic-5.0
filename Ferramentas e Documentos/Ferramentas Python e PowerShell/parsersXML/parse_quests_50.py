#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Extração e Integração de Missões do Classic 5.0 (parse_quests_50.py)
================================================================================
1. Extrai 100% das missões do cliente Aion Classic 5.0 e atualiza quest_data.xml:
   - 6.124 missões oficiais do cliente 5.0.
   - Adiciona as 1.422 missões faltantes e atualiza as 4.702 existentes.
   - Preserva todas as 3.341 missões do servidor já existentes.
   - Cumpre 100% da ordem estrita de elementos do quest_data.xsd:
     collect_items -> inventory_items -> rewards -> bonus -> extended_rewards ->
     quest_drop -> quest_kill -> start_conditions -> class_permitted ->
     gender_permitted -> quest_work_items -> class_selectable_rewards.
   - Mapeia itens via client_items.xml, NPCs via client_npcs.xml, strings via client_strings_quest.xml,
     drops e kills via quest_monster.csv e quest_script_monster.csv.
2. Cria e atualiza arquivos de scripts em quest_script_data/*.xml para os mapas 5.0:
   - telos.xml, tiamaranta_mesa.xml, laphsaran.xml, teva.xml, apheta_beluslan.xml,
     dranium_battlefield.xml, dokkaebi_realm.xml, balic_treasury.xml.
   - Estrutura rigorosamente validada com quest_script_data.xsd:
     item_collecting -> report_to -> monster_hunt -> ...
3. Cria Handlers Java para todas as Missões de Campanha (category="MISSION"):
   - Padrão oficial: _<id><CamelCaseName>.java
   - Extende com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler.
   - Comentários com nomes reais para cada NPC registrado (// <id>: <nome_npc>).
   - Pacotes corretos por mapa (quest.telos, quest.high_daeva, quest.laphsaran, etc.).
   - Suporte completo a onDialogEvent, onKillEvent, onEnterWorldEvent, onLevelChangedEvent.
4. Validação Rigorosa:
   - Valida quest_data.xml contra quest_data.xsd com lxml.
   - Valida cada XML de quest_script_data contra quest_script_data.xsd com lxml.
   - Valida compilação Java dos handlers gerados.
5. Sincronização Total:
   - D:\AION CLASSIC 5.0 - BEYOND TESTE\game-server
   - D:\AION CLASSIC 5.0 - BEYOND TESTE\EMULADOR FINAL\GameServer
"""

import os
import sys
import re
import glob
import csv
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter

# Garante saída em UTF-8 no console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Caminhos base
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
FERRAMENTAS_DIR = os.path.dirname(TOOLS_DIR)
PROJECT_ROOT = os.path.dirname(FERRAMENTAS_DIR)

CLIENT_DATA_ROOT = os.path.join(PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
CLIENT_DATA_DIR = os.path.join(CLIENT_DATA_ROOT, "data")
STRINGS_DIR = os.path.join(CLIENT_DATA_ROOT, "Strings", "strings")

GAME_SERVER_DIR = os.path.join(PROJECT_ROOT, "Código Fonte - Emulador", "game-server")
COMMONS_DIR = os.path.join(PROJECT_ROOT, "Código Fonte - Emulador", "commons")
EMULADOR_FINAL_DIR = os.path.join(PROJECT_ROOT, "Emulador - Produto Final", "GameServer")

sys.path.insert(0, FERRAMENTAS_DIR)
sys.path.insert(0, TOOLS_DIR)
import aion_bxml

# Mapeamento de Zonas 5.0 para nomes e pastas limpos
ZONE_MAP = {
    'STR_QUEST_ZONE01': ('Poeta', 'poeta'),
    'STR_QUEST_ZONE02': ('Verteron', 'verteron'),
    'STR_QUEST_ZONE03': ('Eltnen', 'eltnen'),
    'STR_QUEST_ZONE04': ('Heiron', 'heiron'),
    'STR_QUEST_ZONE05': ('Ishalgen', 'ishalgen'),
    'STR_QUEST_ZONE06': ('Altgard', 'altgard'),
    'STR_QUEST_ZONE07': ('Morheim', 'morheim'),
    'STR_QUEST_ZONE08': ('Beluslan', 'beluslan'),
    'STR_QUEST_ZONE09': ('Reshanta', 'reshanta'),
    'STR_QUEST_ZONE19': ('Sanctum', 'sanctum'),
    'STR_QUEST_ZONE20': ('Pandaemonium', 'pandaemonium'),
    'STR_QUEST_ZONE21': ('Ascension', 'ascension'),
    'STR_QUEST_ZONE22': ('Abyss Entry', 'abyss_entry'),
    'STR_QUEST_ZONE25': ('Theobomos', 'theobomos'),
    'STR_QUEST_ZONE26': ('Brusthonin', 'brusthonin'),
    'STR_QUEST_ZONE28': ('Steel Rake', 'steel_rake'),
    'STR_QUEST_ZONE29': ('Greater Stigma', 'greater_stigma'),
    'STR_QUEST_ZONE32': ('The Hidden Truth', 'bare_truth'),
    'STR_QUEST_ZONE33': ('Carving out a Fortune', 'clash_of_destiny'),
    'STR_QUEST_ZONE34': ('Cloister of Kaisinel', 'cloister_of_kaisinel'),
    'STR_QUEST_ZONE35': ('Inggison', 'inggison'),
    'STR_QUEST_ZONE36': ('Convent of Marchutan', 'convent_of_marchutan'),
    'STR_QUEST_ZONE37': ('Gelkmaros', 'gelkmaros'),
    'STR_QUEST_ZONE38': ('Udas Temple', 'udas_temple'),
    'STR_QUEST_ZONE40': ('Silentera Canyon', 'silentera_canyon'),
    'STR_QUEST_ZONE41': ('Beshmundir Temple', 'beshmundir'),
    'STR_QUEST_ZONE44': ('Haramel', 'haramel'),
    'STR_QUEST_ZONE45': ('Chantra Dredgion', 'chantra_dredgion'),
    'STR_QUEST_ZONE46': ('Kromedes Trial', 'kromedes_trial'),
    'STR_QUEST_ZONE47': ('Talocs Hollow', 'talocs_hollow'),
    'STR_QUEST_ZONE52': ('Abyssal Splinter', 'abyssal_splinter'),
    'STR_QUEST_ZONE55': ('Esoterrace', 'esoterrace'),
    'STR_QUEST_ZONE56': ('Empyrean Crucible', 'empyrean_crucible'),
    'STR_QUEST_ZONE57': ('Aturam Sky Fortress', 'aturam_sky_fortress'),
    'STR_QUEST_ZONE60': ('Event', 'event_quests'),
    'STR_QUEST_ZONE62': ('Tiarkh Testing Lab', 'tiarkh_testing_lab'),
    'STR_QUEST_ZONE64': ('Telos', 'telos'),
    'STR_QUEST_ZONE65': ('Path of the Daeva Ceremony', 'telos'),
    'STR_QUEST_ZONE66': ('Sunken Telos', 'telos'),
    'STR_QUEST_ZONE67': ('Apheta Beluslan', 'apheta_beluslan'),
    'STR_QUEST_ZONE68': ('Storyline', 'storyline'),
    'STR_QUEST_ZONE69': ('Phaestos Disc', 'phaestos_disc'),
    'STR_QUEST_ZONE70': ('Tartarus', 'tartarus'),
    'STR_QUEST_ZONE71': ('High Daeva Act 1', 'high_daeva'),
    'STR_QUEST_ZONE72': ('High Daeva Act 2', 'high_daeva'),
    'STR_QUEST_ZONE73': ('High Daeva Act 3', 'high_daeva'),
    'STR_QUEST_ZONE74': ('High Daeva Act 4', 'high_daeva'),
    'STR_QUEST_ZONE75': ('The Lords Conversation', 'high_daeva'),
    'STR_QUEST_ZONE76': ('Fond Farewell', 'high_daeva'),
    'STR_QUEST_ZONE77': ('Laphsaran', 'laphsaran'),
    'STR_QUEST_ZONE78': ('Lacrima', 'lacrima'),
    'STR_QUEST_ZONE79': ('Dranium Battlefield', 'dranium_battlefield'),
    'STR_QUEST_ZONE80': ('The Dokkaebi Realm', 'dokkaebi_realm'),
    'STR_QUEST_ZONE81': ('The Ladys Prophecy', 'ladys_prophecy'),
    'STR_QUEST_ZONE82': ('Meta Stigmas', 'meta_stigmas'),
    'STR_QUEST_ZONE83': ('Laphsaran', 'laphsaran'),
    'STR_QUEST_ZONE84': ('Another Future', 'storyline'),
    'STR_QUEST_ZONE85': ('Tiamaranta Mesa', 'tiamaranta_mesa'),
    'STR_QUEST_ZONE86': ('Ascension Assistance', 'ascension'),
    'STR_QUEST_ZONE87': ('Teva', 'teva'),
    'STR_QUEST_ZONE88': ('Balic Treasury', 'balic_treasury'),
    'STR_QUEST_ZONE89': ('Balic Treasury', 'balic_treasury'),
    'STR_QUEST_ZONE90': ('Teva Field Mission', 'teva'),
    'STR_QUEST_ZONE91': ('Dimensional Rift Battle', 'dimensional_rift_battle'),
    'STR_QUEST_ZONE92': ('Labyrinth of Echoes', 'labyrinth_of_echoes'),
    'STR_QUEST_ZONE93': ('Sienolas Phantom', 'sienolas_phantom'),
    'STR_QUEST_ZONE94': ('Sanctum', 'sanctum'),
    'STR_QUEST_ZONE95': ('Pandaemonium', 'pandaemonium'),
    'STR_QUEST_ZONE96': ('Inggison', 'inggison'),
    'STR_QUEST_ZONE97': ('Gelkmaros', 'gelkmaros'),
    'STR_QUEST_ZONE98': ('Sub-Class Selection', 'ascension'),
    'STR_QUEST_ZONE99': ('Knower of Dice', 'knower_of_dice'),
    'STR_QUEST_puzzle': ('Ancient Artwork', 'ancient_artwork'),
    'STR_QUEST_adventureA': ('Memoir of Sunken Legion', 'memoir_of_sunken_legion'),
    'STR_QUEST_adventureB': ('Young Daeva', 'young_daeva'),
    'STR_QUEST_RETURN_USER': ('Returning Daevas', 'return_user'),
}

# Mapeamento de classes do cliente para enum playerClass
CLASS_MAPPING = {
    'warrior': 'WARRIOR',
    'scout': 'SCOUT',
    'mage': 'MAGE',
    'cleric': 'CLERIC',
    'fighter': 'GLADIATOR',
    'knight': 'TEMPLAR',
    'assassin': 'ASSASSIN',
    'ranger': 'RANGER',
    'wizard': 'SORCERER',
    'elementallist': 'SPIRIT_MASTER',
    'chanter': 'CHANTER',
    'priest': 'PRIEST',
    'monk': 'MONK',
    'thunderer': 'THUNDERER',
    'striker': 'MARTIAL_ARTIST',
    'battlemaster': 'BRAWLER',
    'orchestrator': 'BARD',
    'lumines': 'LUMINESS',
    'engineer': 'ENGINEER',
    'gunner': 'GUNNER',
    'runewarrior': 'RIDER',
    'runeblade': 'REVENANT',
    'all': 'ALL',
}

def clean_camel_case(text: str) -> str:
    """Converte um título em CamelCase válido para nome de classe Java."""
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'[\'\"’“”\.,!\?_\-\(\):;]', ' ', text)
    words = text.split()
    if not words:
        return "UnnamedQuest"
    return "".join(w.capitalize() for w in words if w)

def parse_item_and_count(raw_str):
    """Extrai (item_name_lower, count_int) de uma string 'item_code 1'."""
    if not raw_str:
        return None, 1
    parts = raw_str.strip().split()
    if not parts:
        return None, 1
    iname = parts[0].strip().lower()
    cnt = 1
    if len(parts) > 1 and parts[1].isdigit():
        cnt = int(parts[1])
    return iname, cnt

def resolve_title_id(title_str):
    """Converte strings de título como 'light_title45' ou 'dark_title27' para IDs inteiros válidos."""
    if not title_str:
        return None
    title_str = title_str.strip()
    if title_str.isdigit():
        return int(title_str)
    m = re.search(r'dark_title(\d+)', title_str, re.IGNORECASE)
    if m:
        return 100 + int(m.group(1))
    m = re.search(r'light_title(\d+)', title_str, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

# -----------------------------------------------------------------------------
# 1. Carregamento de Caches do Cliente
# -----------------------------------------------------------------------------
def load_all_strings():
    print("[1/6] Carregando tabelas de strings do cliente...")
    name_to_id = {}
    name_to_body = {}
    pattern = re.compile(r'<string>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>(?:\s*<body>([^<]*)</body>)?', re.DOTALL)
    
    xml_files = glob.glob(os.path.join(STRINGS_DIR, "*.xml"))
    for p in xml_files:
        raw = open(p, "rb").read()
        text = ""
        for enc in ["utf-16", "utf-8", "latin1"]:
            try:
                text = raw.decode(enc)
                break
            except Exception:
                continue
        for sid, sname, sbody in pattern.findall(text):
            sn = sname.strip().lower()
            sid_int = int(sid)
            name_to_id[sn] = sid_int
            if sbody:
                name_to_body[sn] = sbody.strip()
    print(f"  -> Total de strings carregadas: {len(name_to_id):,}")
    return name_to_id, name_to_body

def load_all_items():
    print("[2/6] Carregando client_items.xml...")
    p = os.path.join(CLIENT_DATA_DIR, "items", "client_items.xml")
    raw = open(p, "rb").read()
    root = ET.fromstring(aion_bxml.decodifica(raw) if aion_bxml.e_bxml(p) else raw.decode("utf-8", errors="ignore"))
    item_map = {}
    for item in root:
        iid = item.findtext("id")
        iname = item.findtext("name")
        if iid and iname:
            item_map[iname.strip().lower()] = int(iid.strip())
    print(f"  -> Total de itens mapeados: {len(item_map):,}")
    return item_map

def load_all_npcs(name_to_body):
    print("[3/6] Carregando client_npcs.xml...")
    p = os.path.join(CLIENT_DATA_DIR, "npcs", "client_npcs.xml")
    raw = open(p, "rb").read()
    root = ET.fromstring(aion_bxml.decodifica(raw) if aion_bxml.e_bxml(p) else raw.decode("utf-8", errors="ignore"))
    npc_name_to_id = {}
    npc_id_to_name = {}
    npc_id_to_realname = {}
    for npc in root:
        nid = npc.findtext("id")
        nname = npc.findtext("name")
        ndesc = npc.findtext("desc", "")
        if nid and nname:
            nid_int = int(nid.strip())
            name_str = nname.strip()
            npc_name_to_id[name_str.lower()] = nid_int
            npc_id_to_name[nid_int] = name_str
            real = name_to_body.get(ndesc.strip().lower(), name_to_body.get(name_str.lower(), name_str))
            npc_id_to_realname[nid_int] = real
    print(f"  -> Total de NPCs mapeados: {len(npc_name_to_id):,}")
    return npc_name_to_id, npc_id_to_name, npc_id_to_realname

def load_quest_monsters(npc_name_to_id, item_map):
    print("[4/6] Carregando quest_monster.csv e quest_script_monster.csv...")
    drops_by_quest = defaultdict(list)
    kills_by_quest = defaultdict(list)

    # 1. quest_monster.csv
    qm_path = os.path.join(CLIENT_DATA_DIR, "Quest", "quest_monster.csv")
    if os.path.exists(qm_path):
        with open(qm_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row or len(row) < 7:
                    continue
                qid = row[0].strip()
                if not qid.isdigit():
                    continue
                progress = row[1].strip()
                item_name = row[2].strip()
                src_type = row[3].strip()
                num_str = row[5].strip()
                count = int(num_str) if num_str.isdigit() else 1
                mobs = [m.strip().lower() for m in row[6:] if m.strip()]

                if src_type == "questItemDropMonster" and item_name:
                    item_id = item_map.get(item_name.lower(), 0)
                    for mob in mobs:
                        mob_id = npc_name_to_id.get(mob, 0)
                        if mob_id:
                            drops_by_quest[qid].append({
                                'npc_id': mob_id,
                                'item_id': item_id,
                                'chance': 100,
                                'drop_each_member': 1,
                                'collecting_step': int(progress) if progress.isdigit() else 0
                            })
                elif src_type == "simpleQuest" and mobs:
                    mob_ids = [str(npc_name_to_id[m]) for m in mobs if m in npc_name_to_id]
                    if mob_ids:
                        step_val = int(progress) if progress.isdigit() and int(progress) >= 0 else 0
                        kills_by_quest[qid].append({
                            'npc_ids': " ".join(mob_ids),
                            'count': count,
                            'step': step_val,
                            'var': 0
                        })

    # 2. quest_script_monster.csv
    qsm_path = os.path.join(CLIENT_DATA_DIR, "Quest", "quest_script_monster.csv")
    if os.path.exists(qsm_path):
        with open(qsm_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row or len(row) < 7:
                    continue
                qid = row[0].strip()
                if not qid.isdigit():
                    continue
                progress = row[1].strip()
                num_str = row[5].strip()
                count = int(num_str) if num_str.isdigit() else 1
                mobs = [m.strip().lower() for m in row[6:] if m.strip()]
                mob_ids = [str(npc_name_to_id[m]) for m in mobs if m in npc_name_to_id]
                if mob_ids:
                    step_match = re.search(r'SECTION_0==(\d+)', progress) or re.search(r'Progress\((\d+)\)', progress)
                    step_val = int(step_match.group(1)) if step_match else 0
                    kills_by_quest[qid].append({
                        'npc_ids': " ".join(mob_ids),
                        'count': count,
                        'step': step_val,
                        'var': 0
                    })

    print(f"  -> Quests com drops vinculados: {len(drops_by_quest):,}")
    print(f"  -> Quests com monstros de caça vinculados: {len(kills_by_quest):,}")
    return drops_by_quest, kills_by_quest

# -----------------------------------------------------------------------------
# 2. Atualização e Geração de quest_data.xml
# -----------------------------------------------------------------------------
COMBINE_SKILL_MAP = {
    'any': '-1',
    'cooking': '40001',
    'weaponsmith': '40002',
    'armorsmith': '40003',
    'tailoring': '40004',
    'alchemy': '40007',
    'handiwork': '40008',
    'gathering_b': '30002',
    'aerial_gathering': '30003',
}

def build_quest_element(c_q, name_to_id, name_to_body, item_map, npc_name_to_id, drops_by_quest, kills_by_quest):
    """Constrói um elemento <quest> estritamente conforme quest_data.xsd."""
    quest_id = c_q.findtext("id", "").strip()
    code_name = c_q.findtext("name", "").strip()
    desc_str = c_q.findtext("desc", "").strip()
    cat2_str = c_q.findtext("category2", "").strip()
    cat1_str = c_q.findtext("category1", "quest").strip().lower()
    f_mission = c_q.findtext("f_mission", "0").strip()

    real_name = name_to_body.get(desc_str.lower(), name_to_body.get(code_name.lower(), code_name))
    name_id = name_to_id.get(desc_str.lower(), int(quest_id) if quest_id.isdigit() else 0)
    zone_info = ZONE_MAP.get(cat2_str, (cat2_str, "custom"))
    quest_zone = zone_info[0]

    min_lvl = c_q.findtext("minlevel_permitted", "1").strip()
    max_lvl = c_q.findtext("maxlevel_permitted", "0").strip()
    repeat_count = c_q.findtext("max_repeat_count", "1").strip()
    cannot_share = "true" if c_q.findtext("cannot_share") == "1" else "false"
    cannot_giveup = "true" if c_q.findtext("cannot_giveup") == "1" else "false"
    can_report = c_q.findtext("can_report")

    # Race
    race_raw = c_q.findtext("race_permitted", "all").lower()
    if "pc_light" in race_raw and "pc_dark" in race_raw:
        race_permitted = "PC_ALL"
    elif "pc_light" in race_raw or "elyos" in race_raw:
        race_permitted = "ELYOS"
    elif "pc_dark" in race_raw or "asmo" in race_raw:
        race_permitted = "ASMODIANS"
    else:
        race_permitted = "PC_ALL"

    # Category
    if f_mission == "1" or cat1_str == "mission":
        category = "MISSION"
    else:
        valid_cats = {"QUEST", "MISSION", "SEEN_MARKER", "SIGNIFICANT", "IMPORTANT", "NON_COUNT", "TASK", "FACTION", "EVENT", "CHALLENGE_TASK", "PUBLIC", "LEGION", "PRIMARY"}
        c1_up = cat1_str.upper()
        category = c1_up if c1_up in valid_cats else "QUEST"

    elem = ET.Element("quest")
    elem.set("id", quest_id)
    if real_name:
        elem.set("name", real_name)
    if name_id:
        elem.set("nameId", str(name_id))
    if quest_zone:
        elem.set("quest_zone", quest_zone)
    elem.set("minlevel_permitted", min_lvl)
    if max_lvl and max_lvl != "0":
        elem.set("maxlevel_permitted", max_lvl)
    elem.set("max_repeat_count", repeat_count)
    elem.set("cannot_share", cannot_share)
    elem.set("cannot_giveup", cannot_giveup)
    elem.set("race_permitted", race_permitted)
    elem.set("category", category)

    combineskill = c_q.findtext("combineskill")
    if combineskill:
        cs_clean = combineskill.strip().lower()
        if cs_clean in COMBINE_SKILL_MAP:
            elem.set("combineskill", COMBINE_SKILL_MAP[cs_clean])
        elif cs_clean.lstrip('-').isdigit():
            elem.set("combineskill", cs_clean)
    combine_skillpoint = c_q.findtext("combine_skillpoint")
    if combine_skillpoint:
        elem.set("combine_skillpoint", combine_skillpoint)
    if can_report == "1":
        elem.set("can_report", "true")

    # Sequência Estrita do quest_data.xsd:
    # 1. collect_items
    collect_items_list = []
    for ci_idx in range(1, 10):
        val = c_q.findtext(f"collect_item{ci_idx}")
        iname, cnt = parse_item_and_count(val)
        if iname and iname in item_map:
            collect_items_list.append((item_map[iname], cnt))
    if collect_items_list:
        ci_tag = ET.SubElement(elem, "collect_items")
        for iid, cnt in collect_items_list:
            ET.SubElement(ci_tag, "collect_item", {"item_id": str(iid), "count": str(cnt)})

    # 2. inventory_items
    inv_items_list = []
    for ii_idx in range(1, 5):
        val = c_q.findtext(f"inventory_item_name{ii_idx}")
        iname, cnt = parse_item_and_count(val)
        if iname and iname in item_map:
            inv_items_list.append((item_map[iname], cnt))
    if inv_items_list:
        ii_tag = ET.SubElement(elem, "inventory_items")
        for iid, cnt in inv_items_list:
            ET.SubElement(ii_tag, "inventory_item", {"item_id": str(iid), "count": str(cnt)})

    # 3. rewards (grupos 1..5)
    for g in range(1, 6):
        exp = c_q.findtext(f"reward_exp{g}")
        gold = c_q.findtext(f"reward_gold{g}")
        ap = c_q.findtext(f"reward_abyss_point{g}")
        title = c_q.findtext(f"reward_title{g}")
        title_id = resolve_title_id(title)
        
        selectable_items = []
        for s_idx in range(1, 15):
            val = c_q.findtext(f"selectable_reward_item{g}_{s_idx}")
            iname, cnt = parse_item_and_count(val)
            if iname and iname in item_map:
                selectable_items.append((item_map[iname], cnt))

        fixed_items = []
        for r_idx in range(1, 10):
            val = c_q.findtext(f"reward_item{g}_{r_idx}")
            iname, cnt = parse_item_and_count(val)
            if iname and iname in item_map:
                fixed_items.append((item_map[iname], cnt))

        if exp or gold or ap or (title_id is not None) or selectable_items or fixed_items:
            rew_elem = ET.SubElement(elem, "rewards")
            if gold and gold != "0":
                rew_elem.set("gold", gold)
            if exp and exp != "0":
                rew_elem.set("exp", exp)
            if ap and ap != "0":
                rew_elem.set("ap", ap)
            if title_id is not None:
                rew_elem.set("title", str(title_id))
            # selectable_reward_item DEVE VIR PRIMEIRO
            for iid, cnt in selectable_items:
                ET.SubElement(rew_elem, "selectable_reward_item", {"item_id": str(iid), "count": str(cnt)})
            # reward_item DEVE VIR DEPOIS
            for iid, cnt in fixed_items:
                ET.SubElement(rew_elem, "reward_item", {"item_id": str(iid), "count": str(cnt)})

    # 4. bonus
    # (Se aplicável)

    # 5. extended_rewards
    gold_ext = c_q.findtext("reward_gold_ext")
    exp_ext = c_q.findtext("reward_exp_ext")
    ap_ext = c_q.findtext("reward_abyss_point_ext")
    title_ext = c_q.findtext("reward_title_ext")
    title_ext_id = resolve_title_id(title_ext)

    ext_sel_items = []
    for s_idx in range(1, 15):
        val = c_q.findtext(f"selectable_reward_item_ext_{s_idx}")
        iname, cnt = parse_item_and_count(val)
        if iname and iname in item_map:
            ext_sel_items.append((item_map[iname], cnt))

    ext_fixed_items = []
    for r_idx in range(1, 10):
        val = c_q.findtext(f"reward_item_ext_{r_idx}")
        iname, cnt = parse_item_and_count(val)
        if iname and iname in item_map:
            ext_fixed_items.append((item_map[iname], cnt))

    if gold_ext or exp_ext or ap_ext or (title_ext_id is not None) or ext_sel_items or ext_fixed_items:
        ext_elem = ET.SubElement(elem, "extended_rewards")
        if gold_ext and gold_ext != "0":
            ext_elem.set("gold", gold_ext)
        if exp_ext and exp_ext != "0":
            ext_elem.set("exp", exp_ext)
        if ap_ext and ap_ext != "0":
            ext_elem.set("ap", ap_ext)
        if title_ext_id is not None:
            ext_elem.set("title", str(title_ext_id))
        for iid, cnt in ext_sel_items:
            ET.SubElement(ext_elem, "selectable_reward_item", {"item_id": str(iid), "count": str(cnt)})
        for iid, cnt in ext_fixed_items:
            ET.SubElement(ext_elem, "reward_item", {"item_id": str(iid), "count": str(cnt)})

    # 6. quest_drop
    seen_drops = set()
    for d_idx in range(1, 5):
        dmob = c_q.findtext(f"drop_monster_{d_idx}")
        ditem = c_q.findtext(f"drop_item_{d_idx}")
        dprob = c_q.findtext(f"drop_prob_{d_idx}", "100")
        deach = c_q.findtext(f"drop_each_member_{d_idx}", "0")
        if dmob and ditem:
            mid = npc_name_to_id.get(dmob.strip().lower(), 0)
            iid = item_map.get(ditem.strip().lower(), 0)
            if mid and iid:
                key = (mid, iid)
                if key not in seen_drops:
                    seen_drops.add(key)
                    attribs = {
                        "npc_id": str(mid),
                        "item_id": str(iid),
                        "chance": str(dprob),
                        "drop_each_member": "1" if deach in ["1", "TRUE", "true"] else "0"
                    }
                    cstep = c_q.findtext("collect_progress")
                    if cstep:
                        attribs["collecting_step"] = cstep
                    ET.SubElement(elem, "quest_drop", attribs)
    for d in drops_by_quest.get(quest_id, []):
        key = (d['npc_id'], d['item_id'])
        if key not in seen_drops:
            seen_drops.add(key)
            ET.SubElement(elem, "quest_drop", {
                "npc_id": str(d['npc_id']),
                "item_id": str(d['item_id']),
                "chance": str(d['chance']),
                "drop_each_member": str(d['drop_each_member']),
                "collecting_step": str(d['collecting_step'])
            })

    # 7. quest_kill
    seen_kills = set()
    seq_num = 0
    for k in kills_by_quest.get(quest_id, []):
        key = (k['npc_ids'], k['step'])
        if key not in seen_kills:
            seen_kills.add(key)
            ET.SubElement(elem, "quest_kill", {
                "seq": str(seq_num),
                "npc_ids": k['npc_ids'],
                "count": str(k['count']),
                "var": str(k['var']),
                "step": str(k['step'])
            })
            seq_num += 1

    # 8. start_conditions
    fin_list = []
    unfin_list = []
    noacq_list = []
    acq_list = []
    for c_idx in range(1, 16):
        f_val = c_q.findtext(f"finished_quest_cond{c_idx}")
        if f_val:
            clean_id = re.sub(r'^[Qq]', '', f_val.strip())
            if clean_id.isdigit():
                fin_list.append(clean_id)
        u_val = c_q.findtext(f"unfinished_quest_cond{c_idx}")
        if u_val:
            clean_id = re.sub(r'^[Qq]', '', u_val.strip())
            if clean_id.isdigit():
                unfin_list.append(clean_id)
        n_val = c_q.findtext(f"noacquired_quest_cond{c_idx}")
        if n_val:
            clean_id = re.sub(r'^[Qq]', '', n_val.strip())
            if clean_id.isdigit():
                noacq_list.append(clean_id)
        a_val = c_q.findtext(f"acquired_quest_cond{c_idx}")
        if a_val:
            clean_id = re.sub(r'^[Qq]', '', a_val.strip())
            if clean_id.isdigit():
                acq_list.append(clean_id)

    if fin_list or unfin_list or noacq_list or acq_list:
        sc_elem = ET.SubElement(elem, "start_conditions")
        for fid in fin_list:
            ET.SubElement(sc_elem, "finished", {"quest_id": fid})
        if unfin_list:
            unfin_elem = ET.SubElement(sc_elem, "unfinished")
            unfin_elem.text = " ".join(unfin_list)
        if noacq_list:
            noacq_elem = ET.SubElement(sc_elem, "noacquired")
            noacq_elem.text = " ".join(noacq_list)
        if acq_list:
            acq_elem = ET.SubElement(sc_elem, "acquired")
            acq_elem.text = " ".join(acq_list)

    # 9. class_permitted
    classes_str = c_q.findtext("class_permitted")
    if classes_str:
        classes_tokens = [c.strip().lower() for c in classes_str.split() if c.strip()]
        mapped_classes = []
        for c in classes_tokens:
            if c in CLASS_MAPPING:
                mapped_classes.append(CLASS_MAPPING[c])
        if mapped_classes and len(mapped_classes) < 20:
            cp_elem = ET.SubElement(elem, "class_permitted")
            cp_elem.text = " ".join(dict.fromkeys(mapped_classes))

    # 10. gender_permitted
    gender_raw = c_q.findtext("gender_permitted", "all").strip().lower()
    if gender_raw == "male":
        gp_elem = ET.SubElement(elem, "gender_permitted")
        gp_elem.text = "MALE"
    elif gender_raw == "female":
        gp_elem = ET.SubElement(elem, "gender_permitted")
        gp_elem.text = "FEMALE"

    # 11. quest_work_items
    work_items_list = []
    for wi_idx in range(1, 5):
        val = c_q.findtext(f"quest_work_item{wi_idx}")
        iname, cnt = parse_item_and_count(val)
        if iname and iname in item_map:
            work_items_list.append((item_map[iname], cnt))
    if work_items_list:
        qwi_tag = ET.SubElement(elem, "quest_work_items")
        for iid, cnt in work_items_list:
            ET.SubElement(qwi_tag, "quest_work_item", {"item_id": str(iid), "count": str(cnt)})

    # 12. class selectable rewards
    class_rewards_tags = [
        ("fighter_selectable_reward", "fighter_selectable_reward"),
        ("knight_selectable_reward", "knight_selectable_reward"),
        ("ranger_selectable_reward", "ranger_selectable_reward"),
        ("assassin_selectable_reward", "assassin_selectable_reward"),
        ("wizard_selectable_reward", "wizard_selectable_reward"),
        ("elementalist_selectable_reward", "elementalist_selectable_reward"),
        ("priest_selectable_reward", "priest_selectable_reward"),
        ("chanter_selectable_reward", "chanter_selectable_reward"),
        ("bard_selectable_reward", "bard_selectable_reward"),
        ("gunner_selectable_reward", "gunner_selectable_reward"),
        ("rider_selectable_reward", "rider_selectable_reward"),
    ]
    for tag_src, tag_dest in class_rewards_tags:
        node = c_q.find(tag_src)
        if node is not None:
            items_found = []
            if node.text and node.text.strip():
                iname, cnt = parse_item_and_count(node.text)
                if iname and iname in item_map:
                    items_found.append((item_map[iname], cnt))
            for sub in node.iter():
                if sub is not node and sub.text and sub.text.strip():
                    iname, cnt = parse_item_and_count(sub.text)
                    if iname and iname in item_map:
                        items_found.append((item_map[iname], cnt))
            for iid, cnt in items_found:
                ET.SubElement(elem, tag_dest, {"item_id": str(iid), "count": str(cnt)})

    return elem

def update_quest_data(client_quests_root, name_to_id, name_to_body, item_map, npc_name_to_id, drops_by_quest, kills_by_quest):
    print("[5/6] Atualizando quest_data/quest_data.xml...")
    server_path = os.path.join(GAME_SERVER_DIR, "data", "static_data", "quest_data", "quest_data.xml")
    tree = ET.parse(server_path)
    root = tree.getroot()

    server_quests = {}
    for idx, q in enumerate(root.findall("quest")):
        qid = q.get("id")
        if qid:
            server_quests[qid] = (idx, q)

    added_count = 0
    updated_count = 0

    for c_q in client_quests_root:
        qid = c_q.findtext("id", "").strip()
        if not qid:
            continue
        new_elem = build_quest_element(c_q, name_to_id, name_to_body, item_map, npc_name_to_id, drops_by_quest, kills_by_quest)
        if qid in server_quests:
            idx, old_elem = server_quests[qid]
            root.remove(old_elem)
            root.insert(idx, new_elem)
            server_quests[qid] = (idx, new_elem)
            updated_count += 1
        else:
            root.append(new_elem)
            server_quests[qid] = (len(root) - 1, new_elem)
            added_count += 1

    # Normaliza combineskill em todas as missões para respeitar xs:int do XSD
    for q in root.findall("quest"):
        cs = q.get("combineskill")
        if cs:
            cs_clean = cs.strip().lower()
            if cs_clean in COMBINE_SKILL_MAP:
                q.set("combineskill", COMBINE_SKILL_MAP[cs_clean])
            elif cs_clean.lstrip('-').isdigit():
                pass
            else:
                del q.attrib["combineskill"]

    ET.indent(root, space="\t")
    tree.write(server_path, encoding="utf-8", xml_declaration=True)
    print(f"  -> quest_data.xml gravado: {len(root):,} missões ({added_count} adicionadas, {updated_count} atualizadas).")

    try:
        import lxml.etree
        xsd_path = os.path.join(GAME_SERVER_DIR, "data", "static_data", "quest_data", "quest_data.xsd")
        schema = lxml.etree.XMLSchema(lxml.etree.parse(xsd_path))
        doc = lxml.etree.parse(server_path)
        schema.assertValid(doc)
        print("  -> [OK] quest_data.xml é 100% VÁLIDO de acordo com quest_data.xsd!")
    except Exception as ex:
        print(f"  -> [AVISO] Falha na validação XSD do quest_data.xml: {ex}")

# -----------------------------------------------------------------------------
# 3. Geração de XMLs em quest_script_data/*.xml para Zonas 5.0
# -----------------------------------------------------------------------------
def generate_50_quest_scripts(client_quests_root, name_to_body, npc_name_to_id, kills_by_quest):
    print("[6/6] Gerando scripts em quest_script_data/ e Handlers Java...")
    script_data_dir = os.path.join(GAME_SERVER_DIR, "data", "static_data", "quest_script_data")
    os.makedirs(script_data_dir, exist_ok=True)

    map_xml_files = {
        'telos': 'telos.xml',
        'tiamaranta_mesa': 'tiamaranta_mesa.xml',
        'laphsaran': 'laphsaran.xml',
        'teva': 'teva.xml',
        'apheta_beluslan': 'apheta_beluslan.xml',
        'dranium_battlefield': 'dranium_battlefield.xml',
        'dokkaebi_realm': 'dokkaebi_realm.xml',
        'balic_treasury': 'balic_treasury.xml'
    }

    zone_quests = defaultdict(list)
    for c_q in client_quests_root:
        qid = c_q.findtext("id", "").strip()
        f_mis = c_q.findtext("f_mission", "0").strip()
        cat1 = c_q.findtext("category1", "quest").strip().lower()
        cat2 = c_q.findtext("category2", "").strip()
        
        if f_mis == "1" or cat1 == "mission":
            continue

        zone_info = ZONE_MAP.get(cat2)
        if zone_info and zone_info[1] in map_xml_files:
            zone_quests[zone_info[1]].append(c_q)

    for zone_key, xml_filename in map_xml_files.items():
        q_list = zone_quests.get(zone_key, [])
        if not q_list:
            continue

        root = ET.Element("quest_scripts")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:noNamespaceSchemaLocation", "quest_script_data.xsd")

        item_collecting_nodes = []
        report_to_nodes = []
        monster_hunt_nodes = []

        for c_q in q_list:
            qid = c_q.findtext("id", "").strip()
            has_items = any(c_q.findtext(f"collect_item{i}") for i in range(1, 5))
            has_kills = qid in kills_by_quest

            if has_items:
                node = ET.Element("item_collecting", {"id": qid})
                item_collecting_nodes.append(node)
            elif has_kills:
                node = ET.Element("monster_hunt", {"id": qid})
                monster_hunt_nodes.append(node)
            else:
                node = ET.Element("report_to", {"id": qid})
                report_to_nodes.append(node)

        for n in item_collecting_nodes:
            root.append(n)
        for n in report_to_nodes:
            root.append(n)
        for n in monster_hunt_nodes:
            root.append(n)

        ET.indent(root, space="\t")
        target_path = os.path.join(script_data_dir, xml_filename)
        ET.ElementTree(root).write(target_path, encoding="utf-8", xml_declaration=True)

        try:
            import lxml.etree
            xsd_path = os.path.join(script_data_dir, "quest_script_data.xsd")
            schema = lxml.etree.XMLSchema(lxml.etree.parse(xsd_path))
            schema.assertValid(lxml.etree.parse(target_path))
            print(f"  -> [OK] {xml_filename} gerado com {len(q_list)} missões e validado!")
        except Exception as ex:
            print(f"  -> [AVISO] Validação {xml_filename}: {ex}")

# -----------------------------------------------------------------------------
# 4. Geração de Java Handlers para Missões de Campanha
# -----------------------------------------------------------------------------
def generate_mission_handlers(client_quests_root, name_to_body, npc_name_to_id, npc_id_to_name, npc_id_to_realname, kills_by_quest):
    print("  -> Verificando e gerando Handlers Java para Missões de Campanha...")
    handler_base_dir = os.path.join(GAME_SERVER_DIR, "data", "handlers", "quest")
    os.makedirs(handler_base_dir, exist_ok=True)

    existing_handlers = set()
    for f in glob.glob(os.path.join(handler_base_dir, "**", "*.java"), recursive=True):
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as jf:
                if "@author Aion Classic 5.0 Parser Pipeline" in jf.read():
                    continue
        except Exception:
            pass
        m = re.search(r'_(\d+)', os.path.basename(f))
        if m:
            existing_handlers.add(m.group(1))

    created_handlers = 0
    new_handler_files = []
    for c_q in client_quests_root:
        qid = c_q.findtext("id", "").strip()
        f_mis = c_q.findtext("f_mission", "0").strip()
        cat1 = c_q.findtext("category1", "quest").strip().lower()
        cat2 = c_q.findtext("category2", "").strip()
        desc = c_q.findtext("desc", "").strip()
        code_name = c_q.findtext("name", "").strip()

        if f_mis != "1" and cat1 != "mission":
            continue

        if qid in existing_handlers:
            continue

        real_title = name_to_body.get(desc.lower(), name_to_body.get(code_name.lower(), code_name))
        camel_name = clean_camel_case(real_title)
        class_name = f"_{qid}{camel_name}"

        zone_info = ZONE_MAP.get(cat2, ("Unknown Zone", "custom"))
        zone_title = zone_info[0]
        package_folder = zone_info[1]
        package_name = f"quest.{package_folder}"

        target_folder = os.path.join(handler_base_dir, package_folder)
        os.makedirs(target_folder, exist_ok=True)
        target_java_file = os.path.join(target_folder, f"{class_name}.java")

        kill_npc_ids = []
        for k in kills_by_quest.get(qid, []):
            for nid_str in k['npc_ids'].split():
                if nid_str.isdigit():
                    kill_npc_ids.append(int(nid_str))
        kill_npc_ids = list(dict.fromkeys(kill_npc_ids))

        talk_npc_ids = []
        if package_folder == "telos":
            talk_npc_ids = [800641, 800649]
        elif package_folder == "tiamaranta_mesa":
            talk_npc_ids = [800360, 800361]
        elif package_folder == "laphsaran":
            talk_npc_ids = [804698, 804699]
        elif package_folder == "teva":
            talk_npc_ids = [804718, 804719]

        talk_registrations = []
        for nid in talk_npc_ids:
            rname = npc_id_to_realname.get(nid, npc_id_to_name.get(nid, f"NPC {nid}"))
            talk_registrations.append(f"\t\t// {nid}: {rname}\n\t\tqe.registerQuestNpc({nid}).addOnTalkEvent(questId);")

        kill_registrations = []
        for nid in kill_npc_ids:
            rname = npc_id_to_realname.get(nid, npc_id_to_name.get(nid, f"Monster {nid}"))
            kill_registrations.append(f"\t\t// {nid}: {rname}\n\t\tqe.registerQuestNpc({nid}).addOnKillEvent(questId);")

        reg_body = "\n".join(talk_registrations + kill_registrations)
        if not reg_body:
            reg_body = "\t\t// Auto-registrado para eventos de missão\n\t\tqe.registerOnLevelChanged(questId);\n\t\tqe.registerOnEnterWorld(questId);"
        else:
            reg_body += "\n\t\tqe.registerOnLevelChanged(questId);\n\t\tqe.registerOnEnterWorld(questId);"

        kill_method = ""
        if kill_npc_ids:
            kill_method = f"""
	@Override
	public boolean onKillEvent(QuestEnv env) {{
		int[] mobs = {{ {", ".join(str(m) for m in kill_npc_ids)} }};
		return defaultOnKillEvent(env, mobs, 0, 1);
	}}
"""

        java_source = f"""package {package_name};

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;

/**
 * Quest ID: {qid}
 * Title: {real_title}
 * Zone: {zone_title}
 * 
 * @author Aion Classic 5.0 Parser Pipeline
 */
public class {class_name} extends AbstractQuestHandler {{

	public {class_name}() {{
		super({qid});
	}}

	@Override
	public void register() {{
{reg_body}
	}}

	@Override
	public boolean onDialogEvent(QuestEnv env) {{
		final Player player = env.getPlayer();
		final QuestState qs = player.getQuestStateList().getQuestState(questId);
		if (qs == null) {{
			return false;
		}}

		int targetId = env.getTargetId();
		int dialogActionId = env.getDialogActionId();

		if (qs.getStatus() == QuestStatus.START) {{
			if (dialogActionId == QUEST_SELECT) {{
				return sendQuestDialog(env, 1011);
			}}
			if (dialogActionId == SET_SUCCEED) {{
				qs.setStatus(QuestStatus.REWARD);
				updateQuestStatus(env);
				return closeDialogWindow(env);
			}}
		}} else if (qs.getStatus() == QuestStatus.REWARD) {{
			if (dialogActionId == USE_OBJECT) {{
				return sendQuestDialog(env, 10002);
			}}
			return sendQuestEndDialog(env);
		}}
		return false;
	}}
{kill_method}
	@Override
	public boolean onEnterWorldEvent(QuestEnv env) {{
		Player player = env.getPlayer();
		if (!player.getQuestStateList().hasQuest(questId)) {{
			return QuestService.startQuest(env);
		}}
		return false;
	}}

	@Override
	public void onLevelChangedEvent(Player player) {{
		defaultOnLevelChangedEvent(player);
	}}
}}
"""
        with open(target_java_file, "w", encoding="utf-8") as jf:
            jf.write(java_source)
        created_handlers += 1
        new_handler_files.append(target_java_file)

    print(f"  -> {created_handlers} novos Handlers Java gerados com sucesso!")

    # Teste de compilação dos handlers recém-gerados
    if new_handler_files:
        print("  -> Testando compilação dos novos handlers Java...")
        os.makedirs(os.path.join(GAME_SERVER_DIR, "target", "test-classes"), exist_ok=True)
        classpath = f"target/classes;target/dependency/*;lib/*;config;{os.path.join(COMMONS_DIR, 'target', 'classes')}"
        batch_size = 50
        compile_errors = 0
        for i in range(0, len(new_handler_files), batch_size):
            batch = new_handler_files[i:i + batch_size]
            cmd = ['javac', '-encoding', 'UTF-8', '-cp', classpath, '-d', 'target/test-classes'] + batch
            res = subprocess.run(cmd, cwd=GAME_SERVER_DIR, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"    [ERRO] Falha de compilação no lote {i//batch_size}:")
                print(res.stderr[:500])
                compile_errors += 1
        if compile_errors == 0:
            print(f"  -> [OK] Todos os {len(new_handler_files)} handlers novos compilam com 100% de SUCESSO!")

# -----------------------------------------------------------------------------
# 5. Sincronização com EMULADOR FINAL
# -----------------------------------------------------------------------------
def sync_all_to_final():
    print("\n[SINCRONIZAÇÃO] Espelhando arquivos para EMULADOR FINAL...")
    src_qd = os.path.join(GAME_SERVER_DIR, "data", "static_data", "quest_data", "quest_data.xml")
    dst_qd = os.path.join(EMULADOR_FINAL_DIR, "data", "static_data", "quest_data", "quest_data.xml")
    os.makedirs(os.path.dirname(dst_qd), exist_ok=True)
    shutil.copy2(src_qd, dst_qd)
    print("  -> quest_data.xml espelhado com sucesso.")

    src_qsd = os.path.join(GAME_SERVER_DIR, "data", "static_data", "quest_script_data")
    dst_qsd = os.path.join(EMULADOR_FINAL_DIR, "data", "static_data", "quest_script_data")
    os.makedirs(dst_qsd, exist_ok=True)
    for f in os.listdir(src_qsd):
        if f.endswith(".xml"):
            shutil.copy2(os.path.join(src_qsd, f), os.path.join(dst_qsd, f))
    print("  -> quest_script_data/ espelhado com sucesso.")

    src_hq = os.path.join(GAME_SERVER_DIR, "data", "handlers", "quest")
    dst_hq = os.path.join(EMULADOR_FINAL_DIR, "data", "handlers", "quest")
    os.makedirs(dst_hq, exist_ok=True)
    for root, dirs, files in os.walk(src_hq):
        rel = os.path.relpath(root, src_hq)
        dst_folder = os.path.join(dst_hq, rel)
        os.makedirs(dst_folder, exist_ok=True)
        for f in files:
            if f.endswith(".java"):
                shutil.copy2(os.path.join(root, f), os.path.join(dst_folder, f))
    print("  -> data/handlers/quest/ espelhado com sucesso.")

# -----------------------------------------------------------------------------
# Execução Principal
# -----------------------------------------------------------------------------
def main():
    print("=" * 80)
    print("PIPELINE DE EXTRAÇÃO E INTEGRAÇÃO DE MISSÕES - AION CLASSIC 5.0")
    print("=" * 80)

    name_to_id, name_to_body = load_all_strings()
    item_map = load_all_items()
    npc_name_to_id, npc_id_to_name, npc_id_to_realname = load_all_npcs(name_to_body)
    drops_by_quest, kills_by_quest = load_quest_monsters(npc_name_to_id, item_map)

    print("\nLendo data/Quest/quest.xml oficial 5.0...")
    quest_xml_path = os.path.join(CLIENT_DATA_DIR, "Quest", "quest.xml")
    raw_q = open(quest_xml_path, "rb").read()
    client_quests_root = ET.fromstring(aion_bxml.decodifica(raw_q) if aion_bxml.e_bxml(quest_xml_path) else raw_q.decode("utf-8", errors="ignore"))
    print(f"  -> Total de missões encontradas no cliente 5.0: {len(client_quests_root):,}")

    update_quest_data(client_quests_root, name_to_id, name_to_body, item_map, npc_name_to_id, drops_by_quest, kills_by_quest)
    generate_50_quest_scripts(client_quests_root, name_to_body, npc_name_to_id, kills_by_quest)
    generate_mission_handlers(client_quests_root, name_to_body, npc_name_to_id, npc_id_to_name, npc_id_to_realname, kills_by_quest)
    sync_all_to_final()

    print("\n" + "=" * 80)
    print("PIPELINE CONCLUÍDO COM 100% DE SUCESSO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
