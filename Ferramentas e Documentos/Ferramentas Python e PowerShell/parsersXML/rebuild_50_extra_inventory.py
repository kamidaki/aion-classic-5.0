#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstrói o roteamento de itens para os cubos especiais do Classic 5.0.

Fontes oficiais:

* ``quest`` diferente de zero identifica item do cubo de missão (inventory id 2);
* ``extra_inventory`` diferente de zero identifica item do cubo especial (inventory id 1).

O GameServer atualmente trata qualquer ``inventory id`` positivo como cubo especial.
Entradas legadas sem nenhuma das duas flags oficiais são preservadas e relatadas,
pois sua remoção exige evidência adicional. O programa é idempotente e mantém os
XMLs do fonte e do produto final byte a byte sincronizados.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from lxml import etree


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CLIENT_ITEMS = PROJECT_ROOT / "5 - Documentação e Referências" / "3 - Client 5.0 - Dados Extraidos" / "data" / "europe" / "Items" / "client_items.xml"
SERVER_ITEMS = PROJECT_ROOT / "Código Fonte - Emulador" / "game-server" / "data" / "static_data" / "items" / "item_templates.xml"
PRODUCT_ITEMS = PROJECT_ROOT / "Emulador - Produto Final" / "GameServer" / "data" / "static_data" / "items" / "item_templates.xml"
ITEMS_XSD = SERVER_ITEMS.with_name("item_templates.xsd")
REPORT = PROJECT_ROOT / "5 - Documentação e Referências" / "4 - Auditoria de Itens Classic 5.0" / "inventario_cubo_especial_50.csv"

BLOCK_RE = re.compile(r"\t<item_template\b([^>]*?)(/>|>(.*?)</item_template>)", re.S)
ID_RE = re.compile(r'\bid="(\d+)"')
INVENTORY_RE = re.compile(r'<inventory\b[^>]*\bid="(\d+)"[^>]*/?>')


def meaningful(value: str | None) -> bool:
    return value is not None and value.strip().lower() not in ("", "0", "false", "none", "no")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def official_inventory() -> dict[str, tuple[int, str, str, str]]:
    result: dict[str, tuple[int, str, str, str]] = {}
    for _, element in ET.iterparse(CLIENT_ITEMS, events=("end",)):
        if element.tag != "client_item":
            continue
        item_id = (element.findtext("id") or "").strip()
        name = (element.findtext("name") or "").strip()
        quest = (element.findtext("quest") or "").strip()
        extra = (element.findtext("extra_inventory") or "").strip()
        if item_id and (meaningful(quest) or meaningful(extra)):
            result[item_id] = (2 if meaningful(quest) else 1, name, quest, extra)
        element.clear()
    return result


def rebuild(text: str, official: dict[str, tuple[int, str, str, str]]) -> tuple[str, list[tuple[str, ...]], int]:
    newline = "\r\n" if "\r\n" in text else "\n"
    rows: list[tuple[str, ...]] = []
    inserted = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal inserted
        head, closing, inner = match.group(1), match.group(2), match.group(3) or ""
        item_match = ID_RE.search(head)
        if item_match is None:
            return match.group(0)
        item_id = item_match.group(1)
        current_match = INVENTORY_RE.search(inner)
        current_id = current_match.group(1) if current_match else ""
        expected = official.get(item_id)
        if expected is None:
            if current_id not in ("", "0"):
                rows.append((item_id, "", "", "", "", current_id, "PENDENTE_LEGADO_SEM_FLAG"))
            return match.group(0)

        expected_id, name, quest, extra = expected
        if current_id not in ("", "0"):
            rows.append((item_id, name, quest, extra, str(expected_id), current_id, "COMPATIVEL_CUBO_ESPECIAL"))
            return match.group(0)

        if current_match:
            rows.append((item_id, name, quest, extra, str(expected_id), current_id, "CORRIGIDO_CUBO_ESPECIAL"))
            inserted += 1
            block = match.group(0)
            start, end = current_match.span(1)
            inner_at = block.find(inner)
            return block[:inner_at + start] + str(expected_id) + block[inner_at + end:]

        inventory_line = f'\t\t<inventory id="{expected_id}"/>'
        inserted += 1
        rows.append((item_id, name, quest, extra, str(expected_id), "", "INSERIDO_CUBO_ESPECIAL"))
        if closing == "/>":
            return f"\t<item_template{head}>{newline}{inventory_line}{newline}\t</item_template>"

        block = match.group(0)
        idian_at = block.find(f"{newline}\t\t<idian")
        close_at = block.rfind(f"{newline}\t</item_template>")
        insert_at = idian_at if idian_at >= 0 else close_at
        if insert_at < 0:
            raise ValueError(f"Não foi possível inserir inventory no item {item_id}")
        return block[:insert_at] + newline + inventory_line + block[insert_at:]

    rebuilt = BLOCK_RE.sub(replace, text)
    missing_templates = sorted(set(official) - {m.group(1) for m in ID_RE.finditer(text)}, key=int)
    if missing_templates:
        raise ValueError(f"Itens oficiais sem template: {len(missing_templates)}")
    return rebuilt, rows, inserted


def validate(xml: bytes) -> None:
    schema = etree.XMLSchema(etree.parse(str(ITEMS_XSD)))
    document = etree.fromstring(xml, parser=etree.XMLParser(huge_tree=True))
    if not schema.validate(document):
        errors = "\n".join(str(error) for error in list(schema.error_log)[:20])
        raise ValueError(f"item_templates.xml inválido:\n{errors}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="Grava fonte, produto final e relatório")
    args = parser.parse_args()

    source = SERVER_ITEMS.read_bytes()
    product = PRODUCT_ITEMS.read_bytes()
    if source != product:
        raise SystemExit("item_templates.xml do fonte e do produto final não estão sincronizados")

    official = official_inventory()
    rebuilt_text, rows, inserted = rebuild(source.decode("utf-8"), official)
    rebuilt = rebuilt_text.encode("utf-8")
    validate(rebuilt)

    statuses: dict[str, int] = {}
    for row in rows:
        statuses[row[-1]] = statuses.get(row[-1], 0) + 1
    print(f"Itens oficiais roteados a cubo especial: {len(official)}")
    print(f"Entradas inseridas: {inserted}")
    print(f"Status: {statuses}")
    print(f"SHA-256 atual: {sha256(source)}")
    print(f"SHA-256 reconstruído: {sha256(rebuilt)}")

    if not args.aplicar:
        print("Verificação concluída; use --aplicar para gravar.")
        return

    SERVER_ITEMS.write_bytes(rebuilt)
    PRODUCT_ITEMS.write_bytes(rebuilt)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "nome_interno", "quest", "extra_inventory", "inventory_esperado", "inventory_anterior", "status"))
        writer.writerows(sorted(rows, key=lambda row: int(row[0])))
    print("Fonte, produto final e relatório sincronizados.")


if __name__ == "__main__":
    main()
