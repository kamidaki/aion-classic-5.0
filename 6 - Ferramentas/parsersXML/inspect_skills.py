import xml.etree.ElementTree as ET

s_tree = ET.parse('G:/Projetos AION/Classic/1 - Código Fonte [Emulador]/game-server/data/static_data/skills/skill_templates.xml')
s_root = s_tree.getroot()

c_tree = ET.parse('G:/Projetos AION/XMLS AION CLASSIC/data/skills/client_skills.xml')
c_root = c_tree.getroot()
c_skills = {sbc.find('id').text: sbc for sbc in c_root.findall('skill_base_client')}

def inspect_skill(sid):
    print('='*70)
    print(f'SKILL ID: {sid}')
    st = s_root.find(f'.//skill_template[@skill_id="{sid}"]')
    if st is not None:
        print('--- SERVER TEMPLATE ---')
        print(ET.tostring(st, encoding='unicode').strip())
    cs = c_skills.get(sid)
    if cs is not None:
        print('--- CLIENT BASE CLIENT ---')
        for child in cs:
            if child.text and child.text.strip():
                if any(k in child.tag for k in ['id', 'name', 'desc', 'delay', 'cooldown', 'multicast', 'chain', 'sub_type', 'skill_category', 'effect', 'type', 'target', 'motion', 'first_target']):
                    print(f'  {child.tag}: {child.text}')

for sid in ['4380', '4596', '4384', '4431']:
    inspect_skill(sid)
