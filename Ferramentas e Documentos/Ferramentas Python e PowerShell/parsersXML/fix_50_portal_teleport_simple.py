#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_portal_teleport_simple.py

Portais por diálogo cujo único botão no cliente é HACTION_TELEPORT_SIMPLE (104).

O cliente manda a ação do botão (C_DIALOG_SELECT); o PortalDialogAI só leva o jogador se existir um <portal_path> com aquele dialog.
Nos portais abaixo o servidor tinha o path em 10000 (ou 10000 + 10002), que o diálogo do cliente nunca manda: o clique não fazia nada.
Captura oficial de 2026-10-21 (doca 730220, Inggison -> Sanctum): ação 104 e S_REQUEST_TELEPORT logo depois.

Regra: portal_dialog cujo HTML do cliente (dialogs/**/<nome interno>.html, decifrado com aion_dialogo_quest) só tem TELEPORT_SIMPLE
como ação e cujos paths não usam nenhuma ação do cliente -> o primeiro path passa a dialog="104" e os outros saem (não há botão para eles).
Destino, kinah, nível e quest_req ficam como estão.

Uso:
    python fix_50_portal_teleport_simple.py --verificar
    python fix_50_portal_teleport_simple.py --aplicar
"""

import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

sys.path.insert(0, backup_manager.TOOLS_DIR)
import aion_dialogo_quest as Q  # noqa: E402

COLETAS = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas")
DIALOGOS = os.path.join(COLETAS, "Tradução - Português Brasil", "dialogs")
CLIENT_NPCS = os.path.join(COLETAS, "Client 5.0 - Dados Extraidos", "data", "europe", "Npcs", "client_npcs.xml")
DIALOG_ACTION = os.path.join(backup_manager.PROJECT_ROOT, "Código Fonte - Emulador", "game-server", "src", "com", "aionemu", "gameserver",
                             "model", "DialogAction.java")
REL = "portals/portal_template2.xml"
TELEPORT_SIMPLE = 104


def acoes_do_cliente():
    acoes = {m.group(1): int(m.group(2))
             for m in re.finditer(r"public static final int (\w+) = (\d+);", open(DIALOG_ACTION, encoding="utf-8").read())}
    nomes = {}
    for _ev, el in ET.iterparse(CLIENT_NPCS):
        if el.find("id") is not None and el.find("name") is not None:
            nomes[int(el.findtext("id"))] = el.findtext("name").lower()
            el.clear()
    arquivos = {os.path.basename(f).lower()[:-5]: f for f in glob.glob(os.path.join(DIALOGOS, "**", "*.html"), recursive=True)}
    maiores = sorted(arquivos.values(), key=os.path.getsize, reverse=True)[:40]
    modelo = Q.Modelo([open(f, "rb").read()[1:] for f in maiores])
    cache = {}

    def do_npc(npc):
        nome = nomes.get(npc)
        if nome not in arquivos:
            return None
        if nome not in cache:
            texto = Q.decifra(open(arquivos[nome], "rb").read(), modelo)
            cache[nome] = {acoes[a] for a in re.findall(r'href="HACTION_(\w+)"', texto) if a in acoes and a != "FINISH_DIALOG"}
        return cache[nome]
    return do_npc, nomes


def edita(texto, do_npc, nomes, relatorio):
    def bloco(m):
        npc = int(m.group(1))
        cli = do_npc(npc)
        paths = re.findall(r'\t\t<portal_path dialog="(\d+)".*?(?:/>|</portal_path>)\n', m.group(0), re.S)
        if cli != {TELEPORT_SIMPLE} or not paths or {int(d) for d in paths} & cli:
            return m.group(0)
        corpo = list(re.finditer(r'\t\t<portal_path dialog="(\d+)".*?(?:/>|</portal_path>)\n', m.group(0), re.S))
        primeiro = corpo[0].group(0).replace(f'dialog="{corpo[0].group(1)}"', f'dialog="{TELEPORT_SIMPLE}"', 1)
        removidos = [c.group(1) for c in corpo[1:]]
        relatorio.append(f"{npc} {nomes.get(npc)}: dialog {corpo[0].group(1)} -> 104" + (f", sai {removidos} (sem botão no cliente)" if removidos else ""))
        novo = m.group(0)[:corpo[0].start()] + primeiro + m.group(0)[corpo[-1].end():]
        return novo
    return re.sub(r'\t<portal_dialog npc_id="(\d+)"[^>]*>\n.*?\t</portal_dialog>\n', bloco, texto, flags=re.S)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    do_npc, nomes = acoes_do_cliente()
    gravar = []
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        caminho = os.path.join(base, REL)
        texto = open(caminho, encoding="utf-8", newline="").read()
        crlf = "\r\n" in texto
        relatorio = []
        novo = edita(texto.replace("\r\n", "\n"), do_npc, nomes, relatorio)
        if crlf:
            novo = novo.replace("\n", "\r\n")
        if not schema.validate(etree.fromstring(novo.encode("utf-8"))):
            for e in list(schema.error_log)[:10]:
                print(f"   linha {e.line}: {e.message}")
            sys.exit("   XSD INVALIDO")
        print(f"== {os.path.relpath(caminho, backup_manager.PROJECT_ROOT)}")
        for linha in relatorio:
            print("   " + linha)
        if novo != texto:
            gravar.append((caminho, novo))
    if args.aplicar and gravar:
        backup_manager.backup_file_before_modification(REL)
        for caminho, novo in gravar:
            open(caminho, "w", encoding="utf-8", newline="").write(novo)
        print("   gravado")


if __name__ == "__main__":
    main()
