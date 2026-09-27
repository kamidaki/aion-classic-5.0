#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza restricoes de classe e nivel dos itens Classic 5.0 Europe."""

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
RESTRICT_SOURCES = ("warrior", "fighter", "knight", "scout", "assassin", "ranger", "mage", "wizard", "elementalist",
                    "cleric", "priest", "chanter", "monk", "thunderer", "thunderer", "striker", "battlemaster",
                    "orchestrator", "lumines", "engineer", "gunner", "runewarrior", "runeblade", None, "gunner")
CLASS_FIELDS = {source for source in RESTRICT_SOURCES if source}
FIELDS = {"id"} | CLASS_FIELDS | {source + "_max" for source in CLASS_FIELDS}
BYTE_MIN = -128
BYTE_MAX = 127


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


def restriction(item: dict[str, str], suffix: str = "") -> tuple[list[int], list[str]]:
    present = any(source and source + suffix in item for source in RESTRICT_SOURCES)
    if not present:
        return ([0 if suffix else 1] * len(RESTRICT_SOURCES), [])
    values, pending = [], []
    for source in RESTRICT_SOURCES:
        if source is None:
            values.append(0)
            continue
        raw = item.get(source + suffix, "0") or "0"
        try:
            value = int(raw)
        except ValueError:
            pending.append(f"{source + suffix}={raw} nao e inteiro")
            value = 0
        if value < BYTE_MIN or value > BYTE_MAX:
            pending.append(f"{source + suffix}={raw} excede xs:byte")
            value = 0
        values.append(value)
    return values, pending


def effective(raw: str | None, maximum: bool = False) -> list[int]:
    size = len(RESTRICT_SOURCES)
    if raw is None:
        return [0 if maximum else 1] * size
    values = [int(value) for value in raw.split()]
    if len(values) >= size:
        return values[:size]
    result = values + [0] * (size - len(values))
    if values and all(values):
        fill = max(values) if maximum else min(values)
        result[len(values):] = [fill] * (size - len(values))
    return result


def set_or_remove(head: str, name: str, values: list[int], default: list[int]) -> str:
    pattern = r"\s+" + name + r'="[^"]*"'
    if values == default:
        return re.sub(pattern, "", head, count=1)
    value = " ".join(map(str, values))
    if re.search(pattern, head):
        return re.sub(pattern, f' {name}="{value}"', head, count=1)
    return head.rstrip() + f' {name}="{value}"'


def generate(raw: bytes, client: dict[str, dict[str, str]]) -> tuple[bytes, list[tuple], list[tuple], collections.Counter]:
    report, pending = [], []
    changed = collections.Counter()

    def replace(match: re.Match) -> str:
        attrs = dict(templates.ATTR_RE.findall(match.group(1)))
        item_id = attrs.get("id")
        official = client.get(item_id)
        if official is None:
            return match.group(0)
        expected_min, pending_min = restriction(official)
        expected_max, pending_max = restriction(official, "_max")
        unresolved = pending_min + pending_max
        pending.extend((item_id, value) for value in unresolved)
        if unresolved:
            return match.group(0)
        current_min = effective(attrs.get("restrict"))
        current_max = effective(attrs.get("restrict_max"), maximum=True)
        # PlayerClass.ALL nao possui campo correspondente no cliente; preserve o valor efetivo atual.
        expected_min[23] = current_min[23]
        expected_max[23] = current_max[23]
        head = match.group(1)
        changes = []
        if current_min != expected_min:
            head = set_or_remove(head, "restrict", expected_min, [1] * len(RESTRICT_SOURCES))
            changes.append("restrict:" + " ".join(map(str, current_min)) + "->" + " ".join(map(str, expected_min)))
            changed["restrict"] += 1
        if current_max != expected_max:
            head = set_or_remove(head, "restrict_max", expected_max, [0] * len(RESTRICT_SOURCES))
            changes.append("restrict_max:" + " ".join(map(str, current_max)) + "->" + " ".join(map(str, expected_max)))
            changed["restrict_max"] += 1
        if not changes:
            return match.group(0)
        report.append((item_id, " | ".join(changes)))
        if match.group(2) == "/>":
            return "\t<item_template" + head + "/>"
        return "\t<item_template" + head + ">" + (match.group(3) or "") + "</item_template>"

    updated = templates.BLOCK_RE.sub(replace, raw.decode("utf-8")).encode("utf-8")
    return updated, report, pending, changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    source_raw, product_raw = SOURCE.read_bytes(), PRODUCT.read_bytes()
    if sha256(source_raw) != sha256(product_raw):
        raise SystemExit("Fonte e produto final estao diferentes")
    client = read_client()
    updated, report, pending, changed = generate(source_raw, client)
    etree.XMLSchema(etree.parse(str(XSD))).assertValid(etree.fromstring(updated, parser=etree.XMLParser(huge_tree=True)))
    print(f"Itens oficiais: {len(client)}")
    print(f"Templates alterados: {len(report)}")
    print(f"Campos alterados: restrict={changed['restrict']}, restrict_max={changed['restrict_max']}")
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
    with (report_dir / "relatorio_sync_item_restrictions_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "alteracoes"))
        writer.writerows(report)
    with (report_dir / "pendencias_item_restrictions_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "pendencia"))
        writer.writerows(pending)
    print(f"SHA-256 sincronizado: {sha256(updated)}")


if __name__ == "__main__":
    main()
