import os
import xml.etree.ElementTree as ET

player_stats_dir = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data\stats\player"

for f in os.listdir(player_stats_dir):
    if not f.endswith(".xml"): continue
    fp = os.path.join(player_stats_dir, f)
    tree = ET.parse(fp)
    root = tree.getroot()
    classes = set(ps.get("class") for ps in root.findall("player_stats"))
    print(f"{f}: {classes}")
