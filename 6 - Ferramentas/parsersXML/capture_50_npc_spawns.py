#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
capture_50_npc_spawns.py

Aplica capturas de pacotes do servidor oficial 5.0 aos spawns de NPC: posicao, altura e direcao exatas. E a
fonte de maior prioridade -- acima do cliente (rebuild_50_npc_spawns, import_50_npc_spawns) e da 4.8 -- e os tres
convivem: depois deste, rodar os outros dois nao muda nada.

O que a primeira captura (Poeta, 2026-09-12, 20 min, 2222 S_PUT_NPC) mediu e que fundamenta as regras:
  * Alinhamento: x/y/z em 0/4/8, objectId em 12, npcId em 16, heading em 27. O l10n em 28 bate com o name_id do
    template em 2222 de 2222 pacotes. O fim do pacote NAO segue o layout do emulador (flag de spawn e alvo de
    movimento saem lixo), por isso nada depois do masterName e usado.
  * S_PUT_NPC manda onde o NPC esta quando entra na visao, nao o ponto de spawn. So entra NPC parado: sem nenhum
    S_MOVE_NEW na sessao e sempre no mesmo lugar -- 834 dos 1077 objetos de Poeta se moveram e ficam de fora.
    creatorId/masterName diferente de zero e invocacao de jogador e tambem fica de fora.
  * O x,y oficial e EXATAMENTE o do npc_info do cliente (140 de 140 a 0,0 m); o z oficial fica no terreno
    (mediana +0,00 m) e o do cliente 2,42 m acima. Por isso o corretor ve o spot aplicado daqui como "mesmo
    lugar" e nao briga com ele.
  * Direcao e o que mais muda: dos 192 NPCs de Poeta ja no lugar certo, so 116 tinham o h oficial.

Regras, as mesmas dos outros dois parsers onde o problema e o mesmo:
  par ate R_LOCAL (um-para-um por npc, menor distancia horizontal)  -> x, y, z e h oficiais
  par acima de R_LOCAL                                               -> so npc com 1 spot de cada lado e sem
                                                                        static_id/walker_id; o resto e pendente
  ponto oficial sem par                                              -> spot novo no <spawn> do npc, ou <spawn>
                                                                        novo se o mapa nao tem o npc
A captura cobre so a area por onde se andou: spot do servidor que ela nao viu fica como esta.

Fora do escopo, por decisao do usuario: os mapas em FORA.

Uso:
    python capture_50_npc_spawns.py <captura.pcapng> [<outra.pcapng> ...]            (mostra e gera relatorio)
    python capture_50_npc_spawns.py <captura.pcapng> [<outra.pcapng> ...] --aplicar  (grava com backup)
"""

import argparse
import collections
import math
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
sys.path.insert(0, os.path.dirname(PARSERS_DIR))  # 6 - Ferramentas, onde fica o aion_pcap
import aion_pcap  # noqa: E402
import backup_manager  # noqa: E402
import import_50_npc_spawns as imp  # noqa: E402
from rebuild_50_npc_spawns import FORA, R_LOCAL, caminho_existente, le_servidor, num  # noqa: E402

RELATORIO = os.path.join(PARSERS_DIR, "relatorio_captura_spawns_50.txt")
OP_PUT_NPC, OP_WORLD, OP_MOVE = 0x0E, 0x0F, 0x37  # S_PUT_NPC, S_WORLD, S_MOVE_NEW (decodificados)
PARADO = 0.5


# ---------------------------------------------------------------- captura
def le_capturas(caminhos):
    """map_id -> {(npc, x, y): (npc, x, y, z, h)} dos NPCs parados, e as contagens do que ficou de fora."""
    pontos, cont = collections.defaultdict(dict), collections.Counter()
    for caminho in caminhos:
        for sessao in aion_pcap.abre_todas(caminho):
            cont["sessoes"] += 1
            mapa, movers, vistos = None, set(), collections.defaultdict(list)
            for _t, lado, op, p in aion_pcap.intercalado(sessao):
                if lado != "servidor":
                    continue
                if op == OP_WORLD and len(p) >= 4:
                    mapa = str(struct.unpack_from("<I", p, 0)[0])
                elif op == OP_MOVE and len(p) >= 4:
                    movers.add(struct.unpack_from("<I", p, 0)[0])
                elif op == OP_PUT_NPC and len(p) >= 49 and mapa:
                    x, y, z, oid, npc = struct.unpack_from("<fffII", p, 0)
                    h = p[27]
                    if not all(map(math.isfinite, (x, y, z))) or h > 120:
                        cont["pacote fora do formato"] += 1
                        continue
                    if struct.unpack_from("<I", p, 43)[0] or p[47:49] != b"\x00\x00":
                        cont["invocacao de jogador"] += 1
                        continue
                    vistos[oid].append((mapa, str(npc), x, y, z, h))
            for oid, vs in vistos.items():
                cont["objetos"] += 1
                if oid in movers:
                    cont["se moveu (S_MOVE_NEW)"] += 1
                elif len({v[0] for v in vs}) > 1 or max(math.dist(vs[0][2:4], v[2:4]) for v in vs) > PARADO:
                    cont["mudou de posicao entre avistamentos"] += 1
                else:
                    mapa, npc, x, y, z, h = vs[0]
                    pontos[mapa][(npc, round(x, 1), round(y, 1))] = (npc, x, y, z, h)
                    cont["parado"] += 1
    return pontos, cont


# ---------------------------------------------------------------- escrita
def reescreve(tag, x, y, z, h):
    """x, y, z e h no lugar; o que nao muda fica com o texto original."""
    for k, v in (("x", x), ("y", y), ("z", z)):
        atual = re.search(r'\b' + k + r'="([^"]*)"', tag)
        if atual and abs(float(atual.group(1)) - v) < 1e-4:
            continue
        tag = re.sub(r'(\b' + k + r'=")[^"]*(")', lambda m, v=v: m.group(1) + num(v) + m.group(2), tag, count=1)
    if re.search(r'\bh="', tag):
        tag = re.sub(r'(\bh=")[^"]*(")', lambda m: m.group(1) + str(h) + m.group(2), tag, count=1)
    elif h:
        tag = re.sub(r'(\bz="[^"]*")', lambda m: m.group(1) + ' h="{}"'.format(h), tag, count=1)
    return tag


def spot_novo(q, fecha):
    _npc, x, y, z, h = q
    return '<spot x="{}" y="{}" z="{}" h="{}"{}>'.format(num(x), num(y), num(z), h, fecha)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capturas", nargs="+")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    for c in args.capturas:
        if not os.path.isfile(c):
            sys.exit("Captura nao encontrada: " + c)

    print("1. Lendo capturas e servidor...")
    pontos, lidos = le_capturas(args.capturas)
    nomes, instancias = imp.le_mapas()
    tpl = imp.le_templates()
    textos, spots = le_servidor()
    _t2, principal, existentes, respawn = imp.le_servidor()
    print("   " + " | ".join("{} {}".format(k, v) for k, v in lidos.items()))

    print("2. Decidindo...")
    edits = collections.defaultdict(list)  # rel -> [(inicio, fim, texto)]
    novos_arquivos = {}
    cont, por_mapa, pendentes = collections.Counter(), collections.defaultdict(collections.Counter), []
    for mid in sorted(pontos):
        if mid in FORA or mid not in nomes:
            cont["mapa fora do escopo ou desconhecido"] += len(pontos[mid])
            continue
        por_npc = collections.defaultdict(list)
        for q in pontos[mid].values():
            por_npc[q[0]].append(q)
        blocos = []
        for npc, ofs in por_npc.items():
            sv = spots[mid].get(npc, [])
            cand = sorted((math.dist(s["pos"][:2], q[1:3]), i, j) for i, s in enumerate(sv) for j, q in enumerate(ofs))
            usados_s, usados_o = set(), set()
            for d, i, j in cand:
                if i in usados_s or j in usados_o:
                    continue
                usados_s.add(i)
                usados_o.add(j)
                s, q = sv[i], ofs[j]
                if d > R_LOCAL:
                    preso = "static_id" in s["a"] or "walker_id" in s["a"]
                    if preso or not (len(sv) == 1 and len(ofs) == 1):
                        motivo = "preso a static_id/walker_id" if preso else "{} spots no servidor, {} oficiais".format(len(sv), len(ofs))
                        pendentes.append((mid, npc, "par a {:.0f} m: {}".format(d, motivo), s["pos"], int(s["a"].get("h", 0) or 0), q))
                        cont["pendente: par distante"] += 1
                        continue
                nova = reescreve(s["tag"], q[1], q[2], q[3], q[4])
                if nova == s["tag"]:
                    cont["ja igual ao oficial"] += 1
                    continue
                edits[s["rel"]].append((s["span"][0], s["span"][1], nova))
                mudou_h = str(q[4]) != s["a"].get("h", "0")
                mudou_pos = max(abs(s["pos"][k] - q[k + 1]) for k in range(3)) > 1e-4
                cont["corrigido: " + ("posicao e h" if mudou_h and mudou_pos else "so h" if mudou_h else "so posicao")] += 1
                por_mapa[mid]["corrigidos"] += 1

            sobra = [q for j, q in enumerate(ofs) if j not in usados_o]
            if not sobra:
                continue
            if npc not in tpl:
                cont["pendente: sem npc_template"] += len(sobra)
                pendentes += [(mid, npc, "sem npc_template", None, None, q) for q in sobra]
                continue
            ex = existentes[mid].get(npc, [])
            if ex:
                alvo = next((e for e in ex if not e["travado"]), None)
                if alvo is None:
                    cont["pendente: npc so em spawn travado (pool/handler/Custom/Base/Rift/Siege)"] += len(sobra)
                    pendentes += [(mid, npc, "npc so em spawn travado", None, None, q) for q in sobra]
                    continue
                t = textos.get(alvo["rel"]) or open(os.path.join(backup_manager.SERVER_DATA_DIR, alvo["rel"]), encoding="utf-8", newline="").read()
                nl = "\r\n" if "\r\n" in t else "\n"
                pos = t.rfind("\n", 0, alvo["fim"]) + 1
                texto = "".join(alvo["recuo"] + spot_novo(q, alvo["fecha"]) + nl for q in sorted(sobra, key=lambda q: q[1:3]))
                edits[alvo["rel"]].append((pos, pos, texto))
                cont["spot oficial acrescentado"] += len(sobra)
                por_mapa[mid]["acrescentados"] += len(sobra)
            else:
                rt = respawn[npc].most_common(1)[0][0] if respawn[npc] else (None if mid in instancias else imp.RESPAWN_MUNDO)
                blocos.append((tpl[npc], npc, rt, sobra))
                cont["spawn novo"] += 1
                cont["pontos em spawn novo"] += len(sobra)
                por_mapa[mid]["novos"] += len(sobra)

        if not blocos:
            continue
        linhas_bloco = lambda recuo, nl: "".join(
            "{r}<!-- {n} -->{nl}{r}<spawn npc_id=\"{i}\"{rt}>{nl}{s}{r}</spawn>{nl}".format(
                r=recuo, n=nome, nl=nl, i=npc, rt=' respawn_time="{}"'.format(rt) if rt else "",
                s="".join(recuo + "\t" + spot_novo(q, "/") + nl for q in sorted(pts, key=lambda q: q[1:3])))
            for nome, npc, rt, pts in sorted(blocos, key=lambda b: (b[0].lower(), int(b[1]))))
        if mid in principal:
            rel, fim_mapa = principal[mid]
            t = textos.get(rel) or open(os.path.join(backup_manager.SERVER_DATA_DIR, rel), encoding="utf-8", newline="").read()
            textos.setdefault(rel, t)
            nl = "\r\n" if "\r\n" in t else "\n"
            ex = re.search(r"\n([ \t]*)<spawn\b", t)
            pos = t.rfind("\n", 0, fim_mapa) + 1
            edits[rel].append((pos, pos, linhas_bloco(ex.group(1) if ex else "\t\t", nl)))
        else:
            pasta = "Instances" if mid in instancias else "Npcs"
            rel = os.path.join("spawns", pasta, "{}_{}.xml".format(mid, nomes[mid]))
            novos_arquivos[rel] = ('<?xml version="1.0" encoding="utf-8"?>\n<spawns xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                                   'xsi:noNamespaceSchemaLocation="../spawns.xsd">\n\t<spawn_map map_id="{}">\n{}\t</spawn_map>\n</spawns>\n'
                                   ).format(mid, linhas_bloco("\t\t", "\n"))
            cont["arquivo novo"] += 1

    for k, v in sorted(cont.items()):
        print("   {:66} {}".format(k, v))

    print("3. Montando e validando...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "spawns", "spawns.xsd")))
    prontos = {}
    for rel, lista in edits.items():
        t = textos.get(rel) or open(os.path.join(backup_manager.SERVER_DATA_DIR, rel), encoding="utf-8", newline="").read()
        out, ant = [], 0
        for a, b, novo in sorted(lista, key=lambda e: (e[0], e[1])):
            if a < ant:
                sys.exit("Edicoes sobrepostas em " + rel + ": nada foi gravado.")
            out.append(t[ant:a])
            out.append(novo)
            ant = b
        out.append(t[ant:])
        prontos[rel] = "".join(out)
    prontos.update(novos_arquivos)
    for rel, texto in prontos.items():
        if not schema.validate(etree.fromstring(texto.encode("utf-8"))):
            for e in list(schema.error_log)[:10]:
                print("   {} linha {}: {}".format(rel, e.line, e.message))
            sys.exit("XSD invalido em " + rel + ": nada foi gravado.")
    print("   {} arquivos alterados, {} novos | XSD valido.".format(len(edits), len(novos_arquivos)))

    if prontos:
        relatorio(args.capturas, lidos, cont, por_mapa, pendentes, nomes, tpl, sorted(novos_arquivos))
    else:
        print("   nada a mudar; relatorio anterior mantido.")
    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    for rel, texto in sorted(prontos.items()):
        backup_manager.backup_file_before_modification(rel)
        for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
            destino = caminho_existente(base, rel)
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "w", encoding="utf-8", newline="") as f:
                f.write(texto)
    print("Gravados {} arquivos nas duas arvores.".format(len(prontos)))


def relatorio(capturas, lidos, cont, por_mapa, pendentes, nomes, tpl, arquivos_novos):
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("Spawns de NPC corrigidos pela captura do servidor oficial: posicao, altura e direcao exatas.\n\n")
        f.write("capturas:\n" + "".join("  {}\n".format(os.path.basename(c)) for c in capturas))
        f.write("lido: " + " | ".join("{} {}".format(k, v) for k, v in lidos.items()) + "\n\n")
        f.write("== resultado ==\n" + "".join("  {:66} {}\n".format(k, v) for k, v in sorted(cont.items())))
        if arquivos_novos:
            f.write("\n  arquivos novos:\n" + "".join("    {}\n".format(r) for r in arquivos_novos))
        f.write("\n== por mapa ==\n")
        for mid in sorted(por_mapa):
            c = por_mapa[mid]
            f.write("  {} {:32} corrigidos {:>4}  acrescentados {:>4}  novos {:>4}\n".format(
                mid, nomes.get(mid, "?")[:32], c.get("corrigidos", 0), c.get("acrescentados", 0), c.get("novos", 0)))
        f.write("\n== pendentes ({}) -- a captura ve o NPC mas nao da para aplicar sem risco ==\n".format(len(pendentes)))
        f.write("  (mapa, npc, nome, motivo, servidor x/y/z h, oficial x/y/z h)\n")
        for mid, npc, motivo, ps, hs, q in sorted(pendentes, key=lambda r: (r[0], int(r[1]))):
            srv = "({:.1f}, {:.1f}, {:.1f}) h{}".format(*ps, hs) if ps else "-"
            f.write("  {} {:>7} {:24} {:44} {:28} -> ({:.1f}, {:.1f}, {:.1f}) h{}\n".format(
                mid, npc, tpl.get(npc, "")[:24], motivo[:44], srv, q[1], q[2], q[3], q[4]))
    print("   relatorio: " + RELATORIO)


if __name__ == "__main__":
    main()
