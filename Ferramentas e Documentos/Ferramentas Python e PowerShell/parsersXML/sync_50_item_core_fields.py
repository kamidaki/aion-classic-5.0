#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza campos basicos de catalogo dos itens Classic 5.0 Europe."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from lxml import etree

import backup_manager
import rebuild_50_item_templates as templates


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CLIENT_ITEMS = PROJECT_ROOT / "5 - Documentação e Referências" / "3 - Client 5.0 - Dados Extraidos" / "data" / "europe" / "Items" / "client_items.xml"
RELATIVE_TEMPLATE = "items/item_templates.xml"
SOURCE = Path(backup_manager.SERVER_DATA_DIR) / RELATIVE_TEMPLATE
PRODUCT = Path(backup_manager.PRODUTO_FINAL_DATA_DIR) / RELATIVE_TEMPLATE
XSD = Path(backup_manager.SERVER_DATA_DIR) / "items" / "item_templates.xsd"
FIELDS = {"id", "level", "price", "max_stack_count", "quality", "race_permitted", "attack_type"}
MANAGED = ("level", "price", "max_stack_count", "quality", "race", "attack_type")
QUALITY = {
    "junk": "JUNK", "common": "COMMON", "rare": "RARE", "legend": "LEGEND",
    "legendary": "LEGEND", "unique": "UNIQUE", "epic": "EPIC", "mythic": "MYTHIC", "divinity": "DIVINITY",
}
RACE = {"pc_light": "ELYOS", "pc_dark": "ASMODIANS", "pc_light pc_dark": "PC_ALL", "all": "PC_ALL"}
ATTACK = {
    "physical": "PHYSICAL", "magic": "MAGICAL", "magical": "MAGICAL",
    "magical_earth": "MAGICAL_EARTH", "magical_water": "MAGICAL_WATER",
    "magical_wind": "MAGICAL_WIND", "magical_fire": "MAGICAL_FIRE",
}
DEFAULTS = {"price": "0", "max_stack_count": "1", "race": "PC_ALL"}
INT_MIN = -2_147_483_648
INT_MAX = 2_147_483_647


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_client() -> dict[str, dict[str, str]]:
    result = {}
    for _, element in ET.iterparse(CLIENT_ITEMS, events=("end",)):
        if element.tag != "client_item":
            continue
        data = {child.tag: (child.text or "").strip() for child in element if child.tag in FIELDS}
        if data.get("id"):
            result[data["id"]] = data
        element.clear()
    return result


def canonical(item: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    values, pending = {}, {}
    for name in ("level", "price", "max_stack_count"):
        raw = item.get(name, "")
        if not raw:
            continue
        try:
            number = int(raw)
        except ValueError:
            pending[name] = f"{name}={raw} nao e inteiro"
            continue
        if number < INT_MIN or number > INT_MAX:
            pending[name] = f"{name}={raw} excede xs:int/Java int"
            continue
        if name == "max_stack_count" and number < 1:
            pending[name] = f"max_stack_count={raw} viola o minimo operacional de uma unidade"
            continue
        values[name] = str(number)

    quality = item.get("quality", "").lower()
    if quality:
        if quality in QUALITY:
            values["quality"] = QUALITY[quality]
        else:
            pending["quality"] = "quality=" + quality

    race = " ".join(item.get("race_permitted", "").lower().split())
    if race:
        if race in RACE:
            values["race"] = RACE[race]
        else:
            pending["race"] = "race_permitted=" + race

    attack = item.get("attack_type", "").lower()
    if attack:
        if attack in ATTACK:
            values["attack_type"] = ATTACK[attack]
        else:
            pending["attack_type"] = "attack_type=" + attack
    return values, pending


def set_or_remove(head: str, name: str, value: str | None) -> str:
    pattern = r"\s+" + name + r'="[^"]*"'
    if value is None:
        return re.sub(pattern, "", head, count=1)
    if re.search(pattern, head):
        return re.sub(pattern, f' {name}="{templates.esc(value)}"', head, count=1)
    return head.rstrip() + f' {name}="{templates.esc(value)}"'


def generate(raw: bytes, client: dict[str, dict[str, str]]) -> tuple[bytes, list[tuple], list[tuple], collections.Counter]:
    report, pending = [], []
    changed_fields = collections.Counter()

    def replace(match: re.Match) -> str:
        attrs = dict(templates.ATTR_RE.findall(match.group(1)))
        item_id = attrs.get("id")
        official = client.get(item_id)
        if official is None:
            return match.group(0)
        expected, unresolved = canonical(official)
        pending.extend((item_id, value) for value in unresolved.values())
        head = match.group(1)
        changes = []
        for name in MANAGED:
            if name in unresolved:
                continue
            new = expected.get(name)
            if new == DEFAULTS.get(name):
                new = None
            old = attrs.get(name)
            old_effective = old if old is not None else DEFAULTS.get(name)
            expected_effective = expected.get(name, DEFAULTS.get(name))
            if old_effective == expected_effective:
                continue
            head = set_or_remove(head, name, new)
            changes.append(f"{name}:{old_effective or '<ausente>'}->{expected_effective or '<ausente>'}")
            changed_fields[name] += 1
        if not changes:
            return match.group(0)
        report.append((item_id, " | ".join(changes)))
        if match.group(2) == "/>":
            return "\t<item_template" + head + "/>"
        return "\t<item_template" + head + ">" + (match.group(3) or "") + "</item_template>"

    updated = templates.BLOCK_RE.sub(replace, raw.decode("utf-8")).encode("utf-8")
    return updated, report, pending, changed_fields


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    source_raw, product_raw = SOURCE.read_bytes(), PRODUCT.read_bytes()
    if sha256(source_raw) != sha256(product_raw):
        raise SystemExit("Fonte e produto final estao diferentes")
    client = read_client()
    updated, report, pending, changed_fields = generate(source_raw, client)
    etree.XMLSchema(etree.parse(str(XSD))).assertValid(etree.fromstring(updated, parser=etree.XMLParser(huge_tree=True)))
    print(f"Itens oficiais: {len(client)}")
    print(f"Templates alterados: {len(report)}")
    print("Campos alterados: " + ", ".join(f"{name}={changed_fields[name]}" for name in MANAGED))
    print(f"Valores pendentes: {len(pending)}")
    for value, count in collections.Counter(value for _, value in pending).most_common():
        print(f"  {count}x {value}")
    for item_id, value in pending[:30]:
        print(f"  {item_id}: {value}")
    if len(pending) > 30:
        print("Ultimas pendencias:")
        for item_id, value in pending[-20:]:
            print(f"  {item_id}: {value}")
    if not args.aplicar:
        print("Modo de verificacao: nenhum arquivo gravado")
        return
    backup_manager.backup_file_before_modification(RELATIVE_TEMPLATE)
    SOURCE.write_bytes(updated)
    PRODUCT.write_bytes(updated)
    report_dir = Path(backup_manager.get_current_session())
    with (report_dir / "relatorio_sync_item_core_fields_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "alteracoes"))
        writer.writerows(report)
    with (report_dir / "pendencias_item_core_fields_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "pendencia"))
        writer.writerows(pending)
    print(f"SHA-256 sincronizado: {sha256(updated)}")


if __name__ == "__main__":
    main()
