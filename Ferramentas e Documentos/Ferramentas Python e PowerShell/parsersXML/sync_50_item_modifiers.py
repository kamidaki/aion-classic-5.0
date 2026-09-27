#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza modificadores diretos comprovados pelo catalogo Classic 5.0 EU.

O sincronizador adiciona tuplas ausentes e corrige conflitos simples um-para-um.
Blocos condicionais, multiplicidades ambiguas e atributos oficiais ainda sem
semantica comprovada ficam intactos e sao registrados como pendentes.
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
DIRECT_MOD_RE = re.compile(r'\s*<(add|sub|rate|set|abs|mean)\b([^>]*?)/>')


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


def direct_modifiers(content: str) -> collections.Counter:
    result = collections.Counter()
    for operation, raw_attrs in DIRECT_MOD_RE.findall(content):
        attrs = dict(templates.ATTR_RE.findall(raw_attrs))
        value = templates.num(attrs.get("value"))
        if value is not None:
            result[(operation, attrs.get("name"), value, attrs.get("bonus", "false") == "true")] += 1
    return result


def generate(raw: bytes, client: dict[str, dict[str, str]]) -> tuple[bytes, list[tuple], list[tuple], list[tuple], collections.Counter, collections.Counter]:
    report, pending, conflicts = [], [], []
    added_stats, corrected_stats = collections.Counter(), collections.Counter()

    def replace(match: re.Match) -> str:
        item_id = dict(templates.ATTR_RE.findall(match.group(1))).get("id")
        official = client.get(item_id)
        if official is None:
            return match.group(0)
        unmapped = collections.Counter()
        expected = collections.Counter(templates.gen_mods(official, unmapped))
        if unmapped:
            pending.extend((item_id, name, count) for name, count in sorted(unmapped.items()))
        if not expected:
            return match.group(0)

        inner = match.group(3) or ""
        block = MODIFIERS_RE.search(inner)
        current = direct_modifiers(block.group(1)) if block else collections.Counter()
        missing = expected - current
        if not missing:
            return match.group(0)

        current_keys = collections.defaultdict(set)
        for operation, stat, value, bonus in current:
            current_keys[(operation, stat, bonus)].add(value)
        collision_keys = set()
        for operation, stat, value, bonus in missing:
            values = current_keys.get((operation, stat, bonus), set())
            if values and value not in values:
                collision_keys.add((operation, stat, bonus))

        ambiguous = []
        for key in collision_keys:
            current_count = sum(count for (operation, stat, _, bonus), count in current.items()
                                if (operation, stat, bonus) == key)
            expected_count = sum(count for (operation, stat, _, bonus), count in expected.items()
                                 if (operation, stat, bonus) == key)
            if current_count != 1 or expected_count != 1:
                ambiguous.append(f"{key[0]}:{key[1]}:atual={current_count}:oficial={expected_count}:bonus={str(key[2]).lower()}")
        if ambiguous:
            conflicts.append((item_id, "multiplicidade ambigua: " + " | ".join(ambiguous)))
            return match.group(0)

        additions = []
        for modifier, count in sorted(missing.items()):
            if (modifier[0], modifier[1], modifier[3]) in collision_keys:
                continue
            additions.extend([modifier] * count)
            added_stats[modifier[1]] += count
        corrections = [modifier for modifier, count in sorted(expected.items())
                       if (modifier[0], modifier[1], modifier[3]) in collision_keys
                       for _ in range(count)]
        for modifier in corrections:
            corrected_stats[modifier[1]] += 1
        rendered = "".join(render_modifier(modifier) for modifier in additions + corrections)
        if block:
            content = block.group(1)
            if collision_keys:
                def remove_collision(modifier_match: re.Match) -> str:
                    attrs = dict(templates.ATTR_RE.findall(modifier_match.group(2)))
                    key = (modifier_match.group(1), attrs.get("name"), attrs.get("bonus", "false") == "true")
                    return "" if key in collision_keys else modifier_match.group(0)
                content = DIRECT_MOD_RE.sub(remove_collision, content)
            replacement = "<modifiers>" + content + rendered + "</modifiers>"
            inner = inner[:block.start()] + replacement + inner[block.end():]
        else:
            inner = "<modifiers>" + rendered + "</modifiers>" + inner
        report.append((item_id,
                       " | ".join(render_modifier(modifier) for modifier in additions),
                       " | ".join(render_modifier(modifier) for modifier in corrections)))
        if match.group(2) == "/>":
            return "\t<item_template" + match.group(1) + ">" + inner + "</item_template>"
        return "\t<item_template" + match.group(1) + ">" + inner + "</item_template>"

    updated = templates.BLOCK_RE.sub(replace, raw.decode("utf-8")).encode("utf-8")
    updated = re.sub(rb"[ \t]+(?=\r?\n)", b"", updated)
    return updated, report, pending, conflicts, added_stats, corrected_stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    source_raw, product_raw = SOURCE.read_bytes(), PRODUCT.read_bytes()
    if sha256(source_raw) != sha256(product_raw):
        raise SystemExit("Fonte e produto final estao diferentes")
    client = read_client()
    updated, report, pending, conflicts, added_stats, corrected_stats = generate(source_raw, client)
    etree.XMLSchema(etree.parse(str(XSD))).assertValid(etree.fromstring(updated, parser=etree.XMLParser(huge_tree=True)))
    print(f"Itens oficiais: {len(client)}")
    print(f"Templates alterados: {len(report)}")
    print(f"Modificadores adicionados: {sum(added_stats.values())}")
    print("Stats adicionados: " + ", ".join(f"{name}={count}" for name, count in added_stats.most_common()))
    print(f"Modificadores corrigidos: {sum(corrected_stats.values())}")
    print("Stats corrigidos: " + ", ".join(f"{name}={count}" for name, count in corrected_stats.most_common()))
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
        writer.writerow(("id", "modificadores_adicionados", "modificadores_corrigidos"))
        writer.writerows(report)
    with (report_dir / "pendencias_item_modifiers_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "tipo", "detalhe", "ocorrencias"))
        writer.writerows((item_id, "sem_mapeamento", name, count) for item_id, name, count in pending)
        writer.writerows((item_id, "conflito_preservado", detail, 1) for item_id, detail in conflicts)
    print(f"SHA-256 sincronizado: {sha256(updated)}")


if __name__ == "__main__":
    main()
