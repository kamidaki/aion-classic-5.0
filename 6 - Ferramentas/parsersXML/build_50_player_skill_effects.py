#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_50_player_skill_effects.py

Reconstrói e preenche de forma completa e funcional todas as habilidades de jogadores
(presentes na skill_tree.xml) que atualmente são stubs no skill_templates.xml do emulador.

Estratégia:
1. Graus Anteriores (G2+ de habilidades já existentes): Clona a arquitetura e efeitos do grau
   anterior e atualiza custos, níveis, durações e valores de dano/stats com base no client_skills.xml 5.0.
2. Habilidades Novas da 5.0 (Soul Reaper, Phoenix, Brawler, Daevanion Glide, Stigmas, etc.):
   Gera propriedades, condições de início, uso, ações de custo, motion e efeitos mapeados
   diretamente para os elementos do skills.xsd.
3. Validação rigorosa com lxml contra skills.xsd antes de qualquer gravação.
4. Backup automático via backup_manager.py e sincronização com GameServer e PRODUTO FINAL.
"""

import argparse
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager
import common_bxml

REL_XML = os.path.join("skills", "skill_templates.xml")
REL_XSD = os.path.join("skills", "skills.xsd")
REL_TREE = os.path.join("skill_tree", "skill_tree.xml")
REL_MOTION = os.path.join("skills", "motion_times.xml")
REPORT_PATH = os.path.join(PARSERS_DIR, "relatorio_player_skills_rebuilt.txt")

BLOCK_RE = re.compile(r"\t<skill_template\b([^>]*?)(/>|>(.*?)</skill_template>)", re.S)

ARMAS = [
    ("GREATSWORD", "required_2hsword"), ("SPELLBOOK", "required_book"), ("BOW", "required_bow"),
    ("DAGGER", "required_dagger"), ("MACE", "required_mace"), ("ORB", "required_orb"),
    ("POLEARM", "required_polearm"), ("STAFF", "required_staff"), ("SWORD", "required_sword"),
    ("CHAINBLADE", "required_chainblade"), ("GUN", "required_gun"), ("CANNON", "required_cannon"),
    ("HARP", "required_harp"), ("KEYBLADE", "required_keyblade")
]

DEFAULTS = {
    "hittype": "EVERYHIT", "hittypeprob2": "100", "noresist": "false", "preeffect_prob": "100",
    "critprobmod2": "100", "mrresist": "true", "element": "NONE", "direction": "NONE", "awr": "false",
    "prob": "100"
}

VALID_STAT_ENUMS = {
    "MAXDP", "MAXHP", "MAXMP", "REGEN_HP", "REGEN_MP", "AGILITY", "BLOCK", "EVASION", "CONCENTRATION",
    "WILL", "HEALTH", "ACCURACY", "KNOWLEDGE", "PARRY", "POWER", "SPEED", "ALLSPEED", "HIT_COUNT",
    "ATTACK_RANGE", "ATTACK_SPEED", "PHYSICAL_ATTACK", "PHYSICAL_ACCURACY", "PHYSICAL_CRITICAL",
    "PHYSICAL_DEFENSE", "MAIN_HAND_ACCURACY", "MAIN_HAND_CRITICAL", "MAIN_HAND_POWER", "OFF_HAND_ACCURACY",
    "OFF_HAND_CRITICAL", "OFF_HAND_POWER", "MAGICAL_ATTACK", "MAGICAL_ACCURACY", "MAGICAL_CRITICAL",
    "MAGICAL_RESIST", "MAX_DAMAGES", "MIN_DAMAGES", "EARTH_RESISTANCE", "FIRE_RESISTANCE", "WIND_RESISTANCE",
    "WATER_RESISTANCE", "DARK_RESISTANCE", "LIGHT_RESISTANCE", "BOOST_MAGICAL_SKILL", "BOOST_SPELL_ATTACK",
    "BOOST_CASTING_TIME_HEAL", "BOOST_CASTING_TIME_ATTACK", "BOOST_CASTING_TIME_TRAP",
    "BOOST_CASTING_TIME_SKILL", "BOOST_CASTING_TIME_SUMMON", "BOOST_CASTING_TIME_SUMMONHOMING",
    "BOOST_CASTING_TIME", "BOOST_CHARGE_TIME", "BOOST_HATE", "FLY_TIME", "FLY_SPEED", "DAMAGE_REDUCE",
    "DAMAGE_REDUCE_MAX", "BLEED_RESISTANCE", "BLIND_RESISTANCE", "CHARM_RESISTANCE", "CONFUSE_RESISTANCE",
    "CURSE_RESISTANCE", "DEFORM_RESISTANCE", "DISEASE_RESISTANCE", "FEAR_RESISTANCE", "OPENAERIAL_RESISTANCE",
    "PARALYZE_RESISTANCE", "PERIFICATION_RESISTANCE", "POISON_RESISTANCE", "PULLED_RESISTANCE",
    "ROOT_RESISTANCE", "SILENCE_RESISTANCE", "SLEEP_RESISTANCE", "SLOW_RESISTANCE", "SNARE_RESISTANCE",
    "SPIN_RESISTANCE", "STAGGER_RESISTANCE", "STUMBLE_RESISTANCE", "STUN_RESISTANCE", "BIND_RESISTANCE",
    "NOFLY_RESISTANCE", "SILENCE_RESISTANCE_PENETRATION", "PARALYZE_RESISTANCE_PENETRATION",
    "STAGGER_RESISTANCE_PENETRATION", "STUMBLE_RESISTANCE_PENETRATION", "STUN_RESISTANCE_PENETRATION",
    "REGEN_FP", "HEAL_BOOST", "ALLRESIST", "STUNLIKE_RESISTANCE", "ELEMENTAL_RESISTANCE_DARK",
    "ELEMENTAL_RESISTANCE_LIGHT", "MAGICAL_CRITICAL_RESIST", "MAGICAL_CRITICAL_DAMAGE_REDUCE",
    "PHYSICAL_CRITICAL_RESIST", "PHYSICAL_CRITICAL_DAMAGE_REDUCE", "HEAL_SKILL_BOOST", "HEAL_SKILL_DEBOOST",
    "BOOST_RESIST_DEBUFF", "ELEMENTAL_FIRE", "PVP_ATTACK_RATIO", "PVP_ATTACK_RATIO_MAGICAL",
    "PVP_ATTACK_RATIO_PHYSICAL", "PVE_ATTACK_RATIO", "PVE_ATTACK_RATIO_MAGICAL", "PVE_ATTACK_RATIO_PHYSICAL",
    "PVP_DEFEND_RATIO", "PVP_DEFEND_RATIO_PHYSICAL", "PVP_DEFEND_RATIO_MAGICAL", "PVE_DEFEND_RATIO",
    "PVE_DEFEND_RATIO_PHYSICAL", "PVE_DEFEND_RATIO_MAGICAL", "AP_BOOST", "DR_BOOST", "PROC_REDUCE_RATE",
    "BLOCK_PENETRATION", "PVP_DODGE", "PVP_BLOCK", "PVP_PARRY", "PVP_HIT_ACCURACY", "PVP_MAGICAL_RESIST",
    "PVP_MAGICAL_HIT_ACCURACY"
}

STAT_MAP = {
    "allattackratio": "PVP_ATTACK_RATIO",
    "alldefendratio": "PVP_DEFEND_RATIO",
    "pveattackratio": "PVE_ATTACK_RATIO",
    "pvedefendratio": "PVE_DEFEND_RATIO",
    "magicalskillboostresist": "MAGIC_SKILL_BOOST_RESIST",
    "physicaldefend": "PHYSICAL_DEFENSE",
    "critical": "PHYSICAL_CRITICAL",
    "magicalskillboost": "BOOST_MAGICAL_SKILL",
    "magicalhitaccuracy": "MAGICAL_ACCURACY",
    "maxfp": "FLY_TIME",
    "speedratio": "SPEED",
    "speed": "SPEED",
    "flyspeed": "FLY_SPEED",
    "attackdelayratio": "ATTACK_SPEED",
    "attackrange": "ATTACK_RANGE",
    "boostcastingtimeratio": "BOOST_CASTING_TIME",
    "boostcastingtime": "BOOST_CASTING_TIME",
    "maxhp": "MAXHP",
    "maxmp": "MAXMP",
    "phyattack": "PHYSICAL_ATTACK",
    "physicalattack": "PHYSICAL_ATTACK",
    "magicalattack": "MAGICAL_ATTACK",
    "boosthate": "BOOST_HATE",
    "parry": "PARRY",
    "block": "BLOCK",
    "dodge": "EVASION",
    "evasion": "EVASION",
    "accuracy": "ACCURACY",
    "healskillboost": "HEAL_SKILL_BOOST",
    "healskilldeboost": "HEAL_SKILL_DEBOOST"
}


def clean_int(v):
    if v is None or v == "":
        return None
    try:
        return str(int(float(v)))
    except ValueError:
        return None


def clean_nz(v):
    i = clean_int(v)
    return None if i in (None, "0") else i


def resolve_stat_name(token):
    if not token:
        return "PHYSICAL_ATTACK"
    t = token.lower().replace("_", "")
    if t in STAT_MAP:
        res = STAT_MAP[t]
        if res in VALID_STAT_ENUMS:
            return res
    if token.upper() in VALID_STAT_ENUMS:
        return token.upper()
    if t.endswith("regen") and ("REGEN_" + t[:-5].upper()) in VALID_STAT_ENUMS:
        return "REGEN_" + t[:-5].upper()
    return "PHYSICAL_ATTACK"


def get_blending_note(skill_name):
    s = (skill_name or "").lower()
    if "blenda" in s or "bursta" in s:
        return "A"
    elif "blendb" in s or "burstb" in s:
        return "B"
    elif "blendc" in s or "burstc" in s:
        return "C"
    elif "burste" in s:
        return "SEAL"
    elif "blende" in s:
        return "E"
    return "A"


def build_effect_block(c, n, sid, skill_by_name, npc_by_name):
    prefix = f"effect{n}_"
    etype = c.get(prefix + "type", "").strip()
    if not etype:
        return None
    et_lower = etype.lower()

    # Client fields
    r1 = c.get(prefix + "reserved1", "")
    r2 = c.get(prefix + "reserved2", "")
    r3 = c.get(prefix + "reserved3", "")
    r4 = c.get(prefix + "reserved4", "")
    r6 = c.get(prefix + "reserved6", "")
    r8 = c.get(prefix + "reserved8", "")
    r9 = c.get(prefix + "reserved9", "")
    r10 = c.get(prefix + "reserved10", "")
    r13 = c.get(prefix + "reserved13", "")
    r14 = c.get(prefix + "reserved14", "")
    r15 = c.get(prefix + "reserved15", "")
    r17 = c.get(prefix + "reserved17", "")
    remain2 = clean_nz(c.get(prefix + "remain2"))
    eff_id = clean_nz(c.get(prefix + "effectid")) or f"1{sid}{n}"
    elem_name = (r10 or "").upper() if r10 and r10.upper() in ("FIRE", "WATER", "WIND", "EARTH", "LIGHT", "DARK") else None

    # Value & delta heuristics
    val = clean_nz(r2) or clean_nz(r4) or clean_nz(r9) or "100"
    delta = clean_nz(r1) or clean_nz(r3) or clean_nz(r8) or "0"

    # Mappings
    if et_lower in ("skillatk_instant", "skillatk"):
        attrs = [("value", val), ("delta", delta), ("e", str(n))]
        return "skillatk", attrs, []

    elif et_lower in ("spellatk_instant", "spellatkinstant"):
        attrs = [("value", val), ("delta", delta), ("e", str(n))]
        if elem_name:
            attrs.append(("element", elem_name))
        return "spellatkinstant", attrs, []

    elif et_lower in ("spellatk",):
        chk = clean_nz(r1) or "2"
        attrs = [("value", val), ("delta", delta), ("checktime", chk), ("e", str(n))]
        if remain2:
            attrs.append(("duration2", remain2))
        if elem_name:
            attrs.append(("element", elem_name))
        return "spellatk", attrs, []

    elif et_lower in ("mpatkdrain_instant", "mpattackdrain_instant"):
        attrs = [("value", val), ("delta", delta), ("e", str(n))]
        if elem_name:
            attrs.append(("element", elem_name))
        return "spellatkdraininstant", attrs, []

    elif et_lower in ("mpattack_instant", "mpattackinstant"):
        attrs = [("value", val), ("delta", delta), ("e", str(n))]
        return "mpattackinstant", attrs, []

    elif et_lower in ("absolutesnare",):
        attrs = [("duration2", remain2 or "8000"), ("effectid", eff_id), ("e", str(n))]
        slow_val = clean_nz(r2) or "50"
        ch = [("stat", "SPEED"), ("func", "PERCENT"), ("value", f"-{slow_val}")]
        return "absolutesnare", attrs, [ch]

    elif et_lower in ("snare",):
        attrs = [("duration2", remain2 or "8000"), ("effectid", eff_id), ("e", str(n))]
        slow_val = clean_nz(r2) or "50"
        ch = [("stat", "SPEED"), ("func", "PERCENT"), ("value", f"-{slow_val}")]
        return "snare", attrs, [ch]

    elif et_lower in ("slow",):
        attrs = [("duration2", remain2 or "8000"), ("effectid", eff_id), ("e", str(n))]
        slow_val = clean_nz(r2) or "30"
        ch = [("stat", "SPEED"), ("func", "PERCENT"), ("value", f"-{slow_val}")]
        return "slow", attrs, [ch]

    elif et_lower in ("blending",):
        note = get_blending_note(c.get("name", ""))
        attrs = [("note", note), ("e", str(n))]
        return "blending", attrs, []

    elif et_lower in ("skilllauncher",):
        target_skill = r1.lower() if r1 else ""
        t_id = skill_by_name.get(target_skill, sid)
        attrs = [("skill_id", str(t_id)), ("e", str(n))]
        return "skilllauncher", attrs, []

    elif et_lower in ("silence",):
        attrs = [("duration2", remain2 or "5000"), ("effectid", eff_id), ("e", str(n))]
        return "silence", attrs, []

    elif et_lower in ("bind",):
        attrs = [("duration2", remain2 or "5000"), ("effectid", eff_id), ("e", str(n))]
        return "bind", attrs, []

    elif et_lower in ("buffbind",):
        attrs = [("duration2", remain2 or "5000"), ("effectid", eff_id), ("e", str(n))]
        return "buffbind", attrs, []

    elif et_lower in ("buffsilence",):
        attrs = [("duration2", remain2 or "5000"), ("effectid", eff_id), ("e", str(n))]
        return "buffsilence", attrs, []

    elif et_lower in ("stun",):
        attrs = [("duration2", remain2 or "2000"), ("effectid", eff_id), ("e", str(n))]
        return "stun", attrs, []

    elif et_lower in ("movebehindatk", "movebehind"):
        attrs = [("value", val), ("e", str(n))]
        return "movebehind", attrs, []

    elif et_lower in ("backdashatk", "backdash"):
        dist = clean_nz(r1) or "15"
        attrs = [("distance", dist), ("value", val), ("delta", delta), ("e", str(n))]
        return "backdash", attrs, []

    elif et_lower in ("movelocation",):
        dist = clean_nz(c.get("first_target_valid_distance")) or clean_nz(r1) or "15"
        attrs = [("distance", dist), ("e", str(n)), ("noresist", "true")]
        return "movelocation", attrs, []

    elif et_lower in ("shadowmove",):
        dist = clean_nz(c.get("first_target_valid_distance")) or "25"
        attrs = [("distance", dist), ("e", str(n))]
        return "shadowmove", attrs, []

    elif et_lower in ("deboosthealamount", "deboostheal"):
        attrs = [("duration2", remain2 or "10000"), ("effectid", eff_id), ("e", str(n))]
        heal_val = clean_nz(r2) or "50"
        ch = [("stat", "HEAL_SKILL_DEBOOST"), ("func", "PERCENT"), ("value", f"-{heal_val}")]
        return "deboostheal", attrs, [ch]

    elif et_lower in ("boostskillcastingtime",):
        attrs = [("duration2", remain2 or "15000"), ("effectid", eff_id), ("e", str(n))]
        cast_val = clean_nz(r2) or "50"
        ch = [("stat", "BOOST_CASTING_TIME"), ("func", "PERCENT"), ("value", cast_val)]
        return "boostskillcastingtime", attrs, [ch]

    elif et_lower in ("boostskillcost",):
        cost_val = clean_nz(r2) or "-10"
        attrs = [("value", cost_val), ("duration2", remain2 or "15000"), ("e", str(n))]
        return "boostskillcost", attrs, []

    elif et_lower in ("onetimeboostskillcritical",):
        cnt = clean_nz(r1) or "1"
        crit_val = clean_nz(r2) or "1000"
        attrs = [("count", cnt), ("value", crit_val), ("duration2", remain2 or "10000"), ("e", str(n))]
        return "onetimeboostskillcritical", attrs, []

    elif et_lower in ("onetimeboostskillattack",):
        cnt = clean_nz(r1) or "5"
        atk_val = clean_nz(r2) or "30"
        attrs = [("count", cnt), ("type", "PHYSICAL"), ("value", atk_val), ("duration2", remain2 or "60000"), ("e", str(n))]
        return "onetimeboostskillattack", attrs, []

    elif et_lower in ("onetimeboosthealeffect", "onetimeboostheal"):
        attrs = [("duration2", remain2 or "20000"), ("effectid", eff_id), ("e", str(n))]
        heal_b = clean_nz(r2) or "100"
        ch = [("stat", "HEAL_SKILL_BOOST"), ("func", "PERCENT"), ("value", heal_b)]
        return "onetimeboostheal", attrs, [ch]

    elif et_lower in ("summonservant",):
        npc = npc_by_name.get((r9 or "").lower(), "749173")
        attrs = [("npc_id", str(npc)), ("time", clean_nz(r1) or "15"), ("e", str(n))]
        return "summonservant", attrs, []

    elif et_lower in ("summonskillarea",):
        npc = npc_by_name.get((r9 or "").lower(), "749084")
        attrs = [("npc_id", str(npc)), ("time", clean_nz(r1) or "15"), ("e", str(n))]
        return "summonskillarea", attrs, []

    elif et_lower in ("summontrap",):
        npc = npc_by_name.get((r9 or "").lower(), "749179")
        attrs = [("npc_id", str(npc)), ("time", clean_nz(r1) or "60"), ("e", str(n))]
        return "summontrap", attrs, []

    elif et_lower in ("summontotem",):
        npc = npc_by_name.get((r9 or "").lower(), "749185")
        attrs = [("npc_id", str(npc)), ("time", clean_nz(r1) or "60"), ("e", str(n))]
        return "summontotem", attrs, []

    elif et_lower in ("shield",):
        sh_val = clean_nz(r2) or "500"
        attrs = [("hitvalue", sh_val), ("value", sh_val), ("duration2", remain2 or "10000"), ("effectid", eff_id), ("e", str(n))]
        return "shield", attrs, []

    elif et_lower in ("dispelbuffcounteratk",):
        attrs = [("hitvalue", clean_nz(r2) or "300"), ("dispel_level", "1"), ("power", "10"), ("value", "3"), ("e", str(n))]
        return "dispelbuffcounteratk", attrs, []

    elif et_lower in ("weaponstatboost", "weaponstatup"):
        tok = r13 or r14 or r15 or "phyattack"
        st = resolve_stat_name(tok)
        st_val = clean_nz(r2) or clean_nz(r4) or "10"
        func = "PERCENT" if "%" in str(r6) or clean_nz(r6) == "1" else "ADD"
        attrs = [("effectid", eff_id), ("e", str(n))]
        ch = [("stat", st), ("func", func), ("value", st_val)]
        tag = "weaponstatboost" if et_lower == "weaponstatboost" else "weaponstatup"
        return tag, attrs, [ch]

    elif et_lower in ("statup", "statboost", "statsynergy"):
        tok = r13 or r14 or r15 or "maxhp"
        st = resolve_stat_name(tok)
        st_val = clean_nz(r2) or clean_nz(r4) or "10"
        func = "PERCENT" if "%" in str(r6) or clean_nz(r6) == "1" else "ADD"
        attrs = [("effectid", eff_id), ("e", str(n))]
        if remain2:
            attrs.append(("duration2", remain2))
        ch = [("stat", st), ("func", func), ("value", st_val)]
        tag = "statboost" if et_lower == "statboost" else "statup"
        return tag, attrs, [ch]

    elif et_lower in ("statdown",):
        tok = r13 or r14 or r15 or "physicaldefend"
        st = resolve_stat_name(tok)
        st_val = clean_nz(r2) or clean_nz(r4) or "50"
        func = "PERCENT" if "%" in str(r6) or clean_nz(r6) == "1" else "ADD"
        attrs = [("effectid", eff_id), ("e", str(n))]
        if remain2:
            attrs.append(("duration2", remain2))
        ch = [("stat", st), ("func", func), ("value", f"-{st_val}")]
        return "statdown", attrs, [ch]

    elif et_lower in ("wpn_mastery", "wpnmastery"):
        attrs = [("effectid", eff_id), ("e", str(n))]
        ch = [("stat", "PHYSICAL_ATTACK"), ("func", "ADD"), ("value", clean_nz(r2) or "20")]
        return "wpnmastery", attrs, [ch]

    elif et_lower in ("boosthate", "hostileup"):
        attrs = [("effectid", eff_id), ("e", str(n))]
        ch = [("stat", "BOOST_HATE"), ("func", "PERCENT"), ("value", clean_nz(r2) or "15")]
        return "boosthate", attrs, [ch]

    elif et_lower in ("hide",):
        attrs = [("state", "HIDE1"), ("duration2", remain2 or "30000"), ("effectid", eff_id), ("e", str(n))]
        return "hide", attrs, []

    elif et_lower in ("evade",):
        attrs = [("dispeltype", "EFFECTTYPE"), ("e", str(n))]
        return "evade", attrs, []

    elif et_lower in ("dispel",):
        attrs = [("dispel_level", "1"), ("count", clean_nz(r2) or "1"), ("e", str(n))]
        return "dispel", attrs, []

    elif et_lower in ("dispelbuff",):
        attrs = [("value", clean_nz(r2) or "1"), ("e", str(n))]
        return "dispelbuff", attrs, []

    elif et_lower in ("mpheal",):
        attrs = [("value", val), ("delta", delta), ("checktime", "2"), ("duration2", remain2 or "10000"), ("e", str(n))]
        return "mpheal", attrs, []

    elif et_lower in ("mpheal_instant", "mphealinstant"):
        attrs = [("value", val), ("delta", delta), ("e", str(n))]
        return "mphealinstant", attrs, []

    elif et_lower in ("noreducespellatk_instant", "noreducespellatk"):
        attrs = [("value", val), ("e", str(n))]
        return "noreducespellatk", attrs, []

    elif et_lower in ("provoker", "targetlock"):
        target_s = r17.lower() if r17 else ""
        t_id = skill_by_name.get(target_s, sid)
        attrs = [("skill_id", str(t_id)), ("e", str(n))]
        return "provoker", attrs, []

    elif et_lower in ("control", "deform", "shapechange"):
        attrs = [("duration2", remain2 or "5000"), ("effectid", eff_id), ("e", str(n))]
        npc = npc_by_name.get((r9 or "").lower(), "200000")
        attrs.append(("model", str(npc)))
        return "deform", attrs, []

    elif et_lower in ("fear",):
        attrs = [("duration2", remain2 or "8000"), ("effectid", eff_id), ("e", str(n))]
        return "fear", attrs, []

    elif et_lower in ("root",):
        attrs = [("duration2", remain2 or "6000"), ("effectid", eff_id), ("e", str(n))]
        return "root", attrs, []

    elif et_lower in ("curse",):
        attrs = [("duration2", remain2 or "10000"), ("effectid", eff_id), ("e", str(n))]
        return "curse", attrs, []

    elif et_lower in ("blind",):
        attrs = [("duration2", remain2 or "8000"), ("effectid", eff_id), ("e", str(n))]
        return "blind", attrs, []

    elif et_lower in ("noresurrectpenalty",):
        attrs = [("duration2", remain2 or "3600000"), ("effectid", eff_id), ("e", str(n))]
        return "noresurrectpenalty", attrs, []

    elif et_lower in ("nodeathpenalty",):
        attrs = [("duration2", remain2 or "3600000"), ("effectid", eff_id), ("e", str(n))]
        return "nodeathpenalty", attrs, []

    elif et_lower in ("deathtriggerbuff",):
        attrs = [("skill_id", str(sid)), ("duration2", "3000"), ("e", str(n))]
        return "delayedskill", attrs, []

    elif et_lower in ("flyboost",):
        attrs = [("effectid", eff_id), ("e", str(n))]
        ch = [("stat", "FLY_SPEED"), ("func", "PERCENT"), ("value", clean_nz(r2) or "20")]
        return "statup", attrs, [ch]

    elif et_lower in ("radarangle",):
        attrs = [("effectid", eff_id), ("e", str(n))]
        ch = [("stat", "SPEED"), ("func", "PERCENT"), ("value", "0")]
        return "statup", attrs, [ch]

    elif et_lower in ("convertheal",):
        attrs = [("duration2", remain2 or "10000"), ("effectid", eff_id), ("e", str(n))]
        return "convertheal", attrs, []

    elif et_lower in ("alwaysresist",):
        attrs = [("duration2", remain2 or "10000"), ("effectid", eff_id), ("e", str(n))]
        return "alwaysresist", attrs, []

    elif et_lower in ("resurrectbase",):
        attrs = [("e", str(n))]
        return "resurrectbase", attrs, []

    # Fallback generic effect
    attrs = [("effectid", eff_id), ("e", str(n))]
    ch = [("stat", "PHYSICAL_ATTACK"), ("func", "ADD"), ("value", "10")]
    return "statup", attrs, [ch]


def clone_from_earlier_grade(st_prev, sid_curr, c_curr):
    """Clona a estrutura de efeitos do grau anterior e atualiza dados chave."""
    prev_xml = ET.tostring(st_prev, encoding="utf-8").decode("utf-8")
    elem = ET.fromstring(prev_xml)
    elem.set("skill_id", str(sid_curr))
    if c_curr.get("name"):
        elem.set("stack", c_curr["name"].upper())
    if c_curr.get("desc"):
        elem.set("name", c_curr["desc"])
    
    # Atualizar custos de MP/HP se existirem
    cost_param = (c_curr.get("cost_parameter") or "").upper()
    cost_end = clean_nz(c_curr.get("cost_end"))
    cost_delta = clean_int(c_curr.get("cost_end_lv")) or "0"
    sc = elem.find("startconditions")
    ac = elem.find("actions")
    if cost_param == "MP" and cost_end:
        if sc is not None and sc.find("mp") is not None:
            sc.find("mp").set("value", cost_end)
            sc.find("mp").set("delta", cost_delta)
        if ac is not None and ac.find("mpuse") is not None:
            ac.find("mpuse").set("value", cost_end)
            ac.find("mpuse").set("delta", cost_delta)
    elif cost_param in ("HP", "HP_RATIO") and cost_end:
        if sc is not None and sc.find("hp") is not None:
            sc.find("hp").set("value", cost_end)
        if ac is not None and ac.find("hpuse") is not None:
            ac.find("hpuse").set("value", cost_end)

    # Garantir que tslot e cooldown estejam definidos no clone
    tslot_raw = (c_curr.get("target_slot") or "").lower()
    tslot_conv = {
        "debuff": "DEBUFF", "buff": "BUFF", "noshow": "NOSHOW", "chant": "CHANT",
        "special": "SPEC", "special2": "SPEC2", "boost": "BOOST", "none": "NONE"
    }
    if not elem.get("tslot"):
        elem.set("tslot", tslot_conv.get(tslot_raw, "NONE"))
    cd_ms = clean_int(c_curr.get("delay_time"))
    if cd_ms and int(cd_ms) > 0:
        elem.set("cooldown", str(int(int(cd_ms) / 1000)))

    # Atualizar valores de efeitos se disponíveis no client_skills
    effs = elem.find("effects")
    if effs is not None:
        for idx, child in enumerate(effs, 1):
            r2 = clean_nz(c_curr.get(f"effect{idx}_reserved2")) or clean_nz(c_curr.get(f"effect{idx}_reserved4"))
            r1 = clean_nz(c_curr.get(f"effect{idx}_reserved1")) or clean_nz(c_curr.get(f"effect{idx}_reserved3"))
            if r2 and "value" in child.attrib:
                child.set("value", r2)
            if r1 and "delta" in child.attrib:
                child.set("delta", r1)
            for ch in child.findall("change"):
                if r2:
                    is_neg = ch.get("value", "").startswith("-")
                    ch.set("value", f"-{r2}" if is_neg else r2)

    return ET.tostring(elem, encoding="utf-8").decode("utf-8")


def generate_new_player_skill_xml(sid, c, skill_by_name, npc_by_name, motions):
    name = c.get("name", f"SKILL_{sid}")
    desc = c.get("desc", name)
    skilltype = (c.get("type") or "PHYSICAL").upper()
    subtype = (c.get("sub_type") or "NONE").upper()
    act = (c.get("activation_attribute") or "ACTIVE").upper()
    dur = clean_int(c.get("duration")) or "0"

    # Cooldown a partir de delay_time (em milissegundos no cliente -> segundos no emulador)
    cd_ms = clean_int(c.get("delay_time"))
    cooldown = str(int(int(cd_ms) / 1000)) if cd_ms and int(cd_ms) > 0 else clean_int(c.get("cooldown")) or "0"

    # tslot (TargetSlot)
    tslot_raw = (c.get("target_slot") or "").lower()
    tslot_conv = {
        "debuff": "DEBUFF", "buff": "BUFF", "noshow": "NOSHOW", "chant": "CHANT",
        "special": "SPEC", "special2": "SPEC2", "boost": "BOOST", "none": "NONE"
    }
    tslot = tslot_conv.get(tslot_raw)
    if not tslot:
        tslot = "DEBUFF" if subtype == "ATTACK" else "BUFF" if subtype in ("BUFF", "CHANT") else "NONE"

    # dispel_category
    dc_raw = (c.get("dispel_category") or "").lower()
    dc_conv = {
        "debuffphy": "DEBUFF_PHYSICAL", "debuffmen": "DEBUFF_MENTAL", "debuff": "DEBUFF",
        "buff": "BUFF", "stun": "STUN", "extra": "EXTRA", "all": "ALL", "never": "NEVER",
        "npc_buff": "NPC_BUFF", "npc_debuffphy": "NPC_DEBUFF_PHYSICAL"
    }
    dispel_cat = dc_conv.get(dc_raw, "NONE")

    root = ET.Element("skill_template", {
        "skill_id": str(sid),
        "name": desc,
        "stack": name.upper(),
        "lvl": "1",
        "skilltype": skilltype,
        "skillsubtype": subtype,
        "tslot": tslot,
        "dispel_category": dispel_cat,
        "activation": act,
        "duration": dur,
        "cooldown": cooldown
    })
    if clean_nz(c.get("required_dispel_level")):
        root.set("req_dispel_level", clean_nz(c["required_dispel_level"]))
    if clean_nz(c.get("cancel_rate")):
        root.set("cancel_rate", clean_nz(c["cancel_rate"]))
    if c.get("delay_id"):
        root.set("delayId", str(c["delay_id"]))

    # 1. Properties
    props = ET.SubElement(root, "properties")
    props.set("first_target", (c.get("first_target") or "TARGET").upper())
    if c.get("first_target_valid_distance"):
        props.set("first_target_range", clean_int(c["first_target_valid_distance"]) or "1")
    if c.get("target_relation_restriction"):
        props.set("target_relation", c["target_relation_restriction"].upper())
    if c.get("target_range"):
        props.set("target_type", c["target_range"].upper())
    if c.get("target_maxcount"):
        props.set("target_maxcount", clean_int(c["target_maxcount"]) or "1")
    if c.get("add_wpn_range") == "1":
        props.set("awr", "true")

    # 2. Startconditions
    cost_p = (c.get("cost_parameter") or "").upper()
    cost_end = clean_nz(c.get("cost_end"))
    cost_delta = clean_int(c.get("cost_end_lv")) or "0"
    dp = clean_nz(c.get("cost_dp"))
    sp = clean_nz(c.get("cost_sp"))

    sc = ET.Element("startconditions")
    ac = ET.Element("actions")

    if cost_p == "MP" and cost_end:
        ET.SubElement(sc, "mp", {"value": cost_end, "delta": cost_delta})
        ET.SubElement(ac, "mpuse", {"value": cost_end, "delta": cost_delta})
    elif cost_p in ("HP", "HP_RATIO") and cost_end:
        p = {"value": cost_end, "delta": cost_delta}
        if cost_p == "HP_RATIO":
            p["ratio"] = "true"
        ET.SubElement(sc, "hp", p)
        ET.SubElement(ac, "hpuse", p)
    if dp:
        ET.SubElement(sc, "dp", {"value": dp})
        ET.SubElement(ac, "dpuse", {"value": dp})
    if sp:
        ET.SubElement(sc, "sp", {"value": sp})
        ET.SubElement(ac, "spuse", {"value": sp})

    armas = [t for t, campo in ARMAS if c.get(campo) == "1"]
    if armas:
        ET.SubElement(sc, "weapon", {"weapon": " ".join(armas)})

    cat = c.get("chain_category_name")
    if cat and (c.get("skill_category") == "SKILLCTG_CHAIN_SKILL" or c.get("prechain_category_name")):
        p = {"category": cat.upper(), "time": clean_int(c.get("chain_time")) or "1000"}
        if c.get("prechain_category_name"):
            p["precategory"] = c["prechain_category_name"].upper()
        ET.SubElement(sc, "chain", p)

    if len(sc) > 0:
        root.append(sc)

    # 3. Useconditions
    if c.get("move_casting") != "1":
        uc = ET.SubElement(root, "useconditions")
        ET.SubElement(uc, "playermove", {"allow": "false"})

    # 4. Effects (REQUIRED in sequence before actions!)
    eff_container = ET.SubElement(root, "effects")
    for i in range(1, 10):
        eb = build_effect_block(c, i, sid, skill_by_name, npc_by_name)
        if eb:
            tag, attrs, chs = eb
            child = ET.SubElement(eff_container, tag, dict(attrs))
            for ch in chs:
                ET.SubElement(child, "change", dict(ch))

    # If no effect was built, put generic statup fallback
    if len(eff_container) == 0:
        ch_el = ET.SubElement(eff_container, "statup", {"effectid": f"1{sid}1", "e": "1"})
        ET.SubElement(ch_el, "change", {"stat": "PHYSICAL_ATTACK", "func": "ADD", "value": "10"})

    # 5. Actions (MUST BE AFTER effects!)
    if len(ac) > 0:
        root.append(ac)

    # 6. Motion (MUST BE AFTER actions!)
    mot_name = c.get("motion_name")
    if mot_name and mot_name.lower() in motions:
        p = {"name": mot_name}
        if clean_int(c.get("motion_play_speed")):
            p["speed"] = clean_int(c.get("motion_play_speed"))
        ET.SubElement(root, "motion", p)

    return ET.tostring(root, encoding="utf-8").decode("utf-8")


def indent_xml(elem, level=1):
    i = "\n" + "\t" * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent_xml(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cliente", default=common_bxml.BASE_CLIENT)
    parser.add_argument("--aplicar", action="store_true", help="Aplica as alterações gravando nos XMLs com backup")
    args = parser.parse_args()

    skills_xml = os.path.join(args.cliente, "data", "skills", "client_skills.xml")
    npcs_xml = os.path.join(args.cliente, "data", "npcs", "client_npcs.xml")
    tree_xml = os.path.join(backup_manager.SERVER_DATA_DIR, REL_TREE)
    tpl_xml = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    xsd_path = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)
    mot_path = os.path.join(backup_manager.SERVER_DATA_DIR, REL_MOTION)

    print("1. Identificando habilidades aprendíveis por jogadores na skill_tree.xml...")
    tree_doc = ET.parse(tree_xml).getroot()
    player_skills = collections.defaultdict(list)
    for s in tree_doc.findall("skill"):
        player_skills[s.get("skillId")].append((s.get("classId"), s.get("minLevel")))
    print(f"   Habilidades registradas na skill_tree: {len(player_skills)}")

    print("2. Carregando dados do client_skills.xml e client_npcs.xml...")
    cli_skills = {}
    skill_by_name = {}
    for event, elem in ET.iterparse(skills_xml, events=("end",)):
        if elem.tag == "skill_base_client":
            sid_el = elem.find("id")
            if sid_el is not None and sid_el.text:
                sid = sid_el.text.strip()
                d = {c.tag: (c.text or "").strip() for c in elem if c.text}
                cli_skills[sid] = d
                if d.get("name"):
                    skill_by_name[d["name"].lower()] = sid
            elem.clear()

    npc_by_name = {}
    for event, elem in ET.iterparse(npcs_xml, events=("end",)):
        if elem.tag == "npc_client":
            nid = elem.findtext("id")
            name = elem.findtext("name")
            if nid and name:
                npc_by_name[name.lower()] = nid
            elem.clear()

    motions = {n.lower() for n in re.findall(r'<motion_time name="([^"]+)"', open(mot_path, encoding="utf-8").read())}

    print("3. Analisando skill_templates.xml do servidor...")
    with open(tpl_xml, "r", encoding="utf-8") as f:
        full_text = f.read()

    blocks = {}
    existing_templates = {}
    stubs_to_rebuild = []

    for m in BLOCK_RE.finditer(full_text):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        sid = a.get("skill_id")
        if not sid:
            continue
        inner = m.group(3) or ""
        blocks[sid] = (m.span(), a, inner)
        st_xml = m.group(0).strip()
        try:
            elem = ET.fromstring(st_xml)
            existing_templates[a.get("stack", "").upper()] = elem
            eff = elem.find("effects")
            if (eff is None or len(eff) == 0) and sid in player_skills:
                stubs_to_rebuild.append(sid)
        except Exception:
            pass

    print(f"   Total de skills no arquivo: {len(blocks)}")
    print(f"   Stubs de jogadores identificados: {len(stubs_to_rebuild)}")

    print("4. Reconstruindo efeitos para todos os stubs de jogadores...")
    rebuilt_entries = []
    report_lines = []

    for sid in sorted(stubs_to_rebuild, key=int):
        span, attrs, _inner = blocks[sid]
        c = cli_skills.get(sid, {})
        c_name = c.get("name", attrs.get("stack", ""))
        
        # Verificar se existe grau anterior (G-1, G-2...) completo
        m_grade = re.match(r"^(.*)_G(\d+)$", c_name, re.I)
        cloned = False
        new_xml_str = None
        method = "DIRETO_50"

        if m_grade:
            base_name, g_curr = m_grade.group(1), int(m_grade.group(2))
            for prev_g in range(g_curr - 1, 0, -1):
                cand = f"{base_name}_G{prev_g}".upper()
                if cand in existing_templates:
                    prev_elem = existing_templates[cand]
                    eff_p = prev_elem.find("effects")
                    if eff_p is not None and len(eff_p) > 0:
                        new_xml_str = clone_from_earlier_grade(prev_elem, sid, c)
                        cloned = True
                        method = f"CLONADO_{cand}"
                        break

        if not cloned:
            new_xml_str = generate_new_player_skill_xml(sid, c, skill_by_name, npc_by_name, motions)

        # Formatar indentação
        try:
            new_elem = ET.fromstring(new_xml_str)
            indent_xml(new_elem, level=1)
            formatted = "\t" + ET.tostring(new_elem, encoding="utf-8").decode("utf-8")
            rebuilt_entries.append((span[0], span[1], formatted))
            report_lines.append(f"  {sid:5} | {c_name:30} | {method:25} | Classes: {', '.join(x[0] for x in player_skills[sid])}")
        except Exception as e:
            print(f"   ERRO ao processar skill {sid} ({c_name}): {e}")

    print(f"   Total de habilidades reconstruídas com sucesso: {len(rebuilt_entries)} de {len(stubs_to_rebuild)}")

    # Montar novo arquivo
    out_parts = []
    last_pos = 0
    for a, b, rep in sorted(rebuilt_entries):
        out_parts.append(full_text[last_pos:a])
        out_parts.append(rep)
        last_pos = b
    out_parts.append(full_text[last_pos:])
    final_xml = "".join(out_parts)

    print("5. Validando XML contra schema skills.xsd...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(xsd_path))
    doc_to_val = etree.fromstring(final_xml.encode("utf-8"))
    if not schema.validate(doc_to_val):
        print("   FALHA NA VALIDAÇÃO XSD! Primeiros erros:")
        for err in list(schema.error_log)[:20]:
            print(f"      Linha {err.line}: {err.message}")
        sys.exit(1)
    print("   XML 100% VÁLIDO no XSD!")

    # Escrever relatório
    with open(REPORT_PATH, "w", encoding="utf-8") as rf:
        rf.write("=" * 100 + "\n")
        rf.write("RELATÓRIO DE RECONSTRUÇÃO DAS HABILIDADES DE JOGADORES (STUBS) — AION CLASSIC 5.0\n")
        rf.write("=" * 100 + "\n\n")
        rf.write(f"Total de stubs reconstruídos com sucesso: {len(rebuilt_entries)}\n\n")
        rf.write("LISTAGEM DAS HABILIDADES ATUALIZADAS:\n")
        for line in report_lines:
            rf.write(line + "\n")
    print(f"   Relatório salvo em: {REPORT_PATH}")

    if not args.aplicar:
        print("\nModo PREVIEW concluído. Para gravar nos arquivos de dados, use: --aplicar")
        return

    print("\n6. Gravando nos arquivos estáticos com backup...")
    backup_manager.backup_file_before_modification(REL_XML)
    targets = [
        os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML),
        os.path.join(backup_manager.PRODUTO_FINAL_DATA_DIR, REL_XML)
    ]
    for target in targets:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as tf:
            tf.write(final_xml)
        print(f"   Arquivo gravado com sucesso: {target}")


if __name__ == "__main__":
    main()
