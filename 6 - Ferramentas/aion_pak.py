"""Le os arquivos `.pak` do cliente do Aion.

**O formato e um ZIP com duas obfuscacoes por cima.** A estrutura -- diretorio central, nomes,
tamanhos, offsets, CRC -- e ZIP padrao, e os dados sao deflate normal. O que a NCsoft mudou foi:

1. **As quatro assinaturas estao invertidas por XOR 0xFF**, para o arquivo nao abrir num
   descompactador qualquer.
2. **Os primeiros 32 bytes de cada fluxo comprimido vao XORados** com uma fatia de uma tabela de
   1056 bytes, indexada pelo proprio tamanho comprimido (ver [`decifra_inicio`]). E por isso que
   varrer o arquivo inteiro atras de um deflate valido nao acha nada: o comeco de todo fluxo esta
   embaralhado, e deflate nao tolera um byte errado no cabecalho.

As assinaturas:

```text
no pak         XOR 0xFF      o que e
AF B4 FC FB -> 50 4B 03 04   PK\\3\\4  cabecalho local
AF B4 FE FD -> 50 4B 01 02   PK\\1\\2  entrada do diretorio central
AF B4 FA F9 -> 50 4B 05 06   PK\\5\\6  fim do diretorio central
AF B4 F9 F8 -> 50 4B 06 07   PK\\6\\7  fim do diretorio, zip64
```

A tabela de XOR e o tamanho de 32 bytes sairam do desempacotador em Rust do projeto vizinho
(`AionEMULATION/AionEMU/EmuRustDurak/pak/src/main.rs`), que e somente leitura -- por isso a
reimplementacao aqui. Ver a memoria `aionemu-somente-leitura`.

**Nao troque as assinaturas com um replace global.** A sequencia de quatro bytes tambem aparece
dentro dos dados comprimidos, e trocar la corrompe o deflate ("invalid distance too far back").
Este modulo anda pela estrutura e le cada campo no lugar certo, sem reescrever byte nenhum.

Uso:

    python tools/aion_pak.py <arquivo.pak>                 lista o conteudo
    python tools/aion_pak.py <arquivo.pak> -x <destino>    extrai
    python tools/aion_pak.py <pasta> -x <destino> -r       extrai todos os .pak da pasta
    ... --dados                                            so .xml, .csv e .txt

O `--dados` importa: dois tercos dos paks do cliente sao icone `.dds`, som e textura, que nao
servem para o servidor. Filtrando, 302 paks viram 595 MB em vez de dezenas de GB.
"""
import os
import struct
import sys
import zlib

# As assinaturas do ZIP, ja invertidas como aparecem no arquivo.
FIM_DO_DIRETORIO = b"\xaf\xb4\xfa\xf9"   # PK\5\6
ENTRADA_CENTRAL = b"\xaf\xb4\xfe\xfd"    # PK\1\2
CABECALHO_LOCAL = b"\xaf\xb4\xfc\xfb"    # PK\3\4


# A tabela que embaralha o inicio de cada fluxo. 1056 bytes: o offset chega a 1023
# (`tamanho & 0x3FF`) e a janela e de 32, entao 1023 + 32 = 1055 cabe justo.
_XOR = bytes.fromhex(
    "86fa1a1c07bdd864ceee5988cda91d06f73d315883a15c7edfa6509e89a812d2"
    "254975e2070feb01974a6635ab329da74ea289620f5541c552101f47b0a063a6"
    "f01c1c4c9b3cace2b34e9ff1a4912982e4760d8d4fa3344acc1cc718488efe18"
    "790887288e24b76b38f258012da8580e9c5429cfa1ae0ad23b4a10f8d819317d"
    "f3ae1b90d22f16c7e53bccefe1e12c8600dd35678d25fced321fa91a126db0f7"
    "3db61fe8814d36e72530219086300eee40be6edac13aaff2ec282cf1cd449872"
    "dacdc6d9dff7ee8804e16200080ecd1637abf9f514aa2e004ef818410bd96f9b"
    "faad2b54562e7f2c3b6a82a17c7ca68f665ee7cf83b9eafce231d410f3f422ec"
    "73144f9478798f1e29ea5f211e0837b8f69a2dc53634c197dc75b2add7e304a7"
    "c0c91c1a00e92d6fd68dbc7352c08ab6ba2ca67d7b6ff4471a72e9b2307dd4d3"
    "099c65b0d017cffcf2ff46d2a64311762be51de5c9472f4b1bdd9afd9d20b643"
    "1a64e368f3215768d4048fc3ceafa3ab69a33c34be1f84a80e74cbb7e6b1398d"
    "68003a9b9cb1091c7d521512a6b083d340479be422e36e30c4fc6f4ffe9f5114"
    "1357f1eb25f7954c92b63cd03479593320beb8bfe00ad277bc435c7dfce15900"
    "de5a7d4411ac13f264844f5da2c436d723faf8d1148df9dd171d524122f51a42"
    "39fe36d50a1001d2ea12825a48d294950af7ab70f7f29889a168f9e1d6e1bd92"
    "38455f19e2ea4676c5c3f2b49f7053093fb8063af346c86acd0ae3f0aa34d972"
    "983423d1968c32323b00a39e4fedbc97d44a2615961d0e36b8ee864557046d2b"
    "c0db910a46ce7c1f3c3a81942226826d83bd132d9691536c260c44febdeedacc"
    "bd52a6113e10422060eb5f5b0d7cbb80ac2fb9f9d24aeb5480606285e51af030"
    "45b74482ef3a0ce0e594fafd2ed9eb8d5ac2ef39517192fadbef148800ffe3f6"
    "b5343440f5bbc8d3b5bdf6cfc7b1f9183da274ef40bc6b39f2c86e0064785288"
    "13f42774148fce345ef9e06d47fc386db003ed6cf66800ac2bfe732c949e3f17"
    "0c33b98f3334de0518e12bb9423f5fa2b41ee945f33843bb8eb00a9439eeff9a"
    "f42d6c4b66b11e0fc21832e174ff9094f238dd56dc789196d10403092139b2d4"
    "cc2aa8abe8991ce7e4433b58c15954e8bd9c28c681fcad334f2416a047d14c4d"
    "397ac1f71d04cfe7ae1771d937dc9c0a0e9d0e04d724c1500c49e3bcca988955"
    "8673f1c38d8f9934f74be7690ab0c12f8597bfc3fdd06275b1adf304f3f37706"
    "aa775ae7eb673fb540a19c5396fd85536eed52053b6e89ef9598b66634d08a3f"
    "44ea06861339ef20ade4732c6177103db90bc20cfdf299d8b157831b24a6a0ab"
    "973ee509073f43ed12e336ce1658f2780063f767dcd95f0daa3e9aa38372feba"
    "92e9d422f0383861e2799b5e8a6227598471c0eb95280d34cbab25c63bbc52a5"
    "ca6b93ca236d358741873e48b9df0efd30b8d1b810683dbc090431945c91af6c"
)
assert len(_XOR) == 1056

#: Quantos bytes do inicio de cada fluxo vao XORados.
JANELA_XOR = 32


def decifra_inicio(dados):
    """Desfaz o XOR do inicio de um fluxo comprimido.

    O offset na tabela e o **tamanho comprimido** mascarado com `0x3FF`. Como a mesma conta vale
    na ida e na volta, aplicar de novo re-embaralha -- a operacao e a sua propria inversa.
    """
    if not dados:
        return dados
    quantos = min(JANELA_XOR, len(dados))
    off = len(dados) & 0x3FF
    saida = bytearray(dados)
    for i in range(quantos):
        saida[i] ^= _XOR[off + i]
    return bytes(saida)


class PakInvalido(Exception):
    pass


class Entrada:
    """Um arquivo dentro do pak."""

    __slots__ = ("nome", "metodo", "tam_comprimido", "tam_original", "crc", "offset_local")

    def __init__(self, nome, metodo, tam_comprimido, tam_original, crc, offset_local):
        self.nome = nome
        self.metodo = metodo
        self.tam_comprimido = tam_comprimido
        self.tam_original = tam_original
        self.crc = crc
        self.offset_local = offset_local

    def __repr__(self):
        return f"<Entrada {self.nome!r} {self.tam_original}b>"


def _acha_fim_do_diretorio(d):
    """O EOCD fica no fim do arquivo; o comentario final pode empurrar ate 64 KB."""
    limite = max(0, len(d) - 65536 - 22)
    i = d.rfind(FIM_DO_DIRETORIO, limite)
    if i < 0:
        raise PakInvalido("nao achei o fim do diretorio central (PK\\5\\6 invertido)")
    return i


def indice(d):
    """Le o diretorio central e devolve a lista de [`Entrada`]."""
    fim = _acha_fim_do_diretorio(d)
    # No EOCD: total de entradas em +10, tamanho do diretorio em +12, offset dele em +16.
    quantas = struct.unpack_from("<H", d, fim + 10)[0]
    off_dir = struct.unpack_from("<I", d, fim + 16)[0]

    entradas, o = [], off_dir
    for _ in range(quantas):
        if d[o:o + 4] != ENTRADA_CENTRAL:
            raise PakInvalido(f"entrada do diretorio fora do lugar em {o}")
        metodo = struct.unpack_from("<H", d, o + 10)[0]
        crc, tam_c, tam_o = struct.unpack_from("<III", d, o + 16)
        n_nome, n_extra, n_com = struct.unpack_from("<HHH", d, o + 28)
        off_local = struct.unpack_from("<I", d, o + 42)[0]
        nome = d[o + 46: o + 46 + n_nome].decode("utf-8", "replace")
        entradas.append(Entrada(nome, metodo, tam_c, tam_o, crc, off_local))
        o += 46 + n_nome + n_extra + n_com
    return entradas


def le(d, e):
    """Devolve os bytes de uma entrada, ja descomprimidos."""
    if d[e.offset_local:e.offset_local + 4] != CABECALHO_LOCAL:
        raise PakInvalido(f"cabecalho local fora do lugar em {e.offset_local} ({e.nome})")
    n_nome, n_extra = struct.unpack_from("<HH", d, e.offset_local + 26)
    ini = e.offset_local + 30 + n_nome + n_extra
    bruto = decifra_inicio(d[ini:ini + e.tam_comprimido])

    if e.metodo == 0:
        saida = bruto
    elif e.metodo == 8:
        saida = zlib.decompressobj(-15).decompress(bruto)
    else:
        raise PakInvalido(f"metodo de compressao {e.metodo} nao suportado ({e.nome})")

    if len(saida) != e.tam_original:
        raise PakInvalido(
            f"{e.nome}: saiu com {len(saida)} bytes, o diretorio diz {e.tam_original}"
        )
    if zlib.crc32(saida) & 0xFFFFFFFF != e.crc:
        raise PakInvalido(f"{e.nome}: CRC nao fecha")
    return saida


def abre(caminho):
    """`(bytes do arquivo, lista de entradas)`."""
    with open(caminho, "rb") as f:
        d = f.read()
    return d, indice(d)


#: Extensoes que valem como "dado" para o servidor.
EXT_DE_DADOS = (".xml", ".csv", ".txt")


def extrai(caminho, destino, so_dados=False):
    """Extrai um `.pak`. Devolve `(quantos, quantos falharam)`.

    Com `so_dados`, pula tudo que nao for [`EXT_DE_DADOS`] -- icone, som e textura ficam de fora.
    """
    d, entradas = abre(caminho)
    ok = falhas = 0
    for e in entradas:
        if e.nome.endswith("/"):
            continue
        if so_dados and not e.nome.lower().endswith(EXT_DE_DADOS):
            continue
        try:
            dados = le(d, e)
        except Exception as erro:
            print(f"    ERRO {e.nome}: {erro}")
            falhas += 1
            continue
        alvo = os.path.join(destino, e.nome.replace("\\", "/"))
        os.makedirs(os.path.dirname(alvo) or ".", exist_ok=True)
        with open(alvo, "wb") as f:
            f.write(dados)
        ok += 1
    return ok, falhas


def _todos_os_paks(raiz):
    for base, _dirs, arqs in os.walk(raiz):
        for a in arqs:
            if a.lower().endswith(".pak"):
                yield os.path.join(base, a)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    alvo = argv[0]
    destino = None
    if "-x" in argv:
        destino = argv[argv.index("-x") + 1]
    recursivo = "-r" in argv
    so_dados = "--dados" in argv

    paks = list(_todos_os_paks(alvo)) if (os.path.isdir(alvo) and recursivo) else [alvo]

    total_ok = total_falha = total_ent = 0
    for p in paks:
        try:
            d, entradas = abre(p)
        except Exception as erro:
            print(f"{p}: NAO ABRIU -- {erro}")
            continue
        total_ent += len(entradas)
        if destino is None:
            print(f"\n{p}  ({len(entradas)} entradas)")
            for e in entradas[:20]:
                print(f"   {e.tam_original:>10}  {e.nome}")
            if len(entradas) > 20:
                print(f"   ... e mais {len(entradas) - 20}")
        else:
            sub = destino
            if len(paks) > 1:
                rel = os.path.relpath(os.path.dirname(p), alvo)
                sub = os.path.join(destino, rel) if rel != "." else destino
            ok, falhas = extrai(p, sub, so_dados)
            total_ok += ok
            total_falha += falhas
            print(f"{p}: {ok} extraidos" + (f", {falhas} falharam" if falhas else ""))

    if destino is not None:
        print(f"\ntotal: {total_ok} arquivos extraidos, {total_falha} falharam")
    else:
        print(f"\ntotal: {total_ent} entradas em {len(paks)} pak(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
