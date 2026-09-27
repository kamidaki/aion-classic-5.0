#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_item_templates.py

Reconstroi, a partir do client_items.xml do Classic 5.0, os templates de item em que o servidor ainda carrega
o conteudo de outro item da base 4.8 (a 5.0 reaproveitou o id para outro item: o cName nao bate) e corrige
desc/name dos itens que so tem o id de texto errado.

As regras cliente -> servidor foram medidas nos itens cujo cName ja bate com o cliente. O modo --verificar mostra
a precisao de cada regra nesses itens (validacao cruzada em duas metades), monta o XML novo em memoria e valida
contra o XSD, sem gravar nada. O modo --aplicar faz o mesmo, grava backup (backup_manager) e escreve o arquivo
no fonte e no Produto Final substituindo apenas os blocos alterados; o resto do arquivo fica byte a byte igual.

Gerado: atributos (nome, texto, nivel, qualidade, preco, mask, grupo, restricoes por classe, enchant, slots...),
modifiers (stats do equipamento e da manastone), weapon_stats, godstone e as acoes skilluse, dye, craftlearn,
decompose, titleadd e cosmetic.
NAO gerado e listado no relatorio:
  - stigma: gerado pelo fix_50_stigma.py (gain skills, requires e fragmentos do client_items); aqui ele e so preservado.
  - enchant (acao das manastones): o count varia pelo nivel e nao existe no cliente; o encaixe nao depende dele.
  - skilllearn, queststart, expandinventory, remodel, charge/improve, toypetspawn, adoptpet, assemble,
    instancetimeclear, uselimits, acquisition, disposition, tradein_list, inventory, idian: sem fonte confiavel.

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python rebuild_50_item_templates.py --cliente "<pasta dos XMLs do cliente 5.0>" --verificar
    python rebuild_50_item_templates.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar
A pasta tambem pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import csv
import glob
import hashlib
import html
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_XML = "items/item_templates.xml"
REL_XSD = "items/item_templates.xsd"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
NL = "\r\n"

# Campos de classe do cliente -> ordinal do enum PlayerClass (ItemTemplate.getRequiredLevel indexa pelo ordinal).
# 0..11 medidos nos itens que batem (~99%); o cliente troca cleric/priest em relacao ao servidor.
# 12..24 pelo nome, seguindo PlayerClass.getStartingClassFor / getPlayerClassByString.
RESTRICT_SOURCES = ["warrior", "fighter", "knight", "scout", "assassin", "ranger", "mage", "wizard", "elementalist",
                    "cleric", "priest", "chanter", "monk", "thunderer", "thunderer", "striker", "battlemaster",
                    "orchestrator", "lumines", "engineer", "gunner", "runewarrior", "runeblade", None, "gunner"]
ORD_ALL = 23
CLASS_FIELDS = sorted({f for f in RESTRICT_SOURCES if f})
CLASS_MAX_FIELDS = [f + "_max" for f in CLASS_FIELDS]

QUALITY = {"junk": "JUNK", "common": "COMMON", "rare": "RARE", "legend": "LEGEND", "unique": "UNIQUE", "epic": "EPIC", "mythic": "MYTHIC"}
RACE = {"pc_light": "ELYOS", "pc_dark": "ASMODIANS"}

# ItemMask (model/items/ItemMask.java) <- flags do cliente
MASK_FLAGS = [(1, "lore"), (2, "can_exchange"), (4, "can_sell_to_npc"), (8, "can_deposit_to_character_warehouse"),
              (16, "can_deposit_to_account_warehouse"), (32, "can_deposit_to_guild_warehouse"), (64, "breakable"),
              (128, "soul_bind"), (256, "remove_when_logout"), (512, "no_enchant"), (1024, "can_proc_enchant"),
              (2048, "can_composite_weapon"), (8192, "can_split"), (16384, "breakable")]

# Stats base do cliente -> modifier (bonus=false). Medidos: 99-100%.
BASE_MODS = {"physical_defend": ("add", "PHYSICAL_DEFENSE"), "magical_resist": ("add", "MAGICAL_RESIST"),
             "dodge": ("add", "EVASION"), "block": ("add", "BLOCK"), "damage_reduce": ("rate", "DAMAGE_REDUCE"),
             "magical_skill_boost_resist": ("add", "MAGIC_SKILL_BOOST_RESIST")}
# bonus_attrN e stat_enchant_type (manastone) do cliente -> modifier (bonus=true); "X%" vira rate.
# Medidos: 84-100% (manastones: 100% nas que o servidor tem stat). Os que nao aparecem nos itens que batem
# foram ligados pelo nome exato do StatEnum.
BONUS_MODS = {"str": "POWER", "vit": "HEALTH", "dex": "ACCURACY", "agi": "AGILITY", "kno": "KNOWLEDGE", "wil": "WILL",
              "maxhp": "MAXHP", "maxmp": "MAXMP", "concentration": "CONCENTRATION", "physicaldefend": "PHYSICAL_DEFENSE",
              "magicalresist": "MAGICAL_RESIST", "magicalskillboost": "BOOST_MAGICAL_SKILL", "dodge": "EVASION",
              "phyattack": "PHYSICAL_ATTACK", "boosthate": "BOOST_HATE", "parry": "PARRY", "critical": "PHYSICAL_CRITICAL",
              "hitaccuracy": "PHYSICAL_ACCURACY", "attackdelay": "ATTACK_SPEED", "attackdelayratio": "ATTACK_SPEED",
              "flyspeed": "FLY_SPEED", "magicalhitaccuracy": "MAGICAL_ACCURACY", "pvpdefendratio": "PVP_DEFEND_RATIO",
              "maxfp": "FLY_TIME", "block": "BLOCK", "magicalcritical": "MAGICAL_CRITICAL",
              "speed": "SPEED", "speedratio": "SPEED",
              "physicalcriticalreducerate": "PHYSICAL_CRITICAL_RESIST", "healskillboost": "HEAL_BOOST",
              "boostcastingtime": "BOOST_CASTING_TIME", "boostcastingtimeratio": "BOOST_CASTING_TIME",
              "magicalattack": "MAGICAL_ATTACK", "physicalcriticaldamagereduce": "PHYSICAL_CRITICAL_DAMAGE_REDUCE",
              "magicalcriticaldamagereduce": "MAGICAL_CRITICAL_DAMAGE_REDUCE",
              "magicalcriticalreducerate": "MAGICAL_CRITICAL_RESIST", "elementaldefendfire": "FIRE_RESISTANCE",
              "elementaldefendearth": "EARTH_RESISTANCE", "elementaldefendair": "WIND_RESISTANCE",
              "elementaldefendwater": "WATER_RESISTANCE", "pvpattackratio": "PVP_ATTACK_RATIO",
              "arparalyze": "PARALYZE_RESISTANCE", "arsilence": "SILENCE_RESISTANCE",
              "arsleep": "SLEEP_RESISTANCE", "arroot": "ROOT_RESISTANCE", "arblind": "BLIND_RESISTANCE",
              "archarm": "CHARM_RESISTANCE", "ardisease": "DISEASE_RESISTANCE", "arfear": "FEAR_RESISTANCE",
              "arcurse": "CURSE_RESISTANCE", "arconfuse": "CONFUSE_RESISTANCE", "arstun": "STUN_RESISTANCE",
              "arperification": "PERIFICATION_RESISTANCE", "arstumble": "STUMBLE_RESISTANCE",
              "arstagger": "STAGGER_RESISTANCE", "aropenareial": "OPENAERIAL_RESISTANCE",
              "arsnare": "SNARE_RESISTANCE", "arslow": "SLOW_RESISTANCE", "arspin": "SPIN_RESISTANCE",
              "silence_arp": "SILENCE_RESISTANCE_PENETRATION", "paralyze_arp": "PARALYZE_RESISTANCE_PENETRATION",
              "arpoison": "POISON_RESISTANCE", "arbleed": "BLEED_RESISTANCE", "magicalskillboostresist": "MAGIC_SKILL_BOOST_RESIST",
              "magical_resist": "MAGICAL_RESIST", "questexpboost": "BOOST_QUEST_XP_RATE",
              "bleedreduceratio": "BLEED_DAMAGE_REDUCE_RATIO",
              "pvedefendratio": "PVE_DEFEND_RATIO", "pvedefendratio_physical": "PVE_DEFEND_RATIO_PHYSICAL",
              "pvedefendratio_magical": "PVE_DEFEND_RATIO_MAGICAL", "pveattackratio": "PVE_ATTACK_RATIO",
              "pveattackratio_physical": "PVE_ATTACK_RATIO_PHYSICAL", "pveattackratio_magical": "PVE_ATTACK_RATIO_MAGICAL"}
MULTI_BONUS_MODS = {
    "allattackratio": ("PVP_ATTACK_RATIO", "PVE_ATTACK_RATIO"),
    "alldefendratio": ("PVP_DEFEND_RATIO", "PVE_DEFEND_RATIO"),
    "elementaldefendall": ("WATER_RESISTANCE", "WIND_RESISTANCE", "FIRE_RESISTANCE", "EARTH_RESISTANCE"),
}
NEGATE = {"attackdelay", "attackdelayratio"}  # cliente "attackDelay 3%" = servidor rate ATTACK_SPEED -3
# stats de manastone (stat_enchant, sem "%") que sao taxa
PCT_STATS = {"attackdelay", "attackdelayratio", "speed", "speedratio", "flyspeed", "boosthate", "boostcastingtime", "boostcastingtimeratio"}

# weapon_stats <- campos do cliente (97-100% nos itens que batem)
WS_FIELDS = [("min_damage", "min_damage", 1), ("max_damage", "max_damage", 1), ("attack_speed", "attack_delay", 1),
             ("critical", "critical", 1), ("physical_accuracy", "hit_accuracy", 1), ("parry", "parry", 1),
             ("magical_accuracy", "magical_hit_accuracy", 1), ("boost_magical_skill", "magical_skill_boost", 1),
             ("attack_range", "attack_range", 1000), ("hit_count", "hit_count", 1)]

# Campos do cliente que indicam uma funcao que este parser nao gera (so para o relatorio)
NOT_GENERATED = {"gain_skill1": "stigma", "skill_to_learn": "skilllearn", "toy_pet_name": "toypetspawn",
                 "func_pet_name": "adoptpet", "extra_inventory": "inventory", "abyss_point": "acquisition AP",
                 "abyss_item": "acquisition item", "charge_level": "improve/charge", "assembly_item": "assemble",
                 "reset_instance_coolt_sync_id": "instancetimeclear"}

KEEP = {"id", "name", "desc", "level", "price", "quality", "max_stack_count", "item_type", "race_permitted",
        "weapon_type", "armor_type", "equipment_slots", "attack_type", "option_slot_bonus", "no_enchant",
        "cannot_changeskin", "can_dye", "activation_skill", "activation_level", "activate_target", "activation_count",
        "casting_delay", "expire_time", "return_alias", "return_worldid", "weapon_boost_value", "proc_enchant_skill",
        "proc_enchant_skill_level", "proc_enchant_effect_occur_prob", "proc_enchant_effect_occur_left_prob",
        "craft_recipe_info", "cosmetic_name", "dyeing_color", "cash_title", "cash_available_minute",
        "disassembly_item", "mgrouptag", "tag", "quest", "icon_name", "stat_enchant_type", "stat_enchant_value"} \
    | {f for _, f in MASK_FLAGS} | set(BASE_MODS) | {c for _, c, _ in WS_FIELDS} | {"reduce_max"} \
    | set(CLASS_FIELDS) | set(CLASS_MAX_FIELDS) | set(NOT_GENERATED)

BLOCK_RE = re.compile(r'\t<item_template\b([^>]*?)(/>|>(.*?)</item_template>)', re.S)
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
MOD_RE = re.compile(r'<(add|sub|rate|set|abs|mean)\b([^>]*?)/?>')
LEGACY_TAGS = ("godstone", "stigma", "idian", "uselimits", "improve", "acquisition", "disposition", "tradein_list", "inventory")
STONE_GROUPS = ("MANASTONE", "SPECIAL_MANASTONE")


def esc(v):
    return str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def num(v):
    if v in (None, ""):
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def low(d, k):
    return (d.get(k) or "").strip().lower()


def iter_depth1(path, keep=None):
    depth = 0
    for ev, el in ET.iterparse(path, events=("start", "end")):
        if ev == "start":
            depth += 1
            continue
        depth -= 1
        if depth == 1:
            yield {c.tag: (c.text or "").strip() for c in el if keep is None or keep(c.tag)}
            el.clear()


def load_strings(client_dir):
    n2id, n2b = {}, {}
    pat = re.compile(r'<string>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>(?:\s*<body>([^<]*)</body>)?', re.S)
    candidates = (
        os.path.join(client_dir, "data", "Strings"),
        os.path.join(client_dir, "Strings", "strings"),
        os.path.join(client_dir, "Strings"),
    )
    strings_dir = next((p for p in candidates if os.path.isdir(p)), None)
    if strings_dir is None:
        return n2id, n2b
    for p in sorted(glob.glob(os.path.join(glob.escape(strings_dir), "*.xml"))):
        raw = open(p, "rb").read()
        text = raw.decode("utf-16", "ignore") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
        for sid, sname, body in pat.findall(text):
            key = sname.strip().upper()
            n2id[key] = sid
            if body and body.strip():
                n2b[key] = html.unescape(body.strip())
    return n2id, n2b


def load_name_ids(path):
    return {d["name"].lower(): d["id"] for d in iter_depth1(path, lambda t: t in ("id", "name")) if d.get("name") and d.get("id")}


def xsd_enum(xsd_text, type_name):
    m = re.search(r'<xs:simpleType name="' + type_name + r'">(.*?)</xs:simpleType>', xsd_text, re.S)
    return set(re.findall(r'value="([^"]+)"', m.group(1))) if m else set()


def category(d):
    if low(d, "weapon_type") not in ("", "none"):
        return "arma"
    if low(d, "armor_type") not in ("", "none"):
        return "armadura"
    return "acessorio" if low(d, "equipment_slots") not in ("", "none") else "outro"


# ------------------------------------------------------------------------------------------------ geradores

def gen_mask(d):
    m = 0
    for bit, f in MASK_FLAGS:
        if (d.get(f) or "").upper() == "TRUE":
            m |= bit
    if d.get("cannot_changeskin") == "0":
        m |= 4096  # REMODELABLE
    if (d.get("can_dye") or "0") not in ("0", "", "FALSE"):
        m |= 32768  # DYEABLE
    return m


def gen_restrict(d, suffix=""):
    if not any(f and f + suffix in d for f in RESTRICT_SOURCES):
        return [0 if suffix else 1] * len(RESTRICT_SOURCES)
    return [(num(d.get(f + suffix)) or 0) if f else 0 for f in RESTRICT_SOURCES]


def gen_mods(d, unmapped=None):
    out = []
    for field, (op, stat) in BASE_MODS.items():
        v = num(d.get(field))
        if v:
            out.append((op, stat, v, False))
    st, sv = low(d, "stat_enchant_type"), num(d.get("stat_enchant_value"))
    if st and sv:
        stats = MULTI_BONUS_MODS.get(st) or ((BONUS_MODS[st],) if st in BONUS_MODS else ())
        if stats:
            out.extend(("rate" if st in PCT_STATS else "add", stat, -sv if st in NEGATE else sv, True) for stat in stats)
        elif unmapped is not None:
            unmapped["manastone:" + st] += 1
    for key in sorted((k for k in d if re.fullmatch(r"bonus_attr\d+", k)), key=lambda k: int(k[10:])):
        parts = d[key].split()
        if len(parts) < 2:
            continue
        name, raw = parts[0].lower(), parts[-1]
        v = num(raw.rstrip("%"))
        if not v:
            continue
        stats = MULTI_BONUS_MODS.get(name) or ((BONUS_MODS[name],) if name in BONUS_MODS else ())
        if not stats:
            if unmapped is not None:
                unmapped[name] += 1
            continue
        out.extend(("rate" if raw.endswith("%") else "add", stat, -v if name in NEGATE else v, True) for stat in stats)
    return out


def gen_weapon_stats(d):
    if category(d) != "arma":
        return None
    ws = []
    for s, c, mul in WS_FIELDS:
        v = d.get(c)
        if v not in (None, ""):
            try:
                ws.append((s, str(int(round(float(v) * mul)))))
            except ValueError:
                pass
    rm = num(d.get("reduce_max"))
    if rm:
        ws.append(("reduce_max", str(rm)))
    return ws or None


def gen_actions(d, ctx):
    """Acoes na ordem da sequencia ItemActions do XSD."""
    acts = []
    skill = ctx.skills.get(low(d, "activation_skill"))
    if skill:
        acts.append(("skilluse", [("skillid", skill), ("level", d.get("activation_level") or "1")]))
    color = d.get("dyeing_color")
    if color:
        try:
            r, g, b = (int(x) for x in color.split(","))
            acts.append(("dye", [("color", f"{r:02x}{g:02x}{b:02x}")]))
        except ValueError:
            pass
    recipe = ctx.recipes.get(low(d, "craft_recipe_info"))
    if recipe:
        acts.append(("craftlearn", [("recipeid", recipe)]))
    if d.get("disassembly_item") == "1" and d.get("id") in ctx.decomposable:
        acts.append(("decompose", []))
    if d.get("cash_title"):
        a = [("titleid", d["cash_title"])]
        if (d.get("cash_available_minute") or "0") != "0":
            a.append(("minutes", d["cash_available_minute"]))
        acts.append(("titleadd", a))
    if d.get("cosmetic_name"):
        acts.append(("cosmetic", [("name", d["cosmetic_name"])]))
    return acts


def gen_godstone(d, ctx, group):
    if group != "GODSTONE":
        return None
    skill = ctx.skills.get(low(d, "proc_enchant_skill"))
    if not skill:
        return None
    a = [("skillid", skill), ("skilllvl", d.get("proc_enchant_skill_level") or "1")]
    if d.get("proc_enchant_effect_occur_prob"):
        a.append(("probability", d["proc_enchant_effect_occur_prob"]))
    if d.get("proc_enchant_effect_occur_left_prob"):
        a.append(("probabilityleft", d["proc_enchant_effect_occur_left_prob"]))
    return a


# ------------------------------------------------------------------------------------------------ regras aprendidas

def k1(d):
    return ("k1", low(d, "weapon_type"), low(d, "armor_type"), low(d, "equipment_slots"), d.get("mgrouptag", ""),
            "Q" if d.get("quest") else "", d.get("tag", ""))


def k2(d):
    return ("k2", low(d, "name").split("_")[0], low(d, "equipment_slots"))


def k3(d):
    return ("k3", re.sub(r"[\d_]+$", "", low(d, "icon_name")))


class Learned:
    """item_group (cascata de chaves), m_slots e max_enchant aprendidos nos itens que batem."""

    def __init__(self, ids, srv, cli):
        self.group_tables = [collections.defaultdict(collections.Counter) for _ in (k1, k2, k3)]
        base = collections.defaultdict(collections.Counter)
        me = collections.defaultdict(collections.Counter)
        for i in ids:
            d, a = cli[i], srv[i]["attrs"]
            for table, key in zip(self.group_tables, (k1, k2, k3)):
                table[key(d)][a.get("item_group", "NONE")] += 1
            cat = category(d)
            if cat in ("arma", "armadura") and not self.noslot(d) and low(d, "item_type") in ("", "normal"):
                base[low(d, "quality")][num(a.get("m_slots")) or 0] += 1
            if cat != "outro":
                me[(cat, low(d, "quality"), (d.get("no_enchant") or "-").upper())][a.get("max_enchant", "")] += 1
        self.base = {q: c.most_common(1)[0][0] for q, c in base.items()}
        delta = collections.defaultdict(collections.Counter)
        for i in ids:
            d = cli[i]
            if category(d) in ("arma", "armadura") and not self.noslot(d):
                delta[(low(d, "item_type") or "normal", low(d, "quality"))][(num(srv[i]["attrs"].get("m_slots")) or 0) - self.base.get(low(d, "quality"), 0)] += 1
        self.delta = {k: c.most_common(1)[0][0] for k, c in delta.items()}
        self.max_enchant_table = {k: c.most_common(1)[0][0] for k, c in me.items()}

    @staticmethod
    def noslot(d):
        return low(d, "armor_type") == "no_armor" or (d.get("no_enchant") or "").upper() == "TRUE"

    def group(self, d, valid):
        for table, key in zip(self.group_tables, (k1, k2, k3)):
            c = table.get(key(d))
            if c:
                total = sum(c.values())
                top, n = c.most_common(1)[0]
                if total >= 5 and n / total >= 0.9 and top in valid:
                    return top
        for table, key in zip(self.group_tables, (k1, k2, k3)):
            c = table.get(key(d))
            if c and c.most_common(1)[0][0] in valid:
                return c.most_common(1)[0][0]
        return "NONE"

    def m_slots(self, d):
        if category(d) not in ("arma", "armadura") or self.noslot(d):
            return 0
        q = low(d, "quality")
        return self.base.get(q, 0) + self.delta.get((low(d, "item_type") or "normal", q), 0)

    def max_enchant(self, d):
        cat = category(d)
        if cat == "outro":
            return ""
        return self.max_enchant_table.get((cat, low(d, "quality"), (d.get("no_enchant") or "-").upper()), "")


# ------------------------------------------------------------------------------------------------ montagem

class Ctx:
    pass


def build(iid, d, ctx, learned, unmapped=None, skipped=None):
    group = learned.group(d, ctx.enum_group)
    a = [("id", iid)]
    desc_key = (d.get("desc") or "").upper()
    a.append(("name", ctx.n2b.get(desc_key) or d.get("name", "")))
    a.append(("level", d.get("level") or "1"))
    a.append(("cName", d.get("name", "")))
    a.append(("mask", str(gen_mask(d))))
    a.append(("item_group", group))
    a.append(("quality", QUALITY.get(low(d, "quality"), "COMMON")))
    a.append(("price", str(num(d.get("price")) or 0)))
    r = gen_restrict(d)
    if any(v != 1 for i, v in enumerate(r) if i != ORD_ALL):
        a.append(("restrict", " ".join(map(str, r))))
    rm = gen_restrict(d, "_max")
    if any(rm):
        a.append(("restrict_max", " ".join(map(str, rm))))
    a.append(("desc", ctx.n2id.get(desc_key, "0")))
    at = (d.get("attack_type") or "").upper()
    if category(d) == "arma" and at:
        if at in ctx.enum_attack:
            a.append(("attack_type", at))
        elif skipped is not None:
            skipped["attack_type=" + at] += 1
    if RACE.get(low(d, "race_permitted")):
        a.append(("race", RACE[low(d, "race_permitted")]))
    it = (d.get("item_type") or "normal").upper()
    if it != "NORMAL":
        if it in ctx.enum_item_type:
            a.append(("item_type", it))
        elif skipped is not None:
            skipped["item_type=" + it] += 1
    ms = num(d.get("max_stack_count"))
    if ms and ms != 1:
        a.append(("max_stack_count", str(ms)))
    me = learned.max_enchant(d)
    if me:
        a.append(("max_enchant", me))
    slots = learned.m_slots(d)
    if slots:
        a.append(("m_slots", str(slots)))
    osb = num(d.get("option_slot_bonus"))
    if osb:
        a.append(("option_slot_bonus", str(osb)))
    tgt = (d.get("activate_target") or "").upper()
    if tgt:
        if tgt in ctx.enum_target:
            a.append(("activate_target", tgt))
        elif skipped is not None:
            skipped["activate_target=" + tgt] += 1
    for attr, field in (("activate_count", "activation_count"), ("casting_delay", "casting_delay"),
                        ("expire_time", "expire_time"), ("return_world", "return_worldid"),
                        ("weapon_boost", "weapon_boost_value")):
        v = num(d.get(field))
        if v:
            a.append((attr, str(v)))
    if d.get("return_alias"):
        a.append(("return_alias", d["return_alias"].upper()))
    return {"attrs": a, "group": group, "mods": gen_mods(d, unmapped), "actions": gen_actions(d, ctx),
            "godstone": gen_godstone(d, ctx, group), "ws": gen_weapon_stats(d)}


def render(t):
    head = "\t<item_template " + " ".join(f'{k}="{esc(v)}"' for k, v in t["attrs"])
    ch = []
    if t["mods"]:
        ch.append("\t\t<modifiers>")
        ch += [f'\t\t\t<{op} name="{stat}" value="{v}"' + (' bonus="true"' if b else "") + " />" for op, stat, v, b in t["mods"]]
        ch.append("\t\t</modifiers>")
    if t["actions"]:
        ch.append("\t\t<actions>")
        ch += ["\t\t\t<" + tag + "".join(f' {k}="{esc(v)}"' for k, v in at) + " />" for tag, at in t["actions"]]
        ch.append("\t\t</actions>")
    if t["godstone"]:
        ch.append("\t\t<godstone" + "".join(f' {k}="{esc(v)}"' for k, v in t["godstone"]) + " />")
    if t["ws"]:
        ch.append("\t\t<weapon_stats" + "".join(f' {k}="{v}"' for k, v in t["ws"]) + " />")
    return head + " />" if not ch else head + ">" + NL + NL.join(ch) + NL + "\t</item_template>"


# ------------------------------------------------------------------------------------------------ verificacao

def legacy_mods(inner):
    blk = re.search(r"<modifiers>(.*?)</modifiers>", inner, re.S)
    out = collections.Counter()
    for op, attrs in MOD_RE.findall(blk.group(1) if blk else ""):
        a = dict(ATTR_RE.findall(attrs))
        v = num(a.get("value"))
        if v is not None:
            out[(op, a.get("name"), v, a.get("bonus", "false") == "true")] += 1
    return out


def pct(a, b):
    return f"{100 * a / b:5.1f}%" if b else "  -  "


DEFAULTS = {"race": "PC_ALL", "item_type": "NORMAL"}


def verify(same, srv, cli, ctx):
    print("\n=== Precisao das regras nos itens cujo cName ja bate ===")
    halves = ([i for i in same if int(i) % 2 == 0], [i for i in same if int(i) % 2 == 1])
    grp = slo = men = n = 0
    for fit_ids, test_ids in ((halves[0], halves[1]), (halves[1], halves[0])):
        lr = Learned(fit_ids, srv, cli)
        for i in test_ids:
            d, a = cli[i], srv[i]["attrs"]
            n += 1
            grp += lr.group(d, ctx.enum_group) == a.get("item_group", "NONE")
            slo += lr.m_slots(d) == (num(a.get("m_slots")) or 0)
            men += lr.max_enchant(d) == a.get("max_enchant", "")
    print(f"  item_group  (validacao cruzada) {pct(grp, n)}")
    print(f"  m_slots     (validacao cruzada) {pct(slo, n)}")
    print(f"  max_enchant (validacao cruzada) {pct(men, n)}")

    c, gaps = collections.Counter(), collections.Counter()
    for i in same:
        d, s = cli[i], srv[i]
        t = build(i, d, ctx, ctx.learned)
        ga, la = dict(t["attrs"]), s["attrs"]
        leg = legacy_mods(s["inner"])
        c["n"] += 1
        if leg:
            c["mods_n"] += 1
            c["mods_ok"] += collections.Counter(t["mods"]) == leg
            if la.get("item_group") in STONE_GROUPS:
                c["stone_n"] += 1
                c["stone_ok"] += collections.Counter(t["mods"]) == leg
        elif t["mods"]:
            gaps["stats de manastone" if la.get("item_group") in STONE_GROUPS else "modifiers"] += 1
        lw = re.search(r"<weapon_stats\b([^>]*)/?>", s["inner"])
        if lw and t["ws"]:
            c["ws_n"] += 1
            current_ws = dict(ATTR_RE.findall(lw.group(1)))
            c["ws_ok"] += all(current_ws.get(k, "0") == v for k, v in t["ws"] if k in ("min_damage", "max_damage", "attack_speed", "hit_count", "attack_range"))
        if "restrict" in la:
            c["r_n"] += 1
            expected_restrict = ga.get("restrict", " ".join("1" for _ in RESTRICT_SOURCES)).split()
            current_restrict = la["restrict"].split()
            if len(current_restrict) < len(RESTRICT_SOURCES):
                fill = str(min(int(v) for v in current_restrict)) if current_restrict and all(int(v) for v in current_restrict) else "0"
                current_restrict += [fill] * (len(RESTRICT_SOURCES) - len(current_restrict))
            c["r_ok"] += all(current_restrict[i] == expected_restrict[i] for i in range(len(RESTRICT_SOURCES)) if i != ORD_ALL)
        c["r_pres"] += ("restrict" in ga) == ("restrict" in la)
        for k in ("level", "desc", "quality", "race", "item_type", "attack_type", "activate_target", "activate_count", "casting_delay", "expire_time"):
            lv, gv = la.get(k, DEFAULTS.get(k)), ga.get(k, DEFAULTS.get(k))
            if lv is not None or gv is not None:
                c[k + "_n"] += 1
                c[k + "_ok"] += lv == gv
        c["mask_ok"] += la.get("mask") == ga.get("mask")
        for tag, key in (("skilluse", "skillid"), ("craftlearn", "recipeid"), ("cosmetic", "name"), ("dye", "color"), ("titleadd", "titleid")):
            m = re.search(r"<" + tag + r'\b[^>]*\b' + key + r'="([^"]*)"', s["inner"])
            g = next((dict(at).get(key) for tg, at in t["actions"] if tg == tag), None)
            if m:
                c[tag + "_n"] += 1
                c[tag + "_ok"] += m.group(1) == g
            elif g:
                gaps[tag] += 1
        ld, gd = "<decompose" in s["inner"], any(tg == "decompose" for tg, _ in t["actions"])
        c["dec_tp"] += ld and gd
        c["dec_fp"] += gd and not ld
        c["dec_fn"] += ld and not gd
        m = re.search(r'<godstone\b[^>]*\bskillid="([^"]*)"', s["inner"])
        g = dict(t["godstone"]).get("skillid") if t["godstone"] else None
        if m:
            c["godstone_n"] += 1
            c["godstone_ok"] += m.group(1) == g
        elif g:
            gaps["godstone"] += 1
        if d.get("gain_skill1") and "<stigma" not in s["inner"]:
            gaps["stigma (nao gerado)"] += 1
    N = c["n"]
    print(f"  modifiers iguais (onde o servidor tem) {pct(c['mods_ok'], c['mods_n'])} ({c['mods_n']}) | manastones {pct(c['stone_ok'], c['stone_n'])} ({c['stone_n']})")
    print(f"  weapon_stats (dano/vel/alcance) {pct(c['ws_ok'], c['ws_n'])}  ({c['ws_n']} armas)")
    print(f"  restrict: presenca {pct(c['r_pres'], N)} | 24 entradas mapeadas iguais {pct(c['r_ok'], c['r_n'])}")
    for k in ("level", "desc", "quality", "race", "item_type", "attack_type", "activate_target", "activate_count", "casting_delay", "expire_time"):
        print(f"  {k:<16} {pct(c[k + '_ok'], c[k + '_n'])}  ({c[k + '_n']})")
    print(f"  mask identico                  {pct(c['mask_ok'], N)}  (diferenca esperada: regras de troca/armazem da 4.8 x 5.0)")
    for tag in ("skilluse", "craftlearn", "cosmetic", "dye", "titleadd", "godstone"):
        print(f"  {tag:<12} igual ao servidor {pct(c[tag + '_ok'], c[tag + '_n'])}  ({c[tag + '_n']})")
    print(f"  decompose    acertos={c['dec_tp']} a_mais={c['dec_fp']} faltando={c['dec_fn']}")
    print(f"  lacunas do servidor atual (o cliente define e o template nao tem; NAO corrigidas aqui): {dict(gaps)}")


# ------------------------------------------------------------------------------------------------ principal

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--catalogo", default=os.path.join("data", "europe", "Items", "client_items.xml"),
                    help="client_items.xml relativo a --cliente; o padrao e a camada Europe do cliente EU")
    ap.add_argument("--atualizar-nomes", action="store_true",
                    help="tambem troca o nome exibido pelo corpo da string extraida; por padrao preserva a localizacao do servidor")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    client_items_xml = os.path.join(args.cliente, args.catalogo)
    if not os.path.isfile(client_items_xml):
        sys.exit(f"client_items.xml nao encontrado em {client_items_xml}. Informe --cliente ou AION_CLIENT_XML_DIR.")
    src = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    prod = os.path.join(backup_manager.PRODUTO_FINAL_DATA_DIR, REL_XML)
    raw_src, raw_prod = open(src, "rb").read(), open(prod, "rb").read()
    if hashlib.sha256(raw_src).digest() != hashlib.sha256(raw_prod).digest():
        sys.exit("O item_templates.xml do fonte e do Produto Final estao diferentes. Sincronize antes de rodar.")
    text = raw_src.decode("utf-8")

    print("1. Lendo dados do cliente 5.0 e do servidor...")
    ctx = Ctx()
    ctx.n2id, ctx.n2b = load_strings(args.cliente)
    cli = {d["id"]: d for d in iter_depth1(client_items_xml, lambda t: t in KEEP or t.startswith("bonus_attr") or t.endswith("_max")) if d.get("id")}
    ctx.skills = load_name_ids(os.path.join(args.cliente, "data", "skills", "client_skills.xml"))
    ctx.recipes = load_name_ids(os.path.join(args.cliente, "data", "items", "client_combine_recipe.xml"))
    ctx.decomposable = set()
    for f in glob.glob(os.path.join(glob.escape(backup_manager.SERVER_DATA_DIR), "**", "*decompos*.xml"), recursive=True):
        ctx.decomposable |= set(re.findall(r'\b(?:item_?id|id)="(\d{9})"', open(f, encoding="utf-8", errors="replace").read()))
    xsd_text = open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD), encoding="utf-8").read()
    mod_xsd = open(os.path.join(backup_manager.SERVER_DATA_DIR, "modifiers.xsd"), encoding="utf-8").read()
    ctx.enum_group = xsd_enum(xsd_text, "ItemGroup")
    ctx.enum_attack = xsd_enum(xsd_text, "ItemAttackType")
    ctx.enum_item_type = xsd_enum(xsd_text, "itemType")
    ctx.enum_target = xsd_enum(xsd_text, "ItemActivationTarget")
    stat_names = set(re.findall(r'value="([A-Z_0-9]+)"', mod_xsd))
    missing = sorted(({s for _, s in BASE_MODS.values()} | set(BONUS_MODS.values())
                      | {stat for stats in MULTI_BONUS_MODS.values() for stat in stats}) - stat_names)
    if missing:
        sys.exit(f"Stats do mapeamento que nao existem no modifiers.xsd: {missing}")
    print(f"   itens: {len(cli)} | strings: {len(ctx.n2id)} | skills: {len(ctx.skills)} | receitas: {len(ctx.recipes)} | decomposicao: {len(ctx.decomposable)}")

    srv = {}
    for m in BLOCK_RE.finditer(text):
        attrs = {k: html.unescape(v) for k, v in ATTR_RE.findall(m.group(1))}
        if attrs.get("id"):
            srv[attrs["id"]] = {"attrs": attrs, "inner": m.group(3) or "", "span": m.span(), "head": m.span(1)}
    same = [i for i in cli if i in srv and srv[i]["attrs"].get("cName", "").lower() == low(cli[i], "name")]
    same_set = set(same)
    swapped = [i for i in cli if i in srv and i not in same_set]
    desc_fix = [i for i in same if (cli[i].get("desc") or "").upper() in ctx.n2id and srv[i]["attrs"].get("desc") != ctx.n2id[(cli[i].get("desc") or "").upper()]]
    print(f"   templates: {len(srv)} | batem: {len(same)} | trocados (reconstruir): {len(swapped)} | so texto errado: {len(desc_fix)}")
    only_srv = [i for i in srv if i not in cli]
    if only_srv:
        print(f"   AVISO: {len(only_srv)} templates sem item no cliente (mantidos como estao)")

    ctx.learned = Learned(same, srv, cli)
    verify(same, srv, cli, ctx)

    print("\n2. Montando os templates novos...")
    unmapped, skipped, dropped, gen, missing_func = (collections.Counter() for _ in range(5))
    edits, report = [], []
    for i in swapped:
        d, s = cli[i], srv[i]
        t = build(i, d, ctx, ctx.learned, unmapped, skipped)
        edits.append((s["span"][0], s["span"][1], render(t)))
        acts = re.search(r"<actions>(.*?)</actions>", s["inner"], re.S)
        for tag in set(re.findall(r"<(\w+)\b", acts.group(1))) if acts else ():
            if tag not in {tg for tg, _ in t["actions"]}:
                dropped["acao " + tag] += 1
        for tag in LEGACY_TAGS:
            if "<" + tag in s["inner"] and not t.get(tag):
                dropped[tag] += 1
        for key in ("mods", "ws", "godstone"):
            gen[key] += bool(t[key])
        gen["restrict"] += any(k == "restrict" for k, _ in t["attrs"])
        gen["m_slots"] += any(k == "m_slots" for k, _ in t["attrs"])
        for tg, _ in t["actions"]:
            gen["acao " + tg] += 1
        for field, label in NOT_GENERATED.items():
            if d.get(field) not in (None, "", "0"):
                missing_func[label] += 1
        if t["group"] in STONE_GROUPS:
            missing_func["enchant (manastone)"] += 1
        report.append((i, "reconstruido", s["attrs"].get("cName", ""), d.get("name", ""), s["attrs"].get("name", ""), dict(t["attrs"])["name"]))
    for i in desc_fix:
        s = srv[i]
        head = text[s["head"][0]:s["head"][1]]
        desc_key = (cli[i].get("desc") or "").upper()
        new_name = (ctx.n2b.get(desc_key) or s["attrs"].get("name", "")) if args.atualizar_nomes else s["attrs"].get("name", "")
        new_head = re.sub(r'(\sdesc=")[^"]*(")', lambda m: m.group(1) + ctx.n2id[desc_key] + m.group(2), head, count=1)
        if args.atualizar_nomes:
            new_head = re.sub(r'(\sname=")[^"]*(")', lambda m: m.group(1) + esc(new_name) + m.group(2), new_head, count=1)
        edits.append((s["head"][0], s["head"][1], new_head))
        report.append((i, "texto", s["attrs"].get("cName", ""), cli[i].get("name", ""), s["attrs"].get("name", ""), new_name))
    edits.sort()
    out, pos = [], 0
    for a, b, new in edits:
        out.append(text[pos:a])
        out.append(new)
        pos = b
    out.append(text[pos:])
    new_text = "".join(out)

    print(f"   gerado nos {len(swapped)} reconstruidos: {dict(gen)}")
    print(f"   funcoes que o item 5.0 tem no cliente e este parser NAO gera: {dict(missing_func.most_common())}")
    print(f"   conteudo da 4.8 descartado (era de outro item): {dict(dropped.most_common())}")
    if unmapped:
        print(f"   stats do cliente sem correspondente no servidor (ignorados): {dict(unmapped.most_common(12))}")
    if skipped:
        print(f"   valores fora do XSD (ignorados): {dict(skipped.most_common(12))}")

    print("3. Validando contra o XSD...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)))
    doc = etree.fromstring(new_text.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))
    if not schema.validate(doc):
        print("   XSD INVALIDO. Primeiros erros:")
        for e in list(schema.error_log)[:25]:
            print(f"     linha {e.line}: {e.message}")
        sys.exit(1)
    print("   XSD valido.")

    if not args.aplicar:
        print("\nModo --verificar: nada foi gravado.")
        return

    print("4. Gravando (com backup)...")
    backup_manager.backup_file_before_modification(REL_XML)
    for path in (src, prod):
        with open(path, "wb") as f:
            f.write(new_text.encode("utf-8"))
    rep = os.path.join(backup_manager.get_current_session(), "relatorio_rebuild_item_templates.csv")
    with open(rep, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "tipo", "cName_antigo", "cName_novo", "nome_antigo", "nome_novo"])
        w.writerows(report)
    print(f"   Gravado: {src}")
    print(f"   Gravado: {prod}")
    print(f"   Relatorio: {rep}")


if __name__ == "__main__":
    main()
