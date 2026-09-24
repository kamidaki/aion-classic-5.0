"""Compara a lista de pacotes de dois `Game.dll` do cliente Aion.

O `Game.dll` carrega, em texto claro, os **nomes** do enum de pacotes -- `C_*` para o que o
cliente manda e `S_*` para o que ele espera receber. Comparar as duas listas entre duas versoes
do cliente responde, sem capturar nada, se o patch mexeu no protocolo e o que ele acrescentou.

    python tools/diff_pacotes_cliente.py <Game.dll antigo> <Game.dll novo>

**O que isto NAO responde: o numero de cada opcode.** O nome esta no binario, mas a tabela que
liga nome a numero nao esta -- o arquivo em disco vem empacotado por um protetor (as secoes de
nome aleatorio e a `.taggant` denunciam), e uma varredura por ponteiro de 8 bytes para essas
strings devolve **zero** ocorrencias no 4.5 e no 5.0. Os nomes que sobram sao restos no pool de
strings do compilador, e a ordem deles la e a do linkeditor, nao a do enum: o bloco do 4.5 comeca
em `C_REMOVE_BUDDY` e o do 5.0 em `C_CUSTOM_ANIM`.

Entao o resultado util e o **conjunto**: quantos entraram, quantos sairam, e quais. Pacote que
sai e o que costuma renumerar tudo que vinha depois; pacote que so entra costuma ser acrescentado
no fim. Para saber o numero de verdade, so a captura -- ver `tools/aion_pcap.py --censo-compara`.
"""
import re
import sys


def nomes(caminho, prefixo):
    """Todos os nomes de pacote com aquele prefixo, como conjunto."""
    with open(caminho, "rb") as f:
        d = f.read()
    padrao = prefixo + rb"[A-Z0-9_]{2,48}\x00"
    return set(m.group(0).rstrip(b"\x00").decode("ascii") for m in re.finditer(padrao, d))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    antigo, novo = argv[0], argv[1]

    for prefixo, rotulo in ((b"C_", "CLIENTE -> SERVIDOR"), (b"S_", "SERVIDOR -> CLIENTE")):
        a, b = nomes(antigo, prefixo), nomes(novo, prefixo)
        entraram, sairam = sorted(b - a), sorted(a - b)
        print("=== {} ===  antigo={}  novo={}".format(rotulo, len(a), len(b)))
        print("  entraram ({}):".format(len(entraram)))
        for n in entraram:
            print("     + {}".format(n))
        print("  sairam ({}):".format(len(sairam)))
        for n in sairam:
            print("     - {}".format(n))
        if sairam:
            print("  [!] pacote que sai costuma renumerar tudo que vinha depois dele.")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
