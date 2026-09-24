import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(PARSERS_DIR)))
import os
import re
import xml.etree.ElementTree as ET

BASE = os.path.join(PROJECT_ROOT, "Código Fonte - Emulador", "GameServer", "data", "static_data")

# Let's inspect quest_data.xml for all category values
qd = os.path.join(BASE, "quest_data", "quest_data.xml")
tree_q = ET.parse(qd)
categories = set()
for q in tree_q.getroot().findall("quest"):
    c = q.get("category")
    if c:
        categories.add(c)
print("Quest categories present:", categories)

# Let's check repeat_cycle, mentor_type, target_type, race_permitted
repeat_cycles = set()
mentor_types = set()
target_types = set()
races = set()

for q in tree_q.getroot().findall("quest"):
    rc = q.get("repeat_cycle")
    if rc: repeat_cycles.add(rc)
    mt = q.get("mentor_type")
    if mt: mentor_types.add(mt)
    tt = q.get("target_type")
    if tt: target_types.add(tt)
    rp = q.get("race_permitted")
    if rp: races.add(rp)

print("Repeat cycles:", repeat_cycles)
print("Mentor types:", mentor_types)
print("Target types:", target_types)
print("Races permitted:", races)
