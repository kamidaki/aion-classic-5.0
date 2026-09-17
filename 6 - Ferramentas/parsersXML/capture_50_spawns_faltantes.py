#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
capture_50_spawns_faltantes.py

Acrescenta ao spawn de um mapa os pontos de mob/NPC que as capturas oficiais 5.0 mostram e o arquivo nao tem.
So acrescenta: spot que ja existe (ate R_EXISTE do ponto da captura, um para um) nao muda.

Diferente do capture_50_npc_spawns.py, que so aceita NPC parado, este aceita mob que anda, que e quase todo mob de
campo. Le todas as capturas (inclusive as sem S_KEY) e separa cada sessao em trechos pelo S_WORLD (0x0F). Trecho sem
S_WORLD -- o comeco de captura sem S_KEY -- recebe o mapa por votacao dos npcIds contra os arquivos de spawn.

Ponto de cada objeto (npcId + objectId na sessao)
------------------------------------------------
  nascimento visto (S_PUT_NPC p[-32] == 1)   x/y/z/h exatos do pacote
  senao                                       centro das posicoes vistas e dos alvos de andar aleatorio (S_MOVE_NEW
                                              0xE0/0xE2/0xE4); z do ponto visto mais perto do centro, h do 1o put.
                                              Em NPC visto nascer e depois andar, o erro medido foi de 0,3 m com 60
                                              alvos e de 1-7 m com ~10 (comportamento oficial, 2026-09-13).
Objetos vivos ao mesmo tempo na mesma sessao sao spots distintos. Objetos de sessoes diferentes, ou de uma morte
(S_REMOVE_OBJECT com animacao != 0) seguida de outro objeto, viram um spot so quando ficam a ate R_FUNDE.

random_walk por npcId: 0 se nenhum objeto andou; senao 5 ou 10, pelo p90 do espalhamento dos pontos (Tiamaranta
agrupa nesses dois raios; o raio nao sai da velocidade). Acima de LIMITE_ROTA o NPC anda por rota: so entra o ponto de
nascimento, sem random_walk, e o resto sai no relatorio como candidato a rota. respawn_time: o do proprio npc no mapa, senao o mais comum
do mapa -- nao ha morte seguida de nascimento suficiente nas capturas para medir.

Uso:
    python capture_50_spawns_faltantes.py --mapa 800040000 --npc 221092-221107 220582-220585            (mostra)
    python capture_50_spawns_faltantes.py --mapa 800040000 --npc 221092-221107 220582-220585 --aplicar  (grava)
"""

import argparse
import collections
import glob
import math
import os
import re
import statistics
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "6 - Ferramentas"))
sys.path.insert(0, AQUI)
import aion_pcap  # noqa: E402
import backup_manager  # noqa: E402

CAPTURAS = os.path.join(RAIZ, "5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0")
CLIENT_NPCS = os.path.join(RAIZ, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos", "data", "npcs",
                           "client_npcs.xml")
ARVORES = (("fonte", os.path.join(RAIZ, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data")),
           ("produto", os.path.join(RAIZ, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data")))
RELATORIO = os.path.join(AQUI, "relatorio_spawns_faltantes_50.txt")
R_EXISTE = 15.0          # ponto da captura ate essa distancia de um spot do arquivo = spot ja existe
R_FUNDE = 12.0           # objetos que nao coexistiram, ate essa distancia = mesmo spot
ANDAR = (0xE0, 0xE2, 0xE4)
MIN_PONTOS_RAIO = 3
RAIO_CURTO, RAIO_LONGO, LIMITE_RAIO = 5, 10, 7.0
LIMITE_ROTA = 30.0      # espalhamento acima disso e rota (Roamer, refugiado), nao andar aleatorio em volta do spawn


# ---------------------------------------------------------------- capturas
def trechos_do_mapa(mapa, npc_mapas):
    """Cada trecho de sessao no mapa pedido: (nome da captura, lista de eventos (t, tipo, dados))."""
    for pasta, _, arquivos in sorted(os.walk(CAPTURAS)):
        for arq in sorted(a for a in arquivos if a.endswith(".pcapng")):
            for s in aion_pcap.abre_todas(os.path.join(pasta, arq), sem_skey=True):
                trechos, atual = [], dict(mapa=None, ev=[])
                for (op, p, ok), t in zip(s["servidor"], s["tempo_servidor"]):
                    if not ok:
                        continue
                    if op == 0x0F and len(p) >= 8:
                        trechos.append(atual)
                        m0, m1 = struct.unpack_from("<II", p, 0)
                        atual = dict(mapa=m0 if 100000000 <= m0 < 1000000000 else m1, ev=[])
                    elif op == 0x0E and len(p) >= 107:
                        x, y, z, oid, npc = struct.unpack_from("<fffII", p, 0)
                        if struct.unpack_from("<I", p, 43)[0]:
                            continue                                  # invocacao de jogador
                        cauda = p[-48:]
                        atual["ev"].append((t, "put", dict(oid=oid, npc=npc, x=x, y=y, z=z, h=p[27], nasceu=cauda[16] == 1,
                                                           alvo=struct.unpack_from("<fff", cauda, 17), mm=cauda[29])))
                    elif op == 0x37 and len(p) >= 18:
                        oid, x, y, z, _h, mm = struct.unpack_from("<IfffBB", p, 0)
                        alvo = struct.unpack_from("<fff", p, 18) if len(p) >= 30 and mm in ANDAR else None
                        atual["ev"].append((t, "move", dict(oid=oid, x=x, y=y, z=z, alvo=alvo)))
                    elif op == 0x16 and len(p) >= 5:
                        atual["ev"].append((t, "remove", dict(oid=struct.unpack_from("<I", p, 0)[0], anim=p[4])))
                trechos.append(atual)
                for tr in trechos:
                    if not tr["ev"]:
                        continue
                    if tr["mapa"] is None:
                        votos = collections.Counter(m for _, k, d in tr["ev"] if k == "put" for m in npc_mapas.get(d["npc"], ()))
                        tr["mapa"] = votos.most_common(1)[0][0] if votos else None
                    if tr["mapa"] == mapa:
                        yield arq, tr["ev"]


def objetos(mapa, alvos, npc_mapas):
    """Um dict por objeto dos npcIds pedidos: pontos, alvos de andar, nascimento, janela de vida."""
    saida = []
    for n_trecho, (arq, eventos) in enumerate(trechos_do_mapa(mapa, npc_mapas)):
        vivos = {}
        for t, tipo, d in eventos:
            o = vivos.get(d["oid"])
            if tipo == "put":
                if d["npc"] not in alvos:
                    continue
                if o is None:
                    o = vivos[d["oid"]] = dict(npc=d["npc"], trecho=n_trecho, captura=arq, pontos=[], alvos=[], nascimento=None,
                                               h=d["h"], inicio=t, fim=t, morreu=False)
                    saida.append(o)
                o["pontos"].append((d["x"], d["y"], d["z"]))
                if d["mm"] in ANDAR and any(d["alvo"]):
                    o["alvos"].append(tuple(d["alvo"]))
                if d["nasceu"] and o["nascimento"] is None:
                    o["nascimento"], o["h"] = (d["x"], d["y"], d["z"]), d["h"]
                o["fim"] = t
            elif o is None:
                continue
            elif tipo == "move":
                o["pontos"].append((d["x"], d["y"], d["z"]))
                if d["alvo"]:
                    o["alvos"].append(tuple(d["alvo"]))
                o["fim"] = t
            elif tipo == "remove":
                o["fim"] = t
                if d["anim"] != 0:
                    o["morreu"] = True
    return saida


def spot_de(o):
    if o["nascimento"]:
        x, y, z = o["nascimento"]
        return dict(x=x, y=y, z=z, h=o["h"], exato=True)
    todos = o["pontos"] + o["alvos"]
    cx, cy = statistics.fmean(p[0] for p in todos), statistics.fmean(p[1] for p in todos)
    z = min(o["pontos"], key=lambda p: math.dist(p[:2], (cx, cy)))[2]
    return dict(x=cx, y=cy, z=z, h=o["h"], exato=False)


def espalhamento(o):
    todos = o["pontos"] + o["alvos"]
    if len(todos) < MIN_PONTOS_RAIO:
        return None
    c = spot_de(o)
    return max(math.dist(p[:2], (c["x"], c["y"])) for p in todos)


def agrupa(objs):
    """Spots distintos de um npcId: objetos que coexistiram nunca se fundem."""
    spots = []
    for o in sorted(objs, key=lambda o: (not o["nascimento"], -len(o["pontos"]) - len(o["alvos"]))):
        s = spot_de(o)
        par = None
        for sp in spots:
            coexistiu = any(m["trecho"] == o["trecho"] and m["inicio"] <= o["fim"] and o["inicio"] <= m["fim"] and not m["morreu"]
                            for m in sp["objetos"])
            if not coexistiu and math.dist((sp["x"], sp["y"], sp["z"]), (s["x"], s["y"], s["z"])) <= R_FUNDE:
                par = sp
                break
        if par:
            par["objetos"].append(o)
            if s["exato"] and not par["exato"]:
                par.update(s)
        else:
            s["objetos"] = [o]
            spots.append(s)
    return spots


# ---------------------------------------------------------------- arquivos
def spawns_do_mapa(base, mapa):
    """npc_id -> spots (x, y, z) em todos os arquivos de spawn do mapa (Npcs, Bases, ...)."""
    out = collections.defaultdict(list)
    for caminho in glob.glob(os.path.join(glob.escape(base), "spawns", "*", "%d_*.xml" % mapa)):
        texto = open(caminho, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'<spawn [^>]*npc_id="(\d+)"[^>]*>(.*?)</spawn>', texto, re.S):
            out[int(m.group(1))] += [tuple(map(float, s)) for s in re.findall(r'x="([^"]+)" y="([^"]+)" z="([^"]+)"', m.group(2))]
    return out


def npc_para_mapas(base):
    out = collections.defaultdict(set)
    for caminho in glob.glob(os.path.join(glob.escape(base), "spawns", "*", "*.xml")):
        m = re.match(r"(\d{9})_", os.path.basename(caminho))
        if m:
            for i in set(re.findall(r'npc_id="(\d+)"', open(caminho, encoding="utf-8", errors="replace").read())):
                out[int(i)].add(int(m.group(1)))
    return out


def nomes(ids):
    texto = open(CLIENT_NPCS, encoding="utf-8", errors="replace").read()
    return {int(i): n for i, n in re.findall(r"<id>(\d+)</id>\s*<name>([^<]+)</name>", texto) if int(i) in ids}


def num(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return s if s else "0"


def ids_de(argumentos):
    out = set()
    for a in argumentos:
        if "-" in a:
            i, f = map(int, a.split("-"))
            out.update(range(i, f + 1))
        else:
            out.add(int(a))
    return out


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mapa", type=int, required=True)
    ap.add_argument("--npc", nargs="+", required=True, help="npcIds ou faixas (221092-221107)")
    ap.add_argument("--aplicar", action="store_true", help="grava as duas arvores (com backup)")
    args = ap.parse_args()
    alvos = ids_de(args.npc)
    base_ref = ARVORES[0][1]

    print("[1/3] Lendo as capturas no mapa %d..." % args.mapa)
    objs = objetos(args.mapa, alvos, npc_para_mapas(base_ref))
    por_npc = collections.defaultdict(list)
    for o in objs:
        por_npc[o["npc"]].append(o)
    nome = nomes(alvos)

    print("[2/3] Montando os spots...")
    novos, rel = {}, ["capture_50_spawns_faltantes.py --mapa %d -- %s" % (args.mapa, "APLICADO" if args.aplicar else "simulacao"), ""]
    existentes = spawns_do_mapa(base_ref, args.mapa)
    for n in sorted(alvos):
        if n not in por_npc:
            rel.append("%d %s: nao aparece nas capturas" % (n, nome.get(n)))
            continue
        spots = agrupa(por_npc[n])
        livres = list(existentes.get(n, []))
        faltam = []
        for s in sorted(spots, key=lambda s: not s["exato"]):
            par = min(livres, key=lambda e: math.dist(e, (s["x"], s["y"], s["z"])), default=None)
            if par is not None and math.dist(par, (s["x"], s["y"], s["z"])) <= R_EXISTE:
                livres.remove(par)
            else:
                faltam.append(s)
        esp = sorted(e for e in (espalhamento(o) for o in por_npc[n]) if e is not None)
        andou = any(o["alvos"] or len({tuple(round(c, 1) for c in p) for p in o["pontos"]}) > 1 for o in por_npc[n])
        p90 = esp[int(len(esp) * 0.9)] if esp else None
        raio = 0 if not andou else (RAIO_CURTO if p90 is not None and p90 <= LIMITE_RAIO else RAIO_LONGO)
        rota = p90 is not None and p90 > LIMITE_ROTA
        if rota:
            # o centro de um caminho longo nao e ponto de spawn: so entra o nascimento visto, parado no lugar
            descartados = sum(1 for s in faltam if not s["exato"])
            faltam, raio = [s for s in faltam if s["exato"]], 0
        novos[n] = dict(spots=faltam, raio=raio)
        linha = "%d %-40s objetos %3d  spots %3d  ja no arquivo %3d  novos %3d (exatos %d)  random_walk %d  p90 espalhamento %s%s" % (
            n, (nome.get(n) or "?")[:40], len(por_npc[n]), len(spots), len(spots) - len(faltam) - (descartados if rota else 0), len(faltam),
            sum(1 for s in faltam if s["exato"]), raio, round(p90, 1) if p90 is not None else "-",
            ("  ROTA: %d ponto(s) sem nascimento descartado(s), candidato a rota pela captura" % descartados) if rota else "")
        print("   " + linha)
        rel.append(linha)
        for s in faltam:
            rel.append("      x=%s y=%s z=%s h=%d %s  objetos=%d capturas=%s" % (num(s["x"]), num(s["y"]), num(s["z"]), s["h"],
                       "exato" if s["exato"] else "centro", len(s["objetos"]), sorted({o["captura"][:40] for o in s["objetos"]})))

    print("[3/3] Gravando em cada arvore...")
    for nome_arv, base in ARVORES:
        arquivos = glob.glob(os.path.join(glob.escape(base), "spawns", "Npcs", "%d_*.xml" % args.mapa))
        if len(arquivos) != 1:
            sys.exit("ABORTADO: esperado 1 arquivo Npcs do mapa em %s, achei %s" % (base, arquivos))
        caminho = arquivos[0]
        texto = open(caminho, encoding="utf-8", newline="").read()
        novo, acrescidos, criados = texto, 0, 0
        respawns = collections.Counter(re.findall(r'respawn_time="(\d+)"', texto))
        respawn_mapa = respawns.most_common(1)[0][0] if respawns else "295"
        blocos_novos = []
        for n, info in sorted(novos.items()):
            if not info["spots"]:
                continue
            linhas = "".join('\t\t\t<spot x="%s" y="%s" z="%s" h="%d"%s/>\n' % (
                num(s["x"]), num(s["y"]), num(s["z"]), s["h"], ' random_walk="%d"' % info["raio"] if info["raio"] else "")
                for s in info["spots"])
            m = re.search(r'(\t*<spawn npc_id="%d"(?![^>]*\b(?:pool|handler)=)[^>]*>)(?:(?!</spawn>).)*?(\t*</spawn>)' % n, novo, re.S)
            if m and "<temporary_spawn" not in m.group(0):
                novo = novo[:m.start(2)] + linhas + novo[m.start(2):]
                acrescidos += len(info["spots"])
            else:
                rt = re.search(r'<spawn npc_id="%d" [^>]*respawn_time="(\d+)"' % n, novo)
                blocos_novos.append('\t\t<!-- %s (capturas oficiais 5.0) -->\n\t\t<spawn npc_id="%d" respawn_time="%s">\n%s\t\t</spawn>\n' % (
                    nome.get(n, "?"), n, rt.group(1) if rt else respawn_mapa, linhas))
                criados += 1
                acrescidos += len(info["spots"])
        if blocos_novos:
            fim = novo.rindex("\t</spawn_map>")
            novo = novo[:fim] + "".join(blocos_novos) + novo[fim:]
        antes, depois = len(re.findall(r"<spot\b", texto)), len(re.findall(r"<spot\b", novo))
        if depois != antes + acrescidos:
            sys.exit("ABORTADO: %s ficaria com %d spots (esperado %d)" % (caminho, depois, antes + acrescidos))
        from lxml import etree
        xsd = etree.XMLSchema(etree.parse(os.path.join(base, "spawns", "spawns.xsd")))
        if not xsd.validate(etree.fromstring(novo.encode("utf-8"))):
            sys.exit("ABORTADO: %s nao valida no spawns.xsd: %s" % (caminho, xsd.error_log.last_error))
        print("   %s: +%d spots (%d <spawn> novos), %d -> %d, valida no spawns.xsd" % (nome_arv, acrescidos, criados, antes, depois))
        if args.aplicar and novo != texto:
            backup_manager.backup_file_before_modification(caminho)
            open(caminho, "w", encoding="utf-8", newline="").write(novo)
    open(RELATORIO, "w", encoding="utf-8", newline="\n").write("\n".join(rel) + "\n")
    print("Relatorio: %s" % RELATORIO)
    if not args.aplicar:
        print("Simulacao: nada gravado. Rode com --aplicar para gravar.")


if __name__ == "__main__":
    main()
