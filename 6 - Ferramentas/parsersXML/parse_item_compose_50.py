#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_item_compose_50.py

Receitas do Altar of Transcendence (fusão) do Classic 5.0 para o items/item_compose.xml.

Fonte (data/items do cliente, servidor normal; o special/ tem as taxas pela metade):
  client_item_compose.xml   receita: compose_fee_6ea ou compose_fee_2ea (6 ou 2 materiais), faixas same/up/top com rate em 1/10000,
                            item e quantidade de cada faixa
  client_items.xml          compose_group_id = id da receita em que o item entra como material; name -> id dos resultados

Captura oficial (06_Sistemas_Novo_Global_Auction_House_and_Altar_of_Transcendences, 2026-09-11): a receita 16 gastou 6 rare_title_token
(compose_group_id 16) e 220.000 de kinah, a 5 gastou 6 manastones do grupo 5 e 25.000; os dois resultados são o item "up" da receita.

Receita sem taxa, sem material com template no servidor, com resultado sem template ou com faixas que não somam 10000 fica de fora e
vai para o relatório.

Uso:
    python parse_item_compose_50.py --verificar
    python parse_item_compose_50.py --aplicar
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

REL_OUT = "items/item_compose.xml"
REL_ITEMS = "items/item_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_item_compose_50.txt")
GRADES = (("SAME", "same"), ("UP", "up"), ("TOP", "top"))


def ids_do_servidor():
    texto = open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_ITEMS), encoding="utf-8").read()
    return set(int(i) for i in re.findall(r'<item_template\s+id="(\d+)"', texto))


def le_cliente(pasta):
    base = os.path.join(pasta, "data", "items")
    por_nome, grupos = {}, collections.defaultdict(list)
    for _, e in ET.iterparse(os.path.join(base, "client_items.xml")):
        if e.tag != "client_item":
            continue
        item_id, nome, grupo = e.findtext("id"), e.findtext("name"), e.findtext("compose_group_id")
        if item_id and nome:
            por_nome[nome.strip().lower()] = int(item_id)
        if item_id and grupo and grupo.strip() not in ("", "0"):
            grupos[int(grupo)].append(int(item_id))
        e.clear()
    receitas = [{c.tag: (c.text or "").strip() for c in r} for r in ET.parse(os.path.join(base, "client_item_compose.xml")).getroot()]
    return por_nome, grupos, receitas


def monta(receitas, por_nome, grupos, servidor, rel):
    raiz = ET.Element("item_composes", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                        "xsi:noNamespaceSchemaLocation": "item_compose.xsd"})
    for r in sorted(receitas, key=lambda r: int(r["id"])):
        rid, nome = int(r["id"]), r.get("name", "")
        modo = "6ea" if r.get("compose_fee_6ea") else "2ea" if r.get("compose_fee_2ea") else None
        if modo is None:
            rel["receita sem compose_fee_6ea nem compose_fee_2ea"].append(f"{rid} {nome}")
            continue
        materiais = sorted(i for i in grupos.get(rid, []) if i in servidor)
        sem_template = sorted(i for i in grupos.get(rid, []) if i not in servidor)
        if sem_template:
            rel["material sem template no servidor (fora da receita)"].append(f"{rid} {nome}: {sem_template}")
        if not materiais:
            rel["receita sem material com template no servidor"].append(f"{rid} {nome}")
            continue
        faixas, erro = [], None
        for grade, prefixo in GRADES:
            taxa = r.get(f"{prefixo}_rate_{modo}")
            if not taxa:
                continue
            item = r.get(f"{prefixo}_result_item_{modo}", "").lower()
            item_id = por_nome.get(item)
            if item_id is None or item_id not in servidor:
                erro = f"resultado {prefixo} {item} sem template"
                break
            faixas.append((grade, int(taxa), item_id, int(r.get(f"{prefixo}_result_item_cnt_{modo}") or 1)))
        if erro is None and sum(f[1] for f in faixas) != 10000:
            erro = f"faixas somam {sum(f[1] for f in faixas)}"
        if erro:
            rel["receita descartada"].append(f"{rid} {nome}: {erro}")
            continue
        e = ET.SubElement(raiz, "compose", id=str(rid), name=nome, material_count=modo[0], fee=r[f"compose_fee_{modo}"])
        ET.SubElement(e, "materials").text = " ".join(map(str, materiais))
        for grade, taxa, item_id, qtd in faixas:
            ET.SubElement(e, "result", grade=grade, rate=str(taxa), item_id=str(item_id), count=str(qtd))
        rel["receita gerada"].append(f"{rid} {nome}: {modo}, taxa {r[f'compose_fee_{modo}']}, {len(materiais)} materiais, "
                                     + ", ".join(f"{g} {t} -> {i} x{q}" for g, t, i, q in faixas))
    ET.indent(raiz, space="\t")
    return raiz


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    print("1. Lendo o cliente e o servidor...")
    por_nome, grupos, receitas = le_cliente(args.cliente)
    servidor = ids_do_servidor()
    print(f"   receitas: {len(receitas)} | grupos com material: {len(grupos)} | templates no servidor: {len(servidor)}")

    rel = collections.defaultdict(list)
    raiz = monta(receitas, por_nome, grupos, servidor, rel)
    texto = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"
    print(f"   receitas geradas: {len(raiz)}")

    print("2. Validando contra o static_data.xsd agregado...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    doc = etree.fromstring(texto.encode("utf-8"))
    if not schema.validate(doc):
        for e in list(schema.error_log)[:20]:
            print(f"   linha {e.line}: {e.message}")
        sys.exit("   XSD INVALIDO")
    print("   valido")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("parse_item_compose_50.py\n")
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
