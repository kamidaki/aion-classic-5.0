"""Associa Strike aos NPCs com o título Tiamaranta Mutant e sincroniza a distribuição."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'Código Fonte - Emulador/game-server/data/static_data'
PRODUCT = ROOT / 'Emulador - Produto Final/GameServer/data/static_data'
RELATIVE = Path('npc_skills/open_worlds/800040000_Tiamaranta_Mesa.xml')
TITLE_ID = '345836'
SKILL_ID = '16516'


def main():
    targets = sorted(int(n.get('npc_id')) for n in ET.parse(SOURCE / 'npcs/npc_templates.xml').getroot()
                     if n.get('title_id') == TITLE_ID)
    assert targets, 'Título sem NPCs'
    assert any(n.get('skill_id') == SKILL_ID for n in ET.parse(SOURCE / 'skills/skill_templates.xml').getroot())
    matching = []
    for path in (SOURCE / 'npc_skills').rglob('*.xml'):
        for group in ET.parse(path).getroot().findall('npc_skills'):
            overlap = set(targets) & {int(i) for i in group.get('npc_ids', '').split()}
            if overlap:
                matching.append((path, group, overlap))
    expected = {'id': SKILL_ID, 'lv': '50', 'prob': '25'}
    if matching:
        assert len(matching) == 1, 'Existem listas adicionais; preservar e revisar antes de alterar'
        path, group, overlap = matching[0]
        assert path == SOURCE / RELATIVE and overlap == set(targets)
        assert {int(i) for i in group.get('npc_ids').split()} == set(targets)
        assert len(group) == 1 and group[0].attrib == expected
    else:
        path = SOURCE / RELATIVE
        original = path.read_bytes()
        newline = '\r\n' if b'\r\n' in original else '\n'
        text = original.decode('utf-8')
        block = newline.join([
            '\t<!-- Tiamaranta Mutant (title_id 345836): Strike lv 50 observado na captura oficial',
            '\t     2026-10-28 06-49-56 em 220468, 220494 e 220755; associação por título solicitada.',
            '\t     prob 25 segue o padrão existente de Strike; não inferido da captura. -->',
            f'\t<npc_skills npc_ids="{" ".join(map(str, targets))}">',
            '\t\t<npc_skill id="16516" lv="50" prob="25" />',
            '\t</npc_skills>',
            '',
        ])
        updated = text.replace('</npc_skill_templates>', block + '</npc_skill_templates>')
        assert updated != text
        ET.fromstring(updated)
        path.write_bytes(updated.encode('utf-8'))
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(str(SOURCE / 'npc_skills/npc_skills.xsd')))
    schema.assertValid(etree.parse(str(SOURCE / RELATIVE)))
    (PRODUCT / RELATIVE).write_bytes((SOURCE / RELATIVE).read_bytes())
    assert (PRODUCT / RELATIVE).read_bytes() == (SOURCE / RELATIVE).read_bytes()
    print(f'{len(targets)} NPCs associados a Strike 16516 lv 50 prob 25; XSD válido; Produto Final sincronizado.')


if __name__ == '__main__':
    main()
