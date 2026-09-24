#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_50_npc_spawns.py

Cria os spawns de NPC que o cliente 5.0 tem (client_world_*.xml, <npc_info>) e o servidor nao. O corretor
rebuild_50_npc_spawns.py so move spot que ja existe; este e o passo que acrescenta. Os dois convivem: rodar o
corretor depois deste nao muda nada, e rodar este de novo nao cria duplicata.

Nem todo <npc_info> e um spawn fixo. O que cada marca quer dizer, medido nos 20 mil pontos do cliente:
  abyss_info (ALi/ADa/ADr...)   dono da fortaleza: e o sistema de cerco (siege_spawn por siege_id/raca/mod),
                                que nao tem coordenada em siege_locations.xml. Fica de fora, listado por mapa.
  condition_info c1/C1          condicao base na maioria dos mapas: a Shugo_Imperial_Tomb inteira e c1. Entra --
                                exceto onde c1 e so uma alternativa entre c1..cN (Reshanta tem 42-45 pontos em
                                cada um): ai spawnar todas empilharia os conjuntos. Regra: c1 e base se tiver pelo
                                menos 3x a contagem do cN mais comum do mapa.
  condition_info c2+, Day, Night, WindBox_On, Event1...
                                fase, horario ou gatilho de script. Fica de fora, listado.
  select_prob (10000 = 100%)    probabilidade por ponto, nao normalizada por grupo. Vira <spawn pool="N">, que o
                                SpawnEngine usa para sortear N dos spots (e so vale com N < spots).
  movetype true                 NPC que anda. Sem waypoint.csv no cliente extraido e com route_id sem mapa, reusar
                                rota arriscaria pegar a de outro mapa: vai com random_walk="8", o valor mais usado.

Duplicata e o maior risco. Para npc que o mapa ja tem, so entra o excedente: emparelha um-para-um com os spots
existentes, sem limite de distancia, e so o que sobra pode virar spot -- se o servidor ja tem tantos spots quanto o
cliente tem pontos, nada falta. E mesmo o excedente nao entra a menos de R_DUPLICATA de um spot do mesmo npc: e o
mesmo acampamento com outra distribuicao (1108 dos 1200 dessa faixa estao a menos de 20 m). So acrescenta em <spawn> sem pool, handler ou temporary_spawn,
e fora de Bases/Rifts/Sieges/Custom, porque somar spots nesses muda o comportamento do grupo.

Altura e direcao: z do terreno quando o marcador do cliente esta 0-4 m acima dele (o z do cliente e ~1,8 m acima
do chao); fora do terreno, o z do cliente, contado no relatorio. h="0": o cliente nao tem direcao -- vem da captura.
respawn_time: o do proprio npc em outro mapa (8817 de 8849 usam um valor so); sem referencia, 295 no mundo e
nenhum em instancia (spawn unico, como ja e la).

Fora do escopo, por decisao do usuario: os mapas em FORA e os mapas de teste.

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python import_50_npc_spawns.py --cliente "<pasta dos XMLs do cliente 5.0>"            (mostra e gera relatorio)
    python import_50_npc_spawns.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
"""

import argparse
import collections
import glob
import html
import math
import os
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402
from rebuild_50_item_templates import DEFAULT_CLIENT_DIR  # noqa: E402
from rebuild_50_npc_spawns import FORA, GEO_DIR, Terrenos, caminho_existente, num  # noqa: E402

RELATORIO = os.path.join(PARSERS_DIR, "relatorio_spawns_novos_50.txt")
MAPAS_TESTE = {"900020000", "900220000"}  # TestBasic e System_Basic
R_DUPLICATA = 30.0
RANDOM_WALK = "8"
RESPAWN_MUNDO = "295"
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
MAP_RE = re.compile(r'<spawn_map\b[^>]*\bmap_id="(\d+)"[^>]*>(.*?)</spawn_map>', re.S)
SPAWN_RE = re.compile(r"<spawn\b([^>]*)>(.*?)</spawn>", re.S)
SPOT_RE = re.compile(r"([ \t]*)<spot\b([^>]*?)(\s?/)>")


# ---------------------------------------------------------------- leitura
def le_cliente(cdir):
    wdir = os.path.join(cdir, "data", "world")
    ids = {}
    for m in re.finditer(r"<data\b([^>]*)>([^<]+)</data>", open(os.path.join(wdir, "WorldId.xml"), encoding="utf-8", errors="replace").read()):
        a = dict(ATTR_RE.findall(m.group(1)))
        if a.get("id"):
            ids[m.group(2).strip().lower()] = a["id"]
    out = collections.defaultdict(list)
    for f in glob.glob(os.path.join(glob.escape(wdir), "client_world_*.xml")):
        mid = ids.get(os.path.basename(f)[len("client_world_"):-4].lower())
        if not mid or mid in FORA or mid in MAPAS_TESTE:
            continue
        for b in re.findall(r"<npc_info>(.*?)</npc_info>", open(f, encoding="utf-8", errors="replace").read(), re.S):
            def g(k):
                v = re.search(r"<" + k + r">([^<]*)</" + k + r">", b)
                return v.group(1).strip() if v else None
            try:
                pos = (float(g("x")), float(g("y")), float(g("z")))
            except (TypeError, ValueError):
                continue
            if not (g("nameid") or "").isdigit():
                continue
            out[mid].append({"npc": g("nameid"), "pos": pos, "anda": (g("movetype") or "").lower() == "true",
                             "cond": g("condition_info"), "abyss": g("abyss_info"), "prob": int(g("select_prob") or 10000)})
    return out


def le_mapas():
    t = open(os.path.join(backup_manager.SERVER_DATA_DIR, "world_maps.xml"), encoding="utf-8", errors="replace").read()
    nomes, inst = {}, set()
    for m in re.finditer(r"<map\b([^>]*)/?>", t):
        a = dict(ATTR_RE.findall(m.group(1)))
        if a.get("id"):
            nomes[a["id"]] = a.get("name", a["id"])
            if a.get("instance") == "true":
                inst.add(a["id"])
    return nomes, inst


def le_templates():
    t = open(os.path.join(backup_manager.SERVER_DATA_DIR, "npcs", "npc_templates.xml"), encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r"\t<npc_template\b([^>]*)>", t):
        a = dict(ATTR_RE.findall(m.group(1)))
        if a.get("npc_id"):
            out[a["npc_id"]] = html.unescape(a.get("name", "")).replace("--", "-")
    return out


def le_servidor():
    """Textos, spawns existentes por (mapa, npc) com onde inserir, o arquivo principal de cada mapa e os respawns."""
    base = backup_manager.SERVER_DATA_DIR
    textos, principal = {}, {}
    spawns = collections.defaultdict(lambda: collections.defaultdict(list))
    respawn = collections.defaultdict(collections.Counter)
    for p in sorted(glob.glob(os.path.join(glob.escape(base), "spawns", "**", "*.xml"), recursive=True)):
        rel = os.path.relpath(p, base)
        partes = rel.split(os.sep)
        with open(p, encoding="utf-8", newline="") as f:
            t = f.read()
        textos[rel] = t
        editavel = len(partes) == 3 and partes[1] in ("Npcs", "Instances")  # spawns/<pasta>/<arquivo>: sem Custom
        for sm in MAP_RE.finditer(t):
            mid = sm.group(1)
            if editavel:
                principal.setdefault(mid, (rel, sm.end(2)))
            for sp in SPAWN_RE.finditer(t, sm.start(2), sm.end(2)):
                a = dict(ATTR_RE.findall(sp.group(1)))
                if not a.get("npc_id"):
                    continue
                if a.get("respawn_time"):
                    respawn[a["npc_id"]][a["respawn_time"]] += 1
                spots = list(SPOT_RE.finditer(sp.group(2)))
                pts = []
                for s in spots:
                    sa = dict(ATTR_RE.findall(s.group(2)))
                    try:
                        pts.append((float(sa["x"]), float(sa["y"])))
                    except (KeyError, ValueError):
                        pass
                travado = (not editavel or a.get("pool") or a.get("handler") or a.get("custom") == "true"
                           or "<temporary_spawn" in sp.group(2) or not spots)
                ult = spots[-1] if spots else None
                spawns[mid][a["npc_id"]].append({
                    "rel": rel, "pts": pts, "travado": bool(travado), "fim": sp.end(2),
                    "recuo": ult.group(1) if ult else "", "fecha": ult.group(3) if ult else "/"})
    return textos, principal, spawns, respawn


# ---------------------------------------------------------------- decisao
def c1_e_base(pts):
    cs = collections.Counter(p["cond"].lower() for p in pts if p["cond"] and re.fullmatch(r"c\d+", p["cond"].lower()))
    outros = max((v for k, v in cs.items() if k != "c1"), default=0)
    return cs.get("c1", 0) >= 3 * outros


def livres(gp, existentes):
    """So o excedente do cliente: emparelha um-para-um pela menor distancia, sem limite, e devolve os pontos que
    sobraram com a distancia ao spot mais proximo. Com limite, um spot que o corretor nao pode mover (preso,
    ambiguo, sem altura) deixava o ponto dele 'livre' e o npc ganhava uma copia -- 159 dos 884 acrescentados na
    primeira versao eram isso, inclusive npc com 1 spot no servidor e 1 ponto no cliente."""
    todos = [xy for e in existentes for xy in e["pts"]]
    if not todos:
        return [(p, None) for p in gp]
    cand = sorted((math.dist(p["pos"][:2], e), i, j) for i, p in enumerate(gp) for j, e in enumerate(todos))
    ui, uj = set(), set()
    for _d, i, j in cand:
        if i in ui or j in uj:
            continue
        ui.add(i)
        uj.add(j)
    return [(p, min(math.dist(p["pos"][:2], e) for e in todos)) for i, p in enumerate(gp) if i not in ui]


def motivo_resumido(k):
    """Para o total: dezenas de condicoes que aparecem 1 vez viram tres categorias. O detalhe fica no relatorio."""
    k = re.sub(r" \(.*\)$", "", k)
    if not k.startswith("condicao "):
        return k
    v = k[len("condicao "):]
    if v.startswith("c1 que"):
        return "condicao c1 que e alternativa no mapa"
    return "condicao de fase (c2..cN)" if re.fullmatch(r"[cC]\d+", v) else "condicao de evento/horario/script"


def spot(p, mid, terr, fecha, cont):
    x, y, z = p["pos"]
    t = terr.z(mid, x, y)
    if t is not None and -0.5 <= z - t <= 4.0:
        z = t
        cont["z do terreno"] += 1
    else:
        cont["z do cliente (sem terreno util)"] += 1
    anda = ' random_walk="{}"'.format(RANDOM_WALK) if p["anda"] else ""
    return '<spot x="{}" y="{}" z="{}" h="0"{}{}>'.format(num(x), num(y), num(z), anda, fecha)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    if not os.path.isfile(os.path.join(args.cliente, "data", "world", "WorldId.xml")):
        sys.exit("WorldId.xml do cliente nao encontrado em " + args.cliente + ". Informe --cliente ou AION_CLIENT_XML_DIR.")
    if not os.path.isdir(GEO_DIR):
        sys.exit("Sem " + GEO_DIR + ": o heightmap e o que impede o NPC novo de flutuar.")

    print("1. Lendo cliente, servidor, templates e terreno...")
    cli = le_cliente(args.cliente)
    nomes, instancias = le_mapas()
    tpl = le_templates()
    textos, principal, spawns, respawn = le_servidor()
    terr = Terrenos(GEO_DIR)

    print("2. Decidindo...")
    cont, fora = collections.Counter(), collections.defaultdict(collections.Counter)
    insercoes = collections.defaultdict(lambda: collections.defaultdict(list))  # rel -> posicao -> linhas
    novos_arquivos = collections.defaultdict(list)  # rel -> blocos
    por_mapa = collections.defaultdict(collections.Counter)
    for mid in sorted(cli):
        if mid not in nomes:
            fora[mid]["mapa que o servidor nao conhece"] += len(cli[mid])
            continue
        base = c1_e_base(cli[mid])
        grupos = collections.defaultdict(list)
        for p in cli[mid]:
            c = (p["cond"] or "").lower()
            if p["abyss"]:
                fora[mid]["cerco (abyss_info " + p["abyss"] + ")"] += 1
            elif c and not (c == "c1" and base):
                fora[mid]["condicao " + (p["cond"] if c != "c1" else "c1 que e alternativa neste mapa")] += 1
            elif p["npc"] not in tpl:
                fora[mid]["sem npc_template (" + p["npc"] + ")"] += 1
            else:
                grupos[p["npc"]].append(p)

        blocos = []
        for npc, gp in grupos.items():
            existentes = spawns[mid].get(npc, [])
            soltos = livres(gp, existentes)
            if not soltos:
                continue
            if existentes:
                alvo = next((e for e in existentes if not e["travado"]), None)
                for p, dmin in soltos:
                    if alvo is None:
                        fora[mid]["npc ja tem spawn com pool/handler/temporary/base/rift/custom"] += 1
                    elif p["prob"] < 10000:
                        fora[mid]["probabilidade em npc que ja existe sem pool"] += 1
                    elif dmin < R_DUPLICATA:
                        fora[mid]["a menos de {:.0f} m de um spot do mesmo npc".format(R_DUPLICATA)] += 1
                    else:
                        nl = "\r\n" if "\r\n" in textos[alvo["rel"]] else "\n"
                        linha = alvo["recuo"] + spot(p, mid, terr, alvo["fecha"], cont) + nl
                        # antes da linha do </spawn>: volta ate o inicio dela
                        t = textos[alvo["rel"]]
                        pos = t.rfind("\n", 0, alvo["fim"]) + 1
                        insercoes[alvo["rel"]][pos].append(linha)
                        cont["spot acrescentado em spawn existente"] += 1
                        por_mapa[mid]["acrescentados"] += 1
                continue
            pts = [p for p, _d in soltos]
            k, pm = len(pts), statistics.median(p["prob"] for p in pts)
            pool = 0
            if pm < 10000:
                # nunca arredonda para 0: 3 pontos a 5% viram pool 1, mais perto do que spawnar os 3
                pool = max(1, round(k * pm / 10000))
                if pool >= k:  # SpawnEngine.checkPool ignora pool >= spots: 1 ponto so, ou probabilidade alta
                    cont["probabilidade sem pool possivel: spawna sempre"] += k
                    pool = 0
            rt = respawn[npc].most_common(1)[0][0] if respawn[npc] else (None if mid in instancias else RESPAWN_MUNDO)
            blocos.append((tpl[npc], npc, rt, pool, pts))
            cont["spawn novo"] += 1
            cont["pontos em spawn novo"] += k
            if pool:
                cont["spawn novo com pool"] += 1
            por_mapa[mid]["novos"] += k

        if not blocos:
            continue
        if mid in principal:
            rel, fim_mapa = principal[mid]
            t = textos[rel]
            nl = "\r\n" if "\r\n" in t else "\n"
            ex = re.search(r"\n([ \t]*)<spawn\b", t)
            recuo = ex.group(1) if ex else "\t\t"
            pos = t.rfind("\n", 0, fim_mapa) + 1
        else:
            pasta = "Instances" if mid in instancias else "Npcs"
            rel = os.path.join("spawns", pasta, "{}_{}.xml".format(mid, nomes[mid]))
            nl, recuo, pos = "\n", "\t\t", None
            cont["arquivo novo"] += 1
        linhas = []
        for nome, npc, rt, pool, pts in sorted(blocos, key=lambda b: (b[0].lower(), int(b[1]))):
            linhas.append("{}<!-- {} -->{}".format(recuo, nome, nl))
            attrs = ' npc_id="{}"'.format(npc) + (' respawn_time="{}"'.format(rt) if rt else "") + (' pool="{}"'.format(pool) if pool else "")
            linhas.append("{}<spawn{}>{}".format(recuo, attrs, nl))
            for p in sorted(pts, key=lambda q: q["pos"]):
                linhas.append(recuo + "\t" + spot(p, mid, terr, "/", cont) + nl)
            linhas.append("{}</spawn>{}".format(recuo, nl))
        if pos is None:
            novos_arquivos[rel] = ['<?xml version="1.0" encoding="utf-8"?>\n',
                                   '<spawns xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../spawns.xsd">\n',
                                   '\t<spawn_map map_id="{}">\n'.format(mid)] + linhas + ["\t</spawn_map>\n", "</spawns>\n"]
        else:
            insercoes[rel][pos].extend(linhas)

    for k, v in cont.most_common():
        print("   {:62} {}".format(k, v))
    total_fora = collections.Counter()
    for c in fora.values():
        for k, v in c.items():
            total_fora[motivo_resumido(k)] += v
    print("   fora:")
    for k, v in total_fora.most_common():
        print("     {:60} {}".format(k, v))

    print("3. Montando e validando...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "spawns", "spawns.xsd")))
    prontos = {}
    for rel, por_pos in insercoes.items():
        t, out, ant = textos[rel], [], 0
        for pos in sorted(por_pos):
            out.append(t[ant:pos])
            out.append("".join(por_pos[pos]))
            ant = pos
        out.append(t[ant:])
        prontos[rel] = "".join(out)
    for rel, linhas in novos_arquivos.items():
        prontos[rel] = "".join(linhas)
    for rel, texto in prontos.items():
        if not schema.validate(etree.fromstring(texto.encode("utf-8"))):
            for e in list(schema.error_log)[:10]:
                print("   {} linha {}: {}".format(rel, e.line, e.message))
            sys.exit("XSD invalido em " + rel + ": nada foi gravado.")
    print("   {} arquivos alterados, {} novos | XSD valido.".format(len(insercoes), len(novos_arquivos)))

    if prontos:
        relatorio(cont, total_fora, fora, por_mapa, nomes, sorted(novos_arquivos))
    else:
        print("   nada a criar; relatorio anterior mantido.")

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


def relatorio(cont, total_fora, fora, por_mapa, nomes, arquivos_novos):
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("NPCs criados a partir do cliente 5.0 onde o servidor nao tinha spawn.\n")
        f.write("h=\"0\" em todos (o cliente nao tem direcao); z do terreno quando mensuravel. Tudo vem da captura depois.\n\n")
        f.write("== criado ==\n")
        for k, v in cont.most_common():
            f.write("  {:62} {}\n".format(k, v))
        if arquivos_novos:
            f.write("\n  arquivos novos:\n" + "".join("    {}\n".format(r) for r in arquivos_novos))
        f.write("\n== por mapa ==\n")
        for mid in sorted(set(por_mapa) | set(fora)):
            c = por_mapa.get(mid, {})
            f.write("  {} {:32} novos {:>5}  acrescentados {:>4}  fora {:>5}\n".format(
                mid, nomes.get(mid, "?")[:32], c.get("novos", 0), c.get("acrescentados", 0), sum(fora[mid].values())))
        f.write("\n== fora, por motivo ==\n")
        for k, v in total_fora.most_common():
            f.write("  {:60} {}\n".format(k, v))
        f.write("\n== fora, detalhado por mapa (o cerco e as condicoes sao os proximos passos) ==\n")
        for mid in sorted(fora):
            f.write("  {} {}\n".format(mid, nomes.get(mid, "?")))
            for k, v in fora[mid].most_common():
                f.write("      {:>5}  {}\n".format(v, k))
    print("   relatorio: " + RELATORIO)


if __name__ == "__main__":
    main()
