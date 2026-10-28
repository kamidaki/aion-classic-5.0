"""Valida o extrai_spawns_cliente.py contra as capturas oficiais.

Uso: valida_spawns_cliente.py <captura decodificada .pkl> [<mais .pkl> ...]
Para cada S_PUT_NPC oficial (opcode 14: x, y, z, obj, npc; heading no byte 27), procura o spot extraído mais perto do mesmo
NPC no mesmo mapa (mapa pelo opcode 15 ou, sem ele, pelo único mapa extraído que contém o NPC) e mede: distância em x/y,
diferença de z e de heading (para os que estão parados no ponto: < 0,5 m).
"""
import collections, math, os, pickle, struct, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
res = pickle.load(open(os.path.join(AQUI, "extrai_spawns_cliente.pkl"), "rb"))
spots = collections.defaultdict(list)   # (mapa, npc) -> [(x, y, z, h)]
mapas_do_npc = collections.defaultdict(set)
for mapa, (level, grupos, _) in res.items():
    for cat, g in grupos.items():
        for nid, info in g.items():
            for x, y, z, h, rw, zed in info["spots"]:
                spots[(mapa, nid)].append((x, y, z, h, zed))
            mapas_do_npc[nid].add(mapa)

dist, dz, dzed, dh, falta = [], [], [], collections.Counter(), collections.Counter()
vistos = 0
for arq in sys.argv[1:]:
    P = pickle.load(open(arq, "rb"))
    mapa = None
    for t, s, op, p in P:
        if not s:
            continue
        if op == 15 and len(p) >= 4:
            mapa = struct.unpack_from("<I", p, 0)[0]
            continue
        if op != 14 or len(p) < 40:
            continue
        x, y, z, o, n = struct.unpack_from("<fffII", p, 0)
        h = p[27]
        m = mapa if mapa in res else (next(iter(mapas_do_npc[n])) if len(mapas_do_npc[n]) == 1 else None)
        if m is None or m not in res:
            continue
        vistos += 1
        c = spots.get((m, n))
        if not c:
            falta[n] += 1
            continue
        b = min(c, key=lambda q: math.hypot(q[0] - x, q[1] - y))
        d = math.hypot(b[0] - x, b[1] - y)
        dist.append(d)
        if d < 0.5:
            dz.append(z - b[2])
            dzed.append(z - b[4])
            e = (h - b[3]) % 120
            dh[min(e, 120 - e)] += 1


def q(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))] if v else float("nan")


print(f"S_PUT_NPC oficiais nos mapas extraídos: {vistos}")
print(f"  NPC sem nenhum spot extraído: {sum(falta.values())} ({len(falta)} tipos; ex.: {falta.most_common(6)})")
if dist:
    print(f"  distância ao spot mais perto: mediana {q(dist, .5):.2f} m | <0,5 m {100 * sum(d < .5 for d in dist) / len(dist):.1f}% | "
          f"<3 m {100 * sum(d < 3 for d in dist) / len(dist):.1f}% | <10 m {100 * sum(d < 10 for d in dist) / len(dist):.1f}%")
if dz:
    print(f"  parados no ponto (<0,5 m): {len(dz)}")
    print(f"    z oficial - z extraído (piso):  mediana {q(dz, .5):+.3f} | p5 {q(dz, .05):+.3f} | p95 {q(dz, .95):+.3f} | |dz|<0,15 {100 * sum(abs(v) < .15 for v in dz) / len(dz):.1f}%")
    print(f"    z oficial - z do editor (cru):  mediana {q(dzed, .5):+.3f} | p5 {q(dzed, .05):+.3f} | p95 {q(dzed, .95):+.3f} | |dz|<0,15 {100 * sum(abs(v) < .15 for v in dzed) / len(dzed):.1f}%")
    tot = sum(dh.values())
    print(f"    heading: igual {100 * dh[0] / tot:.1f}% | +-1 {100 * (dh[0] + dh[1]) / tot:.1f}% | distribuição {sorted(dh.items())[:8]}")
