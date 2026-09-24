import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(PARSERS_DIR)))
import os
import re
import xml.etree.ElementTree as ET

npc_xml = os.path.join(PROJECT_ROOT, "Código Fonte - Emulador", "GameServer", "data", "static_data", "npcs\npc_templates.xml")
tree_npc = ET.parse(npc_xml)

ai_patterns = {}
for npc in tree_npc.getroot().findall("npc_template"):
    ai = npc.get("ai")
    if ai:
        prefix = ai.split('_')[0]
        ai_patterns[prefix] = ai_patterns.get(prefix, 0) + 1

for k, v in sorted(ai_patterns.items(), key=lambda x: x[1], reverse=True)[:40]:
    print(f"{k}: {v}")
