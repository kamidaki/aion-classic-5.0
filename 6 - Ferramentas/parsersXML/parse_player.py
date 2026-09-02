"""
Parser 5.0 para Tabelas de Jogador, EXP, Títulos e Status (tools/parsersXML/parse_player.py)
Analisa e sincroniza tabelas de EXP, títulos com nomes reais de body, status de classes
com server/data/player_experience_table.xml, player_titles.xml, player_initial_data.xml, stats/
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml


def parse_player():
    print("=== [10/17] Processando Dados de Jogador 5.0 (player_experience_table, player_titles, player_initial_data) ===")
    
    # 1. Atualiza player_experience_table.xml com dados oficiais 5.0
    print("  -> Carregando PC/pcexp_table.xml oficial 5.0...")
    c_exp_root = common_bxml.read_client_xml("PC/pcexp_table.xml")
    
    tree, s_exp_root = common_bxml.read_server_xml("player_experience_table.xml")
    orig_exp_count = len(s_exp_root)
    s_exp_root.clear()
    
    lvl = 1
    for entry in c_exp_root:
        exp_val = entry.findtext("exp", "0")
        elem = ET.SubElement(s_exp_root, "exp")
        elem.text = exp_val
        lvl += 1
        
    common_bxml.write_server_xml("player_experience_table.xml", s_exp_root)
    common_bxml.log_step("Tabela de EXP (player_experience_table)", orig_exp_count, len(s_exp_root) - orig_exp_count, orig_exp_count, len(s_exp_root))

    # 2. Atualiza player_titles.xml com nomes reais
    print("  -> Carregando PC/client_titles.xml oficial 5.0...")
    try:
        c_titles_root = common_bxml.read_client_xml("PC/client_titles.xml")
        _, s_titles = common_bxml.read_server_xml("player_titles.xml")
        t_orig = len(s_titles)
        existing_t = {t.get("id"): t for t in s_titles.findall("title")}
        t_added = 0
        
        for child in c_titles_root:
            t_id = child.findtext("id")
            if not t_id:
                continue
            code_name = child.findtext("name", "")
            desc_str = child.findtext("desc", "")
            name_id = common_bxml.resolve_name_id(desc_str, int(t_id) if t_id.isdigit() else 0)
            real_name = common_bxml.resolve_body(desc_str, code_name)
            
            if t_id in existing_t:
                elem = existing_t[t_id]
                elem.set("nameId", name_id)
                elem.set("desc", real_name)
            else:
                elem = ET.SubElement(s_titles, "title")
                elem.set("id", t_id)
                elem.set("nameId", name_id)
                elem.set("desc", real_name)
                elem.set("race", "PC_ALL")
                t_added += 1
                
        common_bxml.write_server_xml("player_titles.xml", s_titles)
        common_bxml.log_step("Títulos (player_titles)", t_orig, t_added, t_orig, len(s_titles))
    except Exception as e:
        print(f"  [AVISO] Titles: {e}")

    # 3. Valida player_initial_data.xml
    _, s_initial = common_bxml.read_server_xml("player_initial_data.xml")
    common_bxml.log_step("Kits Iniciais (player_initial_data)", len(s_initial), 0, 0, len(s_initial))


if __name__ == "__main__":
    parse_player()
