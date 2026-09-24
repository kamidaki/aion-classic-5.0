#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_item_self_resurrect.py

Marca com self_resurrect="true" no item_templates.xml as pedras que ressuscitam o próprio dono morto (C_DEAD_RESTART tipo 2).

O cliente 5.0 marca essas pedras com <mgrouptag>I_RESURRECT</mgrouptag> no client_items.xml. A pedra só de aliado (164000010,
soulstone_resurrect_other_10) usa a mesma skill 9912, mas não tem a marca. Antes o emulador tinha uma lista fixa de 4 ids no
Player.getSelfRezStone() e deixava de fora 161001003, 161001004 e 188053614.

Só o atributo é acrescentado; o resto do arquivo fica byte a byte igual.

Uso:
    python fix_50_item_self_resurrect.py --verificar
    python fix_50_item_self_resurrect.py --aplicar
A pasta do cliente (a que contem data/) vem de --cliente ou da variavel AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import hashlib
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_ITEMS = "items/item_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_item_self_resurrect_50.txt")
START_TAG_RE = re.compile(r'<item_template\s+id="(\d+)"[^>]*?(/?)>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    src = os.path.join(backup_manager.SERVER_DATA_DIR, REL_ITEMS)
    prod = os.path.join(backup_manager.PRODUTO_FINAL_DATA_DIR, REL_ITEMS)
    if hashlib.sha256(open(src, "rb").read()).digest() != hashlib.sha256(open(prod, "rb").read()).digest():
        sys.exit(f"{REL_ITEMS} do fonte e do Produto Final estao diferentes. Sincronize antes de rodar.")

    print("1. Lendo o cliente...")
    texto_cliente = open(os.path.join(args.cliente, "data", "items", "client_items.xml"), encoding="utf-8").read()
    marcados = {}
    for m in re.finditer(r"<client_item>\s*<id>(\d+)</id>\s*<name>([^<]*)</name>(.*?)</client_item>", texto_cliente, re.S):
        if re.search(r"<mgrouptag>\s*I_RESURRECT\s*</mgrouptag>", m.group(3)):
            marcados[int(m.group(1))] = m.group(2).strip()
    print(f"   itens I_RESURRECT no cliente: {len(marcados)}")

    texto = open(src, encoding="utf-8", newline="").read()
    rel = collections.defaultdict(list)
    vistos = set()

    def marca(m):
        item_id = int(m.group(1))
        tag = m.group(0)
        if item_id not in marcados:
            return tag
        vistos.add(item_id)
        if 'self_resurrect="' in tag:
            rel["já marcado"].append(f"{item_id} {marcados[item_id]}")
            return tag
        rel["marcado"].append(f"{item_id} {marcados[item_id]}")
        fim = len(tag) - (2 if m.group(2) else 1)
        return tag[:fim] + ' self_resurrect="true"' + tag[fim:]

    novo = START_TAG_RE.sub(marca, texto)
    for item_id in sorted(set(marcados) - vistos):
        rel["I_RESURRECT sem template no servidor"].append(f"{item_id} {marcados[item_id]}")
    for k, v in rel.items():
        print(f"   {k}: {len(v)}")

    print("2. Validando contra o static_data.xsd agregado...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    if not schema.validate(etree.fromstring(novo.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))):
        for e in list(schema.error_log)[:20]:
            print(f"   linha {e.line}: {e.message}")
        sys.exit("   XSD INVALIDO")
    print("   valido")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("fix_50_item_self_resurrect.py\n")
        for k, v in rel.items():
            f.write(f"\n== {k}: {len(v)}\n")
            f.writelines(f"  {x}\n" for x in v)
    print(f"   relatorio: {RELATORIO}")

    if not args.aplicar:
        print("\nModo --verificar: nada foi gravado.")
        return
    print("3. Gravando (com backup)...")
    backup_manager.backup_file_before_modification(REL_ITEMS)
    for caminho in (src, prod):
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        print(f"   Gravado: {caminho}")


if __name__ == "__main__":
    main()
