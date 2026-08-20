"""
Sonda passiva na porta de login.

Todo servidor que testamos ate agora fala primeiro -- o AL manda SM_INIT assim que aceita a
conexao, e o auth-server do Rust manda o greeting. Com isso nunca soubemos se o cliente tem algo
a dizer por conta propria. Esta sonda nao manda nada: so aceita, escuta e registra o que vier,
com o tempo de cada bloco.

  python tools/probe_login.py            # escuta na 2106, silencio total
  python tools/probe_login.py --port 13001
  python tools/probe_login.py --reply-after 3   # fica em silencio 3s, depois envia bytes de teste

Se o cliente enviar algo sem ser provocado, esse e o primeiro pacote de verdade do protocolo --
e ai a conversa comeca a ser lida do lado certo.
"""
import argparse
import socket
import sys
import time


def hexdump(data, indent="    "):
    lines = []
    for off in range(0, len(data), 16):
        chunk = data[off:off + 16]
        hexa = " ".join(f"{b:02x}" for b in chunk)
        texto = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{indent}{off:04x}  {hexa:<47}  {texto}")
    return "\n".join(lines)


def descreve_framing(data):
    """O framing candidato: [u16 tamanho][u8 opcode]. Confere se o tamanho bate."""
    if len(data) < 3:
        return "curto demais para ter framing"
    declarado = int.from_bytes(data[0:2], "little")
    bate = "confere" if declarado == len(data) else f"NAO bate (recebido {len(data)})"
    return f"se [u16 tam][u8 opcode]: tam={declarado} ({bate}), opcode=0x{data[2]:02x}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=2106)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--reply-after", type=float, default=None,
                    help="segundos de silencio antes de enviar --reply-hex")
    ap.add_argument("--reply-hex", default="",
                    help="bytes a enviar depois do silencio, em hex")
    ap.add_argument("--timeout", type=float, default=60.0)
    args = ap.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.host, args.port))
    srv.listen(1)
    print(f"sonda escutando em {args.host}:{args.port} -- nao envia nada por conta propria")
    sys.stdout.flush()

    conn, addr = srv.accept()
    t0 = time.monotonic()
    print(f"[{0.0:6.2f}s] conexao de {addr[0]}:{addr[1]}")
    sys.stdout.flush()

    enviado = args.reply_after is None
    conn.settimeout(0.5)
    total = 0

    while time.monotonic() - t0 < args.timeout:
        if not enviado and time.monotonic() - t0 >= args.reply_after:
            payload = bytes.fromhex(args.reply_hex)
            if payload:
                conn.sendall(payload)
                print(f"[{time.monotonic()-t0:6.2f}s] enviados {len(payload)} bytes de teste")
                sys.stdout.flush()
            enviado = True

        try:
            data = conn.recv(65535)
        except socket.timeout:
            continue
        except ConnectionError as e:
            print(f"[{time.monotonic()-t0:6.2f}s] conexao caiu: {e}")
            break

        if not data:
            print(f"[{time.monotonic()-t0:6.2f}s] cliente fechou a conexao "
                  f"(total recebido: {total} bytes)")
            break

        total += len(data)
        print(f"[{time.monotonic()-t0:6.2f}s] <- {len(data)} bytes")
        print(f"    {descreve_framing(data)}")
        print(hexdump(data))
        sys.stdout.flush()

    if total == 0:
        print("\n>>> o cliente NAO enviou nada sem ser provocado: quem fala primeiro e o servidor")
    else:
        print(f"\n>>> o cliente falou primeiro: {total} bytes sem nenhum estimulo nosso")
    conn.close()
    srv.close()


if __name__ == "__main__":
    main()
