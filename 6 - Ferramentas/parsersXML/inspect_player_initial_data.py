import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PARSERS_DIR))
import xml.etree.ElementTree as ET

path = os.path.join(PROJECT_ROOT, "1 - Código Fonte [Emulador]", "GameServer", "data", "static_data", "player_initial_data.xml")
tree = ET.parse(path)
root = tree.getroot()

for pd in root.findall("player_data"):
    print(pd.get("class"))
