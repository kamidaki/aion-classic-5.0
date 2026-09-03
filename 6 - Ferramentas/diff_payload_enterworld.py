# -*- coding: utf-8 -*-
"""Compara o CORPO de cada pacote da nossa entrada no mundo com o da captura oficial.

O `compara_enterworld.py` responde "mandamos o pacote, e com o tamanho certo?". Quando o opcode e o
tamanho batem mas o cliente continua travando, a diferenca esta dentro do corpo -- e e isso que
este script mostra: para cada opcode presente dos dois lados, o primeiro byte que diverge, com o
contexto em volta e a leitura dos dois valores como u32 e float.

Exige o rastro gravado com o corpo inteiro:

    gameserver.network.wiretrace.bytes = 8192

Uso (da raiz do projeto):

    python "6 - Ferramentas/diff_payload_enterworld.py" [wiretrace.log] [captura.pcapng] [sessao]

Bytes que sao objectId, tempo ou coordenada divergem por natureza -- personagens diferentes. O que
interessa sao campos estruturais: contagens, tamanhos de lista, flags e enchimento.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aion_pcap

RASTRO = os.path.join("2 - Emulador [Produto Final]", "GameServer", "log", "wiretrace.log")
CAPTURA = os.path.join("5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0",
                       "Outros", "subida-1-60-2026-08-28.pcapng")
SESSAO = 1
ENTER_WORLD, LEVEL_READY = 0x0018, 0x0019
LINHA = re.compile(r"\d{6}\|([CS])\|0x([0-9A-Fa-f]{4})\|0x[0-9A-Fa-f]{4}\|(\d+)\|([^|]*)\|"
                   r"[^|]*\|[^|]*\|?([0-9a-f]*)")


def leituras(b, i):
    """Como o byte em `i` se le nos dois formatos que importam."""
    saida = []
    if i + 4 <= len(b):
        saida.append("u32=%d" % struct.unpack_from("<I", b, i)[0])
        f = struct.unpack_from("<f", b, i)[0]
        if -1e9 < f < 1e9:
            saida.append("f32=%.3f" % f)
    return "  ".join(saida)


def nossos():
    pacotes, dentro = [], False
    with open(RASTRO, encoding="utf-8", errors="replace") as f:
        for texto in f:
            m = LINHA.search(texto)
            if not m:
                continue
            lado, op, tam, nome, hexa = m.group(1), int(m.group(2), 16), int(m.group(3)), m.group(4), m.group(5)
            if lado == "C" and op == ENTER_WORLD:
                pacotes, dentro = [], True
                continue
            if not dentro:
                continue
            if lado == "C" and op == LEVEL_READY:
                break
            if lado == "S":
                pacotes.append((op, bytes.fromhex(hexa), tam, nome))
    return pacotes


def oficiais(caminho, sessao):
    s = aion_pcap.abre_todas(caminho)[sessao]
    linha = aion_pcap.intercalado(s)
    ini = next(i for i, e in enumerate(linha) if e[1] == "cliente" and e[2] == ENTER_WORLD)
    fim = next((i for i in range(ini + 1, len(linha))
                if linha[i][1] == "cliente" and linha[i][2] == LEVEL_READY), len(linha))
    return [(op, p) for _t, lado, op, p in linha[ini:fim] if lado == "servidor"]


def main():
    global RASTRO, CAPTURA, SESSAO
    if len(sys.argv) > 1:
        RASTRO = sys.argv[1]
    if len(sys.argv) > 2:
        CAPTURA = sys.argv[2]
    if len(sys.argv) > 3:
        SESSAO = int(sys.argv[3])

    nossa = nossos()
    if not nossa:
        print("Nao achei a janela de entrada no mundo em %s" % RASTRO)
        return 2
    truncados = [n for op, b, tam, n in nossa if len(b) < tam]
    if truncados:
        print("AVISO: %d pacotes vieram truncados no rastro. Suba"
              " `gameserver.network.wiretrace.bytes` e rode de novo.\n" % len(truncados))

    oficial = oficiais(CAPTURA, SESSAO)
    prim_of, prim_no = {}, {}
    for op, p in oficial:
        prim_of.setdefault(op, p)
    nomes = {}
    for op, b, _tam, nome in nossa:
        prim_no.setdefault(op, b)
        nomes.setdefault(op, nome)

    comuns = sorted(set(prim_of) & set(prim_no))
    print("opcodes presentes nos dois lados: %d\n" % len(comuns))
    iguais = []
    for op in comuns:
        a, b = prim_of[op], prim_no[op]
        if a == b:
            iguais.append(op)
            continue
        n = min(len(a), len(b))
        i = next((k for k in range(n) if a[k] != b[k]), n)
        print("0x%04X  %-32s oficial %dB  nosso %dB" % (op, nomes.get(op, "?"), len(a), len(b)))
        if i == n and len(a) != len(b):
            print("     iguais ate o fim do menor; diferem so no tamanho")
        else:
            print("     primeira diferenca no byte %d" % i)
            lo = max(0, i - 4)
            print("       oficial %s   %s" % (a[lo:i + 12].hex(' '), leituras(a, i)))
            print("       nosso   %s   %s" % (b[lo:i + 12].hex(' '), leituras(b, i)))
        print()
    print("identicos byte a byte (%d): %s"
          % (len(iguais), " ".join("0x%04X" % o for o in iguais)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
