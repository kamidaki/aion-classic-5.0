#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gera_50_camp_world_states.py

Gera siege/camp_world_states.xml: o que o servidor oficial 5.0 manda ao entrar em Tiamaranta Mesa (800040000) para
o cliente pintar o mapa -- as variaveis de mundo (S_WORLD_VARIABLE, 0x180) e a lista inteira de zonas
(S_ZONE_STATE_LIST, 0x19D).

Medido na captura 06_Sistemas_Novos_5.0_2026-09-16_05-01-15 (sessao em Tiamaranta, pacotes #185-#189, logo depois do
S_ABYSS_INFO com as 120 localizacoes):
  0x180 = [D mapa][S nome][D valor]            -> disable_pvp, disable_pvp_e, disable_pvp_w = 1
  0x19D = [H n][n x (S zona, C estado)]        -> 48 + 26 zonas, sempre na mesma ordem
Comparada com a de 2026-09-15, a lista tem os mesmos 74 nomes na mesma ordem; so mudam as 21
LDF4b_TowerWar_PvPArea_<id> (que seguem a vulnerabilidade da torre) e AttributeShapeLDF4b_PvPArea_ID501. Por isso as
TowerWar saem com camp="<id>" (o estado vem da torre em tempo real) e o resto com o estado fixo da captura.

Uso:
    python gera_50_camp_world_states.py [--dry]
"""

import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "6 - Ferramentas"))
import aion_pcap  # noqa: E402

CAPTURA = os.path.join(RAIZ, "5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0",
                       "06_Sistemas_Novos_5.0", "06_Sistemas_Novos_5.0_2026-09-16_05-01-15_00001_20260916050115.pcapng")
DESTINOS = [
    os.path.join(RAIZ, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data", "siege", "camp_world_states.xml"),
    os.path.join(RAIZ, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data", "siege", "camp_world_states.xml"),
]
MAPA = 800040000
TORRE = re.compile(r"^LDF4b_TowerWar_PvPArea_(\d+)$")


def wstr(p, off):
    fim = off
    while fim + 1 < len(p) and not (p[fim] == 0 and p[fim + 1] == 0):
        fim += 2
    return p[off:fim].decode("utf-16-le"), fim + 2


def le_captura():
    """(variaveis, pacotes_de_zona) da primeira entrada em Tiamaranta Mesa."""
    for sessao in aion_pcap.abre_todas(CAPTURA):
        variaveis, pacotes, no_mapa = [], [], False
        for op, p, _ok in sessao["servidor"]:
            if op == 0x0F and len(p) >= 4:
                no_mapa = struct.unpack_from("<I", p, 0)[0] == MAPA
            elif no_mapa and op == 0x180:
                nome, off = wstr(p, 4)
                if struct.unpack_from("<I", p, 0)[0] == MAPA:
                    variaveis.append((nome, struct.unpack_from("<i", p, off)[0]))
            elif no_mapa and op == 0x19D:
                n, off, zonas = struct.unpack_from("<H", p, 0)[0], 2, []
                for _ in range(n):
                    nome, off = wstr(p, off)
                    zonas.append((nome, p[off]))
                    off += 1
                if off != len(p):
                    sys.exit("0x19D com %d bytes sobrando: layout diferente do esperado" % (len(p) - off))
                pacotes.append(zonas)
            if pacotes and op not in (0x180, 0x19D) and len(pacotes) >= 2:
                return variaveis, pacotes
        if pacotes:
            return variaveis, pacotes
    sys.exit("a captura nao tem entrada em Tiamaranta Mesa")


def monta(variaveis, pacotes):
    linhas = ["<?xml version='1.0' encoding='utf-8'?>",
              '<camp_world_states xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="camp_world_states.xsd">',
              "\t<!-- Gerado por 6 - Ferramentas/parsersXML/gera_50_camp_world_states.py a partir da captura oficial",
              "\t     06_Sistemas_Novos_5.0_2026-09-16_05-01-15; nao editar a mao. -->",
              '\t<camp_world world="%d">' % MAPA]
    for nome, valor in variaveis:
        linhas.append('\t\t<camp_world_variable name="%s" value="%d" />' % (nome, valor))
    for zonas in pacotes:
        linhas.append("\t\t<camp_zone_packet>")
        for nome, estado in zonas:
            m = TORRE.match(nome)
            if m:
                linhas.append('\t\t\t<camp_zone name="%s" camp="%s" />' % (nome, m.group(1)))
            else:
                linhas.append('\t\t\t<camp_zone name="%s" state="%d" />' % (nome, estado))
        linhas.append("\t\t</camp_zone_packet>")
    linhas += ["\t</camp_world>", "</camp_world_states>", ""]
    return "\n".join(linhas)


def main():
    seco = "--dry" in sys.argv
    variaveis, pacotes = le_captura()
    print("variaveis de mundo: %s" % variaveis)
    print("pacotes de zona: %s zonas" % [len(z) for z in pacotes])
    print("zonas de torre (estado vivo): %d" % sum(1 for z in pacotes for n, _ in z if TORRE.match(n)))
    xml = monta(variaveis, pacotes)
    for destino in DESTINOS:
        if seco:
            print("[dry] " + destino)
        else:
            open(destino, "w", encoding="utf-8", newline="\n").write(xml)
            print("gravado: " + destino)


if __name__ == "__main__":
    main()
