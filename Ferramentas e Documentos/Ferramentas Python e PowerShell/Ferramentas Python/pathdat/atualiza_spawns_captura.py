"""Acerta os spots fixos de um arquivo de spawn pela posição oficial (S_PUT_NPC) de uma captura do mapa.

Uso: atualiza_spawns_captura.py <captura .pkl> <mapa> <arquivo de spawn> [<mais arquivos com o mesmo conteúdo>] [--aplica]

Objeto oficial "fixo": todas as aparições no mesmo x/y (0,3 m) e com o mesmo heading; NPC invocado por jogador fica de fora,
assim como tipos criados dinamicamente (muitos objetos no mesmo ponto, ex.: 209359 Soul Catcher).
  - spot do mesmo NPC a até 1 m, sem walker_id e sem random_walk: x/y/z/h viram os oficiais;
  - nenhum spot do NPC a 1 m e o NPC não anda (sem random_walk/walker_id em nenhum spot dele): spot novo com a posição oficial;
  - o resto (rota, andar aleatório) só vai para o relatório.
Edita só os atributos do <spot> (o resto do arquivo fica igual) e confere que todos os arquivos passados terminam iguais.
"""
import collections, math, pickle, re, struct, sys


def oficiais(pkl, mapa):
    P = pickle.load(open(pkl, "rb"))
    no, vis = None, collections.defaultdict(list)
    for t, s, op, p in P:
        if not s:
            continue
        if op == 15 and len(p) >= 4:
            no = struct.unpack_from("<I", p, 0)[0]
        elif op == 14 and no == mapa and len(p) > 47:
            x, y, z, o, n = struct.unpack_from("<fffII", p, 0)
            if struct.unpack_from("<I", p, 43)[0] == 0 and p[47:49] == b"\0\0":
                itens = bin(struct.unpack_from("<I", p, 55)[0]).count("1")
                cauda = 59 + 20 * itens
                st = struct.unpack_from("<H", p, cauda + 30)[0] if len(p) - cauda == 48 else 0   # static_id (objeto do mapa)
                vis[(n, o)].append((x, y, z, p[27], st))
    por_ponto = collections.Counter((n, round(v[0][0], 1), round(v[0][1], 1)) for (n, o), v in vis.items())
    fixos = []
    for (n, o), v in vis.items():
        if por_ponto[(n, round(v[0][0], 1), round(v[0][1], 1))] > 3:          # criado dinamicamente
            continue
        if max(math.hypot(a[0] - v[0][0], a[1] - v[0][1]) for a in v) > 0.3 or len({a[3] for a in v}) > 1:
            continue
        fixos.append((n, v[0][0], v[0][1], v[0][2], v[0][3], v[0][4]))
    return fixos


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def processa(texto, fixos, rel):
    msk = re.sub(r"(?s)<!--.*?-->", lambda m: " " * len(m.group(0)), texto)
    spots = collections.defaultdict(list)     # npc -> [(ini, fim, x, y, anda, static_id)]
    blocos = {}
    for sm in re.finditer(r'(?s)<spawn\b[^>]*npc_id="(\d+)"[^>]*>(.*?)</spawn>', msk):
        n = int(sm.group(1))
        blocos.setdefault(n, sm.end(2))
        for sp in re.finditer(r"<spot\b[^>]*>", sm.group(2)):
            tag = sp.group(0)
            g = lambda k: float(re.search(r'\b%s="([-\d.]+)"' % k, tag).group(1))
            si = re.search(r'static_id="(\d+)"', tag)
            ini = sm.start(2) + sp.start()
            spots[n].append((ini, ini + len(tag), g("x"), g("y"), "walker_id" in tag or "random_walk" in tag, int(si.group(1)) if si else 0))
    edits, novos, usados = [], collections.defaultdict(list), set()
    statics_oficiais = {(n, st) for n, x, y, z, h, st in fixos if st}
    for n, x, y, z, h, st in fixos:
        c = [s for s in spots.get(n, []) if s[0] not in usados]
        b = min(c, key=lambda s: math.hypot(s[2] - x, s[3] - y)) if c else None
        if b and math.hypot(b[2] - x, b[3] - y) <= 1.0:
            usados.add(b[0])
            if b[4]:
                rel["mantido: spot com rota ou andar aleatório"] += 1
                continue
            tag = texto[b[0]:b[1]]
            novo = tag
            for k, v in (("x", fmt(x)), ("y", fmt(y)), ("z", fmt(z)), ("h", str(h))):
                novo = re.sub(r'(\b%s=")[^"]*(")' % k, lambda m: m.group(1) + v + m.group(2), novo, count=1)
            if st and b[5] != st:            # o objeto oficial é ligado a um objeto do mapa (porta, livro, estante)
                novo = re.sub(r'\s*static_id="\d*"', "", novo)
                novo = re.sub(r'(\s*/?>)$', lambda m: f' static_id="{st}"' + m.group(1), novo, count=1)
                rel["static_id posto"] += 1
            if novo != tag:
                edits.append((b[0], b[1], novo))
                rel["ajustado para o oficial"] += 1
            else:
                rel["já igual ao oficial"] += 1
        elif any(s[4] for s in spots.get(n, [])):
            rel["mantido: NPC que anda (visto fora do ponto)"] += 1
        elif n in blocos:
            novos[n].append((x, y, z, h, st))
            rel["spot novo (NPC já tem spawn no arquivo)"] += 1
        else:
            rel["sem spawn do NPC no arquivo (não acrescentado)"] += 1
            rel.setdefault("_sem_spawn", []).append(n)
    # spot antigo (4.x) cujo static_id agora é do spot oficial: dois NPCs no mesmo objeto do mapa -> sai o antigo
    for n, l in spots.items():
        for s_ in l:
            if s_[0] in usados or not s_[5]:
                continue
            if (n, s_[5]) in statics_oficiais:
                ini = texto.rfind("\n", 0, s_[0]) + 1
                fim = texto.index("\n", s_[1]) + 1
                edits.append((ini, fim, ""))
                rel["spot antigo removido (static_id passou ao spot oficial)"] += 1
            else:
                rel.setdefault("_static_sem_oficial", []).append((n, s_[2], s_[3], s_[5]))
    nl = "\r\n" if "\r\n" in texto else "\n"
    for n, l in novos.items():
        fim = blocos[n]
        # insere antes do fechamento do <spawn> (depois do último spot)
        ultimo = texto.rfind("<spot", 0, fim)
        ind = texto[texto.rfind("\n", 0, ultimo) + 1:ultimo]
        pos = texto.index(">", ultimo) + 1
        add = "".join(f'{nl}{ind}<spot x="{fmt(x)}" y="{fmt(y)}" z="{fmt(z)}" h="{h}"' + (f' static_id="{st}"' if st else "") + " />"
                      for x, y, z, h, st in l)
        edits.append((pos, pos, add))
    for i, f, s in sorted(edits, reverse=True):
        texto = texto[:i] + s + texto[f:]
    return texto


def main():
    a = [v for v in sys.argv[1:] if v != "--aplica"]
    pkl, mapa, arqs = a[0], int(a[1]), a[2:]
    fixos = oficiais(pkl, mapa)
    print(f"objetos oficiais fixos: {len(fixos)}")
    saidas = []
    for arq in arqs:
        rel = collections.Counter()
        txt = open(arq, encoding="utf-8", newline="").read()
        novo = processa(txt, fixos, rel)
        saidas.append(novo)
        sem = rel.pop("_sem_spawn", [])
        sso = rel.pop("_static_sem_oficial", [])
        print(arq[-60:], dict(rel), "| NPCs sem spawn no arquivo:", sorted(set(sem))[:20])
        if sso:
            print(f"   spots com static_id sem objeto oficial perto (mantidos; fora da área da captura?): {len(sso)}", sso[:40])
        if "--aplica" in sys.argv:
            open(arq, "w", encoding="utf-8", newline="").write(novo)
    if len(set(saidas)) > 1:
        print("ATENÇÃO: os arquivos ficaram diferentes entre si")


if __name__ == "__main__":
    main()
