import os
import xml.etree.ElementTree as ET

VALID_13_CLASSES = [
    "GLADIATOR",
    "TEMPLAR",
    "ASSASSIN",
    "RANGER",
    "SORCERER",
    "SPIRIT_MASTER",
    "CLERIC",
    "CHANTER",
    "REVENANT",
    "BRAWLER",
    "LUMINESS",
    "PHOENIX",
    "SOUL_REAPER"
]

import backup_manager

for base_dir in [
    r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data",
    r"D:\AION CLASSIC 5.0 - EMULADOR\2 - Emulador [Produto Final]\GameServer\data\static_data"
]:
    path = os.path.join(base_dir, "player_initial_data.xml")
    backup_manager.backup_file_before_modification(path)
    tree = ET.parse(path)
    root = tree.getroot()

    new_root = ET.Element("player_initial_data", root.attrib)
    # copy spawn location elements
    for child in root:
        if child.tag != "player_data":
            new_root.append(child)

    seen = set()
    for pd in root.findall("player_data"):
        cls = pd.get("class")
        if cls in VALID_13_CLASSES and cls not in seen:
            seen.add(cls)
            new_root.append(pd)

    print(f"File {path}: kept {len(seen)} / 13 classes: {seen}")
    new_tree = ET.ElementTree(new_root)
    new_tree.write(path, encoding="utf-8", xml_declaration=True)
