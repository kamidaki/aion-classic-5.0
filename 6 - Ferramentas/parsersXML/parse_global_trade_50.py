#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_global_trade_50.py

Itens anunciáveis na Global Auction House do Classic 5.0, por categoria, para o items/global_trade.xml.

Fonte: data/items/client_items.xml
  vendor_category_index    categoria da janela (hierárquica: 1010100 = grupo 1, subgrupo 01, 01); o C_GLOBAL_TRADE_LIST manda a
                           categoria escolhida e o servidor filtra por prefixo (captura: 3000000 traz 3010000, 3020000...)
  can_world_kina_vendor    pode ser anunciado em kinah (moeda 1 no C_GLOBAL_TRADE_COMMIT)
  can_world_vendor         pode ser anunciado em Luna (moeda 0); os itens world_cash_* têm só este

Item sem template no servidor fica de fora e vai para o relatório. Item anunciável sem vendor_category_index entra na categoria 0:
só aparece pela busca por nome, que manda a lista de itemIds.

Uso:
    python parse_global_trade_50.py --verificar
    python parse_global_trade_50.py --aplicar
A pasta do cliente (a que contem data/) vem de --cliente ou da variavel AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_OUT = "items/global_trade.xml"
REL_ITEMS = "items/item_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_global_trade_50.txt")


def ids_do_servidor():
    texto = open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_ITEMS), encoding="utf-8").read()
    return set(int(i) for i in re.findall(r'<item_template\s+id="(\d+)"', texto))


def le_cliente(pasta):
    itens = []
    for _, e in ET.iterparse(os.path.join(pasta, "data", "items", "client_items.xml")):
        if e.tag != "client_item":
            continue
        kinah = (e.findtext("can_world_kina_vendor") or "").strip().upper() == "TRUE"
        luna = (e.findtext("can_world_vendor") or "").strip().upper() == "TRUE"
        if kinah or luna:
            categoria = (e.findtext("vendor_category_index") or "").strip() or "0"
            itens.append((int(e.findtext("id")), (e.findtext("name") or "").strip(), int(categoria), kinah, luna))
        e.clear()
    return itens


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    print("1. Lendo o cliente e o servidor...")
    itens = le_cliente(args.cliente)
    servidor = ids_do_servidor()
    rel = collections.defaultdict(list)
    categorias = collections.defaultdict(lambda: ([], []))
    for item_id, nome, categoria, kinah, luna in sorted(itens):
        if item_id not in servidor:
            rel["anunciável no cliente sem template no servidor"].append(f"{item_id} {nome}")
            continue
        if categoria == 0:
            rel["anunciável sem vendor_category_index (categoria 0, só pela busca)"].append(f"{item_id} {nome}")
        if kinah:
            categorias[categoria][0].append(item_id)
        if luna:
            categorias[categoria][1].append(item_id)
        if luna and not kinah:
            rel["só em Luna (can_world_kina_vendor falso)"].append(f"{item_id} {nome}")
    print(f"   anunciáveis no cliente: {len(itens)} | com template: {sum(1 for i in itens if i[0] in servidor)} | categorias: {len(categorias)}")

    raiz = ET.Element("global_trade", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                       "xsi:noNamespaceSchemaLocation": "global_trade.xsd"})
    for categoria in sorted(categorias):
        kinah, luna = categorias[categoria]
        e = ET.SubElement(raiz, "category", id=str(categoria))
        if kinah:
            ET.SubElement(e, "kinah").text = " ".join(map(str, kinah))
        if luna:
            ET.SubElement(e, "luna").text = " ".join(map(str, luna))
        rel["categorias"].append(f"{categoria}: {len(kinah)} em kinah, {len(luna)} em Luna")
    ET.indent(raiz, space="\t")
    texto = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"

    print("2. Validando contra o static_data.xsd agregado...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    if not schema.validate(etree.fromstring(texto.encode("utf-8"))):
        for e in list(schema.error_log)[:20]:
            print(f"   linha {e.line}: {e.message}")
        sys.exit("   XSD INVALIDO")
    print("   valido")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("parse_global_trade_50.py\n")
        for k, v in rel.items():
            f.write(f"\n== {k}: {len(v)}\n")
            f.writelines(f"  {x}\n" for x in v)
    print(f"   relatorio: {RELATORIO}")

    if not args.aplicar:
        print("\nModo --verificar: nada foi gravado.")
        return
    print("3. Gravando...")
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        caminho = os.path.join(base, REL_OUT)
        if os.path.exists(caminho):
            backup_manager.backup_file_before_modification(REL_OUT)
        with open(caminho, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print(f"   Gravado: {caminho}")


if __name__ == "__main__":
    main()
