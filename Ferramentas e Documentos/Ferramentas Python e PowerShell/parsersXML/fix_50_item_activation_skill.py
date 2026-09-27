#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza ações ``skilluse`` com o catálogo oficial Classic 5.0 EU.

O nome de ``activation_skill`` resolve para ID pelo ``client_skills.xml``. A
ação só é inserida ou corrigida quando o mesmo ID existe no
``skill_templates.xml`` do servidor e, quando presente, seu ``name_desc``
confirma o nome oficial. Pequenos valores numéricos de ``activation_skill``
usados por equipamentos não são IDs e permanecem documentados como pendência.

Uso:
    python fix_50_item_activation_skill.py --verificar
    python fix_50_item_activation_skill.py --aplicar
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
REL_SKILLS = "skills/skill_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_item_activation_skill_50.txt")
TEMPLATE_RE = re.compile(r'(<item_template\s+id="(\d+)"[^>]*?(?:/>|>.*?</item_template>))', re.S)
SKILLUSE_RE = re.compile(r'<skilluse\b[^>]*/>')
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def le_cliente(pasta):
    skills = {}
    path = os.path.join(pasta, "data", "skills", "client_skills.xml")
    for _, elemento in ET.iterparse(path, events=("end",)):
        if elemento.tag == "skill_base_client":
            nome = (elemento.findtext("name") or "").strip().lower()
            skill_id = (elemento.findtext("id") or "").strip()
            if nome and skill_id:
                skills.setdefault(nome, int(skill_id))
            elemento.clear()

    ativacao = {}
    catalogo_eu = os.path.join(pasta, "data", "europe", "Items", "client_items.xml")
    catalogo = catalogo_eu if os.path.isfile(catalogo_eu) else os.path.join(pasta, "data", "items", "client_items.xml")
    for _, elemento in ET.iterparse(catalogo, events=("end",)):
        if elemento.tag == "client_item":
            item_id = (elemento.findtext("id") or "").strip()
            nome = (elemento.findtext("activation_skill") or "").strip().lower()
            nivel = (elemento.findtext("activation_level") or "1").strip() or "1"
            if item_id and nome:
                ativacao[int(item_id)] = (nome, nivel)
            elemento.clear()
    return skills, ativacao


def le_skills_servidor():
    texto = open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_SKILLS), encoding="utf-8").read()
    resultado = {}
    for match in re.finditer(r'<skill_template\b([^>]*)>', texto):
        atributos = dict(ATTR_RE.findall(match.group(1)))
        if "skill_id" in atributos:
            resultado[int(atributos["skill_id"])] = atributos.get("name_desc", "").lower()
    return resultado


def atualiza_skilluse(tag, skill_id, nivel):
    atributos = dict(ATTR_RE.findall(tag))
    novo = tag
    if atributos.get("skillid") != str(skill_id):
        novo = re.sub(r'\bskillid="[^"]*"', f'skillid="{skill_id}"', novo)
    if "level" in atributos:
        novo = re.sub(r'\blevel="[^"]*"', f'level="{nivel}"', novo)
    else:
        novo = novo[:-2].rstrip() + f' level="{nivel}"/>'
    return novo


def insere_skilluse(bloco, skill_id, nivel, nl):
    tag = f'<skilluse skillid="{skill_id}" level="{nivel}"/>'
    actions = re.search(r'<actions>(.*?)</actions>', bloco, re.S)
    if actions:
        skilllearn = list(re.finditer(r'<skilllearn\b[^>]*/>', actions.group(1)))
        if skilllearn:
            pos = actions.start(1) + skilllearn[-1].end()
            return bloco[:pos] + nl + "\t\t\t" + tag + bloco[pos:]
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

    print("1. Lendo o catálogo EU, as skills oficiais e o servidor...")
    skills, ativacao = le_cliente(args.cliente)
    servidor = le_skills_servidor()
    texto = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in texto else "\n"
    rel = collections.defaultdict(list)
    insercoes, trocas, niveis = {}, {}, {}

    def corrige(match):
        bloco, item_id = match.group(1), int(match.group(2))
        dados = ativacao.get(item_id)
        if dados is None:
            return bloco
        nome, nivel = dados
        if nome.isdigit():
            rel["codigo numerico de ativacao (nao e skill id)"].append(f"{item_id}: {nome}")
            return bloco
        certo = skills.get(nome)
        if certo is None:
            rel["nome oficial sem ID no client_skills (nao alterado)"].append(f"{item_id}: {nome}")
            return bloco
        if certo not in servidor:
            rel["skill oficial sem template no servidor (nao alterado)"].append(f"{item_id}: {nome} = {certo}")
            return bloco
        if servidor[certo] and servidor[certo] != nome:
            rel["name_desc diferente do nome oficial (nao alterado)"].append(f"{item_id}: {nome} = {certo} ({servidor[certo]})")
            return bloco

        skilluse = SKILLUSE_RE.search(bloco)
        if skilluse is None:
            insercoes[item_id] = (nome, certo, nivel)
            rel["skilluse inserido"].append(f"{item_id}: {nome} = {certo}, nivel {nivel}")
            return insere_skilluse(bloco, certo, nivel, nl)

        atributos = dict(ATTR_RE.findall(skilluse.group(0)))
        atual = int(atributos.get("skillid", "0"))
        nivel_atual = atributos.get("level", "1")
        novo_tag = atualiza_skilluse(skilluse.group(0), certo, nivel)
        if atual != certo:
            trocas[item_id] = (nome, atual, certo)
            rel["skillid corrigido"].append(f"{item_id}: {nome} {atual} -> {certo}")
        if nivel_atual != nivel:
            niveis[item_id] = (nome, nivel_atual, nivel)
            rel["level corrigido"].append(f"{item_id}: {nome} {nivel_atual} -> {nivel}")
        if atual == certo and nivel_atual == nivel:
            rel["skilluse validado"].append(f"{item_id}: {nome} = {certo}, nivel {nivel}")
        return bloco[:skilluse.start()] + novo_tag + bloco[skilluse.end():]

    novo = TEMPLATE_RE.sub(corrige, texto)
    print(f"   itens com activation_skill: {len(ativacao)} | inseridos: {len(insercoes)} | skillid corrigidos: {len(trocas)} | levels corrigidos: {len(niveis)}")

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
        arquivo.write("fix_50_item_activation_skill.py\n")
        arquivo.write("catálogo: data/europe/Items/client_items.xml\n")
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
