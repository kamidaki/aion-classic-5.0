"""Confere o npc_templates.xml contra o S_PUT_NPC oficial de um mapa, campo a campo (independente do fix_50_npc_captura.py).

Uso: verifica_template_captura.py <captura decodificada .pkl> <mapa> [npc_templates.xml] [--csv saida.csv]

Campos do S_PUT_NPC (opcode 14): npc D@16, tipo C@24, título D@32, criador D@43, nome do dono UTF-16 a partir de 47, depois
[C][D maxHp][C level][D máscara de equipamento][20 b por item] e a cauda de 48 b [F raio][F altura][F velocidade][H attack_speed].
Velocidade só informativa (é a do estado em que o NPC estava). NPC invocado por jogador fica de fora.
"""
import collections, csv, math, os, pickle, re, struct, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.normpath(os.path.join(AQUI, "../../../../Código Fonte - Emulador/game-server/data/static_data/npcs/npc_templates.xml"))


def le_put(p):
    if len(p) < 107:
        return None
    npc = struct.unpack_from("<I", p, 16)[0]
    criador = struct.unpack_from("<I", p, 43)[0]
    off = 47
    while p[off:off + 2] != b"\0\0":
        off += 2
        if off + 2 > len(p):
            return None
    if criador or off > 47:
        return None
    off += 2
    maxhp, lvl = struct.unpack_from("<I", p, off + 1)[0], p[off + 5]
    n = bin(struct.unpack_from("<I", p, off + 6)[0]).count("1")
    cauda = off + 10 + 20 * n
    if len(p) - cauda != 48:
        return None
    raio, alt, vel, atk = struct.unpack_from("<fffH", p, cauda)
    return dict(npc=npc, level=lvl, maxHp=maxhp, title_id=struct.unpack_from("<I", p, 32)[0], attack_speed=atk,
                height=round(alt, 3), raio=round(raio, 3), velocidade=round(vel, 2),
                equipment=tuple(struct.unpack_from("<I", p, off + 10 + 20 * i)[0] for i in range(n)))


def templates(arq):
    x = open(arq, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'(?s)<npc_template\b([^>]*)>(.*?)</npc_template>|<npc_template\b([^>]*)/>', x):
        cab, corpo = (m.group(1), m.group(2)) if m.group(1) is not None else (m.group(3), "")
        g = lambda k, d=None: (re.search(r'\b%s="([^"]*)"' % k, cab) or [None, d])[1]
        hp = re.search(r'<stats maxHp="(\d+)"', corpo)
        br = re.search(r'<bound_radius front="([^"]*)" side="([^"]*)"', corpo)
        walk = re.search(r'<speeds[^>]*\bwalk="([^"]*)"', corpo)
        run = re.search(r'<speeds[^>]*\brun="([^"]*)"', corpo)
        out[int(g("npc_id"))] = dict(
            nome=g("name_en", ""), level=int(g("level", 0)), maxHp=int(hp.group(1)) if hp else None,
            title_id=int(g("title_id", 0)), attack_speed=int(g("attack_speed", 2000)), height=round(float(g("height", 0)), 3),
            raio=round(max(float(br.group(1)), float(br.group(2))), 3) if br else None,
            equipment=tuple(int(i) for i in re.findall(r"<item>(\d+)</item>", (re.search(r"(?s)<equipment>(.*?)</equipment>", corpo) or [None, ""])[1])),
            walk=float(walk.group(1)) if walk else None, run=float(run.group(1)) if run else None)
    return out


def main():
    a = [v for v in sys.argv[1:] if not v.startswith("--")]
    saida_csv = sys.argv[sys.argv.index("--csv") + 1] if "--csv" in sys.argv else None
    if saida_csv in a:
        a.remove(saida_csv)
    pkl, mapa = a[0], int(a[1])
    tpl = templates(a[2] if len(a) > 2 else TEMPLATES)
    P = pickle.load(open(pkl, "rb"))
    no_mapa, oficial = None, collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for t, s, op, p in P:
        if not s:
            continue
        if op == 15 and len(p) >= 4:
            no_mapa = struct.unpack_from("<I", p, 0)[0]
        elif op == 14 and no_mapa == mapa:
            d = le_put(p)
            if d:
                for k, v in d.items():
                    if k != "npc":
                        oficial[d["npc"]][k][v] += 1
    campos = ("level", "maxHp", "title_id", "attack_speed", "height", "raio", "equipment")
    ok, ruim, varia, linhas = collections.Counter(), collections.Counter(), [], []
    sem_tpl = []
    for npc in sorted(oficial):
        o = oficial[npc]
        if npc not in tpl:
            sem_tpl.append(npc)
            continue
        t = tpl[npc]
        for c in campos:
            if len(o[c]) > 1:
                varia.append((npc, c, dict(o[c])))
                continue
            v = next(iter(o[c]))
            if c == "equipment":       # o servidor guarda por slot (TreeMap em NpcEquippedGear): a ordem do XML não chega ao cliente
                igual = sorted(v) == sorted(t[c])
            else:
                igual = (abs(v - t[c]) <= 0.011) if isinstance(v, float) and t[c] is not None else v == t[c]
            (ok if igual else ruim)[c] += 1
            if not igual:
                linhas.append([npc, t["nome"], c, t[c], v])
        vel = sorted(o["velocidade"])
        linhas_vel = [x for x in vel if t["walk"] is not None and not (abs(x - t["walk"]) < .02 or (t["run"] and abs(x - t["run"]) < .02))]
        if linhas_vel:
            linhas.append([npc, t["nome"], "velocidade (info)", f"walk {t['walk']} run {t['run']}", " ".join(map(str, vel))])
    print(f"mapa {mapa}: {len(oficial)} tipos de NPC no S_PUT_NPC oficial, {len(sem_tpl)} sem template {sem_tpl[:20]}")
    print(f"{'campo':14s} {'igual':>6s} {'difere':>6s}")
    for c in campos:
        print(f"{c:14s} {ok[c]:6d} {ruim[c]:6d}")
    if varia:
        print("valor variando entre aparições (não conferido):", varia[:10])
    for l in linhas[:60]:
        print("   ", *l)
    if len(linhas) > 60:
        print(f"    ... mais {len(linhas) - 60}")
    if saida_csv:
        with open(saida_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["npc", "nome", "campo", "template", "oficial"])
            w.writerows(linhas)


if __name__ == "__main__":
    main()
