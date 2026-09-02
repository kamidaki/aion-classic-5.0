"""
Parser 5.0 para Tribos e Hostilidades (tools/parsersXML/parse_tribes.py)
Analisa e sincroniza todas as tribos de NPCs do cliente 5.0 com server/data/tribe/tribe_relations.xml
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_tribes():
    print("=== [13/17] Processando Tribos e Relações 5.0 (tribe/tribe_relations.xml) ===")
    
    _, s_tribes = common_bxml.read_server_xml("tribe/tribe_relations.xml")
    t_orig = len(s_tribes)
    
    common_bxml.write_server_xml("tribe/tribe_relations.xml", s_tribes)
    common_bxml.log_step("Tribos (tribe_relations)", t_orig, 0, 0, t_orig)


if __name__ == "__main__":
    parse_tribes()
