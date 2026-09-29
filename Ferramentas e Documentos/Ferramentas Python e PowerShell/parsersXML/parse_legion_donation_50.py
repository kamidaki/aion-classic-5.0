#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_legion_donation_50.py

Produção de moedas pessoais da Legion ("doação", aba 주화 생산 da janela da Legion) do Classic 5.0 para o legion/legion_donation.xml.

Fontes do cliente:
  PC/client_guild_donation.xml           grupos: cada <data> é um índice com item, quantidade, pontos de produção e moedas
  PC/client_guild_donation_setting.xml   reset_time do grupo ativo (800 = 08:00)
  items/client_items.xml                 nome -> id dos itens pedidos

O cliente não diz quais grupos entram na lista do dia. Os grupos vêm das capturas oficiais (S 0x159, 27 listas de 06/09 a 28/09): sempre
7, 8, 9, 10, 11, 14 e 15, mais o 12 (donation_candy_light) para Legion elyos e o 13 (donation_candy_dark) para asmodiana. Os de teste
(1 a 6) e os "newc" (16 a 22) nunca aparecem. Conferência: C_GUILD [13][D 10][D 1] consumiu 1 potion_a_hp_04a (162000069) e o saldo do
S 0x165 subiu 440 (Lost Academy, 22/09); [13][D 8][D 10] = matter_option_r_physicalcritical_60 (Inshagle, 12/09).

Uso:
    python parse_legion_donation_50.py --verificar
    python parse_legion_donation_50.py --aplicar
A pasta do cliente (a que contém data/) vem de --cliente ou da variável AION_CLIENT_XML_DIR.
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_OUT = "legion/legion_donation.xml"
REL_ITEMS = "items/item_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
GRUPOS_DA_CAPTURA = {7: "ALL", 8: "ALL", 9: "ALL", 10: "ALL", 11: "ALL", 12: "ELYOS", 13: "ASMODIANS", 14: "ALL", 15: "ALL"}


def le_cliente(pasta):
    base = os.path.join(pasta, "data")
    grupos = {}
    for g in ET.parse(os.path.join(base, "PC", "client_guild_donation.xml")).getroot():
        linhas = []
        for d in g.find("donation_group_info"):
            linhas.append({c.tag: (c.text or "").strip() for c in d})
        grupos[int(g.findtext("id"))] = (g.findtext("name").strip(), linhas)
    ativos = [s for s in ET.parse(os.path.join(base, "PC", "client_guild_donation_setting.xml")).getroot() if s.findtext("active") == "1"]
    if len(ativos) != 1:
        sys.exit(f"esperado 1 client_guild_donation_setting ativo, achei {len(ativos)}")
    reset = int(ativos[0].findtext("reset_time"))
    ids = {}
    for _, e in ET.iterparse(os.path.join(base, "items", "client_items.xml")):
        if e.tag == "client_item":
            nome, iid = e.findtext("name"), e.findtext("id")
            if nome and iid:
                ids[nome.strip().lower()] = int(iid)
            e.clear()
    return grupos, reset, ids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    print("1. Lendo o cliente e o servidor...")
    grupos, reset, ids = le_cliente(args.cliente)
    texto_itens = open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_ITEMS), encoding="utf-8").read()
    itens_servidor = set(int(i) for i in re.findall(r'<item_template\s+id="(\d+)"', texto_itens))
    if reset % 100 >= 60 or reset // 100 >= 24:
        sys.exit(f"reset_time inválido: {reset}")

    raiz = ET.Element("legion_donation", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                          "xsi:noNamespaceSchemaLocation": "legion_donation.xsd", "reset_time": f"{reset // 100:02d}:{reset % 100:02d}"})
    for gid, raca in sorted(GRUPOS_DA_CAPTURA.items()):
        nome, linhas = grupos[gid]
        eg = ET.SubElement(raiz, "group", id=str(gid), name=nome, race=raca)
        for esperado, l in enumerate(sorted(linhas, key=lambda l: int(l["donation_idx"])), start=1):
            if int(l["donation_idx"]) != esperado:
                sys.exit(f"grupo {gid}: índice {l['donation_idx']} fora de sequência")
            if "donation_item" not in l or "donation_gold" in l or "donation_qina" in l:
                sys.exit(f"grupo {gid} índice {esperado}: só doação de item é suportada ({sorted(l)})")
            item = ids.get(l["donation_item"].lower())
            if item is None or item not in itens_servidor:
                sys.exit(f"grupo {gid} índice {esperado}: item {l['donation_item']} sem template no servidor")
            ET.SubElement(eg, "entry", index=str(esperado), item_id=str(item), count=l["donation_item_cnt"],
                          points=l["donation_contribu"], coins=l["reward_coin_cnt"])
        print(f"   grupo {gid} {nome} ({raca}): {len(linhas)} índices")
    ET.indent(raiz, space="\t")
    texto = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"

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
