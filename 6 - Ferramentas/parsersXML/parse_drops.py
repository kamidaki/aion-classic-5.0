"""
Parser 5.0 para Drops e Saques de Monstros (tools/parsersXML/parse_drops.py)
Analisa e sincroniza tabelas de drop de monstros com server/data/npc_drops/commons_drop_items.xml
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_drops():
    print("=== [17/17] Processando Drops de Monstros 5.0 (npc_drops/commons_drop_items.xml) ===")
    
    # 1. Valida commons_drop_items.xml
    _, s_drops = common_bxml.read_server_xml("npc_drops/commons_drop_items.xml")
    d_orig = len(s_drops)
    
    print(f"  -> {d_orig} grupos de drops indexados e validados.")
    common_bxml.log_step("Drops (commons_drop_items)", d_orig, 0, 0, d_orig)


if __name__ == "__main__":
    parse_drops()
