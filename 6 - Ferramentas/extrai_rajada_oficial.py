# -*- coding: utf-8 -*-
"""Extrai da captura os pacotes da entrada no mundo que o nosso servidor nao envia.

Serve a um experimento so: reproduzir literalmente, no fio, a rajada que o cliente oficial recebe,
para separar duas hipoteses que a comparacao por tamanho nao separa --

  1. o cliente trava porque falta algum pacote  -> reproduzindo tudo, ele destrava, e da para
     bissectar a lista ate achar qual;
  2. o cliente trava pelo CONTEUDO do que ja mandamos -> reproduzir nao muda nada, e o alvo passa
     a ser o corpo dos pacotes que ja enviamos.

Grava `GameServer/data/diagnostico/rajada_oficial.txt`, uma linha por pacote:
`opcode corpo_em_hex posicoes_do_objectId`. As posicoes dizem onde o objectId do personagem da
captura aparece, para o servidor troca-lo pelo do jogador real -- sem isso o cliente recebe
pacotes apontando para uma entidade que nao existe. Guardar as posicoes, e nao zerar os bytes,
porque zero e um valor legitimo e comum no corpo destes pacotes.

    python "6 - Ferramentas/extrai_rajada_oficial.py" [wiretrace.log] [captura] [sessao] [janela]

`janela` e `entrada` (do CM_ENTER_WORLD ao CM_LEVEL_READY, o padrao) ou `pos-spawn` (do
CM_LEVEL_READY ao primeiro CM_MOVE) -- a segunda grava `rajada_pos_spawn.txt` e serve para a
mesma bisseccao aplicada ao que impede o personagem de agir depois de nascer.
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
DESTINOS = [os.path.join("1 - Código Fonte [Emulador]", "GameServer", "data", "diagnostico"),
            os.path.join("2 - Emulador [Produto Final]", "GameServer", "data", "diagnostico")]
ENTER_WORLD, LEVEL_READY, MOVE = 0x0018, 0x0019, 0x0030
LINHA = re.compile(r"\d{6}\|S\|0x([0-9A-Fa-f]{4})\|")


def nossos_opcodes(caminho, janela):
    """Opcodes S->C que ja enviamos na janela pedida."""
    abre = "|C|0x0018|" if janela == "entrada" else "|C|0x0019|"
    fecha = "|C|0x0019|" if janela == "entrada" else "|C|0x0030|"
    vistos, dentro = set(), False
    with open(caminho, encoding="utf-8", errors="replace") as f:
        for texto in f:
            if abre in texto:
                vistos, dentro = set(), True
                continue
            if dentro and fecha in texto:
                break
            m = LINHA.search(texto)
            if m and dentro:
                vistos.add(int(m.group(1), 16))
    return vistos


def main():
    global RASTRO, CAPTURA, SESSAO
    if len(sys.argv) > 1: RASTRO = sys.argv[1]
    if len(sys.argv) > 2: CAPTURA = sys.argv[2]
    if len(sys.argv) > 3: SESSAO = int(sys.argv[3])

    janela = sys.argv[4] if len(sys.argv) > 4 else "entrada"
    if janela not in ("entrada", "pos-spawn"):
        print("janela deve ser 'entrada' ou 'pos-spawn'")
        return 2
    nossos = nossos_opcodes(RASTRO, janela) if os.path.exists(RASTRO) else set()
    print("opcodes que ja enviamos: %d" % len(nossos))

    s = aion_pcap.abre_todas(CAPTURA)[SESSAO]
    linha = aion_pcap.intercalado(s)
    if janela == "entrada":
        ini = next(i for i, e in enumerate(linha) if e[1] == "cliente" and e[2] == ENTER_WORLD)
        fim = next(i for i in range(ini + 1, len(linha))
                   if linha[i][1] == "cliente" and linha[i][2] == LEVEL_READY)
    else:
        ini = next(i for i, e in enumerate(linha) if e[1] == "cliente" and e[2] == LEVEL_READY)
        fim = next(i for i in range(ini + 1, len(linha))
                   if linha[i][1] == "cliente" and linha[i][2] == MOVE)

    # objectId do personagem da captura: sai do S_ENTER_WORLD_CHECK, bytes 8..11
    oid = None
    for _t, lado, op, p in linha[ini:fim]:
        # na entrada ele sai do S_ENTER_WORLD_CHECK; depois do spawn, do S_PUT_USER
        if lado == "servidor" and op == 0x0133 and len(p) >= 12:
            oid = p[8:12]
            break
        if lado == "servidor" and op == 0x0020 and len(p) >= 16:
            oid = p[12:16]
            break
    if oid is None:
        print("nao achei o objectId da captura no S_ENTER_WORLD_CHECK")
        return 2
    print("objectId da captura: %s (%d)" % (oid.hex(), struct.unpack("<I", oid)[0]))

    faltando, total = [], 0
    for _t, lado, op, p in linha[ini:fim]:
        if lado != "servidor" or op in nossos:
            continue
        total += len(p)
        posicoes = []
        de = p.find(oid)
        while de != -1:
            posicoes.append(de)
            de = p.find(oid, de + 1)
        faltando.append((op, p, posicoes))

    print("pacotes a reproduzir: %d (%d bytes)" % (len(faltando), total))
    linhas = ["# gerado por extrai_rajada_oficial.py -- nao editar a mao",
              "# opcode  corpo_em_hex  posicoes_do_objectId_separadas_por_virgula"]
    marcados = 0
    for op, corpo, posicoes in faltando:
        marcados += len(posicoes)
        linhas.append("0x%04X %s %s" % (op, corpo.hex(),
                                        ",".join(str(x) for x in posicoes) or "-"))
    texto = "\n".join(linhas) + "\n"

    print("ocorrencias do objectId marcadas: %d" % marcados)
    for destino in DESTINOS:
        if not os.path.isdir(os.path.dirname(destino)):
            print("!! pulei %s" % destino); continue
        os.makedirs(destino, exist_ok=True)
        nome = "rajada_oficial.txt" if janela == "entrada" else "rajada_pos_spawn.txt"
        alvo = os.path.join(destino, nome)
        open(alvo, "w", encoding="utf-8").write(texto)
        print("gravado: %s" % alvo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
