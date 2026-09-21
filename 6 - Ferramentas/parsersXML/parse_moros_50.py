#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_moros_50.py

Moreth, Chronicle of Time (MOROS no cliente) do Classic 5.0 para o moros/moros.xml.

Fonte (data do cliente, servidor normal):
  PC/client_moros_setting.xml   nível: pontos para chegar nele (moros_point), a passiva do nível (moros_skill + moros_skill_level)
                                e o valor do ponto no nível (moros_point_value, em %). Do 11 ao 101 só há moros_point 100, sem skill
                                nem valor: são linhas de preenchimento e ficam de fora (o nível máximo é o último com skill).
  PC/client_moros_point.xml     categoria -> pontos por unidade gravada
  items/client_items.xml        moros_point de cada item (categoria)
  skills/client_skills.xml      name -> id das passivas

Capturas oficiais (S 0x169 [H nível][D pontos][D 0][H registros], 40 de 40 nas capturas de 11/09 a 21/09):
  - Moreth 2026-09-11: um ac_head_n_r2_44c (gear_etc, 1 ponto) gravado no nível 1 levou os pontos de 1281 para 1283: 1 x 200%.
  - personagem no nível 2 com 1390, 2990 e 3257 pontos: o contador zera a cada nível (8850 para o 2).
Categoria sem ponto (can_not_record, event, quest) não entra: o item não pode ser gravado.

Uso:
    python parse_moros_50.py --verificar
    python parse_moros_50.py --aplicar
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

REL_OUT = "moros/moros.xml"
REL_ITEMS = "items/item_templates.xml"
REL_SKILLS = "skills/skill_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_moros_50.txt")


def ids_do_servidor(rel, padrao):
    texto = open(os.path.join(backup_manager.SERVER_DATA_DIR, rel), encoding="utf-8").read()
    return set(int(i) for i in re.findall(padrao, texto))


def le_cliente(pasta):
    base = os.path.join(pasta, "data")
    por_categoria = collections.defaultdict(list)
    for _, e in ET.iterparse(os.path.join(base, "items", "client_items.xml")):
        if e.tag != "client_item":
            continue
        item_id, categoria = e.findtext("id"), (e.findtext("moros_point") or "").strip()
        if item_id and categoria:
            por_categoria[categoria].append(int(item_id))
        e.clear()
    pontos = {c.findtext("name").strip(): int(c.findtext("point") or 0)
              for c in ET.parse(os.path.join(base, "PC", "client_moros_point.xml")).getroot()}
    niveis = []
    for n in ET.parse(os.path.join(base, "PC", "client_moros_setting.xml")).getroot():
        niveis.append({"level": int(n.get("level")), **{c.tag: (c.text or "").strip() for c in n}})
    skills = {}
    for _, e in ET.iterparse(os.path.join(base, "skills", "client_skills.xml")):
        if e.tag == "skill_base_client":
            nome, sid = e.findtext("name"), e.findtext("id")
            if nome and sid and nome.startswith("Moros_"):
                skills[nome.strip().lower()] = int(sid)
            e.clear()
    return por_categoria, pontos, niveis, skills


def monta(por_categoria, pontos, niveis, skills, itens_servidor, skills_servidor, rel):
    raiz = ET.Element("moros", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                "xsi:noNamespaceSchemaLocation": "moros.xsd"})
    esperado = 1
    for n in sorted(niveis, key=lambda n: n["level"]):
        if not n.get("moros_skill") or not n.get("moros_point_value"):
            rel["nível sem skill ou sem valor de ponto (preenchimento, fora)"].append(f"{n['level']}: {n.get('moros_point')} pontos")
            continue
        if n["level"] != esperado:
            sys.exit(f"nível {n['level']} fora de sequência (esperado {esperado})")
        esperado += 1
        skill_id = skills.get(n["moros_skill"].lower())
        if skill_id is None or skill_id not in skills_servidor:
            sys.exit(f"nível {n['level']}: skill {n['moros_skill']} sem template no servidor")
        ET.SubElement(raiz, "level", level=str(n["level"]), points=n.get("moros_point") or "0", rate=n["moros_point_value"],
                      skill_id=str(skill_id), skill_level=n.get("moros_skill_level") or "1")
        rel["nível gerado"].append(f"{n['level']}: {n.get('moros_point')} pontos, {n['moros_point_value']}%, "
                                   f"{n['moros_skill']} ({skill_id}) nv {n.get('moros_skill_level')}")
    for categoria in sorted(por_categoria, key=lambda c: (pontos.get(c, 0), c)):
        ids = sorted(por_categoria[categoria])
        ponto = pontos.get(categoria)
        if ponto is None:
            rel["categoria de item sem linha no client_moros_point (fora)"].append(f"{categoria}: {len(ids)} itens")
            continue
        if ponto <= 0:
            rel["categoria sem ponto (item não pode ser gravado)"].append(f"{categoria}: {len(ids)} itens")
            continue
        validos = [i for i in ids if i in itens_servidor]
        if len(validos) < len(ids):
            rel["item sem template no servidor (fora)"].append(f"{categoria}: {len(ids) - len(validos)} de {len(ids)}")
        if not validos:
            continue
        ET.SubElement(raiz, "category", name=categoria, point=str(ponto)).text = " ".join(map(str, validos))
        rel["categoria gerada"].append(f"{categoria}: {ponto} ponto(s), {len(validos)} itens")
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
    por_categoria, pontos, niveis, skills = le_cliente(args.cliente)
    itens_servidor = ids_do_servidor(REL_ITEMS, r'<item_template\s+id="(\d+)"')
    skills_servidor = ids_do_servidor(REL_SKILLS, r'<skill_template\s+skill_id="(\d+)"')
    print(f"   categorias: {len(pontos)} | níveis: {len(niveis)} | passivas: {len(skills)}")

    rel = collections.defaultdict(list)
    raiz = monta(por_categoria, pontos, niveis, skills, itens_servidor, skills_servidor, rel)
    texto = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"
    print(f"   níveis: {len(raiz.findall('level'))} | categorias: {len(raiz.findall('category'))}")

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
        f.write("parse_moros_50.py\n")
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
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print(f"   Gravado: {caminho}")


if __name__ == "__main__":
    main()
