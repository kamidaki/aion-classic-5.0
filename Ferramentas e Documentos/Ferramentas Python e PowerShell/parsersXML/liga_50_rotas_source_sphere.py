#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
liga_50_rotas_source_sphere.py

Liga os spots de spawn às rotas oficiais pelo source_sphere.csv + waypoint.csv do cliente
(Client 5.0 - Dados Extraidos/data/world, fora do git).

  source_sphere.csv  name,type,zone,x,y,z,r,wayPointName,clusterNum: uma esfera por NPC posto; com wayPointName o NPC anda
                     naquela rota. Várias esferas na mesma rota = patrulha (o emulador junta em WalkerGroup pelo walker_id).
  waypoint.csv       name,num,x,y,z,...: os passos da rota. O route_id do npc_walker.xml é o SHA-1 do nome em minúsculas
                     (é o nome como está no waypoint.csv; o source_sphere escreve com maiúsculas).

O mapa vem do cName do world_maps.xml e entram todos os arquivos de spawn do mapa (Npcs, Bases, Instances, ...), tratados juntos.
Spot que já tem a rota da esfera (mesmo npc) conta para ela e não muda. Para cada esfera restante: pega o spot do mesmo NPC mais
perto do centro da esfera que esteja a até --tolerancia m da linha da rota e não tenha rota nem random_walk, e põe
walker_id/walker_index nele. Não cria spot nem rota: só usa rota que o npc_walker.xml tem com o mesmo x/y do waypoint.csv (o z
foi colado no geo em parte delas); rota com outro traçado e esfera sem spot só vão para o relatório.

O waypoint.csv manda em todos os mapas, capitais incluídas (decisão de 30/10; antes as capitais vinham só das capturas).

Conferido no Balic Treasury (tiamat_down, 30/10): nas capturas oficiais, os mobs que andam e estão perto de uma rota ficam em
cima dela (mediana 0 m), e nenhum spot ligado é de mob que a captura viu parado.

Uso:
    python liga_50_rotas_source_sphere.py                      (todas as zonas que o emulador tem; só mostra)
    python liga_50_rotas_source_sphere.py --zona tiamat_down   (uma zona)
    python liga_50_rotas_source_sphere.py --parados parados.json --aplicar
"""

import argparse
import collections
import csv
import hashlib
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402

RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
CLIENTE = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")
WORLD = os.path.join(CLIENTE, "data", "world")
# 30/10: o usuário decidiu que o waypoint.csv manda também nas capitais (antes vinham só das capturas de 25/10)
ZONAS_CAPTURA = set()


def route_id(nome):
    return hashlib.sha1(nome.lower().encode("utf-8")).hexdigest().upper()


def le_waypoints():
    rotas = {}
    with open(os.path.join(WORLD, "waypoint.csv"), encoding="utf-8-sig", newline="") as f:
        for x in csv.reader(f):
            if x[0] == "name":
                continue
            v = list(map(float, x[2:2 + 3 * int(x[1])]))
            rotas[x[0].lower()] = [tuple(v[i:i + 3]) for i in range(0, len(v), 3)]
    return rotas


def nomes_npc():
    t = open(os.path.join(CLIENTE, "data", "npcs", "client_npcs.xml"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"<npc_client>(.*?)</npc_client>", t, re.S):
        b = m.group(1)
        out[re.search(r"<name>([^<]*)<", b).group(1).lower()] = int(re.search(r"<id>(\d+)<", b).group(1))
    return out


def le_esferas(zona, n2id):
    esferas, sem_npc = [], collections.Counter()
    with open(os.path.join(WORLD, "source_sphere.csv"), encoding="utf-8-sig", newline="") as f:
        for x in csv.reader(f):
            if x[0] == "name" or x[2].lower() != zona or len(x) < 8 or not x[7]:
                continue
            npc = n2id.get(x[0].lower())
            if npc is None:
                sem_npc[x[0]] += 1
                continue
            esferas.append((npc, float(x[3]), float(x[4]), x[7].lower()))
    return esferas, sem_npc


def le_npc_walker(base):
    return le_npc_walker_texto(open(os.path.join(base, "npc_walker", "npc_walker.xml"), encoding="utf-8").read())


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def substitui_rotas(base, rotas_csv):
    """npc_walker.xml com as rotas do csv: troca os passos das que têm outro traçado x/y (a tag do walker_template fica) e cria as
    que faltam. Rota com o mesmo x/y e outro z não muda (o z foi colado no geo de propósito). Devolve (texto, relatório)."""
    caminho = os.path.join(base, "npc_walker", "npc_walker.xml")
    texto = open(caminho, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in texto else "\n"
    por_rid = {route_id(n): n for n in rotas_csv}
    relatorio, vistos = [], set()

    def passos(pts):
        return "".join(f'{nl}\t\t<routestep x="{fmt(x)}" y="{fmt(y)}" z="{fmt(z)}" />' for x, y, z in pts)

    def troca(m):
        rid = m.group(2).upper()
        vistos.add(rid)
        nome = por_rid.get(rid)
        if nome is None:
            return m.group(0)
        atuais = [tuple(map(float, s)) for s in re.findall(r'x="([-\d.]+)" y="([-\d.]+)" z="([-\d.]+)"', m.group(3))]
        if rota_igual(atuais, rotas_csv[nome]):
            return m.group(0)
        relatorio.append(("trocada", rid, nome, len(atuais), len(rotas_csv[nome])))
        return m.group(1) + passos(rotas_csv[nome]) + nl + "\t</walker_template>"

    texto = re.sub(r'(<walker_template route_id="([0-9A-Fa-f]{40})"[^>]*>)(.*?)</walker_template>', troca, texto, flags=re.S)
    novas = [rid for rid in por_rid if rid not in vistos]
    if novas:
        bloco = "".join(f'\t<!-- {por_rid[rid]} (waypoint.csv) -->{nl}\t<walker_template route_id="{rid}">'
                        f'{passos(rotas_csv[por_rid[rid]])}{nl}\t</walker_template>{nl}' for rid in novas)
        i = texto.rindex("</npc_walker>")
        texto = texto[:i] + bloco + texto[i:]
        relatorio += [("nova", rid, por_rid[rid], 0, len(rotas_csv[por_rid[rid]])) for rid in novas]
    return texto, relatorio


def le_npc_walker_texto(t):
    return {m.group(1): [tuple(map(float, s)) for s in re.findall(r'x="([-\d.]+)" y="([-\d.]+)" z="([-\d.]+)"', m.group(2))]
            for m in re.finditer(r'<walker_template route_id="([0-9A-F]{40})"[^>]*>(.*?)</walker_template>', t, re.S)}


def dist_rota(px, py, passos):
    melhor = 1e9
    for a, b in zip(passos, passos[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L))
        melhor = min(melhor, math.hypot(px - a[0] - t * dx, py - a[1] - t * dy))
    return melhor


def rota_igual(srv, cli):
    return srv is not None and len(srv) == len(cli) and all(math.hypot(a[0] - b[0], a[1] - b[1]) <= 0.05 for a, b in zip(srv, cli))


def ponto_rota(px, py, passos):
    """(distância x/y à linha da rota, z da rota nesse ponto)"""
    melhor = (1e9, 0.0)
    for a, b in zip(passos, passos[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L))
        d = math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)
        if d < melhor[0]:
            melhor = (d, a[2] + t * (b[2] - a[2]))
    return melhor


def le_spots(textos):
    """{arquivo: texto} -> npc -> [[arquivo, ini, fim, x, y, walker_id ou None, livre]]"""
    spots = collections.defaultdict(list)
    for arq, texto in textos.items():
        msk = re.sub(r"(?s)<!--.*?-->", lambda m: " " * len(m.group(0)), texto)
        for sm in re.finditer(r'(?s)<spawn\b[^>]*npc_id="(\d+)"[^>]*>(.*?)</spawn>', msk):
            for sp in re.finditer(r"<spot\b[^>]*?/?>", sm.group(2)):
                tag = sp.group(0)
                g = lambda k: float(re.search(r'\b%s="([-\d.]+)"' % k, tag).group(1))
                w = re.search(r'walker_id="([^"]*)"', tag)
                livre = w is None and not re.search(r'random_walk="[1-9]', tag)
                ini = sm.start(2) + sp.start()
                spots[int(sm.group(1))].append([arq, ini, ini + len(tag), g("x"), g("y"),
                                                 w.group(1).upper() if w else None, livre, g("z")])
    return spots


def processa(textos, esferas, rotas, tol, parados=(), tol_z=5.0):
    """Devolve (textos novos, ligados, já ligados, esferas sem spot, rotas com patrulha)."""
    spots = le_spots(textos)
    usada_esf, usado_spot = set(), set()
    por_rota = collections.Counter()
    ja = 0
    for e, (npc, cx, cy, nome) in enumerate(esferas):        # 1) spot que já tem a rota da esfera
        rid = route_id(nome)
        cands = [s for s in spots.get(npc, []) if s[5] == rid and id(s) not in usado_spot]
        if cands:
            s = min(cands, key=lambda s: math.hypot(s[3] - cx, s[4] - cy))
            usada_esf.add(e)
            usado_spot.add(id(s))
            por_rota[nome] += 1
            ja += 1
    pares = []                                               # 2) spot livre perto do centro e em cima da rota
    for e, (npc, cx, cy, nome) in enumerate(esferas):
        if e in usada_esf:
            continue
        passos = rotas[route_id(nome)]
        for s in spots.get(npc, []):
            d, zr = ponto_rota(s[3], s[4], passos)
            # o z também: em torre de vários andares o mesmo x/y tem rota em outro andar (Tiamaranta, 30/10: spot da captura em
            # z 309 ligado a rota em z 388)
            if s[6] and d <= tol and abs(s[7] - zr) <= tol_z and \
                    not any(n == npc and math.hypot(s[3] - x, s[4] - y) <= 0.5 for n, x, y in parados):
                pares.append((math.hypot(s[3] - cx, s[4] - cy), e, id(s), s))
    edits = collections.defaultdict(list)
    ligados = 0
    for d, e, sid, s in sorted(pares, key=lambda p: (p[0], p[1])):
        if e in usada_esf or sid in usado_spot:
            continue
        usada_esf.add(e)
        usado_spot.add(sid)
        nome = esferas[e][3]
        por_rota[nome] += 1
        arq, a, b = s[0], s[1], s[2]
        tag = textos[arq][a:b]
        fecha = "/>" if tag.endswith("/>") else ">"
        novo = tag[:-len(fecha)].rstrip() + f' walker_id="{route_id(nome)}" walker_index="{por_rota[nome]}" ' + fecha
        edits[arq].append((a, b, novo))
        ligados += 1
    novos = dict(textos)
    for arq, l in edits.items():
        texto = novos[arq]
        for a, b, s in sorted(l, reverse=True):
            texto = texto[:a] + s + texto[b:]
        novos[arq] = texto
    sem_spot = [esf for e, esf in enumerate(esferas) if e not in usada_esf]
    return novos, ligados, ja, sem_spot, sum(1 for c in por_rota.values() if c > 1)


def zonas_do_emulador(base):
    """zona (cName em minúsculas) -> (map id, [arquivos de spawn relativos a static_data])"""
    wm = open(os.path.join(base, "world_maps.xml"), encoding="utf-8").read()
    por_id = collections.defaultdict(list)
    for f in sorted(os.listdir(os.path.join(base, "spawns"))):
        d = os.path.join(base, "spawns", f)
        if os.path.isdir(d):
            for a in sorted(os.listdir(d)):
                m = re.match(r"(\d{9})_.*\.xml$", a)
                if m:
                    por_id[int(m.group(1))].append(f"spawns/{f}/{a}")
    out = {}
    for m in re.finditer(r"<map\b[^>]*>", wm):
        tag = m.group(0)
        c = re.search(r'cName="([^"]*)"', tag)
        i = int(re.search(r'\bid="(\d+)"', tag).group(1))
        if c and c.group(1).lower() not in out:
            out[c.group(1).lower()] = (i, por_id.get(i, []))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zona", nargs="+", help="zonas do source_sphere (ex.: tiamat_down); sem isto, todas as que o emulador tem")
    ap.add_argument("--tolerancia", type=float, default=3.0, help="distância máxima do spot à linha da rota (m)")
    ap.add_argument("--tolerancia-z", type=float, default=5.0, help="diferença máxima de altura entre o spot e a rota (m)")
    ap.add_argument("--parados", help="JSON {parados: {mapa: [[npc, x, y]]}}: objeto oficial visto parado no mesmo ponto por > 30 s "
                                     "sem S_MOVE; o spot do mesmo npc a 0,5 m dele não recebe rota")
    ap.add_argument("--substitui-rotas", action="store_true",
                    help="o waypoint.csv manda: rota do npc_walker.xml com outro traçado x/y é trocada pela do csv e a que falta é "
                         "criada (lista em rotas_substituidas_waypoint.txt, para desfazer)")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    from lxml import etree
    rotas_csv = le_waypoints()
    n2id = nomes_npc()
    bases = (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR)
    zonas = zonas_do_emulador(bases[0])
    with open(os.path.join(WORLD, "source_sphere.csv"), encoding="utf-8-sig", newline="") as f:
        com_rota = sorted({x[2].lower() for x in csv.reader(f) if x[0] != "name" and len(x) > 7 and x[7]})
    alvo = [z.lower() for z in args.zona] if args.zona else com_rota
    walker_novo = {}
    if args.substitui_rotas:
        relatorio = []
        for b in bases:
            walker_novo[b], relatorio = substitui_rotas(b, rotas_csv)
        print(f"npc_walker.xml: {sum(1 for r in relatorio if r[0] == 'trocada')} rotas trocadas pelo waypoint.csv, "
              f"{sum(1 for r in relatorio if r[0] == 'nova')} novas")
    rotas_srv = {b: (le_npc_walker_texto(walker_novo[b]) if b in walker_novo else le_npc_walker(b)) for b in bases}
    import json
    parados = json.load(open(args.parados, encoding="utf-8"))["parados"] if args.parados else {}
    gravar, total = [], collections.Counter()
    for zona in alvo:
        if zona in ZONAS_CAPTURA and not args.zona:
            print(f"{zona}: pulada (movimento pelas capturas)")
            continue
        if zona not in zonas or not zonas[zona][1]:
            print(f"{zona}: sem mapa/spawn no emulador")
            continue
        mapa, arquivos = zonas[zona]
        esferas, sem_npc = le_esferas(zona, n2id)
        # só a rota que o npc_walker tem com o mesmo x/y do waypoint.csv (o z foi colado no geo em parte das rotas, de propósito);
        # rota com outro traçado (herdada da 4.x ou refeita pela captura) fica de fora
        ok = {n for n in {e[3] for e in esferas} if all(rota_igual(rotas_srv[b].get(route_id(n)), rotas_csv[n]) for b in bases)}
        if args.substitui_rotas:   # o npc_walker já foi refeito pelo csv: toda rota da zona vale
            ok = {e[3] for e in esferas}
        divergentes = [e for e in esferas if e[3] not in ok]
        esferas = [e for e in esferas if e[3] in ok]
        total.update(rota_divergente=len(divergentes))
        resultados = []
        for base in bases:
            rotas = rotas_srv[base]
            textos = {arq: open(os.path.join(base, arq), encoding="utf-8", newline="").read() for arq in arquivos}
            novos, ligados, ja, sem_spot, grupos = processa(textos, esferas, rotas, args.tolerancia, parados.get(str(mapa), ()),
                                                            args.tolerancia_z)
            xsd = etree.XMLSchema(etree.parse(os.path.join(base, "spawns", "spawns.xsd")))
            for arq, novo in novos.items():
                if novo != textos[arq] and not xsd.validate(etree.fromstring(novo.encode("utf-8"))):
                    sys.exit(f"ABORTADO: {base}/{arq} não valida: {xsd.error_log.last_error}")
            resultados.append((base, textos, novos, ligados, ja, sem_spot, grupos))
        _, _, novos0, ligados, ja, sem_spot, grupos = resultados[0]
        difere = any(r[3:] != resultados[0][3:] or
                     any((r[2][a] != r[1][a]) != (novos0[a] != resultados[0][1][a]) for a in arquivos) for r in resultados[1:])
        total.update(esferas=len(esferas), ligados=ligados, ja=ja, sem_spot=len(sem_spot))
        print(f"{zona} ({mapa}): {len(esferas)} esferas com rota -> {ligados} ligados, {ja} já tinham a rota, "
              f"{len(sem_spot)} sem spot livre; patrulhas {grupos}"
              + (f"; sem npc no cliente: {sum(sem_npc.values())}" if sem_npc else "")
              + (f"; rota diferente do csv: {len(divergentes)}" if divergentes else "")
              + ("  ** ÁRVORES COM RESULTADO DIFERENTE **" if difere else ""))
        for base, textos, novos, *_ in resultados:
            for arq in arquivos:
                if novos[arq] != textos[arq]:
                    gravar.append((arq, os.path.join(base, arq), novos[arq]))
    print(f"TOTAL: {dict(total)}")
    if not args.aplicar:
        print("Simulação: nada gravado. Rode com --aplicar para gravar.")
        return
    if walker_novo:
        rel = os.path.join("npc_walker", "npc_walker.xml")
        for b, texto in walker_novo.items():
            xsd = etree.XMLSchema(etree.parse(os.path.join(b, "npc_walker", "npc_walker.xsd")))
            if not xsd.validate(etree.fromstring(texto.encode("utf-8"))):
                sys.exit(f"ABORTADO: npc_walker.xml novo não valida em {b}: {xsd.error_log.last_error}")
        backup_manager.backup_file_before_modification(rel)
        for b, texto in walker_novo.items():
            with open(os.path.join(b, rel), "w", encoding="utf-8", newline="") as f:
                f.write(texto)
        with open(os.path.join(AQUI, "rotas_substituidas_waypoint.txt"), "w", encoding="utf-8") as f:
            f.write("# rotas do npc_walker.xml trocadas/criadas pelo waypoint.csv (liga_50_rotas_source_sphere.py --substitui-rotas)\n"
                    "# situacao route_id nome passos_antes passos_depois\n")
            for r in relatorio:
                f.write(" ".join(map(str, r)) + "\n")
        print(f"npc_walker.xml gravado ({len(relatorio)} rotas na lista rotas_substituidas_waypoint.txt)")
    for arq in sorted({a for a, _, _ in gravar}):
        backup_manager.backup_file_before_modification(arq)
    for arq, caminho, novo in gravar:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
    print(f"gravados {len(gravar)} arquivos")


if __name__ == "__main__":
    main()
