#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_item_activation_skill.py

Corrige o <skilluse skillid> do item_templates.xml quando ele não é a skill que o cliente 5.0 dá ao item.

O client_items.xml guarda a skill do item pelo nome (activation_skill); o id sai do client_skills.xml. Em 2026-09-21, 15 dos 1.972 itens
com skilluse apontavam para outra skill: as pedras de auto-ressurreição (161000003, 161000004, 161001001) usavam a 10802, um proc de luva,
em vez da 9912 item_soulstone_resurrect_01 (Resurrect com CL_ResurrectDebuff 8296, o debuff visto na captura do C_DEAD_RESTART tipo 2).

Só troca quando a skill certa existe no skill_templates.xml do servidor e, se o template tiver name_desc, ele é o nome do cliente. O resto do
arquivo fica byte a byte igual.

Uso:
    python fix_50_item_activation_skill.py --verificar
    python fix_50_item_activation_skill.py --aplicar
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
REL_SKILLS = "skills/skill_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_item_activation_skill_50.txt")
TEMPLATE_RE = re.compile(r'(<item_template\s+id="(\d+)".*?(?:/>|</item_template>))', re.S)
SKILLUSE_RE = re.compile(r'(<skilluse\b[^>]*\bskillid=")(\d+)(")')


def le_cliente(pasta):
    skills = {}
    texto = open(os.path.join(pasta, "data", "skills", "client_skills.xml"), encoding="utf-8").read()
    for m in re.finditer(r"<skill_base_client>\s*<id>(\d+)</id>\s*<name>([^<]*)</name>", texto):
        skills.setdefault(m.group(2).strip().lower(), int(m.group(1)))
    ativacao = {}
    texto = open(os.path.join(pasta, "data", "items", "client_items.xml"), encoding="utf-8").read()
    for m in re.finditer(r"<client_item>\s*<id>(\d+)</id>(.*?)</client_item>", texto, re.S):
        a = re.search(r"<activation_skill>([^<]*)<", m.group(2))
        if a and a.group(1).strip():
            ativacao[int(m.group(1))] = a.group(1).strip().lower()
    return skills, ativacao


def le_skills_servidor():
    texto = open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_SKILLS), encoding="utf-8").read()
    return {int(m.group(1)): (m.group(2) or "").lower()
            for m in re.finditer(r'<skill_template\s+skill_id="(\d+)"(?:[^>]*?\bname_desc="([^"]*)")?', texto)}


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

    print("1. Lendo o cliente e o servidor...")
    skills, ativacao = le_cliente(args.cliente)
    servidor = le_skills_servidor()
    texto = open(src, encoding="utf-8", newline="").read()

    rel = collections.defaultdict(list)
    trocas = {}

    def corrige(m):
        bloco, item_id = m.group(1), int(m.group(2))
        nome = ativacao.get(item_id)
        s = SKILLUSE_RE.search(bloco)
        if nome is None or s is None:
            return bloco
        atual, certo = int(s.group(2)), skills.get(nome)
        if certo is None or certo == atual:
            return bloco
        if certo not in servidor:
            rel["skill do cliente sem template no servidor (nao trocado)"].append(f"{item_id}: {nome} = {certo}, servidor usa {atual}")
            return bloco
        if servidor[certo] and servidor[certo] != nome:
            rel["name_desc do template diferente do nome do cliente (nao trocado)"].append(f"{item_id}: {nome} = {certo} ({servidor[certo]})")
            return bloco
        trocas[item_id] = (nome, atual, certo)
        rel["trocado"].append(f"{item_id}: {nome} {atual} -> {certo}")
        return bloco[:s.start(2)] + str(certo) + bloco[s.end(2):]

    novo = TEMPLATE_RE.sub(corrige, texto)
    print(f"   itens com activation_skill: {len(ativacao)} | trocados: {len(trocas)}")
    for item_id, (nome, atual, certo) in sorted(trocas.items()):
        print(f"   {item_id}: {nome} {atual} -> {certo}")

    print("2. Validando contra o static_data.xsd agregado...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    doc = etree.fromstring(novo.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))
    if not schema.validate(doc):
        for e in list(schema.error_log)[:20]:
            print(f"   linha {e.line}: {e.message}")
        sys.exit("   XSD INVALIDO")
    print("   valido")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("fix_50_item_activation_skill.py\n")
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
