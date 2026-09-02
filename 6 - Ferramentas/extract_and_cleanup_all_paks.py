"""
Script para extrair todos os arquivos .PAK em D:\AION CLASSIC 5.0 - EMULADOR\5 - Documentação e Referências\4 - Client 5.0 - Dados Extraidos\data,
garantindo a integridade dos dados (CRC32 exato e tamanho exato),
preservando a codificacao e formato original dos arquivos (.xml, .bxml, .dds, .cgf, etc.)
e, apos confirmacao de 100% de sucesso em todos os PAKs, excluir os arquivos .PAK.
"""
import os
import sys
import struct
import zlib

FIM_DO_DIRETORIO = b"\xaf\xb4\xfa\xf9"   # PK\5\6
ENTRADA_CENTRAL = b"\xaf\xb4\xfe\xfd"    # PK\1\2
CABECALHO_LOCAL = b"\xaf\xb4\xfc\xfb"    # PK\3\4

# Tabela XOR de 1056 bytes
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
JANELA_XOR = 32

def decifra_inicio(dados):
    if not dados:
        return dados
    quantos = min(JANELA_XOR, len(dados))
    off = len(dados) & 0x3FF
    saida = bytearray(dados)
    for i in range(quantos):
        saida[i] ^= _XOR[off + i]
    return bytes(saida)

class Entrada:
    __slots__ = ("nome", "metodo", "tam_comprimido", "tam_original", "crc", "offset_local")
    def __init__(self, nome, metodo, tam_comprimido, tam_original, crc, offset_local):
        self.nome = nome
        self.metodo = metodo
        self.tam_comprimido = tam_comprimido
        self.tam_original = tam_original
        self.crc = crc
        self.offset_local = offset_local

def indice(d):
    limite = max(0, len(d) - 65536 - 22)
    i = d.rfind(FIM_DO_DIRETORIO, limite)
    if i < 0:
        raise ValueError("Fim do diretorio central (EOCD) nao encontrado")
    quantas = struct.unpack_from("<H", d, i + 10)[0]
    off_dir = struct.unpack_from("<I", d, i + 16)[0]

    entradas, o = [], off_dir
    for _ in range(quantas):
        if d[o:o + 4] != ENTRADA_CENTRAL:
            raise ValueError(f"Entrada central invalida em {o}")
        metodo = struct.unpack_from("<H", d, o + 10)[0]
        crc, tam_c, tam_o = struct.unpack_from("<III", d, o + 16)
        n_nome, n_extra, n_com = struct.unpack_from("<HHH", d, o + 28)
        off_local = struct.unpack_from("<I", d, o + 42)[0]
        nome = d[o + 46: o + 46 + n_nome].decode("utf-8", "replace")
        entradas.append(Entrada(nome, metodo, tam_c, tam_o, crc, off_local))
        o += 46 + n_nome + n_extra + n_com
    return entradas

def le_entrada(d, e):
    if d[e.offset_local:e.offset_local + 4] != CABECALHO_LOCAL:
        raise ValueError(f"Cabecalho local invalido em {e.offset_local} ({e.nome})")
    n_nome, n_extra = struct.unpack_from("<HH", d, e.offset_local + 26)
    ini = e.offset_local + 30 + n_nome + n_extra
    bruto = decifra_inicio(d[ini:ini + e.tam_comprimido])

    if e.metodo == 0:
        saida = bruto
    elif e.metodo == 8:
        saida = zlib.decompressobj(-15).decompress(bruto)
    else:
        raise ValueError(f"Metodo de compressao {e.metodo} nao suportado ({e.nome})")

    if len(saida) != e.tam_original:
        raise ValueError(f"{e.nome}: tamanho descomprimido {len(saida)} != esperado {e.tam_original}")
    if (zlib.crc32(saida) & 0xFFFFFFFF) != e.crc:
        raise ValueError(f"{e.nome}: CRC32 falhou (esperado {hex(e.crc)}, obtido {hex(zlib.crc32(saida) & 0xFFFFFFFF)})")
    return saida

def main():
    base_dir = r"D:\AION CLASSIC 5.0 - EMULADOR\5 - Documentação e Referências\4 - Client 5.0 - Dados Extraidos\data"
    print("=" * 80)
    print(f"INICIANDO EXTRACAO E AUDITORIA COMPLETA DE PAKS EM: {base_dir}")
    print("=" * 80)

    paks = []
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.lower().endswith(".pak"):
                paks.append(os.path.join(root, f))

    print(f"Total de arquivos .PAK encontrados: {len(paks)}")

    total_extracted_files = 0
    total_extracted_bytes = 0
    pak_results = {}
    all_errors = []

    for idx, pak_path in enumerate(sorted(paks), 1):
        pak_dir = os.path.dirname(pak_path)
        pak_name = os.path.relpath(pak_path, base_dir)
        try:
            with open(pak_path, "rb") as f:
                d = f.read()
            entradas = indice(d)
        except Exception as e:
            err = f"ERRO ao abrir PAK {pak_name}: {e}"
            print(f"[{idx}/{len(paks)}] {err}")
            all_errors.append((pak_path, err))
            continue

        pak_ok = 0
        pak_fail = 0

        for e in entradas:
            if e.nome.endswith("/") or not e.nome:
                continue
            try:
                data = le_entrada(d, e)

                out_path = os.path.join(pak_dir, e.nome.replace("\\", "/"))
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, "wb") as out_f:
                    out_f.write(data)

                pak_ok += 1
                total_extracted_files += 1
                total_extracted_bytes += len(data)
            except Exception as ex:
                pak_fail += 1
                err = f"ERRO ao extrair '{e.nome}' de {pak_name}: {ex}"
                print(f"    {err}")
                all_errors.append((pak_path, err))

        print(f"[{idx}/{len(paks)}] {pak_name}: {pak_ok} arquivos extraidos ({pak_fail} falhas)")
        pak_results[pak_path] = (pak_ok, pak_fail)

    print("\n" + "=" * 80)
    print("RESUMO DA EXTRACAO:")
    print(f"  PAKs processados com sucesso: {len([p for p, (ok, f) in pak_results.items() if f == 0])}/{len(paks)}")
    print(f"  Total de arquivos extraidos: {total_extracted_files}")
    print(f"  Total de bytes descomprimidos: {total_extracted_bytes:,} bytes ({total_extracted_bytes / (1024*1024):.2f} MB)")
    print(f"  Total de falhas: {len(all_errors)}")
    print("=" * 80)

    if all_errors:
        print("\n[ERRO CRITICO] Ocorreram falhas durante a extracao. Os arquivos .PAK NAO serao excluidos:")
        for pak_p, err in all_errors[:10]:
            print(f"  - {err}")
        return 1

    print("\n[CONFIRMACAO 100% OK] Todos os arquivos PAK foram extraidos e validados com sucesso (CRC32 e tamanhos exatos)!")
    print("Excluindo arquivos .PAK mantendo apenas o conteudo extraido...")

    deleted_paks = 0
    for pak_path in paks:
        try:
            os.remove(pak_path)
            deleted_paks += 1
        except Exception as e:
            print(f"Erro ao remover {pak_path}: {e}")

    print(f"Total de arquivos .PAK excluidos com sucesso: {deleted_paks}/{len(paks)}")
    print("Processo finalizado com 100% de sucesso!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
