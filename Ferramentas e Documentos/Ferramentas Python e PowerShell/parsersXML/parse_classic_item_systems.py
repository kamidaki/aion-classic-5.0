"""Importa regras oficiais 5.0 de enchant, Power Talent e descarte; corrige os 12 seeds.

Executar sem argumentos para verificar; --aplicar sincroniza fonte e Produto Final.
"""
import argparse
import pathlib
import re
import xml.etree.ElementTree as ET
from lxml import etree
import rebuild_50_item_templates as items

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Código Fonte - Emulador/game-server/data/static_data'
PRODUCT = ROOT / 'Emulador - Produto Final/GameServer/data/static_data'
CLIENT = ROOT / 'Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos'


def client_mask(d):
    """GENERAL_INFO mask, measured against official Classic 5.0 inventory blobs.

    This is deliberately distinct from the gameplay ItemMask.
    """
    flags = [(0, 'lore'), (1, 'can_exchange'), (2, 'can_sell_to_npc'),
             (3, 'can_deposit_to_character_warehouse'), (4, 'can_deposit_to_account_warehouse'),
             (5, 'breakable'), (6, 'soul_bind'), (9, 'can_deposit_to_guild_warehouse'),
             (13, 'can_split'), (15, 'cannot_extraction')]
    value = sum(1 << bit for bit, field in flags if d.get(field, '').upper() == 'TRUE')
    if d.get('no_enchant', 'TRUE').upper() != 'FALSE':
        value |= 1 << 8
    if d.get('quest'):
        value |= 1 << 10
    if d.get('weapon_type', 'none').lower() != 'none':
        value |= 1 << 11
    if d.get('cash_item') == '1':
        value |= 1 << 12
    if d.get('cannot_changeskin', '1') != '0':
        value |= 1 << 14
    return value


def generate():
    powers = list(ET.parse(CLIENT / 'data/gamedata/client_combat_power_rule.xml').getroot())
    option_points = {e.findtext('value').lower(): e.findtext('combat_power_point') for e in powers
                     if e.findtext('combat_power_type') == 'enchant_option'}
    rules = list(ET.parse(CLIENT / 'data/items/client_enchant_count_prob.xml').getroot())
    limits = {}
    result = ET.Element('classic_item_systems')
    for e in rules:
        group = e.findtext('enchant_group')
        limits[group] = max(limits.get(group, 0), int(e.findtext('success_enchant_count')))
        components = e.findall('enchant_component/data')
        if len(components) != 1:
            raise ValueError('Quantidade de componentes não suportada: ' + e.findtext('name'))
        c = components[0]
        # Regra solicitada para o emulador: falha perde um nível, sem ficar negativo.
        # O client original mantém o nível; não alterar a fonte canônica do client.
        failure = str(max(0, int(e.findtext('before_enchant_count')) - 1))
        ET.SubElement(result, 'enchant', group=group, before=e.findtext('before_enchant_count'),
                      success=e.findtext('success_enchant_count'), failure=failure,
                      probability=e.findtext('enchant_level_prob'), stones=e.findtext('enchant_essence_item_count'),
                      component=c.findtext('enchant_component_item'), cost=c.findtext('enchant_component_item_count'))
    for e in ET.parse(CLIENT / 'data/items/client_enchant_gap_level_prob.xml').getroot():
        grade = {'enchant_count_grade_one': '1', 'enchant_count_grade_two': '2'}[e.findtext('enchant_count_grade')]
        for q in e.findall('gap_level_enchant/data'):
            ET.SubElement(result, 'gap', grade=grade, level=e.findtext('gap_level'),
                          quality=q.findtext('quality'), probability=q.findtext('quality_gap_level_prob'))
    skills = items.load_name_ids(str(CLIENT / 'data/skills/client_skills.xml'))
    for e in powers:
        typ, value = e.findtext('combat_power_type'), e.findtext('value')
        if typ == 'skill':
            if value.lower() not in skills:
                raise ValueError('Skill oficial não encontrada: ' + value)
            value = skills[value.lower()]
        ET.SubElement(result, 'power', type=typ, value=value, points=e.findtext('combat_power_point'))
    canonical = {d['id']: d for d in items.iter_depth1(str(CLIENT / 'data/items/client_items.xml'))}
    canonical_by_name = {d['name'].lower(): d for d in canonical.values() if d.get('name')}
    for e in ET.parse(CLIENT / 'data/PC/combat_power_reward.xml').getroot():
        item_name = e.findtext('item_name').lower()
        item = canonical_by_name.get(item_name)
        if item is None:
            raise ValueError('Recompensa de Combat Talent não encontrada: ' + item_name)
        ET.SubElement(result, 'combat_reward', id=e.attrib['id'], goal=e.findtext('goal'),
                      item=item['id'], amount=e.findtext('item_amount'))
    name_ids, names = items.load_strings(str(CLIENT))
    raw = (SOURCE / 'items/item_templates.xml').read_bytes().decode('utf-8')
    changed = 0

    def replace(m):
        nonlocal changed
        attrs = dict(items.ATTR_RE.findall(m.group(1)))
        d = canonical.get(attrs.get('id'))
        if d is None:
            return m.group(0)
        old = m.group(0)
        head, inner = m.group(1), m.group(3) or ''
        updates = {'client_mask': str(client_mask(d)),
                   'mask': str((int(attrs.get('mask', '0')) & ~16384) |
                              (16384 if d.get('breakable', '').upper() == 'TRUE' else 0))}
        group = d.get('enchant_group')
        if group:
            updates['enchant_group'] = group
            updates['mask'] = str((int(updates['mask']) & ~512) |
                                  (512 if d.get('no_enchant', 'TRUE').upper() != 'FALSE' else 0))
            if group in limits and d.get('no_enchant', '').upper() != 'TRUE':
                updates['max_enchant'] = str(limits[group])
        points = d.get('combat_power_point', '0')
        if d.get('stat_enchant_type'):
            points = option_points.get((d['stat_enchant_type'] + ' ' + d.get('stat_enchant_value', '')).lower(), '0')
        if points != '0':
            updates['combat_power'] = points
        if d.get('equipment_slots') == 'seed':
            updates.update(item_group='ARCAMANT', mask=str(items.gen_mask(d)))
            desc = d['desc'].upper()
            updates['name'] = names.get(desc, d['name'])
            if desc in name_ids:
                updates['desc'] = name_ids[desc]
            mods = items.gen_mods(d)
            inner = '\r\n\t\t<modifiers>\r\n' + '\r\n'.join(
                f'\t\t\t<{op} name="{stat}" value="{v}"' + (' bonus="true"' if bonus else '') + ' />'
                for op, stat, v, bonus in mods) + '\r\n\t\t</modifiers>\r\n\t'
        if d.get('mgrouptag') == 'I_Enchant_All' and d.get('level') == '120':
            updates['enchant_essence'] = 'true'
            updates['item_group'] = 'ENCHANTMENT'
        for k, v in updates.items():
            if k in attrs:
                head = re.sub(r'\b' + k + r'="[^"]*"', lambda _: f'{k}="{items.esc(v)}"', head)
            else:
                head += f' {k}="{items.esc(v)}"'
        new = '\t<item_template' + head.rstrip() + ('>' + inner + '</item_template>' if inner else ' />')
        changed += old != new
        return new

    updated = items.BLOCK_RE.sub(replace, raw)
    ET.fromstring(updated)
    ET.indent(result, space='\t')
    xml = ET.tostring(result, encoding='utf-8', xml_declaration=True)
    for name, content in [('item_templates', updated.encode('utf-8')), ('classic_item_systems', xml)]:
        schema = etree.XMLSchema(etree.parse(str(SOURCE / 'items' / (name + '.xsd'))))
        schema.assertValid(etree.fromstring(content))
    return updated.encode('utf-8'), xml, changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aplicar', action='store_true')
    args = parser.parse_args()
    templates, rules, changed = generate()
    print(f'{changed} templates atualizados; {len(ET.fromstring(rules))} regras oficiais.')
    if args.aplicar:
        for target in (SOURCE, PRODUCT):
            (target / 'items/item_templates.xml').write_bytes(templates)
            (target / 'items/classic_item_systems.xml').write_bytes(rules)


if __name__ == '__main__':
    main()
