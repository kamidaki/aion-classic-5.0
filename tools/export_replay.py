"""
Exporta uma sessao capturada do game server para o formato que o motor de replay le.

Formato, repetido ate o fim do arquivo:

    [u8 direcao]  0 = servidor->cliente, 1 = cliente->servidor
    [u16 opcode]  little-endian, ja decifrado
    [u32 tamanho] little-endian, tamanho do payload
    [payload]

O payload nao inclui o prelude (opcode, SERVER_BYTE, checksum) -- ele e remontado no envio.

O arquivo gerado acompanha o emulador quando ele e compartilhado, entao duas coisas saem dele:

  - o nome da conta capturada, trocado por um neutro do MESMO tamanho (o campo tem tamanho fixo,
    e encurtar deslocaria o resto do pacote);
  - o token de autenticacao, que viaja em base64 no C_HQ_LOGIN e no S_REPLY_NP_AUTH_TOKEN, mais o
    GUID de sessao. Sao credenciais da conta que gravou -- nao podem sair da maquina.

`--sem-anonimizar` mantem os bytes originais, para quando a comparacao com o pcap precisar bater
exatamente. Nesse caso o arquivo nao pode ser compartilhado.

Uso: python tools/export_replay.py build/capture/gf-login.pcapng build/replay.bin
"""
import argparse
import re
import struct
import subprocess

TSHARK = r"C:/Program Files/Wireshark/tshark.exe"

# Nome da conta que estava logada na captura, e o neutro que entra no lugar. Os dois precisam ter o
# mesmo numero de caracteres: o campo tem tamanho fixo, e encurtar deslocaria o resto do pacote.
NOME_DE_CONTA_CAPTURADO = "niZZin"
NOME_DE_CONTA_NEUTRO = "player"
STATIC_KEY = b"nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9"

# O token de login e um par de GUIDs em base64, e o GUID de sessao vem em claro logo depois. Os dois
# sao substituidos por bytes do mesmo tamanho -- o formato continua valido, o segredo nao vai junto.
TOKEN_BASE64 = re.compile(rb"[A-Za-z0-9+/]{40,}={0,2}")
GUID = re.compile(rb"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")


def tira_credenciais(payload):
    """Devolve (payload limpo, quantos segredos foram trocados)."""
    n = 0

    def por_zeros(m):
        nonlocal n
        n += 1
        return b"A" * len(m.group())

    def por_guid_nulo(m):
        nonlocal n
        n += 1
        return b"00000000-0000-0000-0000-000000000000"

    payload = TOKEN_BASE64.sub(por_zeros, payload)
    payload = GUID.sub(por_guid_nulo, payload)
    return payload, n


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
    dessincronizou = False

    for linha in campos.splitlines():
        if dessincronizou:
            break
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
                dessincronizou = True
                break
            op = ((cif ^ 0xD4) - 0xC4) & 0xFFFF if d == "S" else ((cif ^ 0x36) - 0xC4) & 0xFFFF
            registros.append((0 if d == "S" else 1, op, corpo[5:]))

    if dessincronizou:
        print(f"checksum invalido no pacote {len(registros) + 1} -- dai em diante a captura foi "
              f"descartada.")
        print("No fim do arquivo isso e normal: a gravacao foi cortada no meio de um frame. "
              "No meio, a sessao se perdeu ali e o replay para nesse ponto.")

    if not registros:
        print("nada para exportar -- o arquivo de saida nao foi tocado")
        return

    trocados = 0
    segredos = 0
    with open(args.saida, "wb") as fh:
        for direcao, op, payload in registros:
            if not args.sem_anonimizar:
                if de in payload:
                    trocados += payload.count(de)
                    payload = payload.replace(de, para)
                payload, n = tira_credenciais(payload)
                segredos += n
            fh.write(struct.pack("<BHI", direcao, op, len(payload)))
            fh.write(payload)

    if trocados:
        print(f"nome da conta trocado por '{NOME_DE_CONTA_NEUTRO}' em {trocados} lugar(es)")
    if segredos:
        print(f"token de login e GUID de sessao apagados em {segredos} lugar(es)")
    if args.sem_anonimizar:
        print("ATENCAO: --sem-anonimizar -- este arquivo contem as credenciais da conta capturada")

    n_srv = sum(1 for d, _, _ in registros if d == 0)
    print(f"{len(registros)} pacotes ({n_srv} do servidor, {len(registros)-n_srv} do cliente) "
          f"-> {args.saida}")


if __name__ == "__main__":
    main()
