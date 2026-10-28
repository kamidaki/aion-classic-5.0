"""A* na grade de 0,5 m do path.dat (pathdat_50) + alisamento por linha de visão. Ferramenta de teste, não é o código do servidor.

Nó = ('N', setor, camada, offset) para nós tipo 16 (usa as ligações do arquivo, de mão única)
   = ('L', setor, camada, cx, cy) para células das camadas simples (vizinhas livres com |dz| <= SUBIDA).
"""
import heapq, math
from pathdat_50 import DIR

SUBIDA = 1.9          # maior subida vista nas ligações do arquivo
ENTRADA_PELA_LIGACAO = True
QUEDA = 0.4           # preço da queda por metro (oficial: rampa 3,2 m mais longa ganha de queda de 11,19 m; queda de 9,15 m ganha de rampa 4,4 m mais longa)
DIAGONAL = True
DIVISA_DUPLA = True   # divisa de setor vale nos dois sentidos (hipótese da captura de 27/10 03:01)


class Grade:
    def __init__(self, M):
        self.M = M
        self._cel = {}

    def setor(self, cx, cy):
        return (cx // 32 * 16, cy // 32 * 16)

    def pisos(self, cx, cy):
        """[(nó, z, livre)] da célula."""
        k = (cx, cy)
        if k in self._cel:
            return self._cel[k]
        M, s = self.M, self.setor(cx, cy)
        x, y = cx * 0.5 + 0.25, cy * 0.5 + 0.25
        i = (cy - s[1] * 2) * 32 + (cx - s[0] * 2)
        out = []
        L = M.cam.get(s)
        if not L:
            out.append((("L", s, -1, cx, cy), M.ter.z(x, y), True))
        else:
            for li, c in enumerate(L):
                if c[0] == 16:
                    for rel, n in M.nos(s, li).items():
                        if (n[0], n[1]) == (cx, cy):
                            out.append((("N", s, li, rel), n[2], True))
                else:
                    r = M.celula(c[0], c[1], i)
                    if r[0] == "z":
                        out.append((("L", s, li, cx, cy), r[1], True))
                    elif r[0] in ("ter", "bloq"):
                        out.append((("L", s, li, cx, cy), M.ter.z(x, y), r[0] == "ter"))
        out = [o for o in out if not math.isnan(o[1])]
        self._cel[k] = out
        return out

    def z(self, no):
        if no[0] == "N":
            return self.M.nos(no[1], no[2])[no[3]][2]
        return next(z for k, z, _ in self.pisos(no[3], no[4]) if k == no)

    def cel(self, no):
        if no[0] == "N":
            n = self.M.nos(no[1], no[2])[no[3]]
            return n[0], n[1]
        return no[3], no[4]

    def vizinhos(self, no):
        cx, cy = self.cel(no)
        z = self.z(no)
        if no[0] == "N":
            _, s, li, rel = no
            ligadas = {d for d, _, _ in self.M.nos(s, li)[rel][3]}
            for d in range(4):
                tx, ty = cx + DIR[d][0], cy + DIR[d][1]
                if d in ligadas or self.setor(tx, ty) == s or not DIVISA_DUPLA:
                    continue
                for k, zz, livre in self.pisos(tx, ty):
                    if livre and abs(zz - z) <= SUBIDA:
                        yield k, zz
            for d, t, v in self.M.nos(s, li)[rel][3]:
                tx, ty = cx + DIR[d][0], cy + DIR[d][1]
                if t == 1:
                    q = ("N", s, li, v)
                    yield q, self.M.nos(s, li)[v][2]
                else:
                    camada, off = v
                    if off > 1:
                        s2, li2, rel2 = self.M.no_abs(off)
                        q = ("N", s2, li2, rel2)
                        yield q, self.M.nos(s2, li2)[rel2][2]
                    else:
                        # camada simples: os 7 bits não são o índice da camada (82-95% batem com o andar por altura crescente);
                        # usa o piso livre mais perto da altura de origem e, sem nenhum a SUBIDA, o andar pela ordem de altura
                        livres = [(k, zz) for k, zz, livre in self.pisos(tx, ty) if livre]
                        perto = [q for q in livres if abs(q[1] - z) <= SUBIDA]
                        if perto:
                            yield min(perto, key=lambda a: abs(a[1] - z))
                        elif livres:
                            ordem = sorted(livres, key=lambda a: a[1])
                            yield ordem[min(camada, len(ordem) - 1)]
            return
        for d, (dx, dy) in enumerate(DIR):
            tx, ty = cx + dx, cy + dy
            for k, zz, livre in self.pisos(tx, ty):
                if not livre or abs(zz - z) > SUBIDA:
                    continue
                if k[0] == "N" and ENTRADA_PELA_LIGACAO:
                    # só entra num nó tipo 16 pelo lado em que ele tem ligação de volta (lateral de rampa não sobe)
                    volta = (d + 2) % 4
                    if not any(dd == volta for dd, _, _ in self.M.nos(k[1], k[2])[k[3]][3]):
                        continue
                yield k, zz

    def no_em(self, x, y, z):
        c = [(k, zz) for k, zz, livre in self.pisos(int(x / 0.5), int(y / 0.5)) if livre]
        return min(c, key=lambda a: abs(a[1] - z))[0] if c else None

    @staticmethod
    def custo(h, dz):
        """Passo de h metros no plano; a queda paga QUEDA x altura (entre 0,29 e 0,48 pelas capturas de DF1 e 220040000)."""
        return h + (QUEDA * -dz if dz < -SUBIDA else 0.0)

    def caminho(self, a, b, limite=300000):
        ca, cb = self.cel(a), self.cel(b)
        fila, g, pai, n = [(0, 0, a)], {a: 0}, {a: None}, 0
        while fila:
            _, ga, u = heapq.heappop(fila)
            n += 1
            if u == b or n > limite:
                break
            if ga > g.get(u, 1e18):
                continue
            cu = self.cel(u)
            zu = self.z(u)
            passos = [(v, self.custo(0.5, zz - zu)) for v, zz in self.vizinhos(u)]
            if DIAGONAL:
                orto = {v for v, _ in passos}
                for v1 in list(orto):
                    for v2, zz in self.vizinhos(v1):
                        c2 = self.cel(v2)
                        if abs(c2[0] - cu[0]) == 1 and abs(c2[1] - cu[1]) == 1:
                            passos.append((v2, self.custo(0.7071, zz - zu)))
            for v, custo in passos:
                cv = self.cel(v)
                c = ga + custo
                if c < g.get(v, 1e18):
                    g[v] = c
                    pai[v] = u
                    hx, hy = abs(cv[0] - cb[0]), abs(cv[1] - cb[1])
                    heapq.heappush(fila, (c + 0.5 * (max(hx, hy) + 0.4142 * min(hx, hy)), c, v))
        if b not in pai:
            return None
        out, u = [], b
        while u:
            out.append(u)
            u = pai[u]
        return out[::-1]

    def ponto(self, no):
        cx, cy = self.cel(no)
        return (cx * 0.5 + 0.25, cy * 0.5 + 0.25, self.z(no))

    def _celulas(self, p, q):
        """Células 4-conexas cruzadas pela reta p->q."""
        out = []
        n = max(2, int(math.dist(p[:2], q[:2]) * 8))
        for k in range(n + 1):
            f = k / n
            c = (int((p[0] + (q[0] - p[0]) * f) / 0.5), int((p[1] + (q[1] - p[1]) * f) / 0.5))
            if not out or out[-1] != c:
                if out and abs(c[0] - out[-1][0]) + abs(c[1] - out[-1][1]) == 2:
                    out.append((c[0], out[-1][1]))
                out.append(c)
        return out

    def ve(self, a, b):
        """Reta do nó a ao nó b andando pelas ligações do grafo: cada célula cruzada tem de ser vizinha ligada da anterior
        (sem queda), e a reta termina no próprio nó b. A altura interpolada não conta: o oficial corta rampa e escada
        em linha reta, mas não sobe a lateral de uma rampa nem troca de andar no meio da reta."""
        p, q = self.ponto(a), self.ponto(b)
        u = a
        for c in self._celulas(p, q)[1:]:
            zu = self.z(u)
            cand = [(v, zz) for v, zz in self.vizinhos(u) if self.cel(v) == c and zz - zu >= -SUBIDA]
            if not cand:
                return False
            u = min(cand, key=lambda t: abs(t[1] - zu))[0]
        return u == b

    def alisa(self, nos):
        """Corta o caminho em linhas retas; uma queda (dz < -SUBIDA entre células vizinhas) fica como dois pontos fixos."""
        P = [self.ponto(u) for u in nos]
        quebras = [0] + [k for k in range(1, len(P)) if P[k][2] - P[k - 1][2] < -SUBIDA] + [len(P)]
        out = [P[0]]
        for a, b in zip(quebras, quebras[1:]):
            if a > 0:
                out.append(P[a])                     # pé da queda
            i = a
            while i < b - 1:
                j = b - 1
                while j > i + 1 and not self.ve(nos[i], nos[j]):
                    j -= 1
                out.append(P[j])
                i = j
        return out
