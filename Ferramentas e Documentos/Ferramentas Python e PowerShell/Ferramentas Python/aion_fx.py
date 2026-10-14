"""Le, converte e grava as bibliotecas de efeito do cliente do Aion (`Effects\\Effects_Meshes.pak`).

Dois tipos de arquivo, os dois uma tabela de registros de tamanho fixo:

```text
prt/<lib>.prt   particulas          'CRY' u32 2  u32 campo  u32 n   registros
fxc/<lib>.fxc   efeitos compostos   'FXC' u32 2  u32 sub    u32 n   registros
```

O nome do registro (`sys_hit.ammo.harp`, `fc_sys_hit.harp.ammo`) e a primeira string, e e por ele
que itens, skills e outros efeitos se referem. O registro nao tem o mesmo tamanho no Live 5.8 e no
Classic 5.0, entao um efeito do 5.8 nao pode ser copiado como esta:

| | 5.8 | 5.0 | diferenca |
|---|---|---|---|
| `.prt` | 2235 b | 3007 b | as 9 strings do comeco vao de 64 para 128 bytes; a do som, de 64 para 260 |
| `.fxc` | 1394 b (sub 5) | 1580 b (sub 6) | quatro campos novos, com valor padrao constante |

As duas conversoes foram tiradas da comparacao dos registros que existem com o mesmo nome nas
duas versoes, e [`confere_prt`] / [`confere_fxc`] refazem essa prova: o registro do 5.8,
convertido, tem de sair identico ao do 5.0 na grande maioria dos casos (os que nao saem sao
efeitos que a NCSoft de fato retocou entre as versoes).

O cabecalho `campo` do `.prt` (1904 no 5.0, 1856 no 5.8) nao e usado aqui: fica o do arquivo de
destino.
"""
import struct

PRT_58, PRT_50 = 2235, 3007
FXC_58, FXC_50 = 1394, 1580
FXC_SUB_58, FXC_SUB_50 = 5, 6

#: Campos que o registro `.fxc` do 5.0 tem a mais, na posicao do registro do 5.8 em que entram.
_FXC_NOVOS = (
    (576, bytes(128)),
    (605, bytes.fromhex("010000000000803f0000803f") + bytes(29)),
    (637, bytes(1)),
    (1092, bytes.fromhex("00000700000000000000000000000000")),
)


class FxInvalido(Exception):
    pass


def le(bruto, magica):
    """`(versao, campo, registros)` de um `.prt` (`b"CRY"`) ou `.fxc` (`b"FXC"`)."""
    if bruto[:3] != magica:
        raise FxInvalido(f"esperava {magica!r}, veio {bruto[:3]!r}")
    versao, campo, n = struct.unpack_from("<III", bruto, 3)
    if not n or (len(bruto) - 15) % n:
        raise FxInvalido("tamanho do arquivo nao fecha com a contagem de registros")
    tam = (len(bruto) - 15) // n
    return versao, campo, [bruto[15 + i * tam:15 + (i + 1) * tam] for i in range(n)]


def grava(magica, versao, campo, registros):
    return magica + struct.pack("<III", versao, campo, len(registros)) + b"".join(registros)


def nome(registro):
    return registro.split(b"\0", 1)[0].decode("latin-1")


def prt_58_para_50(r):
    if len(r) != PRT_58:
        raise FxInvalido(f"registro .prt de {len(r)} bytes, esperava {PRT_58}")
    strings = b"".join(r[i * 64:(i + 1) * 64].ljust(128, b"\0") for i in range(9))
    return strings + r[576:2142] + r[2142:2206].ljust(260, b"\0") + r[2206:]


def fxc_58_para_50(r):
    if len(r) != FXC_58:
        raise FxInvalido(f"registro .fxc de {len(r)} bytes, esperava {FXC_58}")
    saida, p = bytearray(), 0
    for pos, novo in _FXC_NOVOS:
        saida += r[p:pos] + novo
        p = pos
    return bytes(saida + r[p:])


def _confere(pares, converte, minimo):
    iguais = sum(1 for r58, r50 in pares if converte(r58) == r50)
    if not pares or iguais < minimo * len(pares):
        raise FxInvalido(f"so {iguais} de {len(pares)} registros comuns convertem identicos")
    return iguais, len(pares)


def confere_prt(prt58, prt50):
    """Prova a conversao de `.prt` num par de arquivos de mesmo nome. Devolve `(iguais, comuns)`."""
    a = {nome(r): r for r in le(prt58, b"CRY")[2]}
    b = {nome(r): r for r in le(prt50, b"CRY")[2]}
    return _confere([(a[n], b[n]) for n in a if n in b], prt_58_para_50, 0.6)


def confere_fxc(pares_de_arquivos):
    """O mesmo para `.fxc`, sobre uma lista de `(bytes do 5.8, bytes do 5.0)` de mesmo nome."""
    pares = []
    for f58, f50 in pares_de_arquivos:
        a = {nome(r): r for r in le(f58, b"FXC")[2]}
        b = {nome(r): r for r in le(f50, b"FXC")[2]}
        pares += [(a[n], b[n]) for n in a if n in b]
    return _confere(pares, fxc_58_para_50, 0.85)


#: Indice (na propria biblioteca) do registro pai; -1 na raiz de um efeito. Um efeito e a raiz
#: mais todos os registros que descendem dela: so a raiz tem o nome que itens e efeitos citam, e
#: os filhos podem ter qualquer nome (`sys_hit.ammo.harp` tem `sys_hit.ammo.cast0` como filho).
PRT_PAI_58, PRT_PAI_50 = 2227, 2999


def subarvore(registros, raiz, pai_em=PRT_PAI_58):
    """Indices de `raiz` e de todos os seus descendentes, na ordem do arquivo."""
    nomes = [nome(r) for r in registros]
    if raiz not in nomes:
        raise FxInvalido(f"{raiz} nao esta na biblioteca")
    dentro = {nomes.index(raiz)}
    for i in range(min(dentro) + 1, len(registros)):
        if struct.unpack_from("<i", registros[i], pai_em)[0] in dentro:
            dentro.add(i)
    return sorted(dentro)


def acrescenta_prt(prt50, prt58, raizes):
    """`prt50` com os efeitos `raizes` de `prt58` (cada um com seus filhos), convertidos.

    Os registros vao para o fim, e o indice do pai de cada um e refeito para a posicao nova.
    Devolve `(bytes novos, nomes de todos os registros acrescentados)`.
    """
    versao, campo, destino = le(prt50, b"CRY")
    if len(destino[0]) != PRT_50:
        raise FxInvalido(f"o destino tem registro de {len(destino[0])} bytes, esperava {PRT_50}")
    origem = le(prt58, b"CRY")[2]
    tem = {nome(r).lower() for r in destino}
    novo_indice = {}
    novos = []
    for raiz in raizes:
        for i in subarvore(origem, raiz):
            if nome(origem[i]).lower() in tem:
                raise FxInvalido(f"{nome(origem[i])} ja existe no 5.0")
            novo_indice[i] = len(destino) + len(novos)
            novos.append(i)
    saida = list(destino)
    for i in novos:
        r = bytearray(prt_58_para_50(origem[i]))
        pai = struct.unpack_from("<i", origem[i], PRT_PAI_58)[0]
        struct.pack_into("<i", r, PRT_PAI_50, novo_indice[pai] if pai >= 0 else -1)
        saida.append(bytes(r))
    return grava(b"CRY", versao, campo, saida), [nome(origem[i]) for i in novos]


# --------------------------------------------------------------------------------------------
# Indices de nomes
# --------------------------------------------------------------------------------------------
#
# O cliente nao procura um efeito abrindo as bibliotecas: consulta `prt/namelist_prt.index` e
# `fxc/namelist_fxc.index`, e so abre a biblioteca em que o indice diz que o nome esta. **Um
# efeito que nao esta no indice nao existe para o jogo**, mesmo com o registro gravado no arquivo
# certo -- nao aparece, nao toca som e nao da erro.
#
# A chave e sempre [`chave`]: CRC32 (polinomio 0xEDB88320) do nome em MAIUSCULAS, comecando em 0 e
# sem o XOR final. A biblioteca entra pelo prefixo do nome (`SYS_HIT`, `FC_SYS_HIT`) e o efeito
# pelo nome inteiro (`SYS_HIT.AMMO.HARP`).
#
# ```text
# namelist_prt.index   u16 0x102, u16 quantas bibliotecas, e os blocos
# namelist_fxc.index   u16 0x1001, u16 0x102, u16 n2, u16 n3, u16 n4, u16 quantas bibliotecas,
#                      6 bytes zero, e quatro secoes, cada uma atras de um [u16 1][u16 numero]:
#                        0  os blocos
#                        1  n2 x [u32 chave][char[64]]   nomes de osso e textura citados
#                        2  n3 x 16 bytes                dados dos efeitos de tipo 1
#                        3  n4 x [f32][u32 chave]        dados dos efeitos de tipo 6 (projetil):
#                                                        um valor e o osso de onde ele sai
# bloco                [u16 1][u16 n][u32 chave da biblioteca]  +  n x [u32 chave][u32 valor]
# ```
#
# Blocos e entradas vem em ordem crescente de chave. No `.prt` o valor da entrada e uma flag
# (0 na grande maioria). No `.fxc` e 0 ou `(indice << 16) | tipo`, com o indice na secao 2
# (tipo 1) ou 3 (tipo 6).

_CRC = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ 0xEDB88320 if _c & 1 else _c >> 1
    _CRC.append(_c)


def chave(nome_do_efeito):
    c = 0
    for byte in nome_do_efeito.upper().encode("latin-1"):
        c = _CRC[(c ^ byte) & 0xFF] ^ (c >> 8)
    return c


def _le_blocos(b, o, quantos):
    blocos = []
    for _ in range(quantos):
        um, n, lib = struct.unpack_from("<HHI", b, o)
        if um != 1:
            raise FxInvalido(f"bloco de indice com marca {um} em {o}")
        blocos.append((lib, [struct.unpack_from("<II", b, o + 8 + i * 8) for i in range(n)]))
        o += 8 + n * 8
    return blocos, o


def _grava_blocos(blocos):
    saida = bytearray()
    for lib, entradas in sorted(blocos):
        saida += struct.pack("<HHI", 1, len(entradas), lib)
        for par in sorted(entradas):
            saida += struct.pack("<II", *par)
    return bytes(saida)


def le_indice_prt(b):
    versao, quantos = struct.unpack_from("<HH", b, 0)
    blocos, o = _le_blocos(b, 4, quantos)
    if versao != 0x102 or o != len(b):
        raise FxInvalido("namelist_prt.index com formato inesperado")
    return blocos


def grava_indice_prt(blocos):
    return struct.pack("<HH", 0x102, len(blocos)) + _grava_blocos(blocos)


def le_indice_fxc(b):
    magica, versao, n2, n3, n4, quantos = struct.unpack_from("<6H", b, 0)
    if magica != 0x1001 or versao != 0x102 or b[12:18] != bytes(6):
        raise FxInvalido("namelist_fxc.index com cabecalho inesperado")
    o = 18
    secoes = []
    for numero, leitor in enumerate((None, 68, 16, 8)):
        if struct.unpack_from("<HH", b, o) != (1, numero):
            raise FxInvalido(f"secao {numero} do namelist_fxc.index fora do lugar")
        o += 4
        if leitor is None:
            blocos, o = _le_blocos(b, o, quantos)
            secoes.append(blocos)
        else:
            n = (n2, n3, n4)[numero - 1]
            secoes.append([b[o + i * leitor:o + (i + 1) * leitor] for i in range(n)])
            o += n * leitor
    if o != len(b):
        raise FxInvalido("sobrou dado no fim do namelist_fxc.index")
    return secoes


def grava_indice_fxc(secoes):
    blocos, s1, s2, s3 = secoes
    saida = struct.pack("<6H", 0x1001, 0x102, len(s1), len(s2), len(s3), len(blocos)) + bytes(6)
    saida += struct.pack("<HH", 1, 0) + _grava_blocos(blocos)
    for numero, linhas in ((1, s1), (2, s2), (3, s3)):
        saida += struct.pack("<HH", 1, numero) + b"".join(linhas)
    return saida


def indexa_prt(indice50, indice58, nomes):
    """`namelist_prt.index` do 5.0 com as particulas `nomes`, com o valor que tem no do 5.8."""
    blocos = le_indice_prt(indice50)
    origem = {lib: dict(entradas) for lib, entradas in le_indice_prt(indice58)}
    por_lib = {lib: entradas for lib, entradas in blocos}
    for n in nomes:
        lib, k = chave(n.split(".", 1)[0]), chave(n)
        if lib not in origem or k not in origem[lib]:
            raise FxInvalido(f"{n} nao esta no indice do 5.8")
        if lib not in por_lib:
            por_lib[lib] = []
            blocos.append((lib, por_lib[lib]))
        if k not in dict(por_lib[lib]):
            por_lib[lib].append((k, origem[lib][k]))
    return grava_indice_prt(blocos)


def indexa_fxc(indice50, indice58, biblioteca):
    """`namelist_fxc.index` do 5.0 com a biblioteca inteira `biblioteca` do 5.8 (`fc_sys_hit`).

    Os dados que as entradas apontam nas secoes 1 a 3 sao copiados junto e os indices refeitos.
    """
    destino, origem = le_indice_fxc(indice50), le_indice_fxc(indice58)
    lib = chave(biblioteca)
    if any(b[0] == lib for b in destino[0]):
        raise FxInvalido(f"{biblioteca} ja esta no indice do 5.0")
    entradas = next((e for k, e in origem[0] if k == lib), None)
    if entradas is None:
        raise FxInvalido(f"{biblioteca} nao esta no indice do 5.8")
    nomes50 = {linha[:4] for linha in destino[1]}
    novas = []
    for k, valor in entradas:
        tipo, i = valor & 0xFFFF, valor >> 16
        if valor == 0:
            novas.append((k, 0))
        elif tipo == 6:
            linha = origem[3][i]
            osso = linha[4:8]
            if osso not in nomes50:
                destino[1].append(next(x for x in origem[1] if x[:4] == osso))
                nomes50.add(osso)
            destino[3].append(linha)
            novas.append((k, ((len(destino[3]) - 1) << 16) | 6))
        else:
            raise FxInvalido(f"entrada de tipo {tipo} em {biblioteca}: copia nao implementada")
    destino[0].append((lib, novas))
    return grava_indice_fxc(destino)


def fxc_para_50(fxc58):
    """Um `.fxc` inteiro do 5.8 no formato do 5.0."""
    versao, sub, registros = le(fxc58, b"FXC")
    if sub != FXC_SUB_58 or len(registros[0]) != FXC_58:
        raise FxInvalido(f".fxc de sub {sub} e registro de {len(registros[0])} bytes: nao e o do 5.8")
    return grava(b"FXC", versao, FXC_SUB_50, [fxc_58_para_50(r) for r in registros])
