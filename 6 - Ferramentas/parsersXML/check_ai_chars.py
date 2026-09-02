import os
import re
import xml.etree.ElementTree as ET

npc_xml = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data\npcs\npc_templates.xml"
tree_npc = ET.parse(npc_xml)

ai_names = set()
for npc in tree_npc.getroot().findall("npc_template"):
    ai = npc.get("ai")
    if ai:
        ai_names.add(ai)

invalid_chars = set()
for a in ai_names:
    for c in a:
        if not (c.isalnum() or c == '_'):
            invalid_chars.add(c)

print(f"Non-alphanumeric chars in AI names: {invalid_chars}")

for a in sorted(list(ai_names)):
    if any(c in invalid_chars for c in a):
        print("Special AI name:", a)
