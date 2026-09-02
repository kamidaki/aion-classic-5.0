"""
Parser 5.0 para Instâncias, Fortalezas, Rifts e Abyss (tools/parsersXML/parse_instances.py)
Analisa e sincroniza instâncias, fortalezas de cerco e rifts com server/data/instance_cooltimes/, siege/, rift/
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_instances():
    print("=== [15/17] Processando Instâncias, Siege e Rifts 5.0 (instance_cooltimes/, siege/, rift/) ===")
    
    # 1. Valida instance_cooltimes.xml
    _, s_ic = common_bxml.read_server_xml("instance_cooltimes/instance_cooltimes.xml")
    common_bxml.write_server_xml("instance_cooltimes/instance_cooltimes.xml", s_ic)
    common_bxml.log_step("Tempos de Instâncias", len(s_ic), 0, 0, len(s_ic))

    # 2. Valida siege_locations.xml
    _, s_sl = common_bxml.read_server_xml("siege/siege_locations.xml")
    common_bxml.write_server_xml("siege/siege_locations.xml", s_sl)
    common_bxml.log_step("Fortalezas (siege_locations)", len(s_sl), 0, 0, len(s_sl))

    # 3. Valida rift_locations.xml
    try:
        _, s_rl = common_bxml.read_server_xml("rift/rift_locations.xml")
        common_bxml.write_server_xml("rift/rift_locations.xml", s_rl)
        common_bxml.log_step("Fendas Dimensionais (rifts)", len(s_rl), 0, 0, len(s_rl))
    except Exception as e:
        print(f"  [AVISO] Rifts: {e}")


if __name__ == "__main__":
    parse_instances()
