#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza ações ``titleadd`` comprovadas pelo catálogo Classic 5.0 EU.

Uma ação só é criada quando ``cash_title`` aponta para um título já presente em
``player_titles.xml``. Itens cujos títulos ainda não têm template no servidor
permanecem inalterados e são relacionados no relatório, evitando uma exceção ao
usar o item. ``cash_available_minute=0`` representa título permanente e omite o
atributo ``minutes``; os demais valores são preservados exatamente como no
cliente oficial.

Uso:
    python sync_50_item_titles.py --verificar
    python sync_50_item_titles.py --aplicar
"""

import argparse
import collections
import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_ITEMS = "items/item_templates.xml"
REL_TITLES = "player_titles.xml"
DEFAULT_CLIENT_DIR = os.path.join(
    backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos"
)
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_item_titles_50.txt")
TEMPLATE_RE = re.compile(r'(<item_template\s+id="(\d+)"[^>]*?(?:/>|>.*?</item_template>))', re.S)
TITLEADD_RE = re.compile(r'<titleadd\b[^>]*/>')
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def le_cliente(pasta):
    catalogo_eu = os.path.join(pasta, "data", "europe", "Items", "client_items.xml")
    catalogo = catalogo_eu if os.path.isfile(catalogo_eu) else os.path.join(pasta, "data", "items", "client_items.xml")
    itens = {}
    for _, elemento in ET.iterparse(catalogo, events=("end",)):
        if elemento.tag == "client_item":
            item_id = (elemento.findtext("id") or "").strip()
            title_id = (elemento.findtext("cash_title") or "").strip()
            minutos = (elemento.findtext("cash_available_minute") or "0").strip() or "0"
            if item_id and title_id not in ("", "0", "none"):
                itens[int(item_id)] = (int(title_id), int(minutos))
            elemento.clear()
    return itens


def le_titulos_servidor():
    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_TITLES)
    return {int(elemento.get("id")) for elemento in ET.parse(caminho).getroot().findall("title")}


def tag_titleadd(title_id, minutos):
    duracao = f' minutes="{minutos}"' if minutos else ""
    return f'<titleadd titleid="{title_id}"{duracao}/>'


def insere_titleadd(bloco, title_id, minutos, nl):
    tag = tag_titleadd(title_id, minutos)
    actions = re.search(r'<actions>(.*?)</actions>', bloco, re.S)
    if actions:
        return bloco[:actions.start(1)] + nl + "\t\t\t" + tag + actions.group(1) + bloco[actions.end(1):]

    acoes = f"\t\t<actions>{nl}\t\t\t{tag}{nl}\t\t</actions>"
    if bloco.rstrip().endswith("/>"):
        fim = bloco.rfind("/>")
        return bloco[:fim] + ">" + nl + acoes + nl + "\t</item_template>" + bloco[fim + 2:]
    modificadores = re.search(r'</modifiers>', bloco)
    if modificadores:
        pos = modificadores.end()
        return bloco[:pos] + nl + acoes + bloco[pos:]
    inicio = bloco.find(">") + 1
    return bloco[:inicio] + nl + acoes + bloco[inicio:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--verificar", action="store_true")
    grupo.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    src = os.path.join(backup_manager.SERVER_DATA_DIR, REL_ITEMS)
    prod = os.path.join(backup_manager.PRODUTO_FINAL_DATA_DIR, REL_ITEMS)
    if hashlib.sha256(open(src, "rb").read()).digest() != hashlib.sha256(open(prod, "rb").read()).digest():
        sys.exit(f"{REL_ITEMS} do fonte e do Produto Final estao diferentes. Sincronize antes de rodar.")

    print("1. Lendo títulos oficiais, catálogo do servidor e templates de item...")
    oficiais = le_cliente(args.cliente)
    titulos_servidor = le_titulos_servidor()
    texto = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in texto else "\n"
    rel = collections.defaultdict(list)
    inseridos, corrigidos = {}, {}

    def corrige(match):
        bloco, item_id = match.group(1), int(match.group(2))
        dados = oficiais.get(item_id)
        if dados is None:
            return bloco
        title_id, minutos = dados
        atual = TITLEADD_RE.search(bloco)
        if title_id not in titulos_servidor:
            rel["título sem template no servidor (não alterado)"].append(
                f"{item_id}: título {title_id}, minutos {minutos}"
            )
            return bloco
        esperado = tag_titleadd(title_id, minutos)
        if atual is None:
            inseridos[item_id] = (title_id, minutos)
            rel["titleadd inserido"].append(f"{item_id}: título {title_id}, minutos {minutos}")
            return insere_titleadd(bloco, title_id, minutos, nl)
        if atual.group(0) != esperado:
            corrigidos[item_id] = (atual.group(0), esperado)
            rel["titleadd corrigido"].append(f"{item_id}: {atual.group(0)} -> {esperado}")
            return bloco[:atual.start()] + esperado + bloco[atual.end():]
        rel["titleadd validado"].append(f"{item_id}: título {title_id}, minutos {minutos}")
        return bloco

    novo = TEMPLATE_RE.sub(corrige, texto)
    pendentes = len(rel["título sem template no servidor (não alterado)"])
    print(
        f"   itens oficiais com cash_title: {len(oficiais)} | inseridos: {len(inseridos)} | "
        f"corrigidos: {len(corrigidos)} | pendentes por título: {pendentes}"
    )

    print("2. Validando contra o static_data.xsd agregado...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    doc = etree.fromstring(novo.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))
    if not schema.validate(doc):
        for erro in list(schema.error_log)[:20]:
            print(f"   linha {erro.line}: {erro.message}")
        sys.exit("   XSD INVALIDO")
    print("   válido")

    with open(RELATORIO, "w", encoding="utf-8") as arquivo:
        arquivo.write("sync_50_item_titles.py\n")
        arquivo.write("catálogo: data/europe/Items/client_items.xml\n")
        arquivo.write(f"títulos no player_titles.xml: {len(titulos_servidor)}\n")
        for chave, valores in rel.items():
            arquivo.write(f"\n== {chave}: {len(valores)}\n")
            arquivo.writelines(f"  {valor}\n" for valor in valores)
    print(f"   relatório: {RELATORIO}")

    if not args.aplicar:
        print("\nModo --verificar: nada foi gravado.")
        return
    print("3. Gravando fonte e Produto Final (com backup)...")
    backup_manager.backup_file_before_modification(REL_ITEMS)
    for caminho in (src, prod):
        with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
            arquivo.write(novo)
        print(f"   Gravado: {caminho}")


if __name__ == "__main__":
    main()
