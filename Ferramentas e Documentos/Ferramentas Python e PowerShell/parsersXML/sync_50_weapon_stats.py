#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza os atributos diretos de weapon_stats com o Classic 5.0 Europe."""

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
FIELD_MAP = (
    ("min_damage", "min_damage", 1), ("max_damage", "max_damage", 1),
    ("attack_delay", "attack_speed", 1), ("critical", "critical", 1),
    ("hit_accuracy", "physical_accuracy", 1), ("parry", "parry", 1),
    ("magical_hit_accuracy", "magical_accuracy", 1),
    ("magical_skill_boost", "boost_magical_skill", 1),
    ("attack_range", "attack_range", 1000), ("hit_count", "hit_count", 1),
    ("reduce_max", "reduce_max", 1),
)
FIELDS = {"id"} | {source for source, _, _ in FIELD_MAP}
WEAPON_RE = re.compile(r"<weapon_stats\b([^>]*?)/?>")
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
    for source, target, multiplier in FIELD_MAP:
        raw = item.get(source, "")
        if raw == "":
            continue
        try:
            value = int(round(float(raw) * multiplier))
        except ValueError:
            pending[target] = f"{source}={raw} nao e numerico"
            continue
        if value < 0 or value > INT_MAX:
            pending[target] = f"{source}={raw} fora do intervalo operacional"
            continue
        values[target] = str(value)
    return values, pending


def set_or_remove(head: str, name: str, value: str) -> str:
    pattern = r"\s+" + name + r'="[^"]*"'
    if value == "0":
        return re.sub(pattern, "", head, count=1)
    if re.search(pattern, head):
        return re.sub(pattern, f' {name}="{value}"', head, count=1)
    return head.rstrip() + f' {name}="{value}"'


def insert_weapon_stats(inner: str, child: str) -> str:
    for tag in ("stigma", "godstone", "actions", "modifiers"):
        matches = list(re.finditer(r"</" + tag + r">", inner))
        if matches:
            pos = matches[-1].end()
            return inner[:pos] + "\n\t\t" + child + inner[pos:]
    return "\n\t\t" + child + inner


def generate(raw: bytes, client: dict[str, dict[str, str]]) -> tuple[bytes, list[tuple], list[tuple], collections.Counter]:
    report, pending = [], []
    changed_fields = collections.Counter()

    def replace(match: re.Match) -> str:
        item_id = dict(templates.ATTR_RE.findall(match.group(1))).get("id")
        official = client.get(item_id)
        if official is None:
            return match.group(0)
        expected, unresolved = canonical(official)
        if not expected and not unresolved:
            return match.group(0)
        pending.extend((item_id, value) for value in unresolved.values())
        inner = match.group(3) or ""
        weapon = WEAPON_RE.search(inner)
        current = dict(templates.ATTR_RE.findall(weapon.group(1))) if weapon else {}
        head = weapon.group(1).rstrip().removesuffix("/") if weapon else ""
        changes = []
        for name, value in expected.items():
            if name in unresolved:
                continue
            old = current.get(name, "0")
            if old == value:
                continue
            head = set_or_remove(head, name, value)
            changes.append(f"{name}:{old}->{value}")
            changed_fields[name] += 1
        if not changes:
            return match.group(0)
        child = "<weapon_stats" + head.rstrip() + "/>"
        if weapon:
            inner = inner[:weapon.start()] + child + inner[weapon.end():]
        else:
            inner = insert_weapon_stats(inner, child)
        report.append((item_id, " | ".join(changes)))
        if match.group(2) == "/>":
            return "\t<item_template" + match.group(1) + ">" + inner + "\n\t</item_template>"
        return "\t<item_template" + match.group(1) + ">" + inner + "</item_template>"

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
    print("Campos alterados: " + ", ".join(f"{target}={changed_fields[target]}" for _, target, _ in FIELD_MAP))
    print(f"Valores pendentes: {len(pending)}")
    for value, count in collections.Counter(value for _, value in pending).most_common(20):
        print(f"  {count}x {value}")
    if not args.aplicar:
        print("Modo de verificacao: nenhum arquivo gravado")
        return
    backup_manager.backup_file_before_modification(RELATIVE_TEMPLATE)
    SOURCE.write_bytes(updated)
    PRODUCT.write_bytes(updated)
    report_dir = Path(backup_manager.get_current_session())
    with (report_dir / "relatorio_sync_weapon_stats_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "alteracoes"))
        writer.writerows(report)
    with (report_dir / "pendencias_weapon_stats_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "pendencia"))
        writer.writerows(pending)
    print(f"SHA-256 sincronizado: {sha256(updated)}")


if __name__ == "__main__":
    main()
