# -*- coding: utf-8 -*-
"""Escolhe um subconjunto da rajada reproduzida, para achar qual pacote destrava a entrada.

O `RajadaOficial` le `data/diagnostico/rajada_oficial.txt`. Este script reescreve esse arquivo a
partir da copia integra (`rajada_oficial.COMPLETA.txt`), mantendo so as linhas pedidas -- assim da
para bissectar reiniciando o launcher, sem recompilar nada.

    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/Ferramentas Python/bissecta_rajada.py" listar
    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/Ferramentas Python/bissecta_rajada.py" 0-28          # so as 29 primeiras
    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/Ferramentas Python/bissecta_rajada.py" 0x0089,0x01B5 # so estes opcodes
    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/Ferramentas Python/bissecta_rajada.py" tudo
"""
import os
import sys

BASE = os.path.join("Emulador - Produto Final", "GameServer", "data", "diagnostico")
COMPLETA = os.path.join(BASE, "rajada_oficial.COMPLETA.txt")
ATIVA = os.path.join(BASE, "rajada_oficial.txt")


def le():
    cabecalho, pacotes = [], []
    for linha in open(COMPLETA, encoding="utf-8"):
        (cabecalho if linha.startswith("#") else pacotes).append(linha.rstrip("\n"))
    return cabecalho, [p for p in pacotes if p.strip()]


def main():
    if not os.path.exists(COMPLETA):
        print("Falta %s" % COMPLETA)
        return 2
    cabecalho, pacotes = le()
    arg = sys.argv[1] if len(sys.argv) > 1 else "listar"

    if arg == "listar":
        for i, p in enumerate(pacotes):
            campos = p.split(" ")
            print("  %2d  %s  %5d bytes" % (i, campos[0], len(campos[1]) // 2))
        print("total: %d pacotes" % len(pacotes))
        return 0

    if arg == "tudo":
        escolhidos = list(range(len(pacotes)))
    elif "-" in arg and not arg.startswith("0x"):
        ini, fim = arg.split("-")
        escolhidos = list(range(int(ini), int(fim) + 1))
    elif arg.startswith("0x"):
        alvos = {a.strip().lower() for a in arg.split(",")}
        escolhidos = [i for i, p in enumerate(pacotes) if p.split(" ")[0].lower() in alvos]
    else:
        escolhidos = [int(a) for a in arg.split(",")]

    escolhidos = [i for i in escolhidos if 0 <= i < len(pacotes)]
    saida = cabecalho + ["# subconjunto ativo: %s (%d de %d)" % (arg, len(escolhidos), len(pacotes))]
    saida += [pacotes[i] for i in escolhidos]
    open(ATIVA, "w", encoding="utf-8").write("\n".join(saida) + "\n")
    print("ativos: %d de %d pacotes" % (len(escolhidos), len(pacotes)))
    for i in escolhidos:
        print("   %2d  %s" % (i, pacotes[i].split(" ")[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
