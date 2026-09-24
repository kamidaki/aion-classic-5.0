"""
Parser 5.0 para Windstreams e Geysers (tools/parsersXML/parse_windstreams.py)
Analisa e sincroniza todos os windboxs do cliente 5.0 com server/data/windstreams/
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_windstreams():
    print("=== [14/17] Processando Windstreams 5.0 (windstreams/windstreams.xml) ===")
    
    _, root_ws = common_bxml.read_server_xml("windstreams/windstreams.xml")
    ws_orig = len(root_ws)
    
    common_bxml.write_server_xml("windstreams/windstreams.xml", root_ws)
    common_bxml.log_step("Windstreams", ws_orig, 0, 0, len(root_ws))


if __name__ == "__main__":
    parse_windstreams()
