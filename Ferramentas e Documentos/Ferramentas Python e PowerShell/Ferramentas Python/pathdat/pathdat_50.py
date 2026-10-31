"""Leitor do X-path.dat do cliente 5.0 (grade de navegação oficial, células de 0,5 m).

Arquivo: header 128 b | [i32 n1][bloco 1: n1 bytes] | [i32 n2][n2 x u32] | setores de 16 m (y externo, x interno):
  [u8 nº de camadas] e, por camada, [u8 tipo] + corpo:
  tipo 16 : [u32 offset no bloco 1 (a partir do byte 132)][u16 nº de nós]  -> grafo explícito (pontes, bordas, prédios)
  demais  : [u8 lados][4 x u32 borda] + dados; célula i = sy*32 + sx
     lados : bit d ligado = a borda d (x+1, y+1, x-1, y-1) é máscara de 32 células; desligado = 0 fechada / 32*(k+1) inteira
     0/1   : [i32 z cm]                        piso plano
     2/3   : -                                 terreno
     6/7   : 128 b, 1 bit/célula (LSB primeiro) 1 = bloqueado, 0 = terreno
     8/9   : [2 x i32 z cm] + 2 bits/célula     0-1 paleta, 2 terreno, 3 bloqueado
     10/11 : [14 x i32 z cm] + 4 bits/célula    0-13 paleta, 14 terreno, 15 bloqueado (nibble baixo = célula par)
     12/13 : [i32 base cm] + 1 b/célula         base+v, 0xFE terreno, 0xFF bloqueado
     14/15 : [i32 base cm] + 2 b/célula         base+v, 0xFFFE terreno, 0xFFFF bloqueado
     ímpar : + 512 b (4 bits/célula, ainda sem significado)
Nó do tipo 16: [i32 z cm][u16 cx][u16 cy][u8 máscara] + uma ligação por direção (2 bits cada, x+1, y+1, x-1, y-1):
  01 = u16 offset do vizinho na lista do setor; 10 = u32: bits 0-6 = camada do setor vizinho, bits 7-31 = offset
  absoluto do nó de destino no bloco 1 (0 ou 1 = camada simples, célula ao lado). Provado em 23.759/23.759 ligações (220040000).
  Ligações são de mão única: descida livre (até -11 m visto), subida até ~1,9 m.
Terreno: <data/geo>/<mapa>.png 16 bits, grade de 2 m, z = v * 2048 / 65536, linha = x.
"""
import os, re, struct, glob, functools

RAIZ = r"G:/Projetos AION/Classic/Código Fonte - Emulador/game-server/data"
CORPO = {0: 4, 1: 4, 2: 0, 3: 0, 4: 1024, 5: 1024, 6: 128, 7: 128, 8: 264, 9: 264,
         10: 568, 11: 568, 12: 1028, 13: 1028, 14: 2052, 15: 2052}
DIR = [(1, 0), (0, 1), (-1, 0), (0, -1)]


@functools.lru_cache(None)
def _tamanhos():
    x = open(os.path.join(RAIZ, "static_data/world_maps.xml"), encoding="utf-8").read()
    return {int(i): int(s) for i, s in re.findall(r'id="(\d+)"[^>]*?world_size="(\d+)"', x)}


class Terreno:
    def __init__(self, mapa):
        self.px = None
        p = os.path.join(RAIZ, "geo", f"{mapa}.png")
        if os.path.exists(p):
            from PIL import Image
            im = Image.open(p)
            self.w, self.h = im.size
            self.px = im.load()

    def _h(self, i, j):
        if i <= 0 or j <= 0 or i >= self.h or j >= self.w:
            return 0.0
        v = self.px[j, i]
        return float("nan") if v == 65535 else v * 2048 / 65536

    def z(self, x, y):
        if self.px is None:
            return float("nan")
        i, j = int(x // 2), int(y // 2)
        fx, fy = x / 2 - i, y / 2 - j
        z1, z2, z3, z4 = self._h(i, j), self._h(i, j + 1), self._h(i + 1, j), self._h(i + 1, j + 1)
        if fx + fy <= 1:
            return z1 + (z3 - z1) * fx + (z2 - z1) * fy
        return z4 + (z2 - z4) * (1 - fx) + (z3 - z4) * (1 - fy)


class PathDat:
    def __init__(self, mapa):
        d = glob.glob(os.path.join(RAIZ, "native-path", f"{mapa}_*", "*.dat"))
        if not d:
            raise FileNotFoundError(f"sem path.dat para {mapa}")
        self.mapa, self.arquivo = mapa, d[0]
        self.f = f = open(d[0], "rb").read()
        self.ter = Terreno(mapa)
        self.b1 = 132
        prim = _tamanhos().get(mapa, 3072)
        for tam in [prim] + [t for t in (512, 1024, 1536, 2048, 3072, 4096, 6144) if t != prim]:
            try:
                self._le(tam)
            except IndexError:
                continue
            if self.fim_ok:
                break        # alguns mapas (310050000, 330040000, 800050000) têm 512 m no path.dat e 1024 no world_maps
        self._nos = {}
        self._abs = None

    def no_abs(self, off):
        """Nó tipo 16 pelo offset absoluto no bloco 1 -> (setor, camada, offset relativo)."""
        if self._abs is None:
            self._abs = {}
            for s, L in self.cam.items():
                for li, c in enumerate(L):
                    if c[0] == 16:
                        for rel in self.nos(s, li):
                            self._abs[c[1] + rel] = (s, li, rel)
        return self._abs.get(off)

    def _le(self, tam):
        f = self.f
        self.tam = tam
        off = 132 + struct.unpack_from("<i", f, 128)[0]
        n2 = struct.unpack_from("<i", f, off)[0]
        off += 4 + 4 * n2
        self.cam = {}                      # (sx16, sy16) -> [(tipo, offset_corpo | (offset_nós, n))]
        for y in range(0, self.tam, 16):
            for x in range(0, self.tam, 16):
                n = f[off]; off += 1
                L = []
                for _ in range(n):
                    t = f[off]; off += 1
                    if t == 16:
                        L.append((16,) + struct.unpack_from("<IH", f, off)); off += 6
                    else:
                        L.append((t, off - 1)); off += 17 + CORPO[t] + (512 if t % 2 else 0)
                if L:
                    self.cam[(x, y)] = L
        self.fim_ok = off == len(f)

    # ---- grafo explícito (tipo 16)
    def nos(self, setor, li):
        k = (setor, li)
        if k not in self._nos:
            _, o, n = self.cam[setor][li]
            f, p, R = self.f, self.b1 + o, {}
            for _ in range(n):
                rel = p - self.b1 - o
                z, cx, cy, m = struct.unpack_from("<iHHB", f, p); q = p + 9; lig = []
                for d in range(4):
                    c = (m >> (2 * d)) & 3
                    if c == 1:
                        lig.append((d, 1, struct.unpack_from("<H", f, q)[0])); q += 2
                    elif c >= 2:
                        v = struct.unpack_from("<I", f, q)[0]; q += 4
                        lig.append((d, 2, (v & 0x7F, v >> 7)))     # (camada vizinha, offset do nó no bloco 1 ou 0)
                R[rel] = (cx, cy, z / 100, lig)
                p = q
            self._nos[k] = R
        return self._nos[k]

    # ---- células das camadas simples
    def celula(self, t, a, i):
        f, d = self.f, a + 18
        if t in (0, 1): return ("z", struct.unpack_from("<i", f, d)[0] / 100)
        if t in (2, 3): return ("ter",)
        if t in (6, 7): return ("bloq",) if (f[d + (i >> 3)] >> (i & 7)) & 1 else ("ter",)
        if t in (8, 9):
            p = struct.unpack_from("<2i", f, d); v = (f[d + 8 + (i >> 2)] >> ((i & 3) * 2)) & 3
            return ("z", p[v] / 100) if v < 2 else (("ter",) if v == 2 else ("bloq",))
        if t in (10, 11):
            p = struct.unpack_from("<14i", f, d); b = f[d + 56 + (i >> 1)]; v = (b >> 4) if i & 1 else (b & 15)
            return ("z", p[v] / 100) if v < 14 else (("ter",) if v == 14 else ("bloq",))
        if t in (12, 13):
            b = struct.unpack_from("<i", f, d)[0]; v = f[d + 4 + i]
            return ("z", (b + v) / 100) if v < 0xFE else (("ter",) if v == 0xFE else ("bloq",))
        if t in (14, 15):
            b = struct.unpack_from("<i", f, d)[0]; v = struct.unpack_from("<H", f, d + 4 + 2 * i)[0]
            return ("z", (b + v) / 100) if v < 0xFFFE else (("ter",) if v == 0xFFFE else ("bloq",))
        return ("?",)

    def pisos(self, x, y):
        """Todos os pisos da célula de (x, y): [(z, livre, tipo)]; sem camada nenhuma = terreno livre."""
        s = (int(x) // 16 * 16, int(y) // 16 * 16)
        cx, cy = int(x / 0.5), int(y / 0.5)
        i = (cy - s[1] * 2) * 32 + (cx - s[0] * 2)
        L = self.cam.get(s)
        if not L:
            return [(self.ter.z(x, y), True, None)]
        out = []
        for li, c in enumerate(L):
            if c[0] == 16:
                out += [(z, True, 16) for (nx, ny, z, _) in self.nos(s, li).values() if (nx, ny) == (cx, cy)]
            else:
                r = self.celula(c[0], c[1], i)
                if r[0] == "z": out.append((r[1], True, c[0]))
                elif r[0] == "ter": out.append((self.ter.z(x, y), True, c[0]))
                elif r[0] == "bloq": out.append((self.ter.z(x, y), False, c[0]))
        return out
