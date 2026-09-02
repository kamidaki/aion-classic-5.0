import os
import re
import xml.etree.ElementTree as ET

spawns_dir = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data\spawns"
world_maps_xml = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data\world_maps.xml"
npc_xml = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data\npcs\npc_templates.xml"
ai_dir = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\scripts\system\handlers\ai"

# 1. Map ID to map info
map_info = {}
tree_wm = ET.parse(world_maps_xml)
for m in tree_wm.getroot().findall("map"):
    mid = m.get("id")
    mname = m.get("name")
    map_info[mid] = mname

# 2. Parse spawns to map npc_id -> set of map_ids
npc_to_maps = {}
for f in os.listdir(spawns_dir):
    if f.endswith(".xml"):
        map_id = f.replace(".xml", "")
        p = os.path.join(spawns_dir, f)
        try:
            tree_s = ET.parse(p)
            for spawn in tree_s.getroot().findall(".//spawn"):
                npc_id = spawn.get("npc_id")
                if npc_id:
                    if npc_id not in npc_to_maps:
                        npc_to_maps[npc_id] = set()
                    npc_to_maps[npc_id].add(map_id)
        except Exception as e:
            pass

print(f"Total spawned NPCs mapped: {len(npc_to_maps)}")

# 3. Existing AIs
existing_ais = set()
for root, dirs, files in os.walk(ai_dir):
    for f in files:
        if f.endswith('.java'):
            with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
                matches = re.findall(r'@AIName\s*\(\s*"([^"]+)"\s*\)', content)
                for m in matches:
                    existing_ais.add(m)
                    existing_ais.add(m.lower())

# 4. NPC Templates AI
tree_npc = ET.parse(npc_xml)
ai_to_npcs = {}
ai_to_maps = {}

for npc in tree_npc.getroot().findall("npc_template"):
    ai = npc.get("ai")
    nid = npc.get("npc_id")
    if ai:
        if ai not in ai_to_npcs:
            ai_to_npcs[ai] = []
            ai_to_maps[ai] = set()
        ai_to_npcs[ai].append(nid)
        if nid in npc_to_maps:
            for mid in npc_to_maps[nid]:
                ai_to_maps[ai].add(mid)

missing_ais = {}
for ai, npcs in ai_to_npcs.items():
    if ai not in existing_ais and ai.lower() not in existing_ais:
        missing_ais[ai] = {
            "npcs": npcs,
            "maps": ai_to_maps[ai]
        }

print(f"Total missing distinct AIs: {len(missing_ais)}")
with_spawn_map = sum(1 for v in missing_ais.values() if len(v["maps"]) > 0)
without_spawn_map = sum(1 for v in missing_ais.values() if len(v["maps"]) == 0)
print(f"Missing AIs with at least one spawn map: {with_spawn_map}")
print(f"Missing AIs without spawn map: {without_spawn_map}")
