"""
Reconstroi a linha do tempo do game server a partir de um pcap.

O primeiro pacote (S_KEY) viaja em claro e traz o seed; com ele a sessao inteira e decifrada.
Cliente e servidor tem chaves independentes que avancam pelo tamanho de cada pacote, e a chave
nao avanca no S_KEY.

Uso:  python tools/decode_game.py build/capture/gf-login.pcapng
      python tools/decode_game.py build/capture/gf-login.pcapng --ate 60
      python tools/decode_game.py build/capture/gf-login.pcapng --dump S_CHARACTER_LIST
"""
import argparse
import csv
import os
import subprocess
import sys

TSHARK = r"C:/Program Files/Wireshark/tshark.exe"
STATIC_KEY = b"nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9"
SUB_SEED, XOR_SEED_32, XOR_SEED_64 = 0x3FF2CC87, 0xCD92E451, 0x87546CA100000000
SERVER_BYTE = 0x65


def gera_chave(seed):
    s = (seed - SUB_SEED) & 0xFFFFFFFF
    s ^= XOR_SEED_32
    return (s ^ XOR_SEED_64) & 0xFFFFFFFFFFFFFFFF


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


def opcode_servidor(cifrado):
    return ((cifrado ^ 0xD4) - 0xC4) & 0xFFFF


def opcode_cliente(cifrado):
    return ((cifrado ^ 0x36) - 0xC4) & 0xFFFF


def quadros(pcap, porta):
    """Devolve (direcao, payload) por quadro TCP, em ordem cronologica."""
    campos = subprocess.run(
        [TSHARK, "-r", pcap, "-Y", f"tcp.port=={porta} && tcp.len>0",
         "-T", "fields", "-e", "tcp.srcport", "-e", "tcp.payload"],
        capture_output=True, text=True).stdout
    saida = []
    for linha in campos.splitlines():
        partes = linha.split("\t")
        if len(partes) != 2 or not partes[1]:
            continue
        origem = int(partes[0])
        dados = bytes.fromhex(partes[1].replace(":", ""))
        saida.append(("S" if origem == porta else "C", dados))
    return saida


def carrega_nomes():
    tabelas = {}
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "protocol")
    for lado, arq in (("S", "opcodes_server.csv"), ("C", "opcodes_client.csv")):
        d = {}
        with open(os.path.join(base, arq), encoding="utf-8") as fh:
            r = csv.reader(fh)
            next(r)
            for linha in r:
                d[int(linha[0])] = linha[2]
        tabelas[lado] = d
    return tabelas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pcap")
    ap.add_argument("--porta", type=int, default=7777)
    ap.add_argument("--ate", type=int, default=40, help="quantos pacotes mostrar")
    ap.add_argument("--dump", help="imprime o payload dos pacotes com este nome")
    args = ap.parse_args()

    nomes = carrega_nomes()
    buf = {"S": bytearray(), "C": bytearray()}
    chave = {"S": None, "C": None}
    mostrados = 0

    print(f"{'#':>4}  {'dir':<3} {'opcode':<7} {'nome':<38} {'bytes':>6}")
    print("-" * 66)

    for direcao, dados in quadros(args.pcap, args.porta):
        buf[direcao].extend(dados)

        while len(buf[direcao]) >= 2:
            tam = int.from_bytes(buf[direcao][0:2], "little")
            if tam < 7 or len(buf[direcao]) < tam:
                break
            bruto = bytes(buf[direcao][:tam])
            del buf[direcao][:tam]

            if chave["S"] is None:
                # primeiro pacote: S_KEY, em claro, carrega o seed
                seed = int.from_bytes(bruto[7:11], "little")
                chave["S"] = chave["C"] = gera_chave(seed)
                corpo = bruto[2:]
                mostrados += 1
                print(f"{mostrados:>4}  {'S':<3} {'0x047':<7} {'S_KEY (seed em claro)':<38} {tam:>6}")
                continue

            corpo, chave[direcao] = decifra(chave[direcao], bruto[2:])
            cif = int.from_bytes(corpo[0:2], "little")
            if int.from_bytes(corpo[3:5], "little") != (~cif) & 0xFFFF:
                print(f"  !! checksum invalido em {direcao} -- decriptacao dessincronizou")
                return
            op = opcode_servidor(cif) if direcao == "S" else opcode_cliente(cif)
            nome = nomes[direcao].get(op, "<sem nome na tabela>")

            mostrados += 1
            if mostrados <= args.ate:
                print(f"{mostrados:>4}  {direcao:<3} 0x{op:03x}   {nome:<38} {tam:>6}")

            if args.dump and args.dump == nome:
                payload = corpo[5:]
                print(f"\n      payload de {nome} ({len(payload)} bytes):")
                for off in range(0, min(len(payload), 512), 16):
                    ch = payload[off:off + 16]
                    txt = "".join(chr(b) if 32 <= b < 127 else "." for b in ch)
                    print(f"      {off:04x}  {' '.join(f'{b:02x}' for b in ch):<47}  {txt}")
                print()

            if mostrados > args.ate and not args.dump:
                return


if __name__ == "__main__":
    main()
