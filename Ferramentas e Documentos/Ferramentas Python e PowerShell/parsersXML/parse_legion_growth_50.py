#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_legion_growth_50.py

Nível de crescimento da Legion do Classic 5.0 (PC/client_guild_growth.xml) para o legion/legion_growth.xml.

Cada <guild_level Guild_level="N">: guild_exp = exp para chegar ao nível N (o contador zera a cada nível) e a essência e os fragmentos
ganhos ao chegar nele. Conferência com o S_GUILD_INFO: Lost Academy nova no nível 1 com 0 de exp e 3000 depois da primeira recompensa de
missão (S 0x164, 22/09); Org Asmo no nível 44 com 88500 (o 45 pede 140000).

Uso:
    python parse_legion_growth_50.py --verificar
    python parse_legion_growth_50.py --aplicar
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_OUT = "legion/legion_growth.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    niveis = ET.parse(os.path.join(args.cliente, "data", "PC", "client_guild_growth.xml")).getroot()
    raiz = ET.Element("legion_growth", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                        "xsi:noNamespaceSchemaLocation": "legion_growth.xsd"})
    for esperado, n in enumerate(sorted(niveis, key=lambda n: int(n.get("Guild_level"))), start=1):
        if int(n.get("Guild_level")) != esperado:
            sys.exit(f"nível {n.get('Guild_level')} fora de sequência")
        ET.SubElement(raiz, "level", level=str(esperado), exp=n.findtext("guild_exp"), essence=n.findtext("essence_reward_num") or "0",
                      essence_piece=n.findtext("essence_piece_reward_num") or "0")
    print(f"níveis: {len(raiz)}")
    ET.indent(raiz, space="\t")
    texto = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    if not schema.validate(etree.fromstring(texto.encode("utf-8"))):
        for e in list(schema.error_log)[:20]:
            print(f"   linha {e.line}: {e.message}")
        sys.exit("XSD INVALIDO")
    print("valido")
    if not args.aplicar:
        print("Modo --verificar: nada foi gravado.")
        return
    for base_dir in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        caminho = os.path.join(base_dir, REL_OUT)
        if os.path.exists(caminho):
            backup_manager.backup_file_before_modification(REL_OUT)
        with open(caminho, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print(f"Gravado: {caminho}")


if __name__ == "__main__":
    main()
