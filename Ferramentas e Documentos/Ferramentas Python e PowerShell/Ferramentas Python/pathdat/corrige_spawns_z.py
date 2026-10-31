"""Corrige o z dos spots de spawn pelo piso da grade oficial (path.dat).

Uso: corrige_spawns_z.py <pasta static_data/spawns> [--aplica] [--relatorio arquivo.csv]
Sem --aplica só simula. Statics ficam de fora (objetos podem estar em cima de mesa, parede etc.).

Regra (27/10/2026): nas capturas oficiais os NPCs de chão ficam no piso da grade a +-3 cm.
  - mantém: spot com aerial_spawn="true"; tipo de NPC que o oficial põe no ar (mediana > 1 m acima do piso) ou em dúvida
    (0,3-1 m); tipo nunca capturado e mais de 10 m acima do piso (pode voar); sem piso livre a até 0,5 m;
  - corrige: z = piso livre mais perto (na célula; se ela não tiver piso, nas 8 vizinhas — borda/parede).
Altura oficial por tipo: oficial_altura_por_npc.pkl (mediana de z - piso dos S_PUT_NPC de todas as capturas).
"""
import argparse, csv, glob, math, os, pickle, re

from pathdat_50 import PathDat

AQUI = os.path.dirname(os.path.abspath(__file__))
OF = pickle.load(open(os.path.join(AQUI, "oficial_altura_por_npc.pkl"), "rb"))
_mapas = {}


def mapa(m):
    if m not in _mapas:
        try:
            _mapas[m] = PathDat(m)
        except Exception:
            _mapas[m] = None
    return _mapas[m]


def mascara(texto):
    """Mesmo texto com os comentários trocados por espaços (posições iguais)."""
    return re.sub(r"(?s)<!--.*?-->", lambda m: " " * len(m.group(0)), texto)


def fmt(z):
    s = f"{z:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def decide(M, npc, X, Y, Z, spot):
    if 'aerial_spawn="true"' in spot:
        return "mantém: marcado aéreo", None
    of = OF.get(npc)
    if of is not None and of > 1:
        return "mantém: voa no oficial", None
    if of is not None and of > 0.3:
        return "mantém: dúvida no oficial", None
    if not (0 <= X < M.tam and 0 <= Y < M.tam):
        return "mantém: fora do mapa", None
    fl = [p[0] for p in M.pisos(X, Y) if p[1] and not math.isnan(p[0])]
    borda = False
    if not fl:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                fl += [p[0] for p in M.pisos(X + dx * 0.5, Y + dy * 0.5) if p[1] and not math.isnan(p[0])]
        if not fl:
            return "mantém: sem piso a 0,5 m", None
        borda = True
    d = min(fl, key=lambda z: abs(z - Z))
    dz = d - Z
    if abs(dz) <= 0.05:
        return "já no chão", None
    if dz < -10 and of is None:
        return "mantém: >10 m acima, tipo sem captura", None
    return "corrige" + (" (borda)" if borda else "") + (" desce" if dz < 0 else " sobe") + (" >6 m" if abs(dz) > 6 else ""), d


def processa(arq, aplica, rel, cont):
    txt = open(arq, encoding="utf-8", newline="").read()
    msk = mascara(txt)
    edits = []
    for mm in re.finditer(r'(?s)<spawn_map\b[^>]*map_id="(\d+)"[^>]*>(.*?)</spawn_map>', msk):
        M = mapa(int(mm.group(1)))
        if M is None:
            continue
        base = mm.start(2)
        for sm in re.finditer(r'(?s)<spawn\b[^>]*npc_id="(\d+)"[^>]*>(.*?)</spawn>', mm.group(2)):
            npc = int(sm.group(1))
            b2 = base + sm.start(2)
            for sp in re.finditer(r"<spot\b[^>]*>", sm.group(2)):
                tag = sp.group(0)
                gx, gy, gz = (re.search(r'\b%s="([-\d.eE]+)"' % k, tag) for k in ("x", "y", "z"))
                if not (gx and gy and gz):
                    continue
                X, Y, Z = float(gx.group(1)), float(gy.group(1)), float(gz.group(1))
                k, novo = decide(M, npc, X, Y, Z, tag)
                cont[k] = cont.get(k, 0) + 1
                if novo is None:
                    continue
                ini = b2 + sp.start() + gz.start(1)
                edits.append((ini, ini + len(gz.group(1)), fmt(novo)))
                if abs(novo - Z) > 6 and rel is not None:
                    rel.writerow([os.path.basename(arq), int(mm.group(1)), npc, f"{X:.2f}", f"{Y:.2f}", f"{Z:.2f}", f"{novo:.2f}", f"{novo - Z:+.2f}", k])
    if edits and aplica:
        for i, f, s in sorted(edits, reverse=True):
            txt = txt[:i] + s + txt[f:]
        open(arq, "w", encoding="utf-8", newline="").write(txt)
    return len(edits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spawns")
    ap.add_argument("--aplica", action="store_true")
    ap.add_argument("--relatorio")
    a = ap.parse_args()
    rel = None
    if a.relatorio:
        fr = open(a.relatorio, "w", encoding="utf-8", newline="")
        rel = csv.writer(fr, delimiter=";")
        rel.writerow(["arquivo", "mapa", "npc", "x", "y", "z_antigo", "z_novo", "dz", "caso"])
    cont, arqs, n = {}, 0, 0
    for f in sorted(glob.glob(os.path.join(a.spawns, "**", "*.xml"), recursive=True)):
        if os.sep + "Statics" + os.sep in f or "/Statics/" in f.replace("\\", "/"):
            continue
        e = processa(f, a.aplica, rel, cont)
        if e:
            arqs += 1
            n += e
    for k, v in sorted(cont.items()):
        print(f"{v:7d}  {k}")
    print(f"{'aplicado' if a.aplica else 'simulado'}: {n} spots em {arqs} arquivos")


if __name__ == "__main__":
    main()
