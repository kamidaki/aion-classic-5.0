"""Configura um Shugo por vez entre os vinte pontos existentes das ilhas."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from lxml import etree

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'Código Fonte - Emulador/game-server/data/static_data'
PRODUCT = ROOT / 'Emulador - Produto Final/GameServer/data/static_data'
RELATIVE = Path('spawns/Npcs/800040000_Tiamaranta_Mesa.xml')


def main():
    path = SOURCE / RELATIVE
    raw = path.read_bytes()
    before = ET.fromstring(raw)
    groups = before.findall('.//spawn[@npc_id="802181"]')
    assert len(groups) == 1 and len(groups[0].findall('spot')) == 20
    spots = [ET.tostring(n) for n in groups[0].findall('spot')]
    text, count = re.subn(r'<spawn npc_id="802181"[^>]*>',
                         '<spawn npc_id="802181" respawn_time="0" pool="1" rotation_time="600">', raw.decode('utf-8'))
    assert count == 1
    updated = text.encode('utf-8')
    parsed = ET.fromstring(updated)
    assert spots == [ET.tostring(n) for n in parsed.findall('.//spawn[@npc_id="802181"]/spot')]
    schema = etree.XMLSchema(etree.parse(str(SOURCE / 'spawns/spawns.xsd')))
    schema.assertValid(etree.fromstring(updated))
    path.write_bytes(updated)
    (PRODUCT / RELATIVE).write_bytes(updated)
    schema_relative = Path('spawns/spawns.xsd')
    (PRODUCT / schema_relative).write_bytes((SOURCE / schema_relative).read_bytes())
    print('Shugo 802181: 20 pontos preservados, pool 1, rotação 600s, respawn independente desativado; XSD válido.')


if __name__ == '__main__':
    main()
