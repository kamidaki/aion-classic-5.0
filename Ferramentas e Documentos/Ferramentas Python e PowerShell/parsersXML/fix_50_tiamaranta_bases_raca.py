#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_tiamaranta_bases_raca.py

Bases de raça de Tiamaranta Mesa (Somnium dos Elyos e Nornir dos Asmodianos) no S_ABYSS_INFO (0xD0).

O client_abyss.xml tem os acampamentos 4201-4203 e 4301-4303 (abyss_type camp, STR_LDF4b_SZ_*_C), e o 0xD0 oficial manda os seis
com dono fixo em todas as capturas (2026-10-21 06:50 e 08_Spawns_Mapas/Tiamaranta_Mesa): 4201-4203 com dono 0 (Elyos),
4301-4303 com dono 1 (Asmodianos), byte 17 = 0 (nunca vulnerável), byte 19 = 0 (sem próxima fase). O servidor não tinha nenhum
dos seis, então o minimapa mostrava as bases sem raça.

Entram em siege/siege_locations.xml como CAMP de dono fixo (camp_reset_time 0 = CampLocation.isStatic: protegida, sem ciclo, sem PvP).

Uso:
    python fix_50_tiamaranta_bases_raca.py --verificar
    python fix_50_tiamaranta_bases_raca.py --aplicar
"""

import argparse
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL = "siege/siege_locations.xml"
# id, name_id (string STR_LDF4b_SZ_<id>_C do cliente), raça
BASES = (
    (4201, 403842, "ELYOS"), (4202, 403949, "ELYOS"), (4203, 404001, "ELYOS"),
    (4301, 403843, "ASMODIANS"), (4302, 403950, "ASMODIANS"), (4303, 404002, "ASMODIANS"),
)
ANCORA = '\t<siege_location id="4401" type="CAMP"'


def edita(texto):
    if 'siege_location id="4201"' in texto:
        return texto
    assert texto.count(ANCORA) == 1
    bloco = "\t<!-- Bases de raça de Tiamaranta (Somnium/Nornir): dono fixo no S_ABYSS_INFO oficial -->\n"
    for loc, nome, raca in BASES:
        bloco += (f'\t<siege_location id="{loc}" type="CAMP" world="800040000" name_id="{nome}" camp_protect_time="0" '
                  f'camp_reset_time="0" camp_default_race="{raca}" />\n')
    i = texto.index(ANCORA)
    return texto[:i] + bloco + texto[i:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    gravar = []
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        caminho = os.path.join(base, REL)
        texto = open(caminho, encoding="utf-8", newline="").read()
        crlf = "\r\n" in texto
        novo = edita(texto.replace("\r\n", "\n"))
        if crlf:
            novo = novo.replace("\n", "\r\n")
        if not schema.validate(etree.fromstring(novo.encode("utf-8"))):
            for e in list(schema.error_log)[:10]:
                print(f"   linha {e.line}: {e.message}")
            sys.exit("   XSD INVALIDO")
        if novo != texto:
            gravar.append(caminho)
            print("   muda: " + os.path.relpath(caminho, backup_manager.PROJECT_ROOT))
    if args.aplicar:
        backup_manager.backup_file_before_modification(REL)
        for caminho in gravar:
            texto = open(caminho, encoding="utf-8", newline="").read()
            crlf = "\r\n" in texto
            novo = edita(texto.replace("\r\n", "\n"))
            open(caminho, "w", encoding="utf-8", newline="").write(novo.replace("\n", "\r\n") if crlf else novo)
        print("   gravado")


if __name__ == "__main__":
    main()
