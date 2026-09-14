#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_player_stubs_report.py
Gera o relatório forense analítico completo de todas as habilidades aprendíveis por jogadores
que atualmente estão sem efeito funcional (stubs) no skill_templates.xml do emulador.
"""

import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter

PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)

import backup_manager
import common_bxml

CLIENT_SKILLS = os.path.join(common_bxml.CLIENT_DATA_DIR, "skills", "client_skills.xml")
SERVER_TEMPLATES = os.path.join(backup_manager.SERVER_DATA_DIR, "skills", "skill_templates.xml")
SERVER_TREE = os.path.join(backup_manager.SERVER_DATA_DIR, "skill_tree", "skill_tree.xml")
REPORT_PATH = os.path.join(PARSERS_DIR, "relatorio_stubs_jogadores_50.txt")

REJECTION_REASONS = {
    'blending': 'Efeito novo da 5.0 (sem mapeamento de atributos no emulador / 0% gabarito)',
    'root': 'Presença no gabarito 4.8 foi de 60.6% (abaixo do limiar de segurança de 70%)',
    'boostskillcastingtime': 'Enums+stats 52.9% e presença 35.3% no gabarito (abaixo dos limiares)',
    'carvesignet': 'Presença no gabarito 0% (atributos de gravação de selo divergem da 4.8)',
    'weaponstatboost': 'Apenas 2 casos de teste no gabarito (amostragem insuficiente)',
    'randommoveloc': 'Presença no gabarito 0% (atributos de teletransporte aleatório não mapeados)',
    'reflector': 'Presença no gabarito 68.0% (abaixo do limiar de segurança de 70%)',
    'sanctuary': 'Presença 50.0% e números 60.0% no gabarito (abaixo dos limiares)',
    'summontrap': 'Presença no gabarito 10.8% (estrutura de armadilha mudou na 5.0)',
    'protect': 'Presença 0% no gabarito (mecanismo de proteção de dano não mapeado)',
    'skillcooltimereset': 'Presença 0% no gabarito (reset de cooldown de skills)',
    'procheal_instant': 'Presença 45.5% e números 28.6% no gabarito (fórmula divergente)',
    'procmpheal_instant': 'Presença 0% no gabarito',
    'deboosthealamount': 'Enums 0% e presença 36.4% no gabarito',
    'noreducespellatk_instant': 'Enums 12.5% e presença 37.5% no gabarito',
    'alwaysresist': 'Presença 0% no gabarito',
    'movelocation': 'Presença 0% no gabarito',
    'xpboost': 'Enums 0% no gabarito',
    'drboost': 'Enums 0% e presença 0% no gabarito',
}

def main():
    print("=== Gerando Relatório Forense dos Stubs de Jogadores na 5.0 ===")
    
    # 1. Carregar skill_tree
    tree_doc = ET.parse(SERVER_TREE)
    player_skills = defaultdict(list)
    for s in tree_doc.getroot().findall('skill'):
        sid = int(s.get('skillId'))
        cid = s.get('classId')
        mlv = s.get('minLevel')
        player_skills[sid].append((cid, mlv))

    # 2. Carregar skill_templates sem efeito
    st_doc = ET.parse(SERVER_TEMPLATES)
    empty_templates = {}
    for st in st_doc.getroot().findall('skill_template'):
        sid = int(st.get('skill_id'))
        eff = st.find('effects')
        if eff is None or len(eff) == 0:
            empty_templates[sid] = {
                'name': st.get('name', ''),
                'activation': st.get('activation', ''),
                'skilltype': st.get('skilltype', ''),
                'cooldown': st.get('cooldown', ''),
                'duration': st.get('duration', ''),
            }

    # Interseção: stubs que são aprendidos por jogadores
    stubs = {sid: empty_templates[sid] for sid in empty_templates if sid in player_skills}
    print(f"  Total de skills jogáveis sem efeito funcional: {len(stubs)}")

    # 3. Ler informações de efeitos do client_skills.xml
    client_info = {}
    for event, elem in ET.iterparse(CLIENT_SKILLS, events=('end',)):
        if elem.tag == 'skill_base_client':
            sid_str = elem.findtext('id')
            if sid_str and int(sid_str) in stubs:
                sid = int(sid_str)
                effs = []
                for i in range(1, 10):
                    et = elem.findtext(f'effect{i}_type')
                    if et:
                        effs.append(et)
                client_info[sid] = {
                    'raw_name': elem.findtext('name', ''),
                    'desc': elem.findtext('desc', ''),
                    'effects': effs
                }
            elem.clear()

    # Estatísticas por classe e efeito
    class_counter = Counter()
    effect_counter = Counter()
    for sid in stubs:
        classes = {c for c, _ in player_skills[sid]}
        for c in classes:
            class_counter[c] += 1
        for e in client_info.get(sid, {}).get('effects', []):
            effect_counter[e] += 1

    # 4. Escrever relatório formatado
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("=" * 100 + "\n")
        f.write("RELATÓRIO FORENSE DE HABILIDADES JOGÁVEIS SEM EFEITO FUNCIONAL (STUBS) — AION CLASSIC 5.0\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Total de habilidades na skill_tree dos jogadores que são stubs (<properties /> sem <effects>): {len(stubs)}\n\n")
        
        f.write("--- DISTRIBUIÇÃO POR CLASSE AFETADA ---\n")
        for c, cnt in sorted(class_counter.items(), key=lambda x: -x[1]):
            f.write(f"  {c:15}: {cnt:4} skills sem efeito\n")
        f.write("\n")

        f.write("--- EFEITOS DO CLIENTE PRESENTES NESSAS SKILLS ---\n")
        for e, cnt in effect_counter.most_common():
            reason = REJECTION_REASONS.get(e.lower(), "Parte de skill composta com outro efeito barrado")
            f.write(f"  {e:25}: {cnt:3} skills | Causa: {reason}\n")
        f.write("\n")

        f.write("=" * 100 + "\n")
        f.write(f"{'ID':>6}  {'NOME NO EMULADOR':<30}  {'CLASSE(S) / NÍVEL':<30}  {'TIPO / ATIVAÇÃO':<20}  {'EFEITOS NO CLIENTE / MOTIVO DO STUB'}\n")
        f.write("=" * 100 + "\n")

        for sid in sorted(stubs.keys()):
            s = stubs[sid]
            c_info = client_info.get(sid, {'raw_name': '', 'effects': []})
            
            # formatar classes e níveis
            class_lv_list = [f"{c} (Nv.{lv})" for c, lv in sorted(player_skills[sid])]
            class_str = ", ".join(class_lv_list[:2])
            if len(class_lv_list) > 2:
                class_str += f" +{len(class_lv_list)-2}"

            type_act = f"{s['skilltype']} / {s['activation']}"
            
            eff_str = ", ".join(c_info['effects']) if c_info['effects'] else "[NENHUM NO CLIENTE]"
            # Identificar causas específicas
            causes = [REJECTION_REASONS[e.lower()] for e in c_info['effects'] if e.lower() in REJECTION_REASONS]
            cause_str = "; ".join(causes) if causes else "Efeito composto não certificado pelo gabarito"

            f.write(f"{sid:>6}  {s['name'][:30]:<30}  {class_str[:30]:<30}  {type_act:<20}  Efeitos: {eff_str}\n")
            f.write(f"{' ':>6}  {'Nome Interno: ' + c_info['raw_name']:<30}  {' ':30}  {' ':20}  Motivo: {cause_str}\n")
            f.write("-" * 100 + "\n")

    print(f"  [OK] Relatório gerado com sucesso em: {REPORT_PATH}")

if __name__ == "__main__":
    main()
