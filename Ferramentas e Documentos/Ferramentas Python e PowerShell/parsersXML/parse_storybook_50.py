#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_storybook_50.py

Book of Legends (USER_STORY_BOOK no Game.dll, storybook nos dados) do Classic 5.0 para o storybook/storybook.xml.

Fonte (data do cliente, servidor normal):
  PC/client_storybook.xml          livro: tipo (collection_type 0 = puzzle, 1 = nature, 2 = adventure) e os itens a registrar
                                   ("nome" = 1 unidade, "nome 30" = 30 unidades do mesmo item)
  PC/client_storybook_reward.xml   recompensa ao completar: reward_type 1 = atributos (reward_attr "Stat valor"), 2 = skill,
                                   3 = itens ("nome qtd"); a recompensa sem livro (1003, 2003) fica de fora
  items/client_appraise_item.xml   identificação do fragmento desconhecido: sorteio por create_rate (1/10000) entre os fragmentos
  items/client_items.xml           name -> id
  skills/client_skills.xml         name -> id

Capturas oficiais (06_Sistemas_Novos_Book_of_Legends, 2026-09-11):
  - C 0xDC identificou 11 classic_puzzleF_piece_unknown_legend e 2 de três outros; o S 0x171 trouxe 17 fragmentos, um sorteio por
    unidade, todos da lista do client_appraise_item.
  - C 0xE4 [D livro] registrou, dos fragmentos que o jogador tinha, cada um que o livro ainda não tinha (um de cada).
Atributo sem StatEnum conhecido derruba o livro inteiro (relatório), para não dar recompensa pela metade.

Uso:
    python parse_storybook_50.py --verificar
    python parse_storybook_50.py --aplicar
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
from rebuild_50_item_templates import BONUS_MODS  # noqa: E402  nome do atributo no cliente (minúsculo) -> StatEnum

REL_OUT = "storybook/storybook.xml"
REL_ITEMS = "items/item_templates.xml"
REL_SKILLS = "skills/skill_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_storybook_50.txt")
TIPOS = {"0": "PUZZLE", "1": "NATURE", "2": "ADVENTURE"}


def ids_do_servidor(rel, padrao):
    texto = open(os.path.join(backup_manager.SERVER_DATA_DIR, rel), encoding="utf-8").read()
    return set(int(i) for i in re.findall(padrao, texto))


def le_cliente(pasta):
    base = os.path.join(pasta, "data")
    itens = {}
    for _, e in ET.iterparse(os.path.join(base, "items", "client_items.xml")):
        if e.tag == "client_item":
            item_id, nome = e.findtext("id"), e.findtext("name")
            if item_id and nome:
                itens[nome.strip().lower()] = int(item_id)
            e.clear()
    skills = {}
    for _, e in ET.iterparse(os.path.join(base, "skills", "client_skills.xml")):
        if e.tag == "skill_base_client":
            nome, sid = e.findtext("name"), e.findtext("id")
            if nome and sid:
                skills[nome.strip().lower()] = int(sid)
            e.clear()
    livros = ET.parse(os.path.join(base, "PC", "client_storybook.xml")).getroot()
    recompensas = {int(r.findtext("storybook_id")): r for r in ET.parse(os.path.join(base, "PC", "client_storybook_reward.xml")).getroot()}
    avaliacoes = ET.parse(os.path.join(base, "items", "client_appraise_item.xml")).getroot()
    return itens, skills, livros, recompensas, avaliacoes


def nome_e_qtd(texto):
    partes = (texto or "").split()
    return partes[0].lower(), int(partes[1]) if len(partes) > 1 else 1


def livro(e, recompensa, itens, skills, itens_servidor, skills_servidor):
    """Devolve o elemento do livro ou levanta ValueError com o motivo."""
    lid, tipo = int(e.findtext("id")), TIPOS.get((e.findtext("collection_type") or "").strip())
    if tipo is None:
        raise ValueError(f"collection_type {e.findtext('collection_type')} desconhecido")
    if recompensa is None:
        raise ValueError("sem recompensa no client_storybook_reward")
    x = ET.Element("storybook", id=str(lid), name=(e.findtext("name") or "").strip(), type=tipo)
    vistos = set()
    lista = e.find("collection_item_list")
    for d in lista if lista is not None else []:
        nome, qtd = nome_e_qtd(d.findtext("collection_item"))
        item_id = itens.get(nome)
        if item_id is None or item_id not in itens_servidor:
            raise ValueError(f"item {nome} sem template")
        if item_id in vistos:
            raise ValueError(f"item {nome} repetido")
        vistos.add(item_id)
        ET.SubElement(x, "piece", item_id=str(item_id), count=str(qtd))
    if not vistos:
        raise ValueError("sem item")
    tipo_recompensa = (recompensa.findtext("reward_type") or "").strip()
    if tipo_recompensa == "1":
        mods = ET.SubElement(x, "modifiers")
        lista = recompensa.find("reward_attr_list")
        for d in lista if lista is not None else []:
            stat, valor = (d.findtext("reward_attr") or "").split()
            enum = BONUS_MODS.get(stat.lower())
            if enum is None:
                raise ValueError(f"atributo {stat} sem StatEnum")
            ET.SubElement(mods, "add", name=enum, value=valor, bonus="true")
        if not len(mods):
            raise ValueError("recompensa de atributo vazia")
    elif tipo_recompensa == "2":
        lista = recompensa.find("reward_skill_list")
        for d in lista if lista is not None else []:
            nome = (d.findtext("reward_skill") or "").strip().lower()
            skill_id = skills.get(nome)
            if skill_id is None or skill_id not in skills_servidor:
                raise ValueError(f"skill {nome} sem template")
            ET.SubElement(x, "reward_skill", skill_id=str(skill_id), level="1")
    elif tipo_recompensa == "3":
        lista = recompensa.find("reward_item_list")
        for d in lista if lista is not None else []:
            nome, qtd = nome_e_qtd(d.findtext("reward_item"))
            item_id = itens.get(nome)
            if item_id is None or item_id not in itens_servidor:
                raise ValueError(f"recompensa {nome} sem template")
            ET.SubElement(x, "reward_item", item_id=str(item_id), count=str(qtd))
    else:
        raise ValueError(f"reward_type {tipo_recompensa} desconhecido")
    if len(x) == len(vistos):
        raise ValueError("recompensa vazia")
    return x


def monta(itens, skills, livros, recompensas, avaliacoes, itens_servidor, skills_servidor, rel):
    raiz = ET.Element("storybooks", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                     "xsi:noNamespaceSchemaLocation": "storybook.xsd"})
    usados = set()
    for e in sorted(livros, key=lambda e: int(e.findtext("id"))):
        lid = int(e.findtext("id"))
        usados.add(lid)
        try:
            x = livro(e, recompensas.get(lid), itens, skills, itens_servidor, skills_servidor)
        except ValueError as erro:
            rel["livro descartado"].append(f"{lid} {e.findtext('name')}: {erro}")
            continue
        raiz.append(x)
        rel["livro gerado"].append(f"{lid} {x.get('name')} {x.get('type')}: {len(x.findall('piece'))} itens, "
                                   f"{len(x.findall('modifiers/add'))} atributos, {len(x.findall('reward_skill'))} skills, "
                                   f"{len(x.findall('reward_item'))} itens de recompensa")
    for lid in sorted(set(recompensas) - usados):
        rel["recompensa sem livro (fora)"].append(f"{lid} {recompensas[lid].findtext('name')}")
    for a in sorted(avaliacoes, key=lambda a: int(a.findtext("id"))):
        nome = (a.findtext("name") or "").strip().lower()
        item_id = itens.get(nome)
        if item_id is None or item_id not in itens_servidor:
            rel["identificação descartada: fragmento desconhecido sem template"].append(nome)
            continue
        resultados, erro = [], None
        lista = a.find("create_item_list")
        for d in lista if lista is not None else []:
            criado = (d.findtext("create_item") or "").strip().lower()
            criado_id = itens.get(criado)
            if criado_id is None or criado_id not in itens_servidor:
                erro = f"resultado {criado} sem template"
                break
            resultados.append((criado_id, int(d.findtext("create_item_num") or 1), int(d.findtext("create_rate") or 0)))
        if erro is None and sum(r[2] for r in resultados) != 10000:
            erro = f"taxas somam {sum(r[2] for r in resultados)}"
        if erro:
            rel["identificação descartada"].append(f"{nome}: {erro}")
            continue
        x = ET.SubElement(raiz, "appraise", item_id=str(item_id))
        for criado_id, qtd, taxa in resultados:
            ET.SubElement(x, "result", item_id=str(criado_id), count=str(qtd), rate=str(taxa))
        rel["identificação gerada"].append(f"{nome} ({item_id}): {len(resultados)} fragmentos")
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
    itens, skills, livros, recompensas, avaliacoes = le_cliente(args.cliente)
    itens_servidor = ids_do_servidor(REL_ITEMS, r'<item_template\s+id="(\d+)"')
    skills_servidor = ids_do_servidor(REL_SKILLS, r'<skill_template\s+skill_id="(\d+)"')
    print(f"   livros: {len(livros)} | recompensas: {len(recompensas)} | identificações: {len(avaliacoes)}")

    rel = collections.defaultdict(list)
    raiz = monta(itens, skills, livros, recompensas, avaliacoes, itens_servidor, skills_servidor, rel)
    texto = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"
    print(f"   livros: {len(raiz.findall('storybook'))} | identificações: {len(raiz.findall('appraise'))}")

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
        f.write("parse_storybook_50.py\n")
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
