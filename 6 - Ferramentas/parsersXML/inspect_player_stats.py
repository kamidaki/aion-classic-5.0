import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PARSERS_DIR))
import os
import xml.etree.ElementTree as ET

player_stats_dir = os.path.join(PROJECT_ROOT, "1 - Código Fonte [Emulador]", "GameServer", "data", "static_data", "stats\player")

for f in os.listdir(player_stats_dir):
    if not f.endswith(".xml"): continue
    fp = os.path.join(player_stats_dir, f)
    tree = ET.parse(fp)
    root = tree.getroot()
    classes = set(ps.get("class") for ps in root.findall("player_stats"))
    print(f"{f}: {classes}")
