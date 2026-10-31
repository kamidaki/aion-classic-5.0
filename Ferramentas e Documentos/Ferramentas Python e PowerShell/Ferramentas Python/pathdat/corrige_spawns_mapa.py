"""Corrige a posição dos spots de um arquivo de spawn de um mapa: captura oficial primeiro, depois geo + grade (path.dat).

Uso: corrige_spawns_mapa.py <mapa> <geo.txt> <captura.pkl>[,<mais .pkl>] <arquivo de spawn> [<mais arquivos iguais>]
                            [--exclui-npc arquivo_de_ids] [--cliente extrai_spawns_cliente.pkl] [--pontos saida.txt]
                            [--aplica] [--relatorio saida.csv]

<geo.txt>: saída do GeoZ.java (Ferramentas Java/pathdat) para todos os spots do arquivo: "x y z abaixo acima", onde
"abaixo" é a primeira superfície de colisão do geo do servidor de z+1 para baixo.
Captura .pkl: [(t, servidor, opcode, payload)] decodificado; o mapa vem do opcode 15 (ou, sem nenhum, a captura toda é do mapa).

Altura de referência: com --cliente, o z do editor do cliente (mission_mission0.xml) do mesmo NPC a até 1 m em x/y;
sem ponto do cliente, o z do próprio spot. Assim um spot levado para outro andar (o //fixspawn antigo gravava o z do
jogador: mob da ilha ia para a base embaixo e vice-versa) volta para o chão debaixo do ponto do editor.
--pontos grava "x y z_referência" de cada spot para rodar o GeoZ antes.

Por spot (fora os NPCs de --exclui-npc, que ficam como estão):
  1. NPC visto na captura num ponto fixo a até 1 m (todas as aparições do objeto no mesmo x/y e heading):
     spot parado -> x/y/z/h oficiais; spot com rota/andar aleatório -> só o z oficial.
     Com aparição de nascimento (S_PUT_NPC com flag de spawn) a até 1 m, o z dela.
  2. Tipo que voa no oficial (mediana de z - piso > 1 m nas capturas ou no oficial_altura_por_npc.pkl) ou aerial_spawn: mantém.
  3. Chão (calibrado em 3.414 pontos oficiais de Tiamaranta Mesa: onde o NPC está no chão, o geo acerta 2.994 e a grade
     2.954; o geo pega também 41 sobre estrutura/convés que a grade não tem):
     - piso livre da grade a até 0,3 m da referência: z = piso;
     - piso da grade acima da referência, a até 6 m (spot enterrado): z = esse piso;
     - senão z = superfície do geo logo abaixo da referência (encaixada no piso da grade se estiver a até 0,3 m dele),
       sem limite de queda (Ignore_heightcheck=0: frutas e baús de Tiamaranta, com o ponto do editor 80+ m acima do chão,
       aparecem no chão nas capturas); sem superfície nenhuma embaixo fica no relatório, sem mudar.
"""
import argparse, collections, csv, math, os, pickle, re, struct, sys

from pathdat_50 import PathDat

AQUI = os.path.dirname(os.path.abspath(__file__))
OF_ALT = pickle.load(open(os.path.join(AQUI, "oficial_altura_por_npc.pkl"), "rb"))
QUEDA_MAX = float("inf")   # o cliente cola no chão sem limite: frutas e baús com o editor 80+ m acima ficam no chão no oficial


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def oficiais(pkls, mapa):
    """npc -> [objeto: [(x, y, z, h, nascimento)]]"""
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    for pkl in pkls:
        P = pickle.load(open(pkl, "rb"))
        tem15 = any(s and op == 15 for _, s, op, _ in P)
        no = None if tem15 else mapa
        for t, s, op, p in P:
            if not s:
                continue
            if op == 15 and len(p) >= 4:
                no = struct.unpack_from("<I", p, 0)[0]
            elif op == 14 and no == mapa and len(p) > 47:
                if struct.unpack_from("<I", p, 43)[0] or p[47:49] != b"\0\0":     # invocado por jogador
                    continue
                x, y, z, o, n = struct.unpack_from("<fffII", p, 0)
                out[n][(pkl, o)].append((x, y, z, p[27], p[-32] == 1))
    return {n: list(v.values()) for n, v in out.items()}


def pisos_livres(M, x, y):
    fl = [q[0] for q in M.pisos(x, y) if q[1] and not math.isnan(q[0])]
    if not fl:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                fl += [q[0] for q in M.pisos(x + dx * 0.5, y + dy * 0.5) if q[1] and not math.isnan(q[0])]
    return fl


def altura_oficial(M, of):
    """npc -> mediana de (z - piso mais perto) das aparições oficiais (99 sem piso)."""
    out = {}
    for n, objs in of.items():
        ds = []
        for v in objs:
            x, y, z = v[0][:3]
            fl = pisos_livres(M, x, y)
            ds.append(z - min(fl, key=lambda q: abs(q - z)) if fl else 99)
        ds.sort()
        out[n] = ds[len(ds) // 2]
    return out


def referencia(cli, npc, X, Y, Z):
    """z do editor do cliente para o mesmo NPC a até 1 m (o mais perto em x/y); sem ponto, o z do spot."""
    m = [q for q in cli.get(npc, ()) if math.hypot(q[0] - X, q[1] - Y) <= 1.0]
    # arredondado como vai para o arquivo de pontos do GeoZ (a chave do geo é o texto relido)
    return float(fmt(min(m, key=lambda q: math.hypot(q[0] - X, q[1] - Y))[2])) if m else Z


def decide(M, geo, of, voa, npc, X, Y, Z, tag, R):
    """R = altura de referência (z do editor do cliente ou o z do spot)."""
    """(caso, novos atributos {x,y,z,h} ou None)"""
    anda = "walker_id" in tag or "random_walk" in tag
    objs = of.get(npc, [])
    melhor = None
    for v in objs:
        fixo = max(math.hypot(a[0] - v[0][0], a[1] - v[0][1]) for a in v) <= 0.3 and len({a[3] for a in v}) == 1
        for a in v:
            d = math.hypot(a[0] - X, a[1] - Y)
            if d <= 1.0 and (fixo or a[4]) and (melhor is None or d < melhor[0]):
                melhor = (d, a, fixo)
    if melhor:
        _, a, fixo = melhor
        if fixo and not anda:
            return "captura: ponto fixo", dict(x=a[0], y=a[1], z=a[2], h=a[3])
        return "captura: z do nascimento/ponto", dict(z=a[2])
    if 'aerial_spawn="true"' in tag:
        return "mantém: aerial_spawn", None
    alt = voa.get(npc, OF_ALT.get(npc))
    if alt is not None and alt > 1:
        return "mantém: voa no oficial", None
    fl = pisos_livres(M, X, Y)
    outro = " (outro andar)" if abs(R - Z) > 30 else ""
    if fl:
        f = min(fl, key=lambda q: abs(q - R))
        if abs(f - R) <= 0.3:
            if abs(f - Z) <= 0.05:
                return "já no chão", None
            return "chão: piso da grade" + outro, dict(z=f)
        acima = [q for q in fl if R < q <= R + 6]
        if acima:
            return "chão: estava enterrado" + outro, dict(z=min(acima))
    g = geo.get((X, Y, R))
    if g is None:
        raise SystemExit("falta o geo de (%s, %s, %s): rode --pontos e o GeoZ" % (X, Y, R))
    if math.isnan(g):
        return "sem decisão: geo sem superfície abaixo", None
    if R - g > QUEDA_MAX:
        return "sem decisão: queda acima do limite", None
    if fl:
        f = min(fl, key=lambda q: abs(q - g))
        if abs(f - g) <= 0.3:
            g = f
    if abs(g - Z) <= 0.05:
        return "já no chão (geo)", None
    return ("chão: geo abaixo" + (" >6 m" if Z - g > 6 else "") + outro), dict(z=g)


def processa(texto, M, geo, of, voa, excluir, cont, rel, arq, cli, pontos=None):
    msk = re.sub(r"(?s)<!--.*?-->", lambda m: " " * len(m.group(0)), texto)
    edits = []
    for sm in re.finditer(r'(?s)<spawn\b[^>]*npc_id="(\d+)"[^>]*>(.*?)</spawn>', msk):
        npc = int(sm.group(1))
        for sp in re.finditer(r"<spot\b[^>]*>", sm.group(2)):
            ini = sm.start(2) + sp.start()
            tag = texto[ini:ini + len(sp.group(0))]
            g = lambda k: re.search(r'\b%s="([-\d.eE]+)"' % k, tag)
            X, Y, Z = (float(g(k).group(1)) for k in "xyz")
            if npc in excluir:
                cont["fora: sistema de torres"] += 1
                continue
            R = referencia(cli, npc, X, Y, Z)
            if pontos is not None:
                pontos.add((g("x").group(1), g("y").group(1), fmt(R) if R != Z else g("z").group(1)))
                continue
            caso, novo = decide(M, geo, of, voa, npc, X, Y, Z, tag, R)
            cont[caso] += 1
            if novo is None:
                if caso.startswith("sem decisão") and rel is not None:
                    rel.writerow([os.path.basename(arq), npc, fmt(X), fmt(Y), fmt(Z), "", "", caso])
                continue
            t2 = tag
            for k, v in novo.items():
                val = str(v) if k == "h" else fmt(v)
                if re.search(r'\b%s="' % k, t2):
                    t2 = re.sub(r'(\b%s=")[^"]*(")' % k, lambda m: m.group(1) + val + m.group(2), t2, count=1)
            if t2 != tag:
                edits.append((ini, ini + len(tag), t2))
                if rel is not None and abs(novo.get("z", Z) - Z) > 1:
                    rel.writerow([os.path.basename(arq), npc, fmt(X), fmt(Y), fmt(Z), fmt(novo["z"]), f"{novo['z'] - Z:+.2f}", caso])
    for i, f, s in sorted(edits, reverse=True):
        texto = texto[:i] + s + texto[f:]
    return texto, len(edits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mapa", type=int)
    ap.add_argument("geo")
    ap.add_argument("capturas")
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("--exclui-npc")
    ap.add_argument("--aplica", action="store_true")
    ap.add_argument("--relatorio")
    ap.add_argument("--cliente")
    ap.add_argument("--pontos")
    a = ap.parse_args()
    M = PathDat(a.mapa)
    cli = collections.defaultdict(list)
    if a.cliente:
        for cat in pickle.load(open(a.cliente, "rb"))[a.mapa][1].values():
            for nid, i in cat.items():
                cli[nid] += [(s[0], s[1], s[5]) for s in i["spots"]]
    if a.pontos:
        pts = set()
        for arq in a.arquivos:
            processa(open(arq, encoding="utf-8", newline="").read(), M, {}, {}, {}, set(), collections.Counter(), None, arq, cli, pts)
        open(a.pontos, "w").write("".join("%s %s %s\n" % p for p in sorted(pts)))
        print(f"{len(pts)} pontos em {a.pontos}")
        return
    geo = {}
    for l in open(a.geo, encoding="utf-8"):
        v = l.split()
        if len(v) >= 4:
            geo[(float(v[0]), float(v[1]), float(v[2]))] = float(v[3])
    of = oficiais(a.capturas.split(","), a.mapa)
    voa = altura_oficial(M, of)
    excluir = set()
    if a.exclui_npc:
        excluir = {int(x) for x in open(a.exclui_npc).read().split()}
    print(f"captura: {len(of)} tipos de NPC, {sum(1 for v in voa.values() if v > 1)} voam; excluídos: {len(excluir)} tipos")
    rel, fr = None, None
    if a.relatorio:
        fr = open(a.relatorio, "w", encoding="utf-8", newline="")
        rel = csv.writer(fr, delimiter=";")
        rel.writerow(["arquivo", "npc", "x", "y", "z_antigo", "z_novo", "dz", "caso"])
    saidas = []
    for arq in a.arquivos:
        cont = collections.Counter()
        txt = open(arq, encoding="utf-8", newline="").read()
        novo, n = processa(txt, M, geo, of, voa, excluir, cont, rel if not saidas else None, arq, cli)
        saidas.append(novo)
        print(arq[-70:], f"{n} spots alterados")
        for k, v in sorted(cont.items()):
            print(f"   {v:6d}  {k}")
        if a.aplica and novo != txt:
            open(arq, "w", encoding="utf-8", newline="").write(novo)
    if len(set(saidas)) > 1:
        print("ATENÇÃO: os arquivos ficaram diferentes entre si")
    if fr:
        fr.close()


if __name__ == "__main__":
    sys.exit(main())
