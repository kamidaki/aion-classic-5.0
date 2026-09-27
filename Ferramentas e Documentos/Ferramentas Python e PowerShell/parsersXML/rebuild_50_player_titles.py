#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstrói os 74 títulos do Classic 5.0 sem apagar o legado persistido.

Os IDs 408..481 vêm de ``data/PC/client_titles.xml``. Títulos 1..300 são
mantidos como camada de compatibilidade para personagens e quests legadas;
eles não são reintroduzidos nos cartões de título atuais.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import html
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from lxml import etree

import backup_manager
import rebuild_50_item_templates as item_templates


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CLIENT_ROOT = PROJECT_ROOT / "5 - Documentação e Referências" / "3 - Client 5.0 - Dados Extraidos"
CLIENT_TITLES = CLIENT_ROOT / "data" / "PC" / "client_titles.xml"
CLIENT_STRINGS = CLIENT_ROOT / "data" / "Strings" / "client_strings_quest.xml"
RELATIVE_TITLES = "player_titles.xml"
SOURCE = Path(backup_manager.SERVER_DATA_DIR) / RELATIVE_TITLES
PRODUCT = Path(backup_manager.PRODUTO_FINAL_DATA_DIR) / RELATIVE_TITLES
XSD = Path(backup_manager.SERVER_DATA_DIR) / "static_data.xsd"
REPORT = Path(__file__).with_name("relatorio_player_titles_50.txt")

ADD_STATS = {
    "str": "POWER", "vit": "HEALTH", "agi": "AGILITY", "dex": "ACCURACY",
    "kno": "KNOWLEDGE", "wil": "WILL", "maxhp": "MAXHP", "maxmp": "MAXMP",
    "maxfp": "FLY_TIME", "physicaldefend": "PHYSICAL_DEFENSE", "magicalresist": "MAGICAL_RESIST",
    "magicalskillboostresist": "MAGIC_SKILL_BOOST_RESIST", "dodge": "EVASION", "block": "BLOCK",
    "parry": "PARRY", "critical": "PHYSICAL_CRITICAL", "magicalcritical": "MAGICAL_CRITICAL",
    "phyattack": "PHYSICAL_ATTACK", "magicalskillboost": "BOOST_MAGICAL_SKILL",
    "hitaccuracy": "PHYSICAL_ACCURACY", "magicalhitaccuracy": "MAGICAL_ACCURACY",
    "healskillboost": "HEAL_BOOST", "hpregen": "REGEN_HP", "mpregen": "REGEN_MP",
    "criticaldamageboost": "CRITICAL_DAMAGE_BOOST",
    "pvpattackratio": "PVP_ATTACK_RATIO", "pvpdefendratio": "PVP_DEFEND_RATIO",
    "pveattackratio": "PVE_ATTACK_RATIO",
}
MULTI_STATS = {
    "allattackratio": ("PVP_ATTACK_RATIO", "PVE_ATTACK_RATIO"),
    "alldefendratio": ("PVP_DEFEND_RATIO", "PVE_DEFEND_RATIO"),
}
PERCENT_STATS = {
    "speed": "SPEED", "attackdelay": "ATTACK_SPEED", "boostcastingtime": "BOOST_CASTING_TIME",
    "flyspeed": "FLY_SPEED",
}
PERMILLE_STATS = {
    "speedratio": "SPEED", "attackdelayratio": "ATTACK_SPEED",
    "boostcastingtimeratio": "BOOST_CASTING_TIME", "flyspeedratio": "FLY_SPEED",
}
NEGATIVE = {"attackdelay", "attackdelayratio"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_strings() -> dict[str, tuple[int, str]]:
    result = {}
    for node in ET.parse(CLIENT_STRINGS).getroot().findall("string"):
        name = (node.findtext("name") or "").strip().upper()
        if name.startswith("STR_ALL_TITLE"):
            result[name] = (int(node.findtext("id")), (node.findtext("body") or name).strip())
    return result


def parse_value(raw: str) -> tuple[int, bool]:
    value = raw.strip()
    percent = value.endswith("%")
    return int(float(value.rstrip("%"))), percent


def modifiers(node: ET.Element, pending: collections.Counter) -> list[tuple[str, str, int]]:
    result = []
    attrs = node.find("bonus_attrs")
    for data in [] if attrs is None else attrs.findall("data"):
        parts = (data.findtext("bonus_attr") or "").split()
        if len(parts) < 2:
            continue
        source = parts[0].lower()
        value, explicit_percent = parse_value(parts[-1])
        if source in MULTI_STATS:
            result.extend(("add", stat, value) for stat in MULTI_STATS[source])
        elif source in ADD_STATS:
            result.append(("add", ADD_STATS[source], value))
        elif source in PERMILLE_STATS and not explicit_percent:
            result.append(("permille", PERMILLE_STATS[source], -value if source in NEGATIVE else value))
        elif source in PERCENT_STATS and explicit_percent:
            result.append(("rate", PERCENT_STATS[source], -value if source in NEGATIVE else value))
        else:
            pending[source] += 1
    return result


def render_title(node: ET.Element, strings: dict[str, tuple[int, str]], pending: collections.Counter) -> str:
    title_id = int(node.findtext("id"))
    string_name = (node.findtext("desc") or "").strip().upper()
    name_id, body = strings[string_name]
    lines = [f'\t<title id="{title_id}" nameId="{name_id}" desc="{html.escape(body, quote=True)}" race="PC_ALL">']
    mods = modifiers(node, pending)
    if mods:
        lines.append("\t\t<modifiers>")
        lines.extend(f'\t\t\t<{operation} name="{stat}" value="{value}" bonus="true"/>' for operation, stat, value in mods)
        lines.append("\t\t</modifiers>")
    lines.append("\t</title>")
    return "\n".join(lines)


def generate(raw: bytes) -> tuple[bytes, collections.Counter, list[int]]:
    strings = load_strings()
    official_nodes = ET.parse(CLIENT_TITLES).getroot().findall("client_title")
    ids = [int(node.findtext("id")) for node in official_nodes]
    if ids != list(range(408, 482)):
        raise SystemExit(f"Catálogo oficial inesperado: {len(ids)} IDs, faixa {min(ids)}..{max(ids)}")

    pending = collections.Counter()
    rendered = [render_title(node, strings, pending) for node in official_nodes]
    text = raw.decode("utf-8")
    # Permite reexecução idempotente, substituindo somente a faixa Classic atual.
    text = re.sub(r'\s*<title id="(?:4(?:0[8-9]|[1-7][0-9]|8[01]))"(?=\s).*?</title>', "", text, flags=re.S)
    insertion = "\n" + "\n".join(rendered) + "\n"
    text = text.replace("</player_titles>", insertion + "</player_titles>")
    return text.encode("utf-8"), pending, ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()

    source_raw = SOURCE.read_bytes()
    product_raw = PRODUCT.read_bytes()
    if sha256(source_raw) != sha256(product_raw):
        raise SystemExit("player_titles.xml da fonte e do Produto Final estão diferentes")
    updated, pending, ids = generate(source_raw)
    etree.XMLSchema(etree.parse(str(XSD))).assertValid(
        etree.fromstring(updated, parser=etree.XMLParser(huge_tree=True)))

    root = ET.fromstring(updated)
    all_ids = [int(node.get("id")) for node in root.findall("title")]
    if len(all_ids) != len(set(all_ids)):
        raise SystemExit("IDs duplicados no player_titles.xml gerado")
    REPORT.write_text(
        "rebuild_50_player_titles.py\n"
        f"títulos oficiais reconstruídos: {len(ids)} ({min(ids)}..{max(ids)})\n"
        f"títulos legados preservados para compatibilidade: {sum(title_id < 408 for title_id in all_ids)}\n"
        f"atributos oficiais sem mapeamento: {sum(pending.values())}\n"
        + "".join(f"  {name}: {count}\n" for name, count in sorted(pending.items())),
        encoding="utf-8")
    print(f"Títulos oficiais reconstruídos: {len(ids)}")
    print(f"Templates totais com camada legada: {len(all_ids)}")
    print(f"Atributos sem mapeamento: {sum(pending.values())}")
    print(f"SHA-256 gerado: {sha256(updated)}")
    if not args.aplicar:
        print("Modo de verificação: nenhum arquivo gravado")
        return
    backup_manager.backup_file_before_modification(RELATIVE_TITLES)
    SOURCE.write_bytes(updated)
    PRODUCT.write_bytes(updated)
    print("Fonte e Produto Final sincronizados")


if __name__ == "__main__":
    main()
