# -*- coding: utf-8 -*-
"""Compara a nossa rajada de entrada no mundo com a da captura oficial.

O `wiretrace.log` do GameServer (ligado por `gameserver.network.wiretrace = true`) registra todo
pacote que entra e sai, na ordem real, com o opcode ja decodificado e o tamanho do payload -- os
mesmos tres campos que o `aion_pcap.py` extrai da captura. Isso deixa as duas sequencias
diretamente comparaveis.

    python "6 - Ferramentas/compara_enterworld.py" [wiretrace.log] [captura.pcapng] [sessao]

A referencia padrao e `01_Login_World/Elyos`, que e um personagem **antigo**, com configuracao de
interface salva. Para comparar contra um personagem **recem-criado** — que e o caso de quem acabou
de entrar num servidor novo — use `Outros/subida-1-60` sessao 1, onde o personagem foi criado na
mesma sessao (ver o roteiro ao lado da captura). As duas rajadas diferem: o recem-criado nao
recebe nenhum `S_LOAD_CLIENT_SETTINGS`, por exemplo.

A janela comparada vai do `CM_ENTER_WORLD` (0x0018) ate o `CM_LEVEL_READY` (0x0019); quando o
`CM_LEVEL_READY` nao chega -- que e exatamente o defeito em investigacao -- vai ate o fim da
sessao. Rode a partir da raiz do projeto.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aion_pcap

CAPTURA = os.path.join("5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0",
                       "01_Login_World", "Elyos",
                       "01_Login_World_Elyos_2026-08-27_10-03-03_00001_20260827100304.pcapng")
RASTRO = os.path.join("2 - Emulador [Produto Final]", "GameServer", "log", "wiretrace.log")
TABELA = os.path.join("1 - Código Fonte [Emulador]", "GameServer", "src", "com", "aionemu",
                      "gameserver", "network", "aion", "ServerPacketsOpcodes.java")

ENTER_WORLD, LEVEL_READY = 0x0018, 0x0019
LINHA = re.compile(r"(\d{6})\|([CS])\|0x([0-9A-Fa-f]{4})\|0x[0-9A-Fa-f]{4}\|(\d+)\|([^|]*)\|"
                   r"[^|]*\|[^|]*\|?([0-9a-f]*)")


def nomes_das_classes():
    """{opcode: nome} da nossa tabela S->C, para dar nome ao que o oficial manda e nos nao."""
    if not os.path.exists(TABELA):
        return {}
    texto = open(TABELA, encoding="utf-8", errors="replace").read()
    achados = re.finditer(r"addPacketOpcode\(\s*(\w+)\.class\s*,\s*(0x[0-9A-Fa-f]+|\d+)", texto)
    return {int(m.group(2), 0): m.group(1) for m in achados}


def janela_oficial(caminho, sessao_alvo=None):
    """(opcode, tamanho) de cada pacote S->C entre o enter world e o level ready da captura."""
    sessoes = aion_pcap.abre_todas(caminho)
    if sessao_alvo is not None:
        sessoes = [sessoes[sessao_alvo]]
    for sessao in sessoes:
        linha = aion_pcap.intercalado(sessao)
        ini = next((i for i, e in enumerate(linha) if e[1] == "cliente" and e[2] == ENTER_WORLD), None)
        if ini is None:
            continue
        fim = next((i for i in range(ini + 1, len(linha))
                    if linha[i][1] == "cliente" and linha[i][2] == LEVEL_READY), len(linha))
        return [(op, len(p), p[:32].hex()) for _t, lado, op, p in linha[ini:fim] if lado == "servidor"]
    return []


def janela_nossa(caminho):
    """Mesma janela, lida do wiretrace.log. Usa a ULTIMA entrada no mundo do arquivo."""
    eventos = []
    with open(caminho, encoding="utf-8", errors="replace") as f:
        for texto in f:
            m = LINHA.search(texto)
            if m:
                eventos.append((m.group(2), int(m.group(3), 16), int(m.group(4)), m.group(5), m.group(6)))
    inicios = [i for i, e in enumerate(eventos) if e[0] == "C" and e[1] == ENTER_WORLD]
    if not inicios:
        return [], False
    ini = inicios[-1]
    fim = next((i for i in range(ini + 1, len(eventos))
                if eventos[i][0] == "C" and eventos[i][1] == LEVEL_READY), len(eventos))
    chegou = fim < len(eventos)
    return [(op, tam, nome, hx) for lado, op, tam, nome, hx in eventos[ini:fim] if lado == "S"], chegou


def resumo(pacotes, chave=lambda p: p[0]):
    conta = collections.Counter(chave(p) for p in pacotes)
    primeiro = {}
    for p in pacotes:
        primeiro.setdefault(chave(p), p[1])
    return conta, primeiro


def main():
    global RASTRO, CAPTURA
    sessao_alvo = None
    if len(sys.argv) > 1:
        RASTRO = sys.argv[1]
    if len(sys.argv) > 2:
        CAPTURA = sys.argv[2]
    if len(sys.argv) > 3:
        sessao_alvo = int(sys.argv[3])
    if not os.path.exists(RASTRO):
        print("Nao existe %s." % RASTRO)
        print("Ligue `gameserver.network.wiretrace = true` em")
        print("  2 - Emulador [Produto Final]/GameServer/config/network/network.properties")
        print("e entre no mundo uma vez com o cliente.")
        return 2

    oficial = janela_oficial(CAPTURA, sessao_alvo)
    nosso, chegou_ready = janela_nossa(RASTRO)
    if not oficial:
        print("Nao achei a janela de enter world na captura %s" % CAPTURA)
        return 2
    if not nosso:
        print("Nao achei nenhum CM_ENTER_WORLD em %s" % RASTRO)
        return 2

    nomes = nomes_das_classes()
    conta_of, tam_of = resumo(oficial)
    conta_no, tam_no = resumo(nosso)
    nossos_nomes, hex_no, hex_of = {}, {}, {}
    for op, _tam, nome, hx in nosso:
        nossos_nomes.setdefault(op, nome)
        hex_no.setdefault(op, hx)
    for op, _tam, hx in oficial:
        hex_of.setdefault(op, hx)

    print("oficial: %d pacotes S->C, %d opcodes distintos" % (len(oficial), len(conta_of)))
    print("nosso:   %d pacotes S->C, %d opcodes distintos" % (len(nosso), len(conta_no)))
    print("CM_LEVEL_READY do cliente: %s\n" % ("chegou" if chegou_ready else "NAO CHEGOU"))

    faltando = [op for op in conta_of if op not in conta_no]
    print("=== O OFICIAL MANDA E NOS NAO (%d) ===" % len(faltando))
    for op in sorted(faltando, key=lambda o: -conta_of[o] * tam_of[o]):
        print("  0x%04X  x%-3d %6dB  %s" % (op, conta_of[op], tam_of[op], nomes.get(op, "SEM CLASSE")))

    sobrando = [op for op in conta_no if op not in conta_of]
    print("\n=== NOS MANDAMOS E O OFICIAL NAO (%d) ===" % len(sobrando))
    for op in sorted(sobrando, key=lambda o: -conta_no[o] * tam_no[o]):
        print("  0x%04X  x%-3d %6dB  %s" % (op, conta_no[op], tam_no[op], nossos_nomes.get(op, "?")))

    print("\n=== MANDAMOS OS DOIS, MAS COM TAMANHO OU CONTAGEM DIFERENTE ===")
    divergentes = 0
    for op in sorted(set(conta_of) & set(conta_no)):
        if conta_of[op] != conta_no[op] or tam_of[op] != tam_no[op]:
            divergentes += 1
            print("  0x%04X  oficial x%-3d %6dB   nosso x%-3d %6dB   %s"
                  % (op, conta_of[op], tam_of[op], conta_no[op], tam_no[op],
                     nossos_nomes.get(op, nomes.get(op, "?"))))
    if not divergentes:
        print("  nenhum")

    print("\n=== MESMO OPCODE E MESMO TAMANHO, MAS PAYLOAD DIFERENTE (32B iniciais) ===")
    conteudo = 0
    for op in sorted(set(conta_of) & set(conta_no)):
        a, b = hex_of.get(op, ""), hex_no.get(op, "")
        if tam_of[op] != tam_no[op] or not a or not b or a == b:
            continue
        conteudo += 1
        print("  0x%04X  %s" % (op, nossos_nomes.get(op, nomes.get(op, "?"))))
        print("      oficial %s" % a)
        print("      nosso   %s" % b)
    if not conteudo:
        print("  nenhum")

    print("\n=== ONDE A ORDEM DIVERGE ===")
    for i, (a, b) in enumerate(zip(oficial, nosso)):
        if a[0] != b[0]:
            print("  divergem no pacote %d: oficial 0x%04X (%dB), nosso 0x%04X (%dB, %s)"
                  % (i, a[0], a[1], b[0], b[1], b[2]))
            break
    else:
        print("  o prefixo comum (%d pacotes) bate" % min(len(oficial), len(nosso)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
