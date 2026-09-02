import os
import re
import xml.etree.ElementTree as ET

# Directories
BASE_GS = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer"
AI_DIR = os.path.join(BASE_GS, r"data\scripts\system\handlers\ai")
NPC_TEMPLATES_XML = os.path.join(BASE_GS, r"data\static_data\npcs\npc_templates.xml")

# 1. Collect all registered @AIName in the AI scripts
registered_ais = set()
registered_files = 0
for root, dirs, files in os.walk(AI_DIR):
    for f in files:
        if f.endswith('.java'):
            registered_files += 1
            with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
                matches = re.findall(r'@AIName\s*\(\s*"([^"]+)"\s*\)', content)
                for m in matches:
                    registered_ais.add(m)
                    registered_ais.add(m.strip())
                    registered_ais.add(m.lower())
                    registered_ais.add(m.strip().lower())

print(f"Total AI script files in {AI_DIR}: {registered_files}")
print(f"Total registered @AIName (unique): {len(registered_ais)//4}")

# 2. Check every NPC in npc_templates.xml
tree = ET.parse(NPC_TEMPLATES_XML)
root = tree.getroot()

total_npcs = 0
npc_with_ai = 0
bad_ai_names = set()

for npc in root.findall("npc_template"):
    total_npcs += 1
    ai = npc.get("ai")
    if ai:
        npc_with_ai += 1
        ai_clean = ai.strip()
        if ai not in registered_ais and ai_clean not in registered_ais and ai.lower() not in registered_ais and ai_clean.lower() not in registered_ais:
            bad_ai_names.add(ai)

print(f"Total NPCs in npc_templates.xml: {total_npcs}")
print(f"NPCs with 'ai' attribute: {npc_with_ai}")
print(f"Bad AI names count: {len(bad_ai_names)}")

if len(bad_ai_names) == 0:
    print("\n>>> SUCESSO ABSOLUTO: 0 BAD AI NAMES! TODAS AS IAS DE NPCS ESTÃO IMPLEMENTADAS E MAPEADAS! <<<")
else:
    print(f"\nAinda faltam {len(bad_ai_names)} IAs:")
    for b in sorted(list(bad_ai_names))[:10]:
        print("  -", b)
