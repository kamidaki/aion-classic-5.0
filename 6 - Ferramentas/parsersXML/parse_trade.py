"""
Parser 5.0 para Comércio, Lojas de NPCs e Expansores (tools/parsersXML/parse_trade.py)
Analisa e sincroniza todas as lojas de NPCs com server/data/goodslists/, npc_trade_list.xml, cube_expander/, warehouse_expander/
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_trade():
    print("=== [7/17] Processando Comércio e Lojas 5.0 (goodslists/, npc_trade_list.xml, cube/warehouse expander) ===")
    
    # 1. Valida goodslists.xml
    _, gl_root = common_bxml.read_server_xml("goodslists/goodslists.xml")
    common_bxml.write_server_xml("goodslists/goodslists.xml", gl_root)
    common_bxml.log_step("Goodslists", len(gl_root), 0, 0, len(gl_root))

    # 2. Valida npc_trade_list.xml
    _, tl_root = common_bxml.read_server_xml("npc_trade_list.xml")
    common_bxml.write_server_xml("npc_trade_list.xml", tl_root)
    common_bxml.log_step("NPC Trade Lists", len(tl_root), 0, 0, len(tl_root))

    # 3. Valida Cube Expander e Warehouse Expander
    try:
        _, cube_root = common_bxml.read_server_xml("cube_expander/cube_expander.xml")
        common_bxml.write_server_xml("cube_expander/cube_expander.xml", cube_root)
        common_bxml.log_step("Cube Expander", len(cube_root), 0, 0, len(cube_root))
    except Exception as e:
        print(f"  [AVISO] Cube expander: {e}")

    try:
        _, wh_root = common_bxml.read_server_xml("warehouse_expander/warehouse_expander.xml")
        common_bxml.write_server_xml("warehouse_expander/warehouse_expander.xml", wh_root)
        common_bxml.log_step("Warehouse Expander", len(wh_root), 0, 0, len(wh_root))
    except Exception as e:
        print(f"  [AVISO] Warehouse expander: {e}")


if __name__ == "__main__":
    parse_trade()
