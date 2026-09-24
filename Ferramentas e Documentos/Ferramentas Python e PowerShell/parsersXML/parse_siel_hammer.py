"""Exporta as tabelas de desmontagem e os itens elegíveis do cliente oficial 5.0."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/data/items'
SERVER = ROOT / 'Código Fonte - Emulador/game-server/data/static_data'


def generate():
    items = {}
    for _, element in ET.iterparse(SERVER / 'items/item_templates.xml'):
        if element.tag == 'item_template':
            items[element.get('cName', '').lower()] = element.get('id')
            element.clear()
    result = ET.Element('siel_hammer', {
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:noNamespaceSchemaLocation': 'siel_hammer.xsd'})
    tables = {}

    def reward(parent, tag, name, count, probability):
        item_id = items.get(name.lower())
        if item_id is None:
            raise ValueError(f'Item do Hammer ausente nos templates: {name}')
        ET.SubElement(parent, tag, item_id=item_id, count=count, probability=probability)

    for source in ET.parse(CLIENT / 'client_item_crush.xml').getroot():
        table_id = source.findtext('id')
        name = source.findtext('name').lower()
        if name in tables:
            raise ValueError(f'Tabela repetida: {name}')
        tables[name] = table_id
        table = ET.SubElement(result, 'table', id=table_id, kinah=source.findtext('crush_cost'))
        for index in (1, 2, 3):
            prefix = f'index{index}_enchant_crush_'
            entries = source.findall(prefix + 'data_list/data')
            if not entries:
                continue
            band = ET.SubElement(table, 'band',
                                 minimum=source.findtext(f'index{index}_enchant_count_min'),
                                 maximum=source.findtext(f'index{index}_enchant_count_max'))
            total = 0
            for entry in entries:
                probability = entry.findtext(prefix + 'result_prob')
                total += int(probability)
                reward(band, 'result', entry.findtext(prefix + 'result_item'),
                       entry.findtext(prefix + 'result_count'), probability)
            if total != 1000:
                raise ValueError(f'Probabilidades inválidas na tabela {table_id}: {total}')
            bonus = source.findtext(prefix + 'bonus_item_1')
            if bonus:
                reward(band, 'bonus', bonus, source.findtext(prefix + 'bonus_count_1'),
                       source.findtext(prefix + 'bonus_prob_1'))
    eligible = 0
    for _, source in ET.iterparse(CLIENT / 'client_items.xml'):
        if source.tag != 'client_item':
            continue
        if source.findtext('can_crush', '').upper() == 'TRUE':
            # Official starter arrows carry a non-table marker; there is no crushing recipe.
            if source.findtext('crush_name', '').lower() == 'can_not_record':
                source.clear()
                continue
            name = source.findtext('name').lower()
            item_id = items.get(name)
            if item_id != source.findtext('id'):
                raise ValueError(f'Item elegível ausente ou divergente: {name}')
            table_id = tables[source.findtext('crush_name').lower()]
            ET.SubElement(result, 'item', item_id=item_id, table_id=table_id)
            eligible += 1
        source.clear()
    ET.indent(result, space='\t')
    ET.ElementTree(result).write(SERVER / 'items/siel_hammer.xml', encoding='utf-8', xml_declaration=True)
    print(f'{len(tables)} tabelas e {eligible} itens elegíveis exportados do cliente oficial 5.0.')


if __name__ == '__main__':
    generate()
