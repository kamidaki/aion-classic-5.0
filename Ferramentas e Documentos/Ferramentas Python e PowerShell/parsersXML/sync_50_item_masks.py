#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza as mascaras de gameplay e wire com o catalogo Europe Classic 5.0.

Nao infere flags ausentes. A mascara interna usa apenas propriedades oficiais
com correspondencia ja existente em ItemMask; a mascara de wire segue o layout
medido do GENERAL_INFO. Executar sem --aplicar apenas valida e relata.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from lxml import etree

import backup_manager
import rebuild_50_item_templates as templates


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CLIENT_ROOT = PROJECT_ROOT / "5 - Documentação e Referências" / "3 - Client 5.0 - Dados Extraidos"
CLIENT_ITEMS = CLIENT_ROOT / "data" / "europe" / "Items" / "client_items.xml"
RELATIVE_TEMPLATE = "items/item_templates.xml"
SOURCE = Path(backup_manager.SERVER_DATA_DIR) / RELATIVE_TEMPLATE
PRODUCT = Path(backup_manager.PRODUTO_FINAL_DATA_DIR) / RELATIVE_TEMPLATE
XSD = Path(backup_manager.SERVER_DATA_DIR) / "items" / "item_templates.xsd"

FIELDS = {name for _, name in templates.MASK_FLAGS} | {
    "id", "quest", "weapon_type", "cash_item", "cannot_extraction", "cannot_changeskin", "can_dye"
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_client() -> dict[str, dict[str, str]]:
    result = {}
    for event, element in ET.iterparse(CLIENT_ITEMS, events=("end",)):
        if element.tag != "client_item":
            continue
        data = {child.tag: (child.text or "").strip() for child in element if child.tag in FIELDS}
        if data.get("id"):
            result[data["id"]] = data
        element.clear()
    return result


def gameplay_mask(item: dict[str, str]) -> int:
    return templates.gen_mask(item)


def wire_mask(item: dict[str, str]) -> int:
    flags = ((0, "lore"), (1, "can_exchange"), (2, "can_sell_to_npc"),
             (3, "can_deposit_to_character_warehouse"), (4, "can_deposit_to_account_warehouse"),
             (5, "breakable"), (6, "soul_bind"), (9, "can_deposit_to_guild_warehouse"),
             (13, "can_split"), (15, "cannot_extraction"))
    value = sum(1 << bit for bit, field in flags if item.get(field, "").upper() == "TRUE")
    if item.get("no_enchant", "TRUE").upper() != "FALSE": value |= 1 << 8
    if item.get("quest", "").strip().lower() not in ("", "0", "false", "none", "no"): value |= 1 << 10
    if item.get("weapon_type", "none").lower() != "none": value |= 1 << 11
    if item.get("cash_item") == "1": value |= 1 << 12
    if item.get("cannot_changeskin", "1") != "0": value |= 1 << 14
    return value


def replace_attribute(head: str, name: str, value: int) -> str:
    if re.search(r"\b" + name + r'="', head):
        return re.sub(r"\b" + name + r'="[^"]*"', f'{name}="{value}"', head, count=1)
    return head.rstrip() + f' {name}="{value}"'


def generate(raw: bytes, client: dict[str, dict[str, str]]) -> tuple[bytes, list[tuple], collections.Counter]:
    text = raw.decode("utf-8")
    report, bit_changes = [], collections.Counter()

    def replace(match: re.Match) -> str:
        attrs = dict(templates.ATTR_RE.findall(match.group(1)))
        item_id = attrs.get("id")
        official = client.get(item_id)
        if official is None:
            return match.group(0)
        old_gameplay = int(attrs.get("mask", "0"))
        old_wire = int(attrs.get("client_mask", "0"))
        new_gameplay = gameplay_mask(official)
        new_wire = wire_mask(official)
        if old_gameplay == new_gameplay and old_wire == new_wire:
            return match.group(0)
        for bit in range(19):
            flag = 1 << bit
            if bool(old_gameplay & flag) != bool(new_gameplay & flag):
                bit_changes[(bit, "adicionado" if new_gameplay & flag else "removido")] += 1
        head = replace_attribute(match.group(1), "mask", new_gameplay)
        head = replace_attribute(head, "client_mask", new_wire)
        report.append((item_id, old_gameplay, new_gameplay, old_wire, new_wire))
        tail = match.group(2)
        if tail == "/>":
            return "\t<item_template" + head + "/>"
        return "\t<item_template" + head + ">" + (match.group(3) or "") + "</item_template>"

    updated = templates.BLOCK_RE.sub(replace, text).encode("utf-8")
    return updated, report, bit_changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    source_raw, product_raw = SOURCE.read_bytes(), PRODUCT.read_bytes()
    if sha256(source_raw) != sha256(product_raw):
        raise SystemExit("Fonte e produto final estao diferentes")
    client = read_client()
    updated, report, bit_changes = generate(source_raw, client)
    schema = etree.XMLSchema(etree.parse(str(XSD)))
    schema.assertValid(etree.fromstring(updated, parser=etree.XMLParser(huge_tree=True)))
    print(f"Itens oficiais: {len(client)}")
    print(f"Templates alterados: {len(report)}")
    for (bit, operation), count in sorted(bit_changes.items(), key=lambda entry: (-entry[1], entry[0])):
        print(f"bit {bit:02d} {operation}: {count}")
    if not args.aplicar:
        print("Modo de verificacao: nenhum arquivo gravado")
        return
    backup_manager.backup_file_before_modification(RELATIVE_TEMPLATE)
    SOURCE.write_bytes(updated)
    PRODUCT.write_bytes(updated)
    report_path = Path(backup_manager.get_current_session()) / "relatorio_sync_item_masks_50.csv"
    with report_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "mask_anterior", "mask_classic_50", "client_mask_anterior", "client_mask_classic_50"))
        writer.writerows(report)
    print(f"SHA-256 sincronizado: {sha256(updated)}")
    print(f"Relatorio: {report_path}")


if __name__ == "__main__":
    main()
