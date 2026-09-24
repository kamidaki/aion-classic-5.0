"""Gera receitas da Bigorna de Siel usando a variante confirmada pela PCAP 5.0."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/data/items/client_item_special_craft.xml'
SERVER = ROOT / 'Código Fonte - Emulador/game-server/data/static_data'


def generate():
    items = {}
    for _, element in ET.iterparse(SERVER / 'items/item_templates.xml'):
        if element.tag == 'item_template':
            items[element.get('cName', '').lower()] = element.get('id')
            element.clear()
    result = ET.Element('siel_anvil_recipes', {
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:noNamespaceSchemaLocation': 'siel_anvil.xsd'})
    enabled = 0
    for source in ET.parse(SOURCE).getroot():
        reasons = []
        if source.findtext('product_display', 'TRUE').upper() == 'FALSE':
            reasons.append('hidden')
        if source.find('product_limit_type') is not None:
            reasons.append('limited')
        recipe = ET.SubElement(result, 'recipe', id=source.findtext('id'))
        for field in ('ceiling_max_point', 'failure_ceiling_point_min', 'failure_ceiling_point_max'):
            if source.find(field) is not None:
                recipe.set(field, source.findtext(field))

        def entry(parent, tag, name, count, **attributes):
            item_id = items.get(name.lower())
            if item_id is None:
                raise ValueError(f'Receita {source.findtext("id")}: item ausente {name}')
            ET.SubElement(parent, tag, item_id=item_id, count=count, **attributes)

        for index in (1, 2):
            name = source.findtext(f'product{index}_result')
            if name:
                entry(recipe, 'product', name, source.findtext(f'product{index}_quantity'),
                      index=str(index), probability=source.findtext(f'product{index}_sucess_prob'))
        for index in range(1, 10):
            name = source.findtext(f'failure_return_{index}')
            if name:
                entry(recipe, 'refund', name, source.findtext(f'failure_return_quantity_{index}'))
        for source_group in source.findall('component_group_list/data'):
            group = ET.SubElement(recipe, 'materials')
            for index in range(1, 20):
                name = source_group.findtext(f'component{index}')
                if name:
                    item_id = int(items[name.lower()])
                    # Client 5.0 Game.dll: IsEquipmentForSpecialCombine (RVA 0x201B00).
                    selected = any(low <= item_id <= high for low, high in (
                        (100000000, 103099999), (110000000, 115099999),
                        (120000000, 125399999), (187000000, 187099999), (130000000, 130099999)))
                    entry(group, 'item', name, source_group.findtext(f'compo_quantity{index}'), selected=str(selected).lower())
        recipe.set('enabled', str(not reasons).lower())
        if reasons:
            recipe.set('disabled_reason', ','.join(reasons))
        else:
            enabled += 1
    ET.indent(result, space='\t')
    output = SERVER / 'items/siel_anvil.xml'
    ET.ElementTree(result).write(output, encoding='utf-8', xml_declaration=True)
    print(f'{len(result)} receitas exportadas; {enabled} habilitadas; {len(result)-enabled} ocultas ou dependentes de protocolo adicional.')


if __name__ == '__main__':
    generate()
