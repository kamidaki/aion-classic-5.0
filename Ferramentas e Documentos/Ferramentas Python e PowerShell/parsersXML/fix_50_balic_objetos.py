#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_balic_objetos.py

Objetos do Balic Treasury (800070000) pela captura oficial "06_Sistemas_Novos_5.0/Balic Treasury.pcapng" (29/10), lado asmodiano:

  802792 TDown_FOBJ_Teleporter_D ("Asmodian Entrance Teleporter", embaixo da entrada): C 0xFFFC -> S 0xC4 3000 ms [1] ->
         S 0xC4 [2] -> S_REQUEST_TELEPORT (800070000, 756.6952, 1344.8342, 1201.5183, h 30), na plataforma. talk_delay_time 3 e
         talking_distance 7 no cliente. Estava com ai flag (não faz nada).
  802953 TDown_to_LDF4b_Center_Local_D ("Tiamaranta Garrison Entrance"): S 0xC4 5000 ms -> S_REQUEST_TELEPORT para
         (800040000, 1526.5, 1789.5, 249.2256, h 30). talk_delay_time 5, talking_distance 10. O 1º uso da captura foi cancelado
         (S 0xC4 [2] com 0 ms). Estava com ai flag.
  801964/801965/801966 TDown_TreasureBox_SuscessA/B/C: S 0xC4 10000 ms e, sem a chave, S_MESSAGE 1111300 (STR_COMMON_SAY_01,
         "precisa de uma chave para abrir a caixa"), sem loot. A chave de cada uma é a do mesmo nome no cliente:
         상자 (Treasure Chest) = key_tiamatdown_r_01 185000141, 궤짝 (Crate) = key_tiamatdown_l_01 185000142,
         황금함 (Golden) = key_tiamatdown_u_01 185000143. Estavam com ai general. O loot não está na captura (a caixa não abriu).
  802959 Tdown_Black_Drana_Tin ("Blood Drana Products", ui craft_ui_always): coleta com barra própria, não é o uso com S 0xC4.
         C 0x131 [D obj] -> S 0x195 [D estado][D progresso][D 700][D 1200] a cada ~2 s (estado 0 = começa, 1 = andando,
         3 = sucesso em 10000) -> 2 x 186020383 (Blood Drana Products) -> S_REMOVE_OBJECT [obj][1] e o objeto renasce depois.
         Recebe a ai tdown_drana_tin (TDownDranaTinAI) e os spawns da captura: não tinha nenhum no arquivo.
  802966 Tdown_Pile_Of_Black_Drana_Tins_Step1 (pilha decorativa, NoAction): spawns da captura, também ausentes.

Também tira os portal_dialog 801965/801966 da 4.x (Sauro Supply Base, mapa que não existe na 5.0), que colidem com os ids
das caixas.

O respawn_time dos spawns novos segue o do arquivo (295): a captura só mostra que o 802959 coletado em 240 s estava de volta
antes de 1219 s.

Uso:
    python fix_50_balic_objetos.py --verificar
    python fix_50_balic_objetos.py --aplicar
"""

import argparse
import collections
import math
import os
import pickle
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

RAIZ = os.path.abspath(os.path.join(PARSERS_DIR, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "Ferramentas e Documentos", "Ferramentas Python e PowerShell", "Ferramentas Python"))
CAPTURA = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Wireshark - Oficial Classic 5.0", "06_Sistemas_Novos_5.0",
                       "Balic Treasury.pcapng")

REL_NPCS = "npcs/npc_templates.xml"
REL_LOC = "portals/portal_loc.xml"
REL_PORTALS = "portals/portal_template2.xml"
REL_CHESTS = "chests/chest_templates.xml"
REL_SPAWN = "spawns/Npcs/800070000_Balic_Treasury.xml"
MAPA = 800070000
NOVOS_SPAWNS = (802959, 802966, 221330, 221331)  # 221330/221331: só os parados (11 e 6); os que andam pedem rota

LOCS = (
    '\t<!-- Balic Treasury (captura oficial de 2026-10-29) -->\n'
    '\t<portal_loc world_id="800070000" loc_id="8000700" x="756.6952" y="1344.8342" z="1201.5183" h="30"/> <!-- Plataforma asmodiana, pelo 802792 -->\n'
    '\t<portal_loc world_id="800040000" loc_id="8000701" x="1526.5" y="1789.5" z="249.2256" h="30"/> <!-- Tiamaranta Mesa, pelo 802953 do Balic Treasury -->\n'
)
PORTAL_USE = (
    '\t<!-- Balic Treasury: teleporte da entrada asmodiana para a plataforma e saída para Tiamaranta Mesa (captura oficial de 2026-10-29) -->\n'
    '\t<portal_use npc_id="802792">\n'
    '\t\t<portal_path loc_id="8000700" race="ASMODIANS" />\n'
    '\t</portal_use>\n'
    '\t<portal_use npc_id="802953">\n'
    '\t\t<portal_path loc_id="8000701" race="ASMODIANS" />\n'
    '\t</portal_use>\n'
)
SAURO = (
    '\t<portal_dialog npc_id="801965">\n'
    '\t\t<portal_path dialog="10000" loc_id="3011300" race="ELYOS" />\n'
    '\t</portal_dialog>\n'
    '\t<portal_dialog npc_id="801966">\n'
    '\t\t<portal_path dialog="10000" loc_id="3011300" race="ASMODIANS" />\n'
    '\t</portal_dialog>\n'
)
CHESTS = (
    '\t<!-- Balic Treasury: caixas do Protetorado, cada uma com a chave do mesmo nome no cliente (captura 29/10: sem chave, msg 1111300) -->\n'
    '\t<chest npc_id="801964">\n\t\t<key_item item_ids="185000141" count="1" />\n\t</chest>\n'
    '\t<chest npc_id="801965">\n\t\t<key_item item_ids="185000142" count="1" />\n\t</chest>\n'
    '\t<chest npc_id="801966">\n\t\t<key_item item_ids="185000143" count="1" />\n\t</chest>\n'
)


def edita_npcs(texto):
    def bloco(npc_id, funcao):
        nonlocal texto
        m = re.search(r'\t<npc_template npc_id="' + str(npc_id) + r'".*?</npc_template>', texto, re.S)
        if m is None:
            raise SystemExit(f"npc_template {npc_id} ausente")
        texto = texto[:m.start()] + funcao(m.group(0)) + texto[m.end():]

    def ai(b, nova):
        a = re.search(r'\bai="([^"]*)"', b)
        return b.replace(a.group(0), f'ai="{nova}"', 1)

    def talk(b, dist, delay):
        novo = f'<talk_info distance="{dist}" delay="{delay}" can_talk_invisible="false" />'
        m = re.search(r"<talk_info\b[^>]*/>", b)
        if m:
            return b.replace(m.group(0), novo, 1)
        br = re.search(r"(\n\t*)(<bound_radius\b[^>]*/>)", b)
        return b.replace(br.group(0), br.group(0) + br.group(1) + novo, 1)

    bloco(802792, lambda b: talk(ai(b, "portal"), 7, 3))
    bloco(802953, lambda b: talk(ai(b, "portal"), 10, 5))
    for n in (801964, 801965, 801966):
        bloco(n, lambda b: talk(ai(b, "chest"), 3, 10))
    bloco(802959, lambda b: talk(ai(b, "tdown_drana_tin"), 3, 5))
    return texto


def edita_loc(texto):
    if 'loc_id="8000700"' in texto:
        return texto
    assert texto.count("</portal_locs>") == 1
    return texto.replace("</portal_locs>", LOCS + "</portal_locs>")


def edita_portais(texto):
    if SAURO in texto:
        texto = texto.replace(SAURO, "")
    if 'portal_use npc_id="802792"' not in texto:
        ancora = "\t<!-- ############### PORTAL DIALOG ############### -->\n"
        assert texto.count(ancora) == 1
        texto = texto.replace(ancora, PORTAL_USE + ancora)
    return texto


def edita_chests(texto):
    if 'chest npc_id="801964"' in texto:
        return texto
    return texto.replace("</chest_templates>", CHESTS + "</chest_templates>")


def oficiais():
    """npc -> [(x, y, z, h)] dos 802959/802966 no 800070000 (uma posição por objeto; o objeto não anda)."""
    import aion_pcap
    pos, mapa = {}, None
    for s in aion_pcap.abre_todas(CAPTURA, sem_skey=True):
        for op, p, ok in s["servidor"]:
            if not ok:
                continue
            if op == 0x0F:
                mapa = struct.unpack_from("<I", p, 0)[0]
            elif op == 0x14:
                mapa = struct.unpack_from("<I", p, 1)[0]
            elif op == 0x0E and mapa == MAPA and len(p) >= 28:
                n = struct.unpack_from("<I", p, 16)[0]
                if n in NOVOS_SPAWNS:
                    x, y, z = struct.unpack_from("<fff", p, 0)
                    pos.setdefault(struct.unpack_from("<I", p, 12)[0], []).append((n, x, y, z, p[27]))
    por = collections.defaultdict(list)
    for vistas in pos.values():
        n, x, y, z, h = vistas[0]
        if any(math.hypot(x - v[1], y - v[2]) > 0.3 or v[4] != h for v in vistas):
            continue  # visto em outro lugar: anda (rota/andar aleatório), fica de fora
        # o mesmo ponto com objeto novo depois do respawn conta uma vez
        if all(math.hypot(x - a, y - b) > 0.5 for a, b, _, _ in por[n]):
            por[n].append((x, y, z, h))
    return {n: sorted(v) for n, v in por.items()}


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def edita_spawn(texto, pos):
    for n in NOVOS_SPAWNS:
        if f'<spawn npc_id="{n}"' in texto:
            continue
        spots = "".join(f'\n\t\t\t<spot x="{fmt(x)}" y="{fmt(y)}" z="{fmt(z)}" h="{h}" />' for x, y, z, h in pos[n])
        bloco = f'\t\t<!-- {n}: posições do S_PUT_NPC da captura oficial de 2026-10-29 (fix_50_balic_objetos.py) -->\n' \
                f'\t\t<spawn npc_id="{n}" respawn_time="295">{spots}\n\t\t</spawn>\n\n'
        i = texto.rindex("\n", 0, texto.rindex("</spawn_map>")) + 1
        texto = texto[:i] + bloco + texto[i:]
    return texto


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    pos = oficiais()
    print("spawns da captura:", {n: len(v) for n, v in pos.items()})
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    gravar = []
    for rel, funcao in ((REL_NPCS, edita_npcs), (REL_LOC, edita_loc), (REL_PORTALS, edita_portais), (REL_CHESTS, edita_chests),
                        (REL_SPAWN, lambda t: edita_spawn(t, pos))):
        for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
            caminho = os.path.join(base, rel)
            texto = open(caminho, encoding="utf-8", newline="").read()
            crlf = "\r\n" in texto
            novo = funcao(texto.replace("\r\n", "\n"))
            if crlf:
                novo = novo.replace("\n", "\r\n")
            doc = etree.fromstring(novo.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))
            xsd = schema if rel != REL_SPAWN else etree.XMLSchema(etree.parse(os.path.join(base, "spawns", "spawns.xsd")))
            if not xsd.validate(doc):
                for e in list(xsd.error_log)[:10]:
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
