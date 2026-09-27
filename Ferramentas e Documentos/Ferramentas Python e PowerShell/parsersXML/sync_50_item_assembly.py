#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstrói combinações ``assembly_item`` pelo catálogo Classic 5.0 EU.

Cada peça informa o nome interno do item resultante. O sincronizador resolve
esse nome no mesmo catálogo, gera ``assembly_items.xml`` e garante que cada
peça tenha ``<assemble item=\"ID_RESULTADO\"/>``. Nomes ausentes ou ambíguos
interrompem a execução; nenhum resultado é inferido.
"""

import argparse
import collections
import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import backup_manager  # noqa: E402

REL_ITEMS = "items/item_templates.xml"
REL_ASSEMBLY = "items/assembly_items.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
REPORT = os.path.join(HERE, "relatorio_item_assembly_50.txt")
ITEM_RE = re.compile(r'(<item_template\s+id="(\d+)"[^>]*?(?:/>|>.*?</item_template>))', re.S)
ASSEMBLE_RE = re.compile(r'<assemble\b[^>]*/>')
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def read_official(client_dir):
    path = os.path.join(client_dir, "data", "europe", "Items", "client_items.xml")
    names = collections.defaultdict(list)
    parts = []
    ids = set()
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "client_item":
            item_id = (element.findtext("id") or "").strip()
            name = (element.findtext("name") or "").strip().lower()
            result_name = (element.findtext("assembly_item") or "").strip().lower()
            if item_id:
                ids.add(int(item_id))
                if name:
                    names[name].append(int(item_id))
                if result_name and result_name not in ("0", "false"):
                    parts.append((int(item_id), name, result_name))
            element.clear()

    groups = collections.defaultdict(list)
    unresolved = []
    ambiguous = []
    for part_id, part_name, result_name in parts:
        targets = names.get(result_name, [])
        if not targets:
            unresolved.append((part_id, part_name, result_name))
        elif len(targets) != 1:
            ambiguous.append((part_id, part_name, result_name, targets))
        else:
            groups[targets[0]].append(part_id)
    if unresolved or ambiguous:
        raise SystemExit(f"Relações não resolvidas: ausentes={len(unresolved)}, ambíguas={len(ambiguous)}")
    if any(result_id not in ids for result_id in groups):
        raise SystemExit("Um resultado de assembly não existe no catálogo oficial")
    if any(len(set(group)) != len(group) for group in groups.values()):
        raise SystemExit("Uma combinação oficial contém a mesma peça mais de uma vez; revisar semântica de quantidade")
    return path, groups


def render_assembly(groups, nl):
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', "<assembly_items>"]
    for result_id in sorted(groups):
        parts = " ".join(str(part) for part in groups[result_id])
        lines.append(f'\t<item id="{result_id}" parts="{parts}" />')
    lines.append("</assembly_items>")
    return nl.join(lines) + nl


def insert_action(block, result_id, nl):
    tag = f'<assemble item="{result_id}"/>'
    actions = re.search(r'<actions>(.*?)</actions>', block, re.S)
    if actions:
        later = re.search(r'<(?:adoptpet|apextract|remodel|expextract|polish|tuning|megaphone|pack|multireturn)\b', actions.group(1))
        if later:
            pos = actions.start(1) + later.start()
            return block[:pos] + "\t\t\t" + tag + nl + block[pos:]
        pos = actions.end(1)
        return block[:pos] + "\t\t\t" + tag + nl + block[pos:]
    action_block = f"\t\t<actions>{nl}\t\t\t{tag}{nl}\t\t</actions>"
    if block.rstrip().endswith("/>"):
        end = block.rfind("/>")
        return block[:end] + ">" + nl + action_block + nl + "\t</item_template>" + block[end + 2:]
    modifiers = re.search(r'</modifiers>', block)
    if modifiers:
        pos = modifiers.end()
        return block[:pos] + nl + action_block + block[pos:]
    start = block.find(">") + 1
    return block[:start] + nl + action_block + block[start:]


def sync_actions(text, groups):
    expected = {part: result for result, parts in groups.items() for part in parts}
    found = set()
    report = collections.defaultdict(list)
    nl = "\r\n" if "\r\n" in text else "\n"

    def update(match):
        block, item_id = match.group(1), int(match.group(2))
        current = ASSEMBLE_RE.search(block)
        result_id = expected.get(item_id)
        if result_id is None:
            if current is not None:
                report["ação legada removida"].append(f"{item_id}: {current.group(0)}")
                new_block = block[:current.start()] + block[current.end():]
                new_block = re.sub(r'\s*<actions>\s*</actions>', "", new_block)
                return new_block
            return block
        found.add(item_id)
        if current is None:
            report["ação inserida"].append(f"{item_id} -> {result_id}")
            return insert_action(block, result_id, nl)
        attrs = dict(ATTR_RE.findall(current.group(0)))
        if attrs.get("item") != str(result_id):
            report["resultado corrigido"].append(f"{item_id}: {attrs.get('item')} -> {result_id}")
            tag = re.sub(r'\bitem="[^"]*"', f'item="{result_id}"', current.group(0))
            return block[:current.start()] + tag + block[current.end():]
        report["ação validada"].append(f"{item_id} -> {result_id}")
        return block

    result = ITEM_RE.sub(update, text)
    missing = sorted(set(expected) - found)
    if missing:
        raise SystemExit(f"Peças oficiais ausentes no item_templates.xml: {missing[:20]} (total {len(missing)})")
    return result, report


def validate(items_text, assembly_text, server_data_dir):
    from lxml import etree
    parser = etree.XMLParser(huge_tree=True)
    item_schema = etree.XMLSchema(etree.parse(os.path.join(server_data_dir, "static_data.xsd")))
    item_doc = etree.fromstring(items_text.encode("utf-8"), parser=parser)
    if not item_schema.validate(item_doc):
        raise SystemExit("item_templates.xml inválido: " + str(item_schema.error_log.last_error))
    assembly_schema = etree.XMLSchema(etree.parse(os.path.join(server_data_dir, "items", "assembly_items.xsd")))
    assembly_doc = etree.fromstring(assembly_text.encode("utf-8"), parser=parser)
    if not assembly_schema.validate(assembly_doc):
        raise SystemExit("assembly_items.xml inválido: " + str(assembly_schema.error_log.last_error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verificar", action="store_true")
    mode.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()

    src_items = os.path.join(backup_manager.SERVER_DATA_DIR, REL_ITEMS)
    dst_items = os.path.join(backup_manager.PRODUTO_FINAL_DATA_DIR, REL_ITEMS)
    src_assembly = os.path.join(backup_manager.SERVER_DATA_DIR, REL_ASSEMBLY)
    dst_assembly = os.path.join(backup_manager.PRODUTO_FINAL_DATA_DIR, REL_ASSEMBLY)
    for source, product in ((src_items, dst_items), (src_assembly, dst_assembly)):
        if sha256(source) != sha256(product):
            raise SystemExit(f"Fonte e Produto Final não estão sincronizados: {source}")

    client_path, groups = read_official(args.cliente)
    item_text = open(src_items, encoding="utf-8", newline="").read()
    old_assembly = open(src_assembly, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in old_assembly else "\n"
    new_items, report = sync_actions(item_text, groups)
    new_assembly = render_assembly(groups, nl)
    validate(new_items, new_assembly, backup_manager.SERVER_DATA_DIR)

    old_root = ET.fromstring(old_assembly)
    old_groups = {int(node.get("id")): [int(value) for value in node.get("parts").split()] for node in old_root}
    exact = sum(old_groups.get(result) == parts for result, parts in groups.items())
    print(f"Catálogo: {os.path.relpath(client_path, args.cliente)}")
    print(f"Peças oficiais: {sum(map(len, groups.values()))} | resultados: {len(groups)}")
    print(f"Tabela anterior: {len(old_groups)} resultados | grupos exatos: {exact}")
    print("Ações: " + ", ".join(f"{key}={len(values)}" for key, values in report.items()))
    print("XSD: válido")

    with open(REPORT, "w", encoding="utf-8") as output:
        output.write("sync_50_item_assembly.py\n")
        output.write(f"peças oficiais: {sum(map(len, groups.values()))}\nresultados oficiais: {len(groups)}\n")
        for result_id in sorted(groups):
            output.write(f"{result_id}: {' '.join(map(str, groups[result_id]))}\n")
        for key, values in report.items():
            output.write(f"\n== {key}: {len(values)}\n")
            output.writelines(f"  {value}\n" for value in values)

    if not args.aplicar:
        print("Modo --verificar: nada foi gravado.")
        return
    backup_manager.backup_file_before_modification(REL_ITEMS)
    backup_manager.backup_file_before_modification(REL_ASSEMBLY)
    for path, content in ((src_items, new_items), (dst_items, new_items), (src_assembly, new_assembly), (dst_assembly, new_assembly)):
        with open(path, "w", encoding="utf-8", newline="") as output:
            output.write(content)
        print(f"Gravado: {path}")


if __name__ == "__main__":
    main()
