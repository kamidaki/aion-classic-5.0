"""
Exporta uma sessao capturada do game server para o formato que o motor de replay le.

Formato, repetido ate o fim do arquivo:

    [u8 direcao]  0 = servidor->cliente, 1 = cliente->servidor
    [u16 opcode]  little-endian, ja decifrado
    [u32 tamanho] little-endian, tamanho do payload
    [payload]

O payload nao inclui o prelude (opcode, SERVER_BYTE, checksum) -- ele e remontado no envio.

O nome da conta capturada aparece dentro dos payloads e e trocado por um neutro do mesmo tamanho,
porque o arquivo gerado acompanha o emulador quando ele e compartilhado. `--sem-anonimizar` mantem
os bytes originais, para quando a comparacao com o pcap precisar bater exatamente.

Uso: python tools/export_replay.py build/capture/gf-login.pcapng build/replay.bin
"""
import argparse
import struct
import subprocess

TSHARK = r"C:/Program Files/Wireshark/tshark.exe"

# Nome da conta que estava logada na captura, e o neutro que entra no lugar. Os dois precisam ter o
# mesmo numero de caracteres: o campo tem tamanho fixo, e encurtar deslocaria o resto do pacote.
NOME_DE_CONTA_CAPTURADO = "niZZin"
NOME_DE_CONTA_NEUTRO = "player"
STATIC_KEY = b"nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9"


def gera_chave(seed):
    s = (seed - 0x3FF2CC87) & 0xFFFFFFFF
    s ^= 0xCD92E451
    return (s ^ 0x87546CA100000000) & 0xFFFFFFFFFFFFFFFF


def decifra(chave, dados):
    kb = chave.to_bytes(8, "little")
    primeiro = kb[0]
    d = bytearray(dados)
    for i in range(len(d) - 1, 0, -1):
        d[i] ^= kb[i & 7]
        d[i] ^= STATIC_KEY[i & 63]
        d[i] ^= d[i - 1]
    d[0] ^= primeiro
    return bytes(d), (chave + len(d)) & 0xFFFFFFFFFFFFFFFF


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pcap")
    ap.add_argument("saida")
    ap.add_argument("--porta", type=int, default=7777)
    ap.add_argument("--sem-anonimizar", action="store_true",
                    help="mantem o nome da conta capturada nos payloads")
    args = ap.parse_args()

    de = NOME_DE_CONTA_CAPTURADO.encode("utf-16-le")
    para = NOME_DE_CONTA_NEUTRO.encode("utf-16-le")
    assert len(de) == len(para), "os dois nomes precisam ter o mesmo tamanho"

    campos = subprocess.run(
        [TSHARK, "-r", args.pcap, "-Y", f"tcp.port=={args.porta} && tcp.len>0",
         "-T", "fields", "-e", "tcp.srcport", "-e", "tcp.payload"],
        capture_output=True, text=True).stdout

    buf = {"S": bytearray(), "C": bytearray()}
    chave = {"S": None, "C": None}
    registros = []
    seed = None

    for linha in campos.splitlines():
        p = linha.split("\t")
        if len(p) != 2 or not p[1]:
            continue
        d = "S" if int(p[0]) == args.porta else "C"
        buf[d].extend(bytes.fromhex(p[1].replace(":", "")))

        while len(buf[d]) >= 2:
            tam = int.from_bytes(buf[d][0:2], "little")
            if tam < 7 or len(buf[d]) < tam:
                break
            bruto = bytes(buf[d][:tam])
            del buf[d][:tam]

            if chave["S"] is None:
                seed = int.from_bytes(bruto[7:11], "little")
                chave["S"] = chave["C"] = gera_chave(seed)
                continue        # o S_KEY e gerado pelo servidor, nao se reproduz

            corpo, chave[d] = decifra(chave[d], bruto[2:])
            cif = int.from_bytes(corpo[0:2], "little")
            if int.from_bytes(corpo[3:5], "little") != (~cif) & 0xFFFF:
                print("checksum invalido -- decriptacao dessincronizou")
                return
            op = ((cif ^ 0xD4) - 0xC4) & 0xFFFF if d == "S" else ((cif ^ 0x36) - 0xC4) & 0xFFFF
            registros.append((0 if d == "S" else 1, op, corpo[5:]))

    trocados = 0
    with open(args.saida, "wb") as fh:
        for direcao, op, payload in registros:
            if not args.sem_anonimizar and de in payload:
                trocados += payload.count(de)
                payload = payload.replace(de, para)
            fh.write(struct.pack("<BHI", direcao, op, len(payload)))
            fh.write(payload)

    if trocados:
        print(f"nome da conta trocado por '{NOME_DE_CONTA_NEUTRO}' em {trocados} lugar(es)")

    n_srv = sum(1 for d, _, _ in registros if d == 0)
    print(f"{len(registros)} pacotes ({n_srv} do servidor, {len(registros)-n_srv} do cliente) "
          f"-> {args.saida}")


if __name__ == "__main__":
    main()
