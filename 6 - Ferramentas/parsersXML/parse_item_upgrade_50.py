#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_item_upgrade_50.py

Receitas do Ascend (C_START_ITEM_UPGRADE, botão "Ascend" / "Cancel Ascension" do quick menu "Altar of Transcendence
(Enchantment)") do Classic 5.0 para o items/item_upgrade.xml.

Fonte (data/items do cliente, servidor normal; o special/ difere só em 130 bytes):
  client_item_upgrade.xml   receita: item de origem (upgrade_item_name), faixa de encantamento exigida (check_enchant_count_min/max),
                            o que passa para o item novo (skill, manastones, godstone, new gemstone) e uma ou duas opções
                            (upgrade_list/data). Cada opção tem kinah, AP, até 3 materiais e as faixas fail/up/top com rate em
                            1/10000, item, quantidade e o encantamento com que o item novo nasce.
  client_items.xml          name -> id

Captura oficial (Outros/outros_2026-09-21_06-10-28, 1 de 1): a receita 1070 (belt_d_a_e2_base_60a, uma opção, up 10000, 54.150 AP)
trocou o cinto 123001181 pelo 123001182; C 0x106 [D receita][D objeto][D 0], o último D é a opção (índice 0).

Receita com item de origem, resultado ou material sem template no servidor, ou com faixas que não somam 10000, fica de fora e vai
para o relatório.

Uso:
    python parse_item_upgrade_50.py --verificar
    python parse_item_upgrade_50.py --aplicar
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

REL_OUT = "items/item_upgrade.xml"
REL_ITEMS = "items/item_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_item_upgrade_50.txt")
GRADES = (("FAIL", "fail"), ("UP", "up"), ("TOP", "top"))


def ids_do_servidor():
    texto = open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_ITEMS), encoding="utf-8").read()
    return set(int(i) for i in re.findall(r'<item_template\s+id="(\d+)"', texto))


def le_cliente(pasta):
    base = os.path.join(pasta, "data", "items")
    por_nome = {}
    for _, e in ET.iterparse(os.path.join(base, "client_items.xml")):
        if e.tag != "client_item":
            continue
        item_id, nome = e.findtext("id"), e.findtext("name")
        if item_id and nome:
            por_nome[nome.strip().lower()] = int(item_id)
        e.clear()
    receitas = ET.parse(os.path.join(base, "client_item_upgrade.xml")).getroot()
    return por_nome, receitas


def booleano(texto):
    return "true" if (texto or "").strip().upper() == "TRUE" else "false"


def opcao(data, por_nome, servidor):
    """Uma entrada de upgrade_list; devolve (atributos, materiais, faixas) ou levanta ValueError com o motivo."""
    campos = {c.tag: (c.text or "").strip() for c in data}
    materiais = []
    for n in (1, 2, 3):
        nome = campos.get(f"sub_material_item{n}", "").lower()
        if not nome:
            continue
        item_id = por_nome.get(nome)
        if item_id is None or item_id not in servidor:
            raise ValueError(f"material {nome} sem template")
        materiais.append((item_id, int(campos.get(f"sub_material_item_count{n}") or 1)))
    faixas = []
    for grade, prefixo in GRADES:
        taxa = int(campos.get(f"{prefixo}_upgrade_item_rate") or 0)
        if taxa <= 0:
            continue
        nome = campos.get(f"{prefixo}_upgrade_item", "").lower()
        item_id = por_nome.get(nome)
        if item_id is None or item_id not in servidor:
            raise ValueError(f"resultado {prefixo} {nome} sem template")
        faixas.append((grade, taxa, item_id, int(campos.get(f"{prefixo}_upgrade_item_cnt") or 1),
                       int(campos.get(f"{prefixo}_upgrade_enchant_count") or 0)))
    total = sum(f[1] for f in faixas)
    if total != 10000:
        raise ValueError(f"faixas somam {total}")
    return {"kinah": campos.get("need_qina") or "0", "ap": campos.get("need_abyss_point") or "0"}, materiais, faixas


def monta(receitas, por_nome, servidor, rel):
    raiz = ET.Element("item_upgrades", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                        "xsi:noNamespaceSchemaLocation": "item_upgrade.xsd"})
    for r in sorted(receitas, key=lambda r: int(r.findtext("id"))):
        rid, nome = int(r.findtext("id")), (r.findtext("name") or "").strip()
        origem_nome = (r.findtext("upgrade_item_name") or "").strip().lower()
        origem = por_nome.get(origem_nome)
        if origem is None or origem not in servidor:
            rel["receita descartada: item de origem sem template"].append(f"{rid} {nome}: {origem_nome}")
            continue
        opcoes, erro = [], None
        lista = r.find("upgrade_list")
        for i, data in enumerate(lista if lista is not None else []):
            try:
                opcoes.append(opcao(data, por_nome, servidor))
            except ValueError as e:
                erro = f"opção {i}: {e}"
                break
        if erro or not opcoes:
            rel["receita descartada"].append(f"{rid} {nome}: {erro or 'sem opção'}")
            continue
        e = ET.SubElement(raiz, "upgrade", id=str(rid), name=nome, item_id=str(origem),
                          enchant_min=(r.findtext("check_enchant_count_min") or "0").strip(),
                          enchant_max=(r.findtext("check_enchant_count_max") or "0").strip(),
                          skill_transfer=booleano(r.findtext("skill_transfer")),
                          option_transfer=booleano(r.findtext("matter_option_transfer")),
                          proc_transfer=booleano(r.findtext("matter_proc_transfer")),
                          gemstone_transfer=booleano(r.findtext("new_gemstone_transfer")))
        resumo = []
        for custo, materiais, faixas in opcoes:
            o = ET.SubElement(e, "option", kinah=custo["kinah"], ap=custo["ap"])
            for item_id, qtd in materiais:
                ET.SubElement(o, "material", item_id=str(item_id), count=str(qtd))
            for grade, taxa, item_id, qtd, enchant in faixas:
                ET.SubElement(o, "result", grade=grade, rate=str(taxa), item_id=str(item_id), count=str(qtd), enchant=str(enchant))
            resumo.append(f"[kinah {custo['kinah']}, AP {custo['ap']}, {len(materiais)} materiais, "
                          + ", ".join(f"{g} {t} -> {i}+{en}" for g, t, i, _, en in faixas) + "]")
        rel["receita gerada"].append(f"{rid} {nome}: {origem} " + " ".join(resumo))
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
    por_nome, receitas = le_cliente(args.cliente)
    servidor = ids_do_servidor()
    print(f"   receitas: {len(receitas)} | templates no servidor: {len(servidor)}")

    rel = collections.defaultdict(list)
    raiz = monta(receitas, por_nome, servidor, rel)
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
        f.write("parse_item_upgrade_50.py\n")
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
