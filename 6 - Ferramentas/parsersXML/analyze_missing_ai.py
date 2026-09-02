import os
import re
import xml.etree.ElementTree as ET

ai_dir = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\scripts\system\handlers\ai"
existing_ais = set()
existing_files = set()

for root, dirs, files in os.walk(ai_dir):
    for f in files:
        if f.endswith('.java'):
            existing_files.add(f.lower())
            with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
                matches = re.findall(r'@AIName\s*\(\s*"([^"]+)"\s*\)', content)
                for m in matches:
                    existing_ais.add(m)
                    existing_ais.add(m.lower())

print(f"Total existing @AIName registered: {len(existing_ais)//2}")

npc_xml = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data\npcs\npc_templates.xml"
tree = ET.parse(npc_xml)
root = tree.getroot()

npc_ais = set()
ai_to_npc = {}
for npc in root.findall('npc_template'):
    ai = npc.get('ai')
    npc_id = npc.get('npc_id')
    if ai:
        npc_ais.add(ai)
        if ai not in ai_to_npc:
            ai_to_npc[ai] = []
        ai_to_npc[ai].append(npc_id)

print(f"Total distinct NPC AI names in npc_templates.xml: {len(npc_ais)}")

missing = set()
for a in npc_ais:
    if a not in existing_ais and a.lower() not in existing_ais:
        missing.add(a)

print(f"Missing AI names: {len(missing)}")
for m in sorted(list(missing))[:30]:
    print(f"  missing: {m} (used by {len(ai_to_npc[m])} npcs, e.g. {ai_to_npc[m][:3]})")
