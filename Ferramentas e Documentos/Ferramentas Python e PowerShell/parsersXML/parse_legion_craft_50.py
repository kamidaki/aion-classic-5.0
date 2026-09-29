#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_legion_craft_50.py

Produção da Legion (aba 생산 da janela da Legion) do Classic 5.0 para o legion/legion_craft.xml.

Fonte: PC/client_guild_craft.xml (receita, raça, tempo, produto e componentes) e items/client_items.xml (nome -> id).
Só entram as receitas active=1: a lista oficial (S 0x15A) da Legion asmodiana Lost Academy (outros2 2026-09-22 10:23) tem exatamente as 40
ativas de raça all + dark, na ordem do id. No pacote, cada receita leva os componentes doáveis por id crescente: kinah (compo_gold, como o
item 182400001) e itens (component); essência e fragmento de essência não entram. O LegionPacketsTest refaz os 1059 b oficiais deste XML. Conferência: C_GUILD [14][D 501][H 2] com 1 kinah e 1
classic_iddramata_01_essence (186020328).

Uso:
    python parse_legion_craft_50.py --verificar
    python parse_legion_craft_50.py --aplicar
A pasta do cliente (a que contém data/) vem de --cliente ou da variável AION_CLIENT_XML_DIR.
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_OUT = "legion/legion_craft.xml"
REL_ITEMS = "items/item_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
RACAS = {"all": "ALL", "light": "ELYOS", "dark": "ASMODIANS"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    print("1. Lendo o cliente e o servidor...")
    base = os.path.join(args.cliente, "data")
    ids = {}
    for _, e in ET.iterparse(os.path.join(base, "items", "client_items.xml")):
        if e.tag == "client_item":
            nome, iid = e.findtext("name"), e.findtext("id")
            if nome and iid:
                ids[nome.strip().lower()] = int(iid)
            e.clear()
    texto_itens = open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_ITEMS), encoding="utf-8").read()
    itens_servidor = set(int(i) for i in re.findall(r'<item_template\s+id="(\d+)"', texto_itens))

    raiz = ET.Element("legion_craft", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                       "xsi:noNamespaceSchemaLocation": "legion_craft.xsd"})
    receitas = sorted(ET.parse(os.path.join(base, "PC", "client_guild_craft.xml")).getroot(), key=lambda r: int(r.findtext("id")))
    sem_produto = []
    for r in receitas:
        if r.findtext("active") != "1":
            continue
        rid = r.findtext("id")
        attrs = {"id": rid, "name": r.findtext("name").strip(), "race": RACAS[r.findtext("race").strip()],
                 "type": r.findtext("type").strip().upper(), "craft_time": r.findtext("craft_time") or "0"}
        produto = (r.findtext("product") or "").strip()
        if produto:
            pid = ids.get(produto.lower())
            if pid is None or pid not in itens_servidor:
                sem_produto.append(f"{rid} {produto}")
            else:
                attrs["product_id"] = str(pid)
                attrs["product_count"] = r.findtext("product_quantity") or "1"
        if r.findtext("essence_quantity"):
            attrs["essence_count"] = r.findtext("essence_quantity")
        er = ET.SubElement(raiz, "recipe", attrs)
        for d in r.find("component_list"):
            campos = {c.tag: (c.text or "").strip() for c in d}
            if "compo_gold" in campos:
                ET.SubElement(er, "kinah", amount=campos["compo_gold"])
            elif "component" in campos:
                item = ids.get(campos["component"].lower())
                if item is None or item not in itens_servidor:
                    sys.exit(f"receita {rid}: componente {campos['component']} sem template no servidor")
                ET.SubElement(er, "item", id=str(item), count=campos["compo_quantity"], points=campos.get("compo_contribu", "0"))
            elif "compo_essence" in campos:
                ET.SubElement(er, "essence", count=campos["compo_essence"])
            elif "essence_piece_quantity" in campos:
                ET.SubElement(er, "essence_piece", count=campos["essence_piece_quantity"])
            else:
                sys.exit(f"receita {rid}: componente desconhecido {campos}")
    print(f"   receitas ativas: {len(raiz)}")
    if sem_produto:
        print(f"   produto sem template no servidor (receita fica sem product_id): {len(sem_produto)}")
        for s in sem_produto:
            print("     " + s)
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

    if not args.aplicar:
        print("\nModo --verificar: nada foi gravado.")
        return
    print("3. Gravando...")
    for base_dir in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        caminho = os.path.join(base_dir, REL_OUT)
        if os.path.exists(caminho):
            backup_manager.backup_file_before_modification(REL_OUT)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print(f"   Gravado: {caminho}")


if __name__ == "__main__":
    main()
