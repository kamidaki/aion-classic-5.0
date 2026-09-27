#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adiciona modificadores diretos ausentes comprovados pelo catalogo Classic 5.0 EU.

O sincronizador e deliberadamente aditivo: nao remove modificadores legados e nao
altera um modificador que ja use a mesma operacao/stat/flag bonus com outro valor.
Itens com atributos oficiais ainda sem semantica comprovada tambem ficam intactos.
"""

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
FIELDS = {"id", "stat_enchant_type", "stat_enchant_value"} | set(templates.BASE_MODS)
MODIFIERS_RE = re.compile(r"<modifiers>(.*?)</modifiers>", re.S)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_client() -> dict[str, dict[str, str]]:
    result = {}
    for _, element in ET.iterparse(CLIENT_ITEMS, events=("end",)):
        if element.tag != "client_item":
            continue
        data = {child.tag: (child.text or "").strip() for child in element
                if child.tag in FIELDS or child.tag.startswith("bonus_attr")}
        if data.get("id"):
            result[data["id"]] = data
        element.clear()
    return result


def render_modifier(modifier: tuple[str, str, int, bool]) -> str:
    operation, stat, value, bonus = modifier
    suffix = ' bonus="true"' if bonus else ""
    return f'<{operation} name="{stat}" value="{value}"{suffix} />'


def generate(raw: bytes, client: dict[str, dict[str, str]]) -> tuple[bytes, list[tuple], list[tuple], list[tuple], collections.Counter]:
    report, pending, conflicts = [], [], []
    changed_stats = collections.Counter()

    def replace(match: re.Match) -> str:
        item_id = dict(templates.ATTR_RE.findall(match.group(1))).get("id")
        official = client.get(item_id)
        if official is None:
            return match.group(0)
        unmapped = collections.Counter()
        expected = collections.Counter(templates.gen_mods(official, unmapped))
        if unmapped:
            pending.extend((item_id, name, count) for name, count in sorted(unmapped.items()))
            return match.group(0)
        if not expected:
            return match.group(0)

        inner = match.group(3) or ""
        block = MODIFIERS_RE.search(inner)
        if block and "<conditions" in block.group(1):
            conflicts.append((item_id, "bloco possui conditions; revisao manual obrigatoria"))
            return match.group(0)
        current = templates.legacy_mods(inner)
        missing = expected - current
        if not missing:
            return match.group(0)

        current_keys = collections.defaultdict(set)
        for operation, stat, value, bonus in current:
            current_keys[(operation, stat, bonus)].add(value)
        collisions = []
        for operation, stat, value, bonus in missing:
            values = current_keys.get((operation, stat, bonus), set())
            if values and value not in values:
                collisions.append(f"{operation}:{stat}:oficial={value}:atual={','.join(map(str, sorted(values)))}:bonus={str(bonus).lower()}")
        if collisions:
            conflicts.append((item_id, " | ".join(collisions)))
            return match.group(0)

        additions = []
        for modifier, count in sorted(missing.items()):
            additions.extend([modifier] * count)
            changed_stats[modifier[1]] += count
        rendered = "".join(render_modifier(modifier) for modifier in additions)
        if block:
            inner = inner[:block.end(1)] + rendered + inner[block.end(1):]
        else:
            inner = "<modifiers>" + rendered + "</modifiers>" + inner
        report.append((item_id, " | ".join(render_modifier(modifier) for modifier in additions)))
        if match.group(2) == "/>":
            return "\t<item_template" + match.group(1) + ">" + inner + "</item_template>"
        return "\t<item_template" + match.group(1) + ">" + inner + "</item_template>"

    updated = templates.BLOCK_RE.sub(replace, raw.decode("utf-8")).encode("utf-8")
    return updated, report, pending, conflicts, changed_stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    source_raw, product_raw = SOURCE.read_bytes(), PRODUCT.read_bytes()
    if sha256(source_raw) != sha256(product_raw):
        raise SystemExit("Fonte e produto final estao diferentes")
    client = read_client()
    updated, report, pending, conflicts, changed_stats = generate(source_raw, client)
    etree.XMLSchema(etree.parse(str(XSD))).assertValid(etree.fromstring(updated, parser=etree.XMLParser(huge_tree=True)))
    print(f"Itens oficiais: {len(client)}")
    print(f"Templates alterados: {len(report)}")
    print(f"Modificadores adicionados: {sum(changed_stats.values())}")
    print("Stats adicionados: " + ", ".join(f"{name}={count}" for name, count in changed_stats.most_common()))
    print(f"Atributos sem mapeamento: {sum(count for _, _, count in pending)} em {len({item_id for item_id, _, _ in pending})} itens")
    for name, count in collections.Counter(name for _, name, count in pending for _ in range(count)).most_common(20):
        print(f"  {count}x {name}")
    print(f"Conflitos preservados: {len(conflicts)}")
    if not args.aplicar:
        print("Modo de verificacao: nenhum arquivo gravado")
        return
    backup_manager.backup_file_before_modification(RELATIVE_TEMPLATE)
    SOURCE.write_bytes(updated)
    PRODUCT.write_bytes(updated)
    report_dir = Path(backup_manager.get_current_session())
    with (report_dir / "relatorio_sync_item_modifiers_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "modificadores_adicionados"))
        writer.writerows(report)
    with (report_dir / "pendencias_item_modifiers_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "tipo", "detalhe", "ocorrencias"))
        writer.writerows((item_id, "sem_mapeamento", name, count) for item_id, name, count in pending)
        writer.writerows((item_id, "conflito_preservado", detail, 1) for item_id, detail in conflicts)
    print(f"SHA-256 sincronizado: {sha256(updated)}")


if __name__ == "__main__":
    main()
