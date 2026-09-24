#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_tiamaranta_teleports.py

Teleportes dos Asmodianos para a base em Tiamaranta Mesa (800040000), pela captura oficial de 2026-09-21 (Outros/outros_2026-09-21_05-50-07):

  NPC 730660 (DC1_to_LDF4b_Teleport_01, Pandaemonium): clique abre a página 1011; a ação 10000 leva o jogador a Tiamaranta Mesa. O oficial
      troca de servidor (S 0x132 com o mapa e nova conexão); o S_WORLD do login seguinte põe o jogador em (1483.98, 2759.69, 458.94), h 83,
      no navio da base.
  Objeto 802001 (LDF4b_OP_Teleport_D_01, embaixo da base): uso com barra de 2 s (S 0xC4 com 2000 ms; talk_delay_time 2 no cliente) e
      S_REQUEST_TELEPORT para (1482.95, 2756.25, 458.90), h 83, no mesmo mapa. O S_PUT_NPC dele está em z 262.42; o spawn tinha 278.41,
      16 m acima do chão onde o jogador ficou para usar (z 262.6).

Alterações:
  npcs/npc_templates.xml     730660 ai general -> portal_dialog; 802001 ai aggressive -> portal e talk_info delay="2"
                             (as duas árvores divergem neste arquivo: cada uma recebe só as edições pontuais)
  portals/portal_loc.xml     8000400 (chegada pelo NPC) e 8000401 (chegada pelo objeto)
  portals/portal_template2.xml  portal_dialog 730660 (página 1011, ação 10000) e portal_use 802001
  spawns/Npcs/800040000_Tiamaranta_Mesa.xml  z do 802001

Uso:
    python fix_50_tiamaranta_teleports.py --verificar
    python fix_50_tiamaranta_teleports.py --aplicar
"""

import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_NPCS = "npcs/npc_templates.xml"
REL_LOC = "portals/portal_loc.xml"
REL_PORTALS = "portals/portal_template2.xml"
REL_SPAWN = "spawns/Npcs/800040000_Tiamaranta_Mesa.xml"

LOCS = (
    '\t<!-- Tiamaranta Mesa (captura oficial de 2026-09-21) -->\n'
    '\t<portal_loc world_id="800040000" loc_id="8000400" x="1483.98" y="2759.69" z="458.94" h="83"/> <!-- Base asmodiana (navio), pelo NPC 730660 de Pandaemonium -->\n'
    '\t<portal_loc world_id="800040000" loc_id="8000401" x="1482.95" y="2756.25" z="458.90" h="83"/> <!-- Base asmodiana (navio), pelo objeto 802001 embaixo dela -->\n'
)
PORTAL_USE = (
    '\t<!-- Tiamaranta Mesa: teleporte embaixo da base asmodiana para o navio (captura oficial de 2026-09-21) -->\n'
    '\t<portal_use npc_id="802001">\n'
    '\t\t<portal_path loc_id="8000401" race="ASMODIANS" />\n'
    '\t</portal_use>\n'
)
PORTAL_DIALOG = (
    '\t<!-- Pandaemonium -> Tiamaranta Mesa, base asmodiana (captura oficial de 2026-09-21: página 1011, ação 10000) -->\n'
    '\t<portal_dialog npc_id="730660" teleport_dialog_id="1011">\n'
    '\t\t<portal_path dialog="10000" loc_id="8000400" race="ASMODIANS" />\n'
    '\t</portal_dialog>\n'
)


def edita_npcs(texto):
    def bloco(npc_id, funcao):
        nonlocal texto
        m = re.search(r'\t<npc_template npc_id="' + npc_id + r'".*?</npc_template>', texto, re.S)
        if m is None:
            raise SystemExit(f"npc_template {npc_id} ausente")
        novo = funcao(m.group(0))
        texto = texto[:m.start()] + novo + texto[m.end():]

    def npc_730660(b):
        if 'ai="portal_dialog"' in b:
            return b
        assert b.count('ai="general"') == 1
        return b.replace('ai="general"', 'ai="portal_dialog"', 1)

    def npc_802001(b):
        if 'ai="aggressive"' in b:
            b = b.replace('ai="aggressive"', 'ai="portal"', 1)
        if 'delay="' not in b:
            assert b.count('<talk_info distance="5" can_talk_invisible="false" />') == 1
            b = b.replace('<talk_info distance="5" can_talk_invisible="false" />', '<talk_info distance="5" delay="2" can_talk_invisible="false" />')
        return b

    bloco("730660", npc_730660)
    bloco("802001", npc_802001)
    return texto


def edita_loc(texto):
    if 'loc_id="8000400"' in texto:
        return texto
    assert texto.count("</portal_locs>") == 1
    return texto.replace("</portal_locs>", LOCS + "</portal_locs>")


def edita_portais(texto):
    if 'portal_use npc_id="802001"' not in texto:
        ancora = "\t<!-- ############### PORTAL DIALOG ############### -->\n"
        assert texto.count(ancora) == 1
        texto = texto.replace(ancora, PORTAL_USE + ancora)
    if 'portal_dialog npc_id="730660"' not in texto:
        ancora = "\t<!-- ############### PORTAL DIALOG END ############### -->\n"
        assert texto.count(ancora) == 1
        texto = texto.replace(ancora, PORTAL_DIALOG + ancora)
    return texto


def edita_spawn(texto):
    velho = '<spawn npc_id="802001" respawn_time="295">\n\t\t\t<spot x="1465.9836" y="2724.6763" z="278.40775" h="75"/>'
    novo = '<spawn npc_id="802001" respawn_time="295">\n\t\t\t<spot x="1465.9836" y="2724.6763" z="262.41797" h="75"/>'
    if novo in texto:
        return texto
    assert texto.count(velho) == 1
    return texto.replace(velho, novo)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    gravar = []
    for rel, funcao in ((REL_NPCS, edita_npcs), (REL_LOC, edita_loc), (REL_PORTALS, edita_portais), (REL_SPAWN, edita_spawn)):
        for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
            caminho = os.path.join(base, rel)
            texto = open(caminho, encoding="utf-8", newline="").read()
            crlf = "\r\n" in texto
            novo = funcao(texto.replace("\r\n", "\n"))
            if crlf:
                novo = novo.replace("\n", "\r\n")
            doc = etree.fromstring(novo.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))
            if rel != REL_SPAWN and not schema.validate(doc):
                for e in list(schema.error_log)[:10]:
                    print(f"   {rel} linha {e.line}: {e.message}")
                sys.exit("   XSD INVALIDO")
            muda = novo != texto
            print(f"   {'muda' if muda else 'igual'}: {caminho}")
            if muda:
                gravar.append((rel, caminho, novo))

    if not args.aplicar:
        print("\nModo --verificar: nada foi gravado.")
        return
    print("Gravando (com backup)...")
    for rel in sorted({r for r, _, _ in gravar}):
        backup_manager.backup_file_before_modification(rel)
    for rel, caminho, novo in gravar:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        print(f"   Gravado: {caminho}")


if __name__ == "__main__":
    main()
