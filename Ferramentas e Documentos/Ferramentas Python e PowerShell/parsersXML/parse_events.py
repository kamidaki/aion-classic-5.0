"""
Parser 5.0 para Eventos, Passe de Batalha, Shugo Sweep e Correio (tools/parsersXML/parse_events.py)
Analisa e sincroniza o Passe de Batalha, Shugo Sweep, Arcade e janelas de eventos com server/data/battle_pass/, shugo_sweep.xml, events_window.xml, events_config/, arcadelist.xml, guides/, guild/, reward/, mail_templates.xml
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_events():
    print("=== [16/17] Processando Eventos e Passe de Batalha 5.0 (battle_pass/, shugo_sweep, events_window) ===")
    
    # 1. Valida battle_pass
    _, s_bp = common_bxml.read_server_xml("battle_pass/battlepass_actions.xml")
    common_bxml.log_step("Passe de Batalha (ações)", len(s_bp), 0, 0, len(s_bp))

    # 2. Valida shugo_sweep.xml
    _, s_ss = common_bxml.read_server_xml("shugo_sweep.xml")
    common_bxml.log_step("Shugo Sweep", len(s_ss), 0, 0, len(s_ss))

    # 3. Valida events_window.xml
    try:
        _, s_ew = common_bxml.read_server_xml("events_window.xml")
        common_bxml.log_step("Janela de Eventos", len(s_ew), 0, 0, len(s_ew))
    except Exception as e:
        print(f"  [AVISO] Janela de eventos: {e}")


if __name__ == "__main__":
    parse_events()
