#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza campos diretos de uso/tempo dos itens Classic 5.0 Europe."""

from __future__ import annotations

import argparse
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
FIELDS = {"id", "activate_target", "activation_count", "casting_delay", "expire_time", "return_alias", "return_worldid"}
TARGETS = {"STANDALONE", "TARGET", "MYMENTO", "WORLD_EVENT_CAKE_D", "WORLD_EVENT_CAKE_L", "BROWNIE",
           "GCHIEF_LIGHT", "GHENCHMAN_LIGHT", "GHENCHMAN_DARK", "KRALL", "LF5_Q_ITEM", "LIVINGWATER", "LYCAN",
           "EVENT_TOWER_LIGHT", "EVENT_TOWER_DARK", "WORLD_EVENT_DEFTOWER"}
INT_MAX = 2_147_483_647


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


def canonical(item: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    values, pending = {}, []
    target = item.get("activate_target", "").upper()
    if target and target not in ("NONE", "0"):
        if target in TARGETS:
            values["activate_target"] = target
        else:
            pending.append("activate_target=" + target)
    for source, target_name in (("activation_count", "activate_count"), ("casting_delay", "casting_delay"),
                                ("expire_time", "expire_time"), ("return_worldid", "return_world")):
        raw = item.get(source, "")
        if not raw or raw == "0":
            continue
        try:
            number = int(raw)
        except ValueError:
            pending.append(source + "=" + raw)
            continue
        if number > INT_MAX or number < -INT_MAX - 1:
            pending.append(source + "=" + raw + " excede xs:int")
            continue
        values[target_name] = str(number)
    alias = item.get("return_alias", "").strip()
    if alias:
        values["return_alias"] = alias.upper()
    return values, pending


def set_or_remove(head: str, name: str, value: str | None) -> str:
    pattern = r"\s+" + name + r'="[^"]*"'
    if value is None:
        return re.sub(pattern, "", head, count=1)
    if re.search(pattern, head):
        return re.sub(pattern, f' {name}="{templates.esc(value)}"', head, count=1)
    return head.rstrip() + f' {name}="{templates.esc(value)}"'


def generate(raw: bytes, client: dict[str, dict[str, str]]) -> tuple[bytes, list[tuple], list[tuple]]:
    report, pending = [], []
    managed = ("activate_target", "activate_count", "casting_delay", "expire_time", "return_world", "return_alias")

    def replace(match: re.Match) -> str:
        attrs = dict(templates.ATTR_RE.findall(match.group(1)))
        item_id = attrs.get("id")
        official = client.get(item_id)
        if official is None:
            return match.group(0)
        expected, unresolved = canonical(official)
        pending.extend((item_id, value) for value in unresolved)
        head = match.group(1)
        changes = []
        for name in managed:
            if any(value.startswith(name.replace("activate_count", "activation_count") + "=") for value in unresolved):
                continue
            old, new = attrs.get(name), expected.get(name)
            if old == new:
                continue
            head = set_or_remove(head, name, new)
            changes.append(f"{name}:{old or '<ausente>'}->{new or '<ausente>'}")
        if not changes:
            return match.group(0)
        report.append((item_id, " | ".join(changes)))
        if match.group(2) == "/>":
            return "\t<item_template" + head + "/>"
        return "\t<item_template" + head + ">" + (match.group(3) or "") + "</item_template>"

    updated = templates.BLOCK_RE.sub(replace, raw.decode("utf-8")).encode("utf-8")
    return updated, report, pending


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    source_raw, product_raw = SOURCE.read_bytes(), PRODUCT.read_bytes()
    if sha256(source_raw) != sha256(product_raw):
        raise SystemExit("Fonte e produto final estao diferentes")
    client = read_client()
    updated, report, pending = generate(source_raw, client)
    etree.XMLSchema(etree.parse(str(XSD))).assertValid(etree.fromstring(updated, parser=etree.XMLParser(huge_tree=True)))
    print(f"Itens oficiais: {len(client)}")
    print(f"Templates alterados: {len(report)}")
    print(f"Valores pendentes: {len(pending)}")
    for item_id, value in pending[:20]:
        print(f"  {item_id}: {value}")
    if not args.aplicar:
        print("Modo de verificacao: nenhum arquivo gravado")
        return
    backup_manager.backup_file_before_modification(RELATIVE_TEMPLATE)
    SOURCE.write_bytes(updated)
    PRODUCT.write_bytes(updated)
    report_dir = Path(backup_manager.get_current_session())
    with (report_dir / "relatorio_sync_item_use_fields_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "alteracoes"))
        writer.writerows(report)
    with (report_dir / "pendencias_item_use_fields_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "pendencia"))
        writer.writerows(pending)
    print(f"SHA-256 sincronizado: {sha256(updated)}")


if __name__ == "__main__":
    main()
