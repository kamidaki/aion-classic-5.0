"""
Decodifica a conversa com o auth server do Aion Classic (GameForge) a partir de um pcap.

O auth server e texto claro. O framing e:

    [u16 tamanho][u8 opcode][3 bytes zero][payload]

O tamanho inclui o proprio cabecalho de 6 bytes.

Uso: python tools/decode_auth.py build/capture/gf-login.pcapng
"""
import argparse
import base64
import subprocess
import sys

TSHARK = r"C:/Program Files/Wireshark/tshark.exe"

OPCODES_SERVIDOR = {0x05: "GREETING", 0x01: "LOGIN_OK", 0x02: "SERVER_LIST", 0x04: "SESSION_KEY"}
OPCODES_CLIENTE = {0x01: "CREDENTIALS", 0x02: "SERVER_SELECT"}

ENTRY_LEN = 63


def stream_bytes(pcap, port):
    """Devolve (do_servidor, do_cliente) como bytes, a partir do follow do tshark."""
    idx = subprocess.run(
        [TSHARK, "-r", pcap, "-Y", f"tcp.port=={port}", "-T", "fields", "-e", "tcp.stream"],
        capture_output=True, text=True).stdout.split()
    if not idx:
        sys.exit(f"nenhum stream na porta {port}")
    out = subprocess.run(
        [TSHARK, "-r", pcap, "-q", "-z", f"follow,tcp,hex,{idx[0]}"],
        capture_output=True, text=True).stdout

    servidor, cliente = bytearray(), bytearray()
    for linha in out.splitlines():
        if not linha.strip() or linha.startswith(("=", "Follow", "Filter", "Node")):
            continue
        # linhas do servidor vem indentadas com tab; as do cliente, nao
        do_servidor = linha.startswith("\t")
        campos = linha.strip().split()
        if len(campos) < 2:
            continue
        octetos = [c for c in campos[1:] if len(c) == 2 and all(d in "0123456789abcdefABCDEF" for d in c)]
        dados = bytes.fromhex("".join(octetos))
        (servidor if do_servidor else cliente).extend(dados)
    return bytes(servidor), bytes(cliente)


def pacotes(dados):
    off = 0
    while off + 6 <= len(dados):
        tam = int.from_bytes(dados[off:off + 2], "little")
        if tam < 6 or off + tam > len(dados):
            break
        yield dados[off:off + tam]
        off += tam


def strings_nulas(payload):
    return [p.decode("ascii", "replace") for p in payload.split(b"\x00") if p]


def decodifica_lista(payload):
    total = int.from_bytes(payload[0:2], "little")
    print(f"    servidores: {total}")
    corpo = payload[2:]
    for i in range(total):
        e = corpo[i * ENTRY_LEN:(i + 1) * ENTRY_LEN]
        if len(e) < ENTRY_LEN:
            break
        ip = e[13:].split(b"\x00")[0].decode("ascii", "replace")
        porta = int.from_bytes(e[53:55], "little")
        print(f"      [{i}] id=0x{e[5]:02x} tipo={e[1]} online={e[4]} "
              f"personagens={e[9]} {ip}:{porta}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pcap")
    ap.add_argument("--port", type=int, default=13001)
    ap.add_argument("--mostrar-token", action="store_true",
                    help="imprime o token de autenticacao; por padrao ele e ocultado")
    args = ap.parse_args()

    servidor, cliente = stream_bytes(args.pcap, args.port)
    print(f"auth server porta {args.port}: {len(servidor)} bytes do servidor, "
          f"{len(cliente)} do cliente\n")

    for rotulo, dados, mapa in (("SERVIDOR -> CLIENTE", servidor, OPCODES_SERVIDOR),
                                ("CLIENTE -> SERVIDOR", cliente, OPCODES_CLIENTE)):
        print(f"===== {rotulo} =====")
        for p in pacotes(dados):
            op = p[2]
            nome = mapa.get(op, "?")
            payload = p[6:]
            print(f"  0x{op:02x} {nome:<14} {len(p):>4} bytes")

            if nome == "GREETING":
                for s in strings_nulas(payload):
                    print(f"    {s}")
            elif nome == "CREDENTIALS":
                bruto = payload.split(b"\x00")[0]
                try:
                    claro = base64.b64decode(bruto).rstrip(b"\x00").decode("ascii", "replace")
                except Exception:
                    claro = "<nao e base64>"
                if args.mostrar_token:
                    print(f"    base64 -> {claro}")
                else:
                    partes = claro.split(":")
                    forma = ":".join("<uuid>" if len(x) == 36 else f"<{len(x)} chars>" for x in partes)
                    print(f"    base64 de {len(bruto)} chars -> {forma}   [ocultado]")
            elif nome == "LOGIN_OK":
                print(f"    conta=0x{int.from_bytes(payload[0:4],'little'):08x} "
                      f"chave=0x{int.from_bytes(payload[4:8],'little'):08x}")
            elif nome == "SERVER_LIST":
                decodifica_lista(payload)
            elif nome == "SERVER_SELECT":
                print(f"    servidor escolhido = 0x{int.from_bytes(payload[0:4],'little'):02x}")
            elif nome == "SESSION_KEY":
                print(f"    servidor=0x{int.from_bytes(payload[0:4],'little'):02x} "
                      f"chave=0x{int.from_bytes(payload[4:8],'little'):08x} "
                      f"erro=0x{int.from_bytes(payload[8:12],'little'):08x} "
                      f"extra=0x{int.from_bytes(payload[12:16],'little'):08x}")
        print()


if __name__ == "__main__":
    main()
