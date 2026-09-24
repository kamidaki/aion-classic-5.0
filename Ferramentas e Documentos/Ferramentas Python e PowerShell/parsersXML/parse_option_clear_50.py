#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_option_clear_50.py

Gera items/option_clear.xml (fonte e Produto Final) a partir do client_option_clear.xml do Classic 5.0: para cada
manastone e godstone do cliente, o custo em kinah da remocao e o destino da pedra (RETURN troca por uma pedra nao
negociavel do mesmo atributo, DELETE apaga), no formato lido por OptionClearData.

As manastones sao ligadas as regras pelo atributo (stat_enchant_type + stat_enchant_value), que e o que a janela de
remocao do cliente mostra; as godstones pelo nome interno (proc_item_name).

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python parse_option_clear_50.py --cliente "<pasta dos XMLs do cliente 5.0>"            (so mostra e valida)
    python parse_option_clear_50.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
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
from rebuild_50_item_templates import DEFAULT_CLIENT_DIR, iter_depth1, low  # noqa: E402

REL_XML = "items/option_clear.xml"
REL_XSD = "items/option_clear.xsd"
NL = "\r\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    rules_xml = os.path.join(args.cliente, "data", "items", "client_option_clear.xml")
    items_xml = os.path.join(args.cliente, "data", "items", "client_items.xml")
    for path in (rules_xml, items_xml):
        if not os.path.isfile(path):
            sys.exit(f"Arquivo do cliente nao encontrado: {path}. Informe --cliente ou AION_CLIENT_XML_DIR.")

    by_stat, by_proc = collections.defaultdict(list), {}
    for r in iter_depth1(rules_xml):
        if r.get("item_modification_type") == "enchant_option":
            by_stat[(low(r, "stat_enchant_type"), r.get("stat_enchant_value"))].append(r)
        elif r.get("item_modification_type") == "proc":
            by_proc[low(r, "proc_item_name")] = r

    name_to_id, stones, godstones = {}, [], []
    for d in iter_depth1(items_xml, lambda t: t in ("id", "name", "stat_enchant_type", "stat_enchant_value")):
        if not d.get("id"):
            continue
        name_to_id[low(d, "name")] = d["id"]
        if d.get("stat_enchant_type") and d.get("stat_enchant_value"):
            stones.append(d)
        elif low(d, "name") in by_proc:
            godstones.append(d)

    rows, problems = {}, collections.Counter()
    for d in stones:
        candidates = by_stat.get((low(d, "stat_enchant_type"), d["stat_enchant_value"]))
        if not candidates:
            problems["manastone sem regra no cliente"] += 1
            continue
        if len({(c.get("item_clear_type"), c.get("item_clear_return"), c.get("item_clear_kina")) for c in candidates}) > 1:
            problems["manastone com regras conflitantes"] += 1
            continue
        rule = candidates[0]
        kind = (rule.get("item_clear_type") or "").upper()
        return_id = name_to_id.get(low(rule, "item_clear_return")) if kind == "RETURN" else None
        if kind == "RETURN" and not return_id:
            problems["pedra devolvida inexistente no cliente"] += 1
            continue
        rows[int(d["id"])] = (kind, rule.get("item_clear_kina") or "0", return_id)
    for d in godstones:
        rule = by_proc[low(d, "name")]
        rows[int(d["id"])] = ((rule.get("item_clear_type") or "").upper(), rule.get("item_clear_kina") or "0", None)

    server_ids = set(re.findall(r'<item_template\b[^>]*?\bid="(\d+)"', open(os.path.join(backup_manager.SERVER_DATA_DIR, "items", "item_templates.xml"), encoding="utf-8").read()))
    for iid, (kind, _, return_id) in rows.items():
        if str(iid) not in server_ids:
            problems["pedra sem template no servidor"] += 1
        if return_id and return_id not in server_ids:
            problems["pedra devolvida sem template no servidor"] += 1

    kinds = collections.Counter(kind for kind, _, _ in rows.values())
    print(f"regras do cliente: {sum(len(v) for v in by_stat.values())} de manastone, {len(by_proc)} de godstone")
    print(f"linhas geradas: {len(rows)} ({dict(kinds)}) | manastones no cliente: {len(stones)} | godstones: {len(godstones)}")
    if problems:
        print(f"avisos: {dict(problems)}")

    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<option_clears xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="option_clear.xsd">']
    for iid in sorted(rows):
        kind, kinah, return_id = rows[iid]
        lines.append(f'\t<option_clear item_id="{iid}" type="{kind}" kinah="{kinah}"' + (f' return_item_id="{return_id}"' if return_id else "") + " />")
    lines.append("</option_clears>")
    text = NL.join(lines) + NL

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)))
    if not schema.validate(etree.fromstring(text.encode("utf-8"))):
        for e in list(schema.error_log)[:20]:
            print(f"   XSD linha {e.line}: {e.message}")
        sys.exit("XSD invalido: nada foi gravado.")
    print("XSD valido.")

    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    backup_manager.backup_file_before_modification(REL_XML)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        path = os.path.join(base, REL_XML)
        with open(path, "wb") as f:
            f.write(text.encode("utf-8"))
        print(f"Gravado: {path}")


if __name__ == "__main__":
    main()
