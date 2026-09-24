#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_50_delay_ids.py
Insere o atributo delayId="..." nas 59 skills de skill_templates.xml que possuem delay_id no client_skills.xml.
Mantém todos os outros atributos intactos e valida contra o skills.xsd.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from lxml import etree

PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)

import backup_manager
import common_bxml

CLIENT_SKILLS = os.path.join(common_bxml.CLIENT_DATA_DIR, "skills", "client_skills.xml")
SERVER_SKILLS = os.path.join(backup_manager.SERVER_DATA_DIR, "skills", "skill_templates.xml")
FINAL_SKILLS = os.path.join(backup_manager.PRODUTO_FINAL_DATA_DIR, "skills", "skill_templates.xml")
XSD_PATH = os.path.join(backup_manager.SERVER_DATA_DIR, "skills", "skills.xsd")

def main():
    print("=== [1.2] Inserindo 59 delayId faltantes em skill_templates.xml ===")
    print(f"Lendo client_skills de: {CLIENT_SKILLS}")
    client_delays = {}
    for event, elem in ET.iterparse(CLIENT_SKILLS, events=('end',)):
        if elem.tag == 'skill_base_client':
            sid = elem.findtext('id')
            did = elem.findtext('delay_id')
            if sid and did:
                client_delays[int(sid)] = did.strip()
            elem.clear()
    print(f"  Total de skills com delay_id no cliente: {len(client_delays)}")

    with open(SERVER_SKILLS, "r", encoding="utf-8", newline="") as f:
        content = f.read()

    patched_count = 0
    tag_pattern = re.compile(r'(<skill_template\b[^>]*>)')
    
    def replacer(match):
        nonlocal patched_count
        tag = match.group(1)
        m_id = re.search(r'\bskill_id="(\d+)"', tag)
        if not m_id:
            return tag
        sid = int(m_id.group(1))
        
        # se o cliente tem delay_id e o template ainda não tem delayId
        if sid in client_delays and 'delayId=' not in tag:
            did = client_delays[sid]
            # inserir após nameId se existir, senão após skill_id
            if 'nameId=' in tag:
                new_tag = re.sub(r'(\bnameId="[^"]*")', r'\1 delayId="' + did + '"', tag)
            else:
                new_tag = re.sub(r'(\bskill_id="\d+")', r'\1 delayId="' + did + '"', tag)
            patched_count += 1
            return new_tag
        return tag

    new_content = tag_pattern.sub(replacer, content)
    print(f"  Total de tags modificadas com delayId: {patched_count}")

    # Validação rigorosa no XSD
    print("Validando XML modificado contra skills.xsd...")
    schema = etree.XMLSchema(etree.parse(XSD_PATH))
    doc = etree.fromstring(new_content.encode("utf-8"))
    if not schema.validate(doc):
        for err in list(schema.error_log)[:10]:
            print(f"  [ERRO XSD] linha {err.line}: {err.message}")
        sys.exit("Falha na validação do XSD. Nenhuma alteração gravada.")
    print("  [OK] Validação no XSD bem-sucedida!")

    # Gravar com backup em ambas as pastas
    backup_manager.backup_file_before_modification(os.path.join("skills", "skill_templates.xml"))
    for target in [SERVER_SKILLS, FINAL_SKILLS]:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as f:
            f.write(new_content.encode("utf-8"))
        print(f"  [OK] Gravado com sucesso em: {target}")

    print("\n--- Concluído com sucesso! ---")

if __name__ == "__main__":
    main()
