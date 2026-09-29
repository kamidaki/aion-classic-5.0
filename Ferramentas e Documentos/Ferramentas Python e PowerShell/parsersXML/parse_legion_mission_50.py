#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_legion_mission_50.py

Missões da Legion (aba de missões da janela da Legion, "Campaigns") do Classic 5.0 para o legion/legion_mission.xml.

Fontes (cliente EU):
  europe/PC/client_achievement_guild.xml   missões: período (daily/weekly/return), raça, atividade, faixa de nível, ações e estágios
                                           (completecount de ações concluídas -> exp de crescimento, essência e fragmentos)
  PC/client_achievement_guild_action.xml   ações: tipo, progresso máximo e o que conta (tags ou nomes)
  europe/Items/client_items.xml, europe/Npcs/client_npcs.xml, europe/Quest/quest.xml, world/WorldId.xml
                                           mgrouptag e nome -> id; o servidor não tem as tags

Código do tipo no S 0x15C (23 de 23 ações conferidas nas criações/logins de Lost Academy e Org Asmo): questclear 1, hunt 2,
enterworld 3, collectitem 4, itemplay 5, PvP 6, gathering 8. Tipos sem código visto (pointchange, useCrush, buyNPC, Vendor) só aparecem
nas missões de atividade PvP/PvE/gather, que nenhuma Legion capturada usa.
PENDENTE_DE_COMPROVACAO: worldcond devapass_exclusion_world_01 não está definido em nenhum arquivo do cliente (fica gravado como veio).

Uso:
    python parse_legion_mission_50.py --verificar
    python parse_legion_mission_50.py --aplicar
A pasta do cliente (a que contém data/) vem de --cliente ou da variável AION_CLIENT_XML_DIR.
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

REL_OUT = "legion/legion_mission.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
RACAS = {"all": "ALL", "light": "ELYOS", "dark": "ASMODIANS"}
PERIODOS = {"daily": "DAILY", "weekly": "WEEKLY", "return": "RETURN"}
TIPOS = {"questclear": ("QUESTCLEAR", 1), "hunt": ("HUNT", 2), "enterworld": ("ENTERWORLD", 3), "collectitem": ("COLLECTITEM", 4),
         "itemplay": ("ITEMPLAY", 5), "pvp": ("PVP", 6), "gathering": ("GATHERING", 8), "pointchange": ("POINTCHANGE", None),
         "usecrush": ("USECRUSH", None), "buynpc": ("BUYNPC", None), "vendor": ("VENDOR", None)}


def ids_do_servidor(rel, padrao):
    texto = open(os.path.join(backup_manager.SERVER_DATA_DIR, rel), encoding="utf-8").read()
    return set(int(i) for i in re.findall(padrao, texto))


def indice(caminho, tag_registro, campo_id="id"):
    """nome -> id e mgrouptag -> ids de um arquivo do cliente com registros <tag_registro>."""
    por_nome, por_tag = {}, collections.defaultdict(set)
    for _, e in ET.iterparse(caminho):
        if e.tag != tag_registro:
            continue
        iid, nome, tags = e.findtext(campo_id), e.findtext("name"), e.findtext("mgrouptag")
        if iid and iid.strip().isdigit():
            iid = int(iid)
            if nome:
                por_nome[nome.strip().lower()] = iid
            for t in (tags or "").split(","):
                if t.strip():
                    por_tag[t.strip().lower()].add(iid)
        e.clear()
    return por_nome, por_tag


def condicao(texto):
    """'1#A,B' -> ['A', 'B']"""
    if not texto:
        return []
    return [p.strip() for p in texto.split("#", 1)[-1].split(",") if p.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    base = os.path.join(args.cliente, "data")

    print("1. Lendo o cliente e o servidor...")
    itens_nome, itens_tag = indice(os.path.join(base, "europe", "Items", "client_items.xml"), "client_item")
    npcs_nome, npcs_tag = indice(os.path.join(base, "europe", "Npcs", "client_npcs.xml"), "npc_client")
    quests_nome, quests_tag = indice(os.path.join(base, "europe", "Quest", "quest.xml"), "quest")
    mundos_nome, mundos_tag = {}, collections.defaultdict(set)
    for d in ET.parse(os.path.join(base, "world", "WorldId.xml")).getroot():
        wid = int(d.get("id"))
        mundos_nome[(d.text or "").strip().lower()] = wid
        for t in (d.get("mgrouptag") or "").split(","):
            if t.strip():
                mundos_tag[t.strip().lower()].add(wid)
    itens_srv = ids_do_servidor("items/item_templates.xml", r'<item_template\s+id="(\d+)"')
    npcs_srv = set()
    for arq in os.listdir(os.path.join(backup_manager.SERVER_DATA_DIR, "npcs")):
        if arq.endswith(".xml"):
            npcs_srv |= ids_do_servidor(os.path.join("npcs", arq), r'<npc_template\s[^>]*npc_id="(\d+)"')
    print(f"   itens {len(itens_nome)} (tags {len(itens_tag)}) | npcs {len(npcs_nome)} (tags {len(npcs_tag)}) | "
          f"quests {len(quests_nome)} (tags {len(quests_tag)}) | mundos {len(mundos_nome)} | npcs no servidor {len(npcs_srv)}")
    if not npcs_nome or not npcs_srv:
        sys.exit("índice de NPC vazio: confira o nome do registro do client_npcs.xml e o atributo do npc_template")

    acoes = {a.findtext("id"): a for a in ET.parse(os.path.join(base, "PC", "client_achievement_guild_action.xml")).getroot()}
    missoes = [m for m in ET.parse(os.path.join(base, "europe", "PC", "client_achievement_guild.xml")).getroot() if m.findtext("active") == "1"]

    raiz = ET.Element("legion_mission", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                         "xsi:noNamespaceSchemaLocation": "legion_mission.xsd"})
    usadas, rel = [], collections.defaultdict(list)
    for m in sorted(missoes, key=lambda m: int(m.findtext("id"))):
        em = ET.SubElement(raiz, "mission", id=m.findtext("id"), name=m.findtext("name").strip(), period=PERIODOS[m.findtext("type").strip()],
                           race=RACAS[m.findtext("race").strip()], activity=m.findtext("activity").strip().upper(),
                           min_level=m.findtext("minlevel"), max_level=m.findtext("maxlevel"))
        for d in m.find("action_list"):
            aid = d.findtext("action").strip()
            ET.SubElement(em, "action", id=aid)
            if aid not in usadas:
                usadas.append(aid)
        for d in m.find("reward_list"):
            ET.SubElement(em, "stage", count=d.findtext("completecount"), exp=d.findtext("exp") or "0",
                          essence=d.findtext("essence_amount") or "0", essence_piece=d.findtext("essence_piece_amount") or "0")

    for aid in usadas:
        a = acoes[aid]
        tipo, codigo = TIPOS[a.findtext("type").strip().lower()]
        attrs = {"id": aid, "name": a.findtext("name").strip(), "type": tipo, "max_progress": a.findtext("maxprogress")}
        if codigo is not None:
            attrs["code"] = str(codigo)
        for campo, attr in (("target_type", "target_type"), ("levelgap", "level_gap"), ("worldcond", "world_condition")):
            if a.findtext(campo):
                attrs[attr] = a.findtext(campo).strip()
        ea = ET.SubElement(raiz, "action_template", attrs)
        tags, nomes = condicao(a.findtext("completecond_tag")), condicao(a.findtext("completecond"))
        alvo = set()
        if tipo in ("ITEMPLAY", "COLLECTITEM"):
            for t in tags:
                alvo |= itens_tag.get(t.lower(), set())
            alvo = {i for i in alvo if i in itens_srv}
            kind = "items"
        elif tipo == "HUNT":
            for t in tags:
                alvo |= npcs_tag.get(t.lower(), set())
            for n in nomes:
                if n.lower() in npcs_nome:
                    alvo.add(npcs_nome[n.lower()])
                else:
                    rel["NPC sem id no cliente"].append(f"{aid} {n}")
            alvo = {i for i in alvo if i in npcs_srv}
            kind = "npcs"
        elif tipo == "QUESTCLEAR":
            for t in tags:
                alvo |= quests_tag.get(t.lower(), set())
            kind = "quests"
        elif tipo == "ENTERWORLD":
            for t in tags:
                alvo |= mundos_tag.get(t.lower(), set())
            for n in nomes:
                if n.lower() in mundos_nome:
                    alvo.add(mundos_nome[n.lower()])
                else:
                    rel["mundo sem id"].append(f"{aid} {n}")
            kind = "worlds"
        else:
            kind = None
            if tags or nomes:
                ea.set("condition", ",".join(tags + nomes))
        if kind:
            if not alvo:
                rel["ação sem alvo resolvido"].append(f"{aid} {tipo} {tags + nomes}")
            ET.SubElement(ea, kind).text = " ".join(map(str, sorted(alvo)))
        print(f"   ação {aid} {tipo}: {len(alvo) if kind else '-'} alvos")

    ET.indent(raiz, space="\t")
    texto = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"
    for k, v in rel.items():
        print(f"   {k}: {v}")

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
