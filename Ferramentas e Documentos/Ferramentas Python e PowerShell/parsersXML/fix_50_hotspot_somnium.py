#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_hotspot_somnium.py

Captura oficial de 2026-10-21 06:50 (06_Sistemas_Novos_5.0, Elyos em Inggison):

Teleporte pelo mapa (hotspot)
  C 0x143 [C 1][D hotspot][Q kinah] -> S 0x1AF [C 1][D jogador][D hotspot]; 3,0 s depois o kinah (300 do cliente, 355 cobrado com a taxa)
  e S 0x1AF [C 3][D jogador][D hotspot][D 15]; o jogador reaparece pelo S_PUT_USER com h = dir/3 (0x71 = 340/3 no hotspot 21).
  A tabela é o gamedata/client_zonemap_hotspot.xml; a do servidor era a da 4.8 (74 pontos com outra numeração, ex.: 15 = Poeta).
  Mapa pelo world/special/WorldId.xml (LDF4_Teva = 800060000); destino sem mapa lá fica de fora.

Somnium (Elyos, Inggison <-> Tiamaranta)
  801994 LF4_Combine_LDF4b_Teleport_01: clique -> página 1011; ação 10000 (HACTION_SETPRO1, "5.000 Kinah") -> S 0x132 para 800040000;
      chegada (S_WORLD) 1567.7424, 318.5808, 436.8534, h 36.
  801995 LDF4b_Combine_LF4_Teleport_01: página 1011; ação 10000 "Teleport to the registered Obelisk" -> bind point (ai portal_bind_point).

Doca de Inggison para Sanctum
  730220 LF4_LC1_TELEPORT: página 10; o botão é HACTION_TELEPORT_SIMPLE (104), não 10000; S_REQUEST_TELEPORT para 1398.0, 1511.0, 572.9943,
      h 0 (o portal_loc 1100103 apontava para o porto, 1739/2063). O 10002 para Oriel (housing) não existe no 5.0.

Uso:
    python fix_50_hotspot_somnium.py --verificar
    python fix_50_hotspot_somnium.py --aplicar
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

CLIENTE = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "data")
REL_HOTSPOT = "hotspot_template.xml"
REL_LOC = "portals/portal_loc.xml"
REL_PORTALS = "portals/portal_template2.xml"
REL_NPCS = "npcs/npc_templates.xml"

RACA = {"light": "ELYOS", "dark": "ASMODIANS", "both": "PC_ALL"}


def mundos():
    out = {}
    for d in ET.parse(os.path.join(CLIENTE, "world", "special", "WorldId.xml")).getroot().iter("data"):
        out[d.text.strip().lower()] = int(d.get("id"))
    return out


def edita_hotspot(_texto):
    ids = mundos()
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<hotspot_template xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="hotspot_template.xsd">',
              "\t<!-- gerado por fix_50_hotspot_somnium.py a partir do client_zonemap_hotspot.xml (5.0) -->"]
    fora = []
    for e in ET.parse(os.path.join(CLIENTE, "gamedata", "client_zonemap_hotspot.xml")).getroot():
        d = {c.tag: (c.text or "").strip() for c in e}
        mapa = ids.get(d["world"].lower())
        if mapa is None:
            fora.append(f'{d["id"]} ({d["world"]})')
            continue
        attrs = (f'id="{d["id"]}" worldId="{mapa}" x="{float(d["x"]):g}" y="{float(d["y"]):g}" z="{float(d["z"]):g}" '
                 f'h="{round(int(d.get("dir") or 0) / 3) % 120}" race="{RACA[d["race"].lower()]}" price="{int(d.get("required_base_gold") or 0)}"')
        if float(d.get("required_distance_gold") or 0):
            attrs += f' distance_price="{float(d["required_distance_gold"]):g}"'
        if int(d.get("required_level") or 0):
            attrs += f' min_level="{int(d["required_level"])}"'
        linhas.append(f"\t<!-- {d['name']} -->")
        linhas.append(f"\t<hotspot_location {attrs}/>")
    linhas.append("</hotspot_template>")
    if fora:
        print(f"   hotspot sem mapa no WorldId.xml, fora: {', '.join(fora)}")
    return "\n".join(linhas) + "\n"


def edita_loc(texto):
    velho = '<portal_loc world_id="110010000" loc_id="1100103" x="1739.5557" y="2063.362" z="517.9073" h="68"/> <!-- Aerolink Exit -->'
    novo = ('<portal_loc world_id="110010000" loc_id="1100103" x="1398.0" y="1511.0" z="572.9943" h="0"/> '
            '<!-- Doca de Inggison -> Sanctum (730220, ação 104), captura oficial de 2026-10-21 -->')
    if velho in texto:
        texto = texto.replace(velho, novo)
    assert novo in texto
    if 'loc_id="8000402"' not in texto:
        ancora = '\t<portal_loc world_id="800040000" loc_id="8000401"'
        assert texto.count(ancora) == 1
        i = texto.index("\n", texto.index(ancora)) + 1
        texto = (texto[:i] + '\t<portal_loc world_id="800040000" loc_id="8000402" x="1567.7424" y="318.5808" z="436.8534" h="36"/> '
                 '<!-- Somnium (801994 de Inggison), captura oficial de 2026-10-21 -->\n' + texto[i:])
    return texto


def edita_portais(texto):
    velho = ('\t<portal_dialog npc_id="730220">\n'
             '\t\t<portal_path dialog="10000" loc_id="1100103" race="ELYOS" min_level="10" kinah="9300" />\n'
             '\t\t<portal_path dialog="10002" loc_id="7000100" race="ELYOS" min_level="10" kinah="9800" />\n'
             '\t</portal_dialog>\n')
    novo = ('\t<portal_dialog npc_id="730220" teleport_dialog_id="10">\n'
            '\t\t<portal_path dialog="104" loc_id="1100103" race="ELYOS" min_level="10" kinah="9300" />\n'
            '\t</portal_dialog>\n')
    if velho in texto:
        texto = texto.replace(velho, novo)
    assert novo in texto
    if 'portal_dialog npc_id="801994"' not in texto:
        ancora = "\t<!-- ############### PORTAL DIALOG END ############### -->\n"
        assert texto.count(ancora) == 1
        texto = texto.replace(ancora, (
            '\t<!-- Inggison -> Tiamaranta Mesa pelo Somnium (captura oficial de 2026-10-21: página 1011, ação 10000, 5.000 kinah) -->\n'
            '\t<portal_dialog npc_id="801994" teleport_dialog_id="1011">\n'
            '\t\t<portal_path dialog="10000" loc_id="8000402" race="ELYOS" kinah="5000" />\n'
            '\t</portal_dialog>\n') + ancora)
    return texto


def edita_npcs(texto):
    for npc, ai in (("801994", "portal_dialog"), ("801995", "portal_bind_point")):
        m = re.search(r'\t<npc_template npc_id="' + npc + r'"[^>]*>', texto)
        if m is None:
            raise SystemExit(f"npc_template {npc} ausente")
        cab = m.group(0)
        novo = re.sub(r'ai="[^"]*"', f'ai="{ai}"', cab, count=1)
        texto = texto[:m.start()] + novo + texto[m.end():]
    return texto


def edita_spawn(velho, novo):
    def f(texto):
        if velho in texto:
            texto = texto.replace(velho, novo)
        assert novo in texto, novo
        return texto
    return f


# h do S_PUT_NPC oficial (p[27]) na captura de 2026-10-21
SPAWNS = (
    ("spawns/Npcs/210050000_Inggison.xml",
     '<spot x="1356" y="358.1" z="589.5781" h="101" />', '<spot x="1356" y="358.1" z="589.5781" h="86" />'),
    ("spawns/Npcs/800040000_Tiamaranta_Mesa.xml",
     '<spot x="1571.9696" y="290.25781" z="433.488" h="39"/>', '<spot x="1571.9696" y="290.25781" z="433.488" h="36"/>'),
)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    gravar = []
    edicoes = [(REL_HOTSPOT, edita_hotspot), (REL_LOC, edita_loc), (REL_PORTALS, edita_portais), (REL_NPCS, edita_npcs)]
    edicoes += [(rel, edita_spawn(a, b)) for rel, a, b in SPAWNS]
    for rel, funcao in edicoes:
        for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
            caminho = os.path.join(base, rel)
            texto = open(caminho, encoding="utf-8", newline="").read()
            crlf = "\r\n" in texto
            novo = funcao(texto.replace("\r\n", "\n"))
            if crlf:
                novo = novo.replace("\n", "\r\n")
            doc = etree.fromstring(novo.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))
            if not schema.validate(doc):
                for e in list(schema.error_log)[:10]:
                    print(f"   {rel} linha {e.line}: {e.message}")
                sys.exit("   XSD INVALIDO")
            if novo != texto:
                gravar.append((rel, caminho, novo))
    for _rel, caminho, _n in gravar:
        print("   muda: " + os.path.relpath(caminho, backup_manager.PROJECT_ROOT))
    if args.aplicar:
        for rel, caminho, novo in gravar:
            backup_manager.backup_file_before_modification(rel)
            open(caminho, "w", encoding="utf-8", newline="").write(novo)
        print("   gravado")


if __name__ == "__main__":
    main()
