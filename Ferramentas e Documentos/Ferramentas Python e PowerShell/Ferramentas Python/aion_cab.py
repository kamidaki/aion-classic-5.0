"""Le e grava o `.cab` do cliente do Aion: a lista de animacoes de um modelo, em binario e cifrada.

O `.cal` e o `.cab` dizem a mesma coisa -- nome logico da animacao -> arquivo `.caf` --, um em
texto e o outro em binario. O `CryAnimation.dll` so le o `.cal` enquanto o cvar
`ca_defaultAnimLength` e 0; o `Game.dll` poe 4.0 nele ao receber a resposta do servidor, e dai em
diante o personagem e carregado pelo `.cab`. Mexer so no `.cal` nao chega ao jogo.

**Formato, depois de decifrado:**

```text
u32      tamanho do que vem a seguir (o arquivo e completado com zeros ate multiplo de 16)
u32      'bncl' (0x6c636e62)
u32      versao, 1
u32      quantos registros
u32 x2   zero
registro, 200 bytes cada, ordenados:
  +0x00  char[64]   nome logico (`cidle_orb_001`)
  +0x40  char[128]  caminho (`Objects\\PC\\LM\\Animation\\LM_cidle_orb_001_loop.caf`)
  +0xC0  u32        flags (2 = $EnableAutoUnload)
  +0xC4  f32        prob (o `// prob=0.8` do `.cal`)
```

**Cifra:** Twofish de 128 bits em ECB, bloco a bloco, com a chave fixa que esta em
`CryAnimation.dll` (a API de referencia do Twofish: `makeKey` sem material, a chave copiada para
`key32` e `reKey`). A marca `bncl` no lugar certo e a prova de que a decifragem esta correta.

Uso:

    python aion_cab.py <arquivo.cab>              lista os registros
    python aion_cab.py <arquivo.cab> <saida.cal>  grava como `.cal` em texto
"""
import struct
import sys

CHAVE = bytes.fromhex("28815719feef89c36a75ff384e60be03")
MAGIC = 0x6C636E62
TAM_REGISTRO = 200

# --------------------------------------------------------------------------------------------
# Twofish, 128 bits
# --------------------------------------------------------------------------------------------

_M32 = 0xFFFFFFFF


def _rol(x, n):
    return ((x << n) | (x >> (32 - n))) & _M32


def _ror(x, n):
    return ((x >> n) | (x << (32 - n))) & _M32


def _ror4(x, n):
    return ((x >> n) | (x << (4 - n))) & 0xF


def _permutacao(t):
    q = []
    for x in range(256):
        a, b = x >> 4, x & 15
        a, b = a ^ b, a ^ _ror4(b, 1) ^ ((8 * a) & 15)
        a, b = t[0][a], t[1][b]
        a, b = a ^ b, a ^ _ror4(b, 1) ^ ((8 * a) & 15)
        a, b = t[2][a], t[3][b]
        q.append(16 * b + a)
    return q


_Q0 = _permutacao((
    (0x8, 0x1, 0x7, 0xD, 0x6, 0xF, 0x3, 0x2, 0x0, 0xB, 0x5, 0x9, 0xE, 0xC, 0xA, 0x4),
    (0xE, 0xC, 0xB, 0x8, 0x1, 0x2, 0x3, 0x5, 0xF, 0x4, 0xA, 0x6, 0x7, 0x0, 0x9, 0xD),
    (0xB, 0xA, 0x5, 0xE, 0x6, 0xD, 0x9, 0x0, 0xC, 0x8, 0xF, 0x3, 0x2, 0x4, 0x7, 0x1),
    (0xD, 0x7, 0xF, 0x4, 0x1, 0x2, 0x6, 0xE, 0x9, 0xB, 0x3, 0x0, 0x8, 0x5, 0xC, 0xA),
))
_Q1 = _permutacao((
    (0x2, 0x8, 0xB, 0xD, 0xF, 0x7, 0x6, 0xE, 0x3, 0x1, 0x9, 0x4, 0x0, 0xA, 0xC, 0x5),
    (0x1, 0xE, 0x2, 0xB, 0x4, 0xC, 0x3, 0x7, 0x6, 0xD, 0xA, 0x5, 0xF, 0x9, 0x0, 0x8),
    (0x4, 0xC, 0x7, 0x5, 0x1, 0x6, 0x9, 0xA, 0x0, 0xE, 0xD, 0x8, 0x2, 0xB, 0x3, 0xF),
    (0xB, 0x9, 0x5, 0x1, 0xC, 0x3, 0xD, 0xE, 0x6, 0x4, 0x7, 0xF, 0x2, 0x0, 0x8, 0xA),
))


def _gf(a, b, poli):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a <<= 1
        if a & 0x100:
            a ^= poli
        b >>= 1
    return r


_MDS = ((0x01, 0xEF, 0x5B, 0x5B), (0x5B, 0xEF, 0xEF, 0x01), (0xEF, 0x5B, 0x01, 0xEF),
        (0xEF, 0x01, 0xEF, 0x5B))
_RS = ((0x01, 0xA4, 0x55, 0x87, 0x5A, 0x58, 0xDB, 0x9E), (0xA4, 0x56, 0x82, 0xF3, 0x1E, 0xC6, 0x68, 0xE5),
       (0x02, 0xA1, 0xFC, 0xC1, 0x47, 0xAE, 0x3D, 0x19), (0xA4, 0x55, 0x87, 0x5A, 0x58, 0xDB, 0x9E, 0x03))
#: coluna j da MDS aplicada ao byte y, ja como palavra de 32 bits.
_MDS_COL = [
    [sum(_gf(_MDS[i][j], y, 0x169) << (8 * i) for i in range(4)) for y in range(256)]
    for j in range(4)
]


def _tabelas_g(l0, l1):
    """As quatro tabelas de `h(X, (l0, l1))`: um XOR de quatro consultas da a funcao inteira."""
    a = [(l0 >> (8 * i)) & 0xFF for i in range(4)]
    b = [(l1 >> (8 * i)) & 0xFF for i in range(4)]
    return (
        [_MDS_COL[0][_Q1[_Q0[_Q0[x] ^ b[0]] ^ a[0]]] for x in range(256)],
        [_MDS_COL[1][_Q0[_Q0[_Q1[x] ^ b[1]] ^ a[1]]] for x in range(256)],
        [_MDS_COL[2][_Q1[_Q1[_Q0[x] ^ b[2]] ^ a[2]]] for x in range(256)],
        [_MDS_COL[3][_Q0[_Q1[_Q1[x] ^ b[3]] ^ a[3]]] for x in range(256)],
    )


def _h(x, t):
    return t[0][x & 0xFF] ^ t[1][(x >> 8) & 0xFF] ^ t[2][(x >> 16) & 0xFF] ^ t[3][x >> 24]


class Twofish:
    def __init__(self, chave):
        if len(chave) != 16:
            raise ValueError("so chave de 128 bits")
        m = struct.unpack("<4I", chave)
        s = []
        for i in range(2):
            bloco = chave[8 * i:8 * i + 8]
            s.append(sum(
                (lambda linha: _reduz(linha, bloco))(_RS[j]) << (8 * j) for j in range(4)
            ))
        par = _tabelas_g(m[0], m[2])
        impar = _tabelas_g(m[1], m[3])
        self.k = []
        for i in range(20):
            a = _h((2 * i) * 0x01010101, par)
            b = _rol(_h((2 * i + 1) * 0x01010101, impar), 8)
            self.k.append((a + b) & _M32)
            self.k.append(_rol((a + 2 * b) & _M32, 9))
        self.g = _tabelas_g(s[1], s[0])

    def cifra(self, bloco):
        k, g = self.k, self.g
        r0, r1, r2, r3 = (p ^ k[i] for i, p in enumerate(struct.unpack("<4I", bloco)))
        for r in range(16):
            t0 = _h(r0, g)
            t1 = _h(_rol(r1, 8), g)
            r2 = _ror(r2 ^ ((t0 + t1 + k[2 * r + 8]) & _M32), 1)
            r3 = _rol(r3, 1) ^ ((t0 + 2 * t1 + k[2 * r + 9]) & _M32)
            r0, r1, r2, r3 = r2, r3, r0, r1
        return struct.pack("<4I", r2 ^ k[4], r3 ^ k[5], r0 ^ k[6], r1 ^ k[7])

    def decifra(self, bloco):
        k, g = self.k, self.g
        c = struct.unpack("<4I", bloco)
        r2, r3, r0, r1 = c[0] ^ k[4], c[1] ^ k[5], c[2] ^ k[6], c[3] ^ k[7]
        for r in range(15, -1, -1):
            r0, r1, r2, r3 = r2, r3, r0, r1
            t0 = _h(r0, g)
            t1 = _h(_rol(r1, 8), g)
            r2 = _rol(r2, 1) ^ ((t0 + t1 + k[2 * r + 8]) & _M32)
            r3 = _ror(r3 ^ ((t0 + 2 * t1 + k[2 * r + 9]) & _M32), 1)
        return struct.pack("<4I", r0 ^ k[0], r1 ^ k[1], r2 ^ k[2], r3 ^ k[3])


def _reduz(linha, bloco):
    r = 0
    for coef, byte in zip(linha, bloco):
        r ^= _gf(coef, byte, 0x14D)
    return r


# --------------------------------------------------------------------------------------------
# .cab
# --------------------------------------------------------------------------------------------

class CabInvalido(Exception):
    pass


def _ecb(dados, funcao):
    return b"".join(funcao(dados[i:i + 16]) for i in range(0, len(dados), 16))


def le(bruto):
    """Devolve a lista de registros `(nome, caminho, flags, prob)` de um `.cab` cifrado."""
    if not bruto or len(bruto) % 16:
        raise CabInvalido("tamanho nao e multiplo de 16")
    claro = _ecb(bruto, Twofish(CHAVE).decifra)
    tam = struct.unpack_from("<I", claro, 0)[0]
    if tam + 4 > len(claro) or len(claro) - 16 >= tam + 4:
        raise CabInvalido(f"tamanho interno {tam} nao bate com o arquivo ({len(claro)})")
    magic, versao, quantos = struct.unpack_from("<3I", claro, 4)
    if magic != MAGIC or versao != 1:
        raise CabInvalido(f"cabecalho inesperado (magic {magic:#x}, versao {versao})")
    if 20 + quantos * TAM_REGISTRO != tam:
        raise CabInvalido(f"{quantos} registros nao cabem em {tam} bytes")
    registros = []
    for i in range(quantos):
        r = claro[24 + i * TAM_REGISTRO:24 + (i + 1) * TAM_REGISTRO]
        nome = r[:0x40].split(b"\0")[0].decode("latin-1")
        caminho = r[0x40:0xC0].split(b"\0")[0].decode("latin-1")
        flags, prob = struct.unpack_from("<If", r, 0xC0)
        registros.append((nome, caminho, flags, prob))
    return registros


def grava(registros):
    """O inverso de [`le`]: registros -> bytes do `.cab` cifrado."""
    corpo = bytearray(struct.pack("<5I", MAGIC, 1, len(registros), 0, 0))
    for nome, caminho, flags, prob in registros:
        n, c = nome.encode("latin-1"), caminho.encode("latin-1")
        if len(n) > 0x3F or len(c) > 0x7F:
            raise CabInvalido(f"nome ou caminho grande demais: {nome} = {caminho}")
        corpo += n.ljust(0x40, b"\0") + c.ljust(0x80, b"\0") + struct.pack("<If", flags, prob)
    claro = struct.pack("<I", len(corpo)) + bytes(corpo)
    claro += b"\0" * (-len(claro) % 16)
    return _ecb(claro, Twofish(CHAVE).cifra)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    with open(argv[0], "rb") as f:
        registros = le(f.read())
    if len(argv) > 1:
        with open(argv[1], "w", encoding="latin-1", newline="\r\n") as f:
            for nome, caminho, flags, prob in registros:
                f.write(f"{nome}\t= {caminho}\n")
    else:
        for nome, caminho, flags, prob in registros:
            print(f"{nome}\t{caminho}\t{flags}\t{prob:g}")
    print(f"{len(registros)} registros", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
