#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
restore_50_walker_ids.py

Repoe nos spawns o walker_id/walker_index que o sync_all_50_spawns.py apagou no commit df2ad9235 (2026-09-15).

O filtro dele tirava todo walker_id com 40 caracteres hexadecimais como "hash SHA1 invalido", mas todo route_id do
npc_walker e o SHA-1 do nome da rota: foram-se 12.830 ligacoes, das quais 5.240 apontavam para rota que existe. O
filtro ja foi corrigido para tirar so walker_id sem walker_template.

Como repoe, em cada arvore separadamente:
  * le os spawns do commit de referencia (1929e30c0, o ultimo antes da perda) pelo git;
  * so entra walker_id cujo route_id existe hoje no npc_walker da arvore;
  * par um-para-um com o spot atual do mesmo arquivo (caminho relativo) e do mesmo npc_id, sem walker_id, a ate
    R_PAR na horizontal; spot que sumiu ou andou mais que isso fica de fora e sai no relatorio;
  * membro de grupo de patrulha (varios spots do mesmo npc no mesmo ponto, mesma rota) que a sincronizacao juntou
    num spot so volta como copia do companheiro, com o walker_index da referencia;
  * se o spot de referencia nao tinha random_walk e o atual tem, o random_walk sai: o WalkManager tenta o andar
    aleatorio antes da rota, e com os dois o NPC nunca seguiria a rota.

Uso:
    python restore_50_walker_ids.py                       (mostra e grava o relatorio)
    python restore_50_walker_ids.py --aplicar             (grava as duas arvores, com backup)
    python restore_50_walker_ids.py --commit <hash>       (outro commit de referencia)
"""

import argparse
import collections
import glob
import math
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402

ARVORES = (("fonte", "Código Fonte - Emulador/game-server/data/static_data"),
           ("produto", "Emulador - Produto Final/GameServer/data/static_data"))
COMMIT_REFERENCIA = "1929e30c0"
R_PAR = 3.0
RELATORIO = os.path.join(AQUI, "relatorio_walker_ids_50.txt")
BLOCO = re.compile(r'<spawn\b[^>]*\bnpc_id="(\d+)"[^>]*>(.*?)</spawn>', re.S)
SPOT = re.compile(r"<spot\b[^>]*?/?>")


def git(*args):
    return subprocess.run(["git", "-C", RAIZ] + list(args), capture_output=True, check=True).stdout.decode("utf-8", "replace")


def atributo(tag, nome):
    m = re.search(r'\b%s="([^"]*)"' % nome, tag)
    return m.group(1) if m else None


def xy(tag):
    return float(atributo(tag, "x")), float(atributo(tag, "y"))


def referencia(commit, rel_static):
    """(arquivo relativo a spawns/, npc_id) -> [(x, y, walker_id, walker_index, random_walk)] com rota."""
    out = collections.defaultdict(list)
    pasta = rel_static + "/spawns"
    for caminho in git("ls-tree", "-r", "--name-only", commit, pasta).splitlines():
        if not caminho.endswith(".xml"):
            continue
        texto = git("show", "%s:%s" % (commit, caminho))
        if "walker_id" not in texto:
            continue
        rel = caminho[len(pasta) + 1:]
        for m in BLOCO.finditer(texto):
            for tag in SPOT.findall(m.group(2)):
                w = atributo(tag, "walker_id")
                if w:
                    out[(rel, int(m.group(1)))].append((*xy(tag), w, atributo(tag, "walker_index"), atributo(tag, "random_walk")))
    return out


def com_rota(tag, walker_id, indice):
    """Tag com o walker_id/walker_index da referencia; um walker_index solto que o spot ja tenha e substituido."""
    tag = re.sub(r'\s+walker_(?:id|index)="[^"]*"', "", tag)
    extra = ' walker_id="%s"' % walker_id + (' walker_index="%s"' % indice if indice and indice != "0" else "")
    return re.sub(r"\s*/?>$", lambda f: extra + f.group(0), tag, count=1)


def rotas(base):
    ids = set()
    for f in glob.glob(os.path.join(glob.escape(base), "npc_walker", "*.xml")):
        ids.update(re.findall(r'route_id="([^"]+)"', open(f, encoding="utf-8").read()))
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commit", default=COMMIT_REFERENCIA)
    ap.add_argument("--aplicar", action="store_true", help="grava as duas arvores (com backup)")
    args = ap.parse_args()
    rel = ["restore_50_walker_ids.py --commit %s -- %s" % (args.commit, "APLICADO" if args.aplicar else "simulacao")]

    for nome, rel_static in ARVORES:
        base = os.path.join(RAIZ, rel_static)
        existentes = rotas(base)
        ref = referencia(args.commit, rel_static)
        total = sum(len(v) for v in ref.values())
        validos = {k: [s for s in v if s[2] in existentes] for k, v in ref.items()}
        n_validos = sum(len(v) for v in validos.values())
        print("%s: referencia %d spots com walker_id, %d com rota existente" % (nome, total, n_validos))
        rel += ["", "=" * 100, "ARVORE %s: referencia %d spots com walker_id, %d com rota existente" % (nome, total, n_validos)]

        por_arquivo = collections.defaultdict(dict)
        for (arq, npc), spots in validos.items():
            if spots:
                por_arquivo[arq][npc] = spots
        repostos = sem_random = membros = 0
        perdidos = collections.Counter()
        grupos = collections.defaultdict(lambda: [0, 0])      # walker_id -> [na referencia, repostos]
        for (arq, npc), spots in validos.items():
            for s in spots:
                grupos[s[2]][0] += 1
        for arq, npcs in sorted(por_arquivo.items()):
            caminho = os.path.join(base, "spawns", arq)
            if not os.path.exists(caminho):
                perdidos["arquivo nao existe mais"] += sum(len(v) for v in npcs.values())
                continue
            texto = open(caminho, encoding="utf-8", newline="").read()
            trocas = {}                                       # posicao do spot -> (tag antiga, tag nova)
            insercoes = collections.defaultdict(list)         # fim do spot companheiro -> tags de membros repostos
            for m in BLOCO.finditer(texto):
                npc = int(m.group(1))
                if npc not in npcs:
                    continue
                inicio = m.start(2)
                livres = [(inicio + t.start(), t.group(0)) for t in SPOT.finditer(m.group(2)) if "walker_id" not in t.group(0)]
                sem_par = []
                for s in npcs[npc]:
                    x, y, w, idx, rw_ref = s
                    par = min(livres, key=lambda a: math.dist(xy(a[1]), (x, y)), default=None)
                    if par is None or math.dist(xy(par[1]), (x, y)) > R_PAR:
                        sem_par.append(s)
                        continue
                    livres.remove(par)
                    tag = par[1]
                    if (not rw_ref or rw_ref == "0") and re.search(r'\brandom_walk="[1-9]\d*"', tag):
                        tag = re.sub(r'\s+random_walk="\d+"', "", tag)
                        sem_random += 1
                    trocas[par[0]] = (par[1], com_rota(tag, w, idx))
                    grupos[w][1] += 1
                # membro de grupo de patrulha: na referencia ficava no mesmo ponto de outro spot com a mesma rota, e a
                # sincronizacao deixou um so. Volta como copia do companheiro que ja recebeu a rota.
                for x, y, w, idx, _rw in sem_par:
                    comp = [(pos, novo) for pos, (_antigo, novo) in trocas.items() if inicio <= pos < m.end(2)
                            and atributo(novo, "walker_id") == w and math.dist(xy(novo), (x, y)) <= R_PAR]
                    if not comp:
                        perdidos["spot nao encontrado a <= %.0f m" % R_PAR] += 1
                        continue
                    pos, novo = min(comp, key=lambda c: math.dist(xy(c[1]), (x, y)))
                    base_tag = re.sub(r'\s+walker_index="\d+"', "", novo)
                    if idx and idx != "0":
                        base_tag = re.sub(r"\s*/?>$", lambda f: ' walker_index="%s"' % idx + f.group(0), base_tag, count=1)
                    insercoes[pos].append(base_tag)
                    grupos[w][1] += 1
            if not trocas:
                continue
            partes, ultimo = [], 0
            for pos in sorted(trocas):
                antigo, novo = trocas[pos]
                recuo = texto[texto.rfind("\n", 0, pos) + 1:pos]
                partes += [texto[ultimo:pos], novo] + ["\n" + recuo + t for t in insercoes.get(pos, [])]
                ultimo = pos + len(antigo)
            novo_texto = "".join(partes) + texto[ultimo:]
            n_ins = sum(len(v) for v in insercoes.values())
            if novo_texto.count("<spot") != texto.count("<spot") + n_ins:
                sys.exit("ABORTADO: contagem de spots nao fecha em %s" % caminho)
            repostos += len(trocas)
            membros += n_ins
            rel.append("  %-60s +%d walker_id, +%d membros de grupo" % (arq, len(trocas), n_ins))
            if args.aplicar:
                backup_manager.backup_file_before_modification(caminho)
                open(caminho, "w", encoding="utf-8", newline="").write(novo_texto)
        incompletos = {w: g for w, g in grupos.items() if g[0] > 1 and 0 < g[1] < g[0]}
        print("   repostos %d, membros de grupo repostos %d, random_walk retirado de %d, fora: %s, grupos incompletos %d" % (
            repostos, membros, sem_random, dict(perdidos), len(incompletos)))
        rel += ["  repostos %d, membros de grupo repostos %d, random_walk retirado de %d, fora: %s" % (repostos, membros, sem_random, dict(perdidos)),
                "  grupos de rota com parte dos membros (formacao incompleta): %d" % len(incompletos)]
        rel += ["    %s: %d de %d" % (w, g[1], g[0]) for w, g in sorted(incompletos.items())]

    if args.aplicar:
        from lxml import etree
        for nome, rel_static in ARVORES:
            base = os.path.join(RAIZ, rel_static)
            sch = etree.XMLSchema(etree.parse(os.path.join(base, "static_data.xsd")))
            ruins = [f for f in glob.glob(os.path.join(glob.escape(base), "spawns", "*", "*.xml"))
                     if "walker_id" in open(f, encoding="utf-8", errors="replace").read() and not sch.validate(etree.parse(f))]
            print("   %s: spawns com walker_id validam no static_data.xsd: %s" % (nome, "sim" if not ruins else "NAO %s" % ruins[:5]))
    open(RELATORIO, "w", encoding="utf-8", newline="\n").write("\n".join(rel) + "\n")
    print("Relatorio: %s" % RELATORIO)
    if not args.aplicar:
        print("Simulacao: nada gravado. Rode com --aplicar para gravar.")


if __name__ == "__main__":
    main()
