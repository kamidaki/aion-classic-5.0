"""Associa a skill anti-voo aos monstros Island of e sincroniza os XMLs."""
from pathlib import Path
import xml.etree.ElementTree as ET
from lxml import etree

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'Código Fonte - Emulador/game-server/data/static_data'
PRODUCT = ROOT / 'Emulador - Produto Final/GameServer/data/static_data'
RELATIVE = Path('npc_skills/open_worlds/800040000_Tiamaranta_Mesa.xml')


def main():
    targets = sorted(int(n.get('npc_id')) for n in ET.parse(SOURCE / 'npcs/npc_templates.xml').getroot()
                     if n.get('name_en', '').lower().startswith('island of ') and n.get('ai') == 'aggressive')
    assert len(targets) == 16
    skill = next(n for n in ET.parse(SOURCE / 'skills/skill_templates.xml').getroot() if n.get('skill_id') == '18166')
    assert skill.find('properties').get('first_target_range') == '16'
    matches = []
    for path in (SOURCE / 'npc_skills').rglob('*.xml'):
        for group in ET.parse(path).getroot().findall('npc_skills'):
            if set(targets) & {int(i) for i in group.get('npc_ids', '').split()}:
                matches.append((path, group))
    if matches:
        assert len(matches) == 1
        path, group = matches[0]
        assert path == SOURCE / RELATIVE
        assert {int(i) for i in group.get('npc_ids').split()} == set(targets)
        assert len(group) == 1 and group[0].attrib == {'id': '18166', 'lv': '1', 'prob': '100'}
        assert group[0].find('cond').attrib == {'cond_type': 'TARGET_IS_FLYING', 'range': '16'}
    else:
        path = SOURCE / RELATIVE
        raw = path.read_bytes()
        newline = '\r\n' if b'\r\n' in raw else '\n'
        block = newline.join([
            '\t<!-- Island of: 18166 lv 1 observado na captura oficial 2026-10-28 06-49-56.',
            '\t     Associação por nome e condição de voo solicitadas; alcance 16 do template.',
            '\t     prob 100 habilita a tentativa quando elegível; frequência oficial não inferida. -->',
            f'\t<npc_skills npc_ids="{" ".join(map(str, targets))}">',
            '\t\t<npc_skill id="18166" lv="1" prob="100">',
            '\t\t\t<cond cond_type="TARGET_IS_FLYING" range="16" />',
            '\t\t</npc_skill>',
            '\t</npc_skills>',
            '',
        ])
        updated = raw.decode('utf-8').replace('</npc_skill_templates>', block + '</npc_skill_templates>')
        ET.fromstring(updated)
        path.write_bytes(updated.encode('utf-8'))
    schema = etree.XMLSchema(etree.parse(str(SOURCE / 'npc_skills/npc_skills.xsd')))
    schema.assertValid(etree.parse(str(SOURCE / RELATIVE)))
    (PRODUCT / RELATIVE).write_bytes((SOURCE / RELATIVE).read_bytes())
    print(f'{len(targets)} mobs: 18166 lv 1, alvo voando, alcance 16; XSD válido; distribuição sincronizada.')


if __name__ == '__main__':
    main()
