#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_legion_settings_50.py

Níveis da Legion do Classic 5.0 (guild/client_guild_setting.xml do cliente) para o legion/legion_settings.xml.

Cada <level level="N"> do cliente traz:
  gold                custo em kinah para chegar ao nível N (o nível 1 é o custo de criação)
  min_member          membros exigidos para subir ao nível N
  exp                 pontos de contribuição exigidos para subir ao nível N (0 em todos na 5.0)
  max_member          limite de membros no nível N
  warehouse           slots do armazém da Legion no nível N
  warehouse_deposit / warehouse_withdraw   limites de kinah do armazém (ainda sem uso no servidor)

Conferência com as capturas oficiais: Legion recém-criada (AinzOO 11/09, Lost Academy 22/09) chega com S_GUILD_INFO nível 1;
a Org Asmo (nível 5, o último da tabela) tem 38 membros, abaixo do max_member 72.

Uso:
    python parse_legion_settings_50.py --verificar
    python parse_legion_settings_50.py --aplicar
A pasta do cliente (a que contém data/) vem de --cliente ou da variável AION_CLIENT_XML_DIR.
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_OUT = "legion/legion_settings.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
CAMPOS = (("gold", "kinah"), ("min_member", "required_members"), ("exp", "required_contribution"), ("max_member", "max_members"),
          ("warehouse", "warehouse_slots"), ("warehouse_deposit", "warehouse_deposit_kinah"), ("warehouse_withdraw", "warehouse_withdraw_kinah"))


def le_cliente(pasta):
    raiz = ET.parse(os.path.join(pasta, "data", "guild", "client_guild_setting.xml")).getroot()
    niveis = []
    for n in raiz.findall("level"):
        linha = {"level": int(n.get("level"))}
        for tag, _ in CAMPOS:
            texto = n.findtext(tag)
            if texto is None:
                sys.exit(f"nível {linha['level']}: falta <{tag}> no client_guild_setting.xml")
            linha[tag] = int(texto)
        niveis.append(linha)
    return sorted(niveis, key=lambda n: n["level"])


def monta(niveis):
    raiz = ET.Element("legion_settings", {"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                          "xsi:noNamespaceSchemaLocation": "legion_settings.xsd"})
    for esperado, n in enumerate(niveis, start=1):
        if n["level"] != esperado:
            sys.exit(f"nível {n['level']} fora de sequência (esperado {esperado})")
        ET.SubElement(raiz, "level", {"level": str(n["level"]), **{attr: str(n[tag]) for tag, attr in CAMPOS}})
    ET.indent(raiz, space="\t")
    return raiz


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    print("1. Lendo o cliente...")
    niveis = le_cliente(args.cliente)
    for n in niveis:
        print("   " + ", ".join(f"{k}={v}" for k, v in n.items()))
    raiz = monta(niveis)
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
