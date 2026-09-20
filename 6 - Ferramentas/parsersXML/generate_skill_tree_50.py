r"""
Gerador Canônico Oficial de Árvores de Habilidades (skill_tree.xml) — Aion Classic 5.0
Lê os dados originais do cliente 5.0 em:
  - 5 - Documentação e Referências\4 - Client 5.0 - Dados Extraidos\data\skills\client_skills.xml
  - 5 - Documentação e Referências\4 - Client 5.0 - Dados Extraidos\data\skills\client_skill_learns.xml
E gera a árvore de habilidades 100% canônica cobrindo todas as 13 classes do Aion 5.0:
GLADIATOR, TEMPLAR, ASSASSIN, RANGER, SORCERER, SPIRIT_MASTER, CLERIC, CHANTER,
REVENANT, BRAWLER, LUMINESS, PHOENIX, SOUL_REAPER e ALL.
"""

import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bxml
import backup_manager

CLASS_EXPANSION = {
    'FIGHTER': ['GLADIATOR', 'TEMPLAR', 'WARRIOR'],
    'WARRIOR': ['GLADIATOR', 'TEMPLAR', 'WARRIOR'],
    'KNIGHT': ['TEMPLAR'],
    'SCOUT': ['ASSASSIN', 'RANGER', 'SCOUT'],
    'ASSASSIN': ['ASSASSIN'],
    'RANGER': ['RANGER'],
    'MAGE': ['SORCERER', 'SPIRIT_MASTER', 'MAGE'],
    'WIZARD': ['SORCERER'],
    'ELEMENTALLIST': ['SPIRIT_MASTER'],
    'PRIEST': ['CLERIC', 'CHANTER', 'PRIEST'],
    'CLERIC': ['CLERIC'],
    'CHANTER': ['CHANTER'],
    'THUNDERER': ['REVENANT', 'THUNDERER'],
    'MONK': ['REVENANT', 'MONK'],
    'BATTLEMASTER': ['BRAWLER'],
    'STRIKER': ['BRAWLER'],
    'LUMINES': ['LUMINESS'],
    'GUNNER': ['PHOENIX'],
    'RUNEBLADE': ['SOUL_REAPER'],
    'REAPER': ['SOUL_REAPER', 'REAPER'],
    'ALL': ['ALL'],
}

RACE_MAP = {
    'all': 'PC_ALL',
    'ALL': 'PC_ALL',
    'All': 'PC_ALL',
    'pc_light': 'ELYOS',
    'PC_LIGHT': 'ELYOS',
    'pc_dark': 'ASMODIANS',
    'PC_DARK': 'ASMODIANS',
}

# Precedência determinística: Classe Específica (30) > Intermediária (20) > Classe Base (10) > ALL (0)
CLASS_PRIORITY = {
    'KNIGHT': 30, 'WIZARD': 30, 'ELEMENTALLIST': 30, 'ASSASSIN': 30, 'RANGER': 30,
    'CLERIC': 30, 'CHANTER': 30, 'BATTLEMASTER': 30, 'STRIKER': 30, 'LUMINES': 30,
    'GUNNER': 30, 'RUNEBLADE': 30, 'REAPER': 30, 'MONK': 30,
    'THUNDERER': 20,
    'FIGHTER': 10, 'WARRIOR': 10, 'SCOUT': 10, 'MAGE': 10, 'PRIEST': 10,
    'ALL': 0
}


def generate_skill_tree():
    print("=== [Gerador 5.0] Construindo skill_tree.xml canônico oficial ===")
    
    # 1. Carregar mapeamento de skills do cliente
    print("  -> Lendo client_skills.xml...")
    client_skills = common_bxml.read_client_xml("skills/client_skills.xml")
    name_to_skill = {}
    for cs in client_skills:
        name = cs.findtext("name")
        sid = cs.findtext("id")
        if name and sid:
            name_to_skill[name.lower()] = int(sid)
            
    print(f"     Carregadas {len(name_to_skill)} definições de skills do cliente.")

    # Regras de Blending: stigma_display=5 não é uma stigma equipável. O cliente
    # a concede quando uma das combinações de pré-requisitos está completa.
    blending_by_result = {}
    for combination in common_bxml.read_client_xml("PC/client_bledingskill_combination.xml"):
        result_name = combination.findtext("blended_skill", "").lower()
        requirements = []
        for data in combination.findall("./blending_combination/data"):
            ids = [name_to_skill.get(name.strip().lower())
                   for name in data.findtext("condition_skill", "").split(",")]
            ids = [skill_id for skill_id in ids if skill_id]
            if ids:
                requirements.append(",".join(map(str, ids)))
        if result_name and requirements:
            blending_by_result.setdefault(result_name, []).append(";".join(requirements))

    # 2. Carregar regras de aprendizado
    print("  -> Lendo client_skill_learns.xml...")
    client_learns = common_bxml.read_client_xml("skills/client_skill_learns.xml")
    print(f"     Carregadas {len(client_learns)} regras de aprendizado do cliente.")

    # 3. Processar e estruturar com precedência determinística
    best_entries = {}

    for l in client_learns:
        raw_skill = l.findtext("skill", "")
        if not raw_skill:
            continue
        skill_id = name_to_skill.get(raw_skill.lower())
        if not skill_id:
            continue

        raw_class = (l.findtext("class") or "").upper()
        targets = CLASS_EXPANSION.get(raw_class, [raw_class])
        prio = CLASS_PRIORITY.get(raw_class, 15)

        raw_race = l.findtext("race") or "All"
        race = RACE_MAP.get(raw_race, "PC_ALL")

        min_level = int(l.findtext("pc_level", "1"))
        skill_level = int(l.findtext("skill_level", "1"))

        auto_learn_val = (l.findtext("autolearn") or "").upper()
        stigma_display = l.findtext("stigma_display", "0")
        learntype = l.findtext("learntype", "0")

        is_blended = stigma_display == '5'
        is_stigma = stigma_display in ('1', '2') or learntype == '1'
        is_autolearn = auto_learn_val == "TRUE"
        is_skillbook = (not is_autolearn) and (not is_stigma) and (not is_blended)

        for target_class in targets:
            key = (target_class, skill_id, skill_level, race)
            entry = {
                'name': raw_skill.lower(),
                'skillId': str(skill_id),
                'skillLevel': str(skill_level),
                'minLevel': str(min_level),
                'race': race,
                'classId': target_class,
            }
            if is_autolearn:
                entry['autoLearn'] = 'true'
            if is_stigma:
                entry['stigma'] = 'true'
            if is_skillbook:
                entry['skillBook'] = 'true'
            if is_blended:
                combinations = blending_by_result.get(raw_skill.lower(), [])
                if not combinations:
                    print(f"  [AVISO] Blending sem combinação resolvida: {raw_skill}")
                    continue
                entry['blendingSources'] = '|'.join(combinations)

            # Sobrescreve se a nova definição tiver maior precedência
            if key not in best_entries or prio > best_entries[key][0]:
                best_entries[key] = (prio, entry)

    skill_entries = [v[1] for v in best_entries.values()]

    # 4. Ordenar deterministicamente
    skill_entries.sort(key=lambda x: (x['classId'], int(x['minLevel']), int(x['skillId']), int(x['skillLevel'])))
    print(f"  -> Total de entradas desduplicadas e validadas: {len(skill_entries)}")

    # 5. Gerar XML
    root = ET.Element("skill_tree")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation", "skill_tree.xsd")

    for e in skill_entries:
        s_elem = ET.SubElement(root, "skill")
        for k, v in e.items():
            s_elem.set(k, v)

    # Converter em XML formatado
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed_dom = minidom.parseString(xml_str)
    pretty_xml = parsed_dom.toprettyxml(indent="\t", encoding="utf-8")

    # 6. Gravar nos destinos (GameServer e PRODUTO FINAL)
    destinations = [
        os.path.join(common_bxml.SERVER_DATA_DIR, "skill_tree", "skill_tree.xml"),
        os.path.join(common_bxml.PRODUTO_FINAL_DATA_DIR, "skill_tree", "skill_tree.xml"),
    ]

    for dest in destinations:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        backup_manager.backup_file_before_modification(dest)
        with open(dest, "wb") as f:
            f.write(pretty_xml)
        print(f"  [OK] Gravado com sucesso em: {dest}")

    # Estatísticas finais por classe
    from collections import Counter
    class_counter = Counter(x['classId'] for x in skill_entries)
    print("\n--- DISTRIBUIÇÃO CANÔNICA DE HABILIDADES POR CLASSE ---")
    for c, cnt in sorted(class_counter.items()):
        print(f"  {c:15}: {cnt:5} skills")
    print(f"Total: {len(skill_entries)} skills em todas as classes.\n")


if __name__ == "__main__":
    generate_skill_tree()
