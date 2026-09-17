#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_50_spawns_filhotes.py

Poe os filhotes em volta de cada spot do pai, no spawn do mapa. So dados: o emulador nao tem acompanhante que nasce
com o pai e o segue, entao cada filhote e um spot independente -- anda (random_walk do pai) e renasce sozinho.

O que as capturas oficiais de Tiamaranta Mesa mostram (2026-09-16):
  * o filhote nasce junto com o pai: object ids colados (Starturtle 2150937727, filhotes ...728 e ...729);
  * fica a uma distancia estavel e acompanha o pai quando ele anda;
  * distancia mediana ao pai quando entra na visao: Enos_Baby 7,9 m (19 amostras), StarturtleBaby 5,6 m (12);
  * 2 por Starturtle; 1 ou 2 por Enos (2 segundo o usuario, que conhece o mob).

Posicao: os dois filhotes ficam a DISTANCIA do pai, um de cada lado (heading do pai +90 e -90 graus). h e random_walk
iguais aos do pai, respawn_time o do <spawn> do pai. z: se o pai esta no terreno (heightmap de data/geo a ate 1 m),
o filhote vai para o terreno no ponto dele, desde que fique a ate 4 m do z do pai; senao, z do pai (ponte, caverna).
Pai que ja tem filhote a ate 2x a distancia fica como esta: rodar de novo nao duplica.

Uso:
    python add_50_spawns_filhotes.py            (mostra)
    python add_50_spawns_filhotes.py --aplicar  (grava as duas arvores, com backup)
"""

import argparse
import glob
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402
from sync_all_50_spawns import Terrenos  # noqa: E402

ARVORES = (("fonte", os.path.join(RAIZ, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data")),
           ("produto", os.path.join(RAIZ, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data")))
GEO = os.path.join(RAIZ, "2 - Emulador [Produto Final]", "GameServer", "data", "geo")
MAPA = 800040000
# (pai, filho, quantidade, distancia em metros) -- medidos nas capturas, ver docstring
FILHOTES = ((220459, 220462, 2, 7.9, "LDF4b_C2_Enos_59_An -> LDF4b_C2_Enos_Baby_59_An"),
            (220715, 220717, 2, 5.6, "LDF4b_T3_Starturtle_58_An -> LDF4b_T3_StarturtleBaby_58_An"))
TERRENO_PAI, TERRENO_FILHO = 1.0, 4.0
SPOT = re.compile(r"<spot\b[^>]*?/?>")


def atributo(tag, nome):
    m = re.search(r'\b%s="([^"]*)"' % nome, tag)
    return m.group(1) if m else None


def num(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return s if s else "0"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="grava as duas arvores (com backup)")
    args = ap.parse_args()
    terreno = Terrenos(GEO)

    for nome, base in ARVORES:
        arquivos = glob.glob(os.path.join(glob.escape(base), "spawns", "Npcs", "%d_*.xml" % MAPA))
        if len(arquivos) != 1:
            sys.exit("ABORTADO: esperado 1 arquivo Npcs do mapa em %s" % base)
        caminho = arquivos[0]
        texto = novo = open(caminho, encoding="utf-8", newline="").read()
        print("%s: %s" % (nome, os.path.basename(caminho)))
        for pai, filho, qtd, dist, rotulo in FILHOTES:
            m = re.search(r'<spawn npc_id="%d"([^>]*)>(.*?)</spawn>' % pai, novo, re.S)
            if not m:
                print("   %s: pai sem spawn no mapa" % rotulo)
                continue
            respawn = atributo("<x %s>" % m.group(1), "respawn_time") or "295"
            existentes = [(float(atributo(t, "x")), float(atributo(t, "y")))
                          for b in re.findall(r'<spawn npc_id="%d"[^>]*>(.*?)</spawn>' % filho, novo, re.S) for t in SPOT.findall(b)]
            linhas, no_terreno, pulados = [], 0, 0
            for tag in SPOT.findall(m.group(2)):
                px, py, pz = (float(atributo(tag, k)) for k in "xyz")
                if any(math.dist((px, py), e) <= 2 * dist for e in existentes):
                    pulados += 1
                    continue
                h = int(atributo(tag, "h") or 0)
                rw = atributo(tag, "random_walk")
                zt_pai = terreno.get_z(MAPA, px, py)
                pai_no_chao = zt_pai is not None and abs(zt_pai - pz) <= TERRENO_PAI
                for lado in (90, -90)[:qtd]:
                    ang = math.radians(h * 3 + lado)
                    fx, fy = px + dist * math.cos(ang), py + dist * math.sin(ang)
                    fz = pz
                    if pai_no_chao:
                        zt = terreno.get_z(MAPA, fx, fy)
                        if zt is not None and abs(zt - pz) <= TERRENO_FILHO:
                            fz = zt
                            no_terreno += 1
                    linhas.append('\t\t\t<spot x="%s" y="%s" z="%s" h="%d"%s/>\n' % (
                        num(fx), num(fy), num(fz), h, ' random_walk="%s"' % rw if rw and rw != "0" else ""))
            if not linhas:
                print("   %s: nada a acrescentar (%d pais ja com filhote)" % (rotulo, pulados))
                continue
            bloco = '\t\t<!-- %s (filhotes em volta do pai, capturas oficiais 5.0) -->\n\t\t<spawn npc_id="%d" respawn_time="%s">\n%s\t\t</spawn>\n' % (
                rotulo.split(" -> ")[1], filho, respawn, "".join(linhas))
            fim = novo.rindex("\t</spawn_map>")
            novo = novo[:fim] + bloco + novo[fim:]
            print("   %s: +%d spots de filhote (%d pais, a %.1f m; z no terreno em %d; %d pais ja tinham)" % (
                rotulo, len(linhas), len(linhas) // qtd, dist, no_terreno, pulados))
        acrescidos = novo.count("<spot") - texto.count("<spot")
        if novo == texto:
            continue
        from lxml import etree
        xsd = etree.XMLSchema(etree.parse(os.path.join(base, "static_data.xsd")))
        if not xsd.validate(etree.fromstring(novo.encode("utf-8"))):
            sys.exit("ABORTADO: %s nao valida: %s" % (caminho, xsd.error_log.last_error))
        print("   +%d spots, valida no static_data.xsd" % acrescidos)
        if args.aplicar:
            backup_manager.backup_file_before_modification(caminho)
            open(caminho, "w", encoding="utf-8", newline="").write(novo)
            print("   gravado")
    if not args.aplicar:
        print("Simulacao: nada gravado. Rode com --aplicar para gravar.")


if __name__ == "__main__":
    main()
