import os
import xml.etree.ElementTree as ET

BASE_GS = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer"
PROD_GS = r"D:\AION CLASSIC 5.0 - EMULADOR\2 - Emulador [Produto Final]\GameServer"

EXPANSION = {
    "WARRIOR": ["GLADIATOR", "TEMPLAR"],
    "SCOUT": ["ASSASSIN", "RANGER"],
    "MAGE": ["SORCERER", "SPIRIT_MASTER"],
    "PRIEST": ["CLERIC", "CHANTER"],
    "MONK": ["REVENANT"],
    "THUNDERER": ["REVENANT"],
}

import backup_manager

def update_skill_tree(base_dir):
    tree_path = os.path.join(base_dir, "data", "static_data", "skill_tree", "skill_tree.xml")
    backup_manager.backup_file_before_modification(tree_path)
    tree = ET.parse(tree_path)
    root = tree.getroot()

    new_root = ET.Element("skill_tree", root.attrib)
    
    converted = 0
    expanded = 0
    for s in root.findall("skill"):
        cid = s.get("classId", "ALL").upper()
        if cid in EXPANSION:
            targets = EXPANSION[cid]
            for t in targets:
                new_s = ET.Element("skill", s.attrib)
                new_s.set("classId", t)
                new_root.append(new_s)
                if len(targets) > 1:
                    expanded += 1
                else:
                    converted += 1
        else:
            new_root.append(s)

    new_tree = ET.ElementTree(new_root)
    new_tree.write(tree_path, encoding="utf-8", xml_declaration=True)
    print(f"Updated {tree_path}: {len(root)} -> {len(new_root)} skills (converted: {converted}, expanded: {expanded})")

update_skill_tree(BASE_GS)
update_skill_tree(PROD_GS)
