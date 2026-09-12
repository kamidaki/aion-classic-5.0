#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_godstones_50.py

Completa o bloco <godstone> dos item_templates a partir do client_items.xml do Classic 5.0. Sem ele
ItemTemplate.getGodstoneInfo() e nulo, e o ItemSocketService recusa o engaste antes de comecar -- a pedra
nao entra na arma nem chega a testar o proc.

Existe porque o rebuild_50_item_templates.py so reconstroi os templates cujo cName nao bate com o nome do
cliente; godstone que ja batia ficou como estava na 4.8, e as de evento nunca tiveram o bloco.

Mapeamento (o mesmo do gen_godstone do rebuild):
    proc_enchant_skill                  -> skillid (pelo nome, via client_skills.xml)
    proc_enchant_skill_level            -> skilllvl
    proc_enchant_effect_occur_prob      -> probability      (mao principal)
    proc_enchant_effect_occur_left_prob -> probabilityleft  (mao secundaria)
breakprob/nonbreakcount ficam em 0: o cliente 5.0 nao tem campo de quebra por proc.

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python parse_godstones_50.py --cliente "<pasta dos XMLs do cliente 5.0>"            (so mostra e valida)
    python parse_godstones_50.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
A pasta tambem pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402
from rebuild_50_item_templates import ATTR_RE, BLOCK_RE, DEFAULT_CLIENT_DIR, esc, iter_depth1, load_name_ids, low  # noqa: E402

REL_XML = "items/item_templates.xml"
REL_XSD = "items/item_templates.xsd"
NL = "\r\n"
GODSTONE_RE = re.compile(r"[ \t]*<godstone\b[^>]*/>[ \t]*(?:\r\n|\n)?")
# <godstone> vem depois de <actions>, que vem depois de <modifiers> (ordem do item_templates.xsd)
AFTER_RE = re.compile(r"</actions>[ \t]*(?:\r\n|\n)|</modifiers>[ \t]*(?:\r\n|\n)")


def bloco(skill_id, d, atual=None):
    """O bloco novo. breakprob/nonbreakcount vem do que ja estava: sao a quebra por proc das godstone de
    ilusao, que o cliente 5.0 nao traz em campo nenhum -- reescrever com 0 apagaria dado bom."""
    atual = atual or {}
    a = [("nonbreakcount", atual.get("nonbreakcount", "0")), ("breakprob", atual.get("breakprob", "0"))]
    if d.get("proc_enchant_effect_occur_left_prob"):
        a.append(("probabilityleft", d["proc_enchant_effect_occur_left_prob"]))
    if d.get("proc_enchant_effect_occur_prob"):
        a.append(("probability", d["proc_enchant_effect_occur_prob"]))
    a += [("skilllvl", d.get("proc_enchant_skill_level") or "1"), ("skillid", skill_id)]
    return "\t\t<godstone" + "".join(f' {k}="{esc(v)}"' for k, v in a) + " />"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    items_xml = os.path.join(args.cliente, "data", "items", "client_items.xml")
    rules_xml = os.path.join(args.cliente, "data", "items", "client_option_clear.xml")
    skills_xml = os.path.join(args.cliente, "data", "skills", "client_skills.xml")
    for path in (items_xml, rules_xml, skills_xml):
        if not os.path.isfile(path):
            sys.exit(f"Arquivo do cliente nao encontrado: {path}. Informe --cliente ou AION_CLIENT_XML_DIR.")

    skills = load_name_ids(skills_xml)
    # a lista autoritativa de godstone da 5.0 e a do client_option_clear.xml (item_modification_type=proc)
    by_proc = {low(r, "proc_item_name") for r in iter_depth1(rules_xml) if r.get("item_modification_type") == "proc"}
    cli = {}
    for d in iter_depth1(items_xml):
        if d.get("id") and low(d, "name") in by_proc:
            cli[d["id"]] = d
    print(f"godstones no cliente 5.0: {len(cli)}")

    text = open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML), encoding="utf-8").read()
    edits, c, exemplos = [], collections.Counter(), []
    for m in BLOCK_RE.finditer(text):
        attrs = dict(ATTR_RE.findall(m.group(1)))
        d = cli.get(attrs.get("id"))
        if d is None:
            continue
        skill_id = skills.get(low(d, "proc_enchant_skill"))
        if not skill_id:
            c["skill do proc sem id no cliente"] += 1
            continue
        inner = m.group(3)
        if inner is None:  # <item_template ... /> sem filhos
            novo = bloco(skill_id, d)
            corpo = ">" + NL + novo + NL + "\t</item_template>"
            edits.append((m.start(2), m.end(2), corpo))
            c["bloco criado (template sem filhos)"] += 1
            exemplos.append((attrs["id"], attrs.get("name", ""), "criado"))
            continue
        atual = GODSTONE_RE.search(inner)
        novo = bloco(skill_id, d, dict(ATTR_RE.findall(atual.group(0))) if atual else None)
        if atual is None:
            pos = AFTER_RE.search(inner)
            corte = m.start(3) + (pos.end() if pos else 0)
            edits.append((corte, corte, novo + NL))
            c["bloco inserido"] += 1
            exemplos.append((attrs["id"], attrs.get("name", ""), "inserido"))
        elif atual.group(0).strip() != novo.strip():
            edits.append((m.start(3) + atual.start(), m.start(3) + atual.end(), novo + NL))
            c["bloco corrigido"] += 1
            exemplos.append((attrs["id"], attrs.get("name", ""), "corrigido: " + atual.group(0).strip()))
        else:
            c["ja estava certo"] += 1

    achados = sum(c.values())
    print(f"templates de godstone no servidor: {achados}")
    for k, v in c.most_common():
        print(f"   {k}: {v}")
    for e in exemplos[:6]:
        print(f"   ex.: {e[0]} {e[1]} -> {e[2]}")
    if not edits:
        print("Nada a fazer.")
        return

    edits.sort()
    out, pos = [], 0
    for a, b, new in edits:
        out.append(text[pos:a])
        out.append(new)
        pos = b
    out.append(text[pos:])
    novo_texto = "".join(out)

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)))
    doc = etree.fromstring(novo_texto.encode("utf-8"))
    if not schema.validate(doc):
        for e in list(schema.error_log)[:20]:
            print(f"   XSD linha {e.line}: {e.message}")
        sys.exit("XSD invalido: nada foi gravado.")
    antes = len(re.findall(r"<godstone\b", text))
    print(f"XSD valido. blocos <godstone>: {antes} -> {len(re.findall(r'<godstone', novo_texto))}")

    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    backup_manager.backup_file_before_modification(REL_XML)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        path = os.path.join(base, REL_XML)
        with open(path, "wb") as f:
            f.write(novo_texto.encode("utf-8"))
        print(f"Gravado: {path}")


if __name__ == "__main__":
    main()
