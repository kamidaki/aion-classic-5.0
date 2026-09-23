#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_land_of_shadows_spawns.py

Refaz o spawn fixo da Land of Shadows (IDTutorialQ, 390000000) pela captura oficial subida-1-60-2026-08-28.pcapng,
em que um Asmodiano faz a instancia inteira (S_WORLD 390000000 ate a saida pela Inggril, 1.451 s).

O que estava errado
  - dois arquivos para o mesmo mapa (spawns/Instances e spawns/Npcs), os dois carregados: quase tudo nascia 2x;
  - os dois lados de raca juntos: gossip Elyos 804114..804122 no mesmo ponto do Asmodiano 804124..804132 e a Inggness
    (804134) em cima da Inggril (804135). No oficial so existe o lado de quem entra (o handler troca na entrada);
  - nenhum mob: os 2243xx da captura nao existiam nos arquivos (nem no npc_info do cliente, que nao traz monstro);
  - NPC de roteiro como spawn fixo (804124/804125/804135 nascem aos 62 s, bosses, baus, 804143/804144/804155...).

Regras
  spawn fixo = objeto cujo primeiro S_PUT_NPC na sessao tem o flag de nascimento (p[-32]) em 0; x/y/z/h desse put
               (nenhum desses objetos tinha se movido antes: 0 de 201). Os de flag 1 sao do roteiro e ficam no handler.
  fora da captura = ponto do spawns/Npcs (npc_info do cliente) a mais de ALCANCE m de todo ponto por onde o jogador
               passou e cujo npcId e de lado neutro ou Asmodiano (o handler faz o Elyos). A captura nao ve nada ali.
  respawn     mob (2243xx) 0: nenhum dos 37 mortos renasceu na sessao; 224328 (deco) 15 s: morreu em 1.012,7 s e
              renasceu no mesmo ponto em 1.028,1 s. O resto 295, o padrao dos spawns de instancia.

Grava spawns/Instances/390000000_Land_of_Shadows.xml nas duas arvores e apaga spawns/Npcs/390000000_Land_of_Shadows.xml
(com backup).

Uso:
    python rebuild_50_land_of_shadows_spawns.py              (mostra e valida)
    python rebuild_50_land_of_shadows_spawns.py --aplicar    (grava, com backup)
A pasta das capturas pode vir de AION_CAPTURAS_DIR.
"""

import argparse
import collections
import glob
import math
import os
import re
import struct
import sys

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.dirname(AQUI))
import aion_pcap  # noqa: E402
import backup_manager  # noqa: E402

ARVORES = (("fonte", backup_manager.SERVER_DATA_DIR), ("produto", backup_manager.PRODUTO_FINAL_DATA_DIR))
CAPTURAS = os.environ.get("AION_CAPTURAS_DIR") or os.path.join(
    backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0")
CAPTURA = "subida-1-60-2026-08-28.pcapng"
MAPA = 390000000
REL_INST = os.path.join("spawns", "Instances", "390000000_Land_of_Shadows.xml")
REL_NPCS = os.path.join("spawns", "Npcs", "390000000_Land_of_Shadows.xml")
REL_XSD = os.path.join("spawns", "spawns.xsd")
OP_WORLD, OP_PUT, OP_MOVE_CLIENTE = 0x0F, 0x0E, 0x30
ALCANCE = 50.0
ELYOS = set(range(804114, 804124)) | {804134}
RESPAWN = {224328: 15}


def sessao_instancia():
    caminho = glob.glob(os.path.join(glob.escape(CAPTURAS), "**", CAPTURA), recursive=True)
    if not caminho:
        sys.exit("captura nao encontrada: " + CAPTURA)
    for r in aion_pcap.abre_todas(caminho[0], sem_skey=True):
        lin = aion_pcap.intercalado(r)
        mundos = [i for i, (t, lado, op, p) in enumerate(lin) if lado == "servidor" and op == OP_WORLD]
        for k, i in enumerate(mundos):
            p = lin[i][3]
            if struct.unpack_from("<I", p, 4)[0] == MAPA:  # em instancia o mapa vem no offset 4
                fim = mundos[k + 1] if k + 1 < len(mundos) else len(lin)
                return lin[i:fim]
    sys.exit("a captura nao tem sessao no mapa %d" % MAPA)


def le_captura():
    seg = sessao_instancia()
    objs, trilha = {}, []
    for t, lado, op, p in seg:
        if lado == "servidor" and op == OP_PUT:
            oid = struct.unpack_from("<I", p, 12)[0]
            if oid not in objs:
                x, y, z = struct.unpack_from("<fff", p, 0)
                objs[oid] = (struct.unpack_from("<I", p, 16)[0], x, y, z, p[27], p[-32])
        elif lado == "cliente" and op == OP_MOVE_CLIENTE and len(p) >= 12:
            trilha.append(struct.unpack_from("<ff", p, 0))
    return objs, trilha


def spots_do_arquivo(caminho):
    out = collections.defaultdict(list)
    if not os.path.isfile(caminho):
        return out
    atual = None
    for linha in open(caminho, encoding="utf-8"):
        m = re.search(r'npc_id="(\d+)"', linha)
        if m:
            atual = int(m.group(1))
        m = re.search(r'<spot x="([^"]+)" y="([^"]+)" z="([^"]+)"(?: h="(\d+)")?', linha)
        if m and atual:
            out[atual].append(tuple(float(v) for v in m.groups()[:3]) + (int(m.group(4) or 0),))
    return out


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def monta(fixos, nl):
    linhas = ["<?xml version='1.0' encoding='utf-8'?>",
              '<spawns xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../spawns.xsd">',
              '\t<spawn_map map_id="%d">' % MAPA]
    for npc in sorted(fixos):
        rt = RESPAWN.get(npc, 0 if 224300 <= npc <= 224335 else 295)
        linhas.append('\t\t<spawn npc_id="%d" respawn_time="%d">' % (npc, rt))
        for x, y, z, h in sorted(fixos[npc]):
            linhas.append('\t\t\t<spot x="%s" y="%s" z="%s" h="%d" />' % (fmt(x), fmt(y), fmt(z), h))
        linhas.append("\t\t</spawn>")
    linhas += ["\t</spawn_map>", "</spawns>", ""]
    return nl.join(linhas)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    objs, trilha = le_captura()
    fixos = collections.defaultdict(list)
    for npc, x, y, z, h, nasce in objs.values():
        if not nasce:
            fixos[npc].append((x, y, z, h))
    print("captura: %d objetos, %d fixos em %d npcIds, %d de roteiro, %d pontos de trilha do jogador" % (
        len(objs), sum(map(len, fixos.values())), len(fixos), sum(1 for o in objs.values() if o[5]), len(trilha)))

    ok, gravar, apagar = True, [], []
    for nome, base in ARVORES:
        npc_info = spots_do_arquivo(os.path.join(base, REL_NPCS))
        extra = collections.defaultdict(list)
        for npc, spots in npc_info.items():
            if npc in ELYOS:
                continue
            for s in spots:
                if min(math.hypot(s[0] - a, s[1] - b) for a, b in trilha) > ALCANCE:
                    extra[npc].append(s)
        todos = collections.defaultdict(list, {k: list(v) for k, v in fixos.items()})
        for npc, spots in extra.items():
            todos[npc] += spots
        cam = os.path.join(base, REL_INST)
        antigo = open(cam, encoding="utf-8", newline="").read() if os.path.isfile(cam) else ""
        nl = "\r\n" if "\r\n" in antigo else "\n"
        novo = monta(todos, nl)
        antes = sum(map(len, spots_do_arquivo(cam).values())) + sum(map(len, npc_info.values()))
        print("[%s] antes: %d spots (Instances + Npcs) | depois: %d (%d da captura, %d do npc_info fora do alcance dela: %s)"
              % (nome, antes, sum(map(len, todos.values())), sum(map(len, fixos.values())), sum(map(len, extra.values())),
                 ", ".join("%d x%d" % (k, len(v)) for k, v in sorted(extra.items()))))
        xsd = etree.XMLSchema(etree.parse(os.path.join(base, REL_XSD)))
        if not xsd.validate(etree.fromstring(novo.encode("utf-8"))):
            print("   XSD: %s" % xsd.error_log.last_error)
            ok = False
        gravar.append((cam, novo))
        if os.path.isfile(os.path.join(base, REL_NPCS)):
            apagar.append(os.path.join(base, REL_NPCS))

    if not ok:
        sys.exit("Erro de validacao: nada foi gravado.")
    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    for caminho, novo in gravar:
        backup_manager.backup_file_before_modification(caminho)
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        print("Gravado: " + caminho)
    for caminho in apagar:
        backup_manager.backup_file_before_modification(caminho)
        os.remove(caminho)
        print("Apagado: " + caminho)


if __name__ == "__main__":
    main()
