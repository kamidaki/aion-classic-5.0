import os
import xml.etree.ElementTree as ET
import backup_manager

base_static = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data"
prod_static = r"D:\AION CLASSIC 5.0 - EMULADOR\2 - Emulador [Produto Final]\GameServer\data\static_data"

def fix_pets_xml(static_dir):
    pets_path = os.path.join(static_dir, "pets", "pets.xml")
    if not os.path.exists(pets_path):
        return
    backup_manager.backup_file_before_modification(pets_path)
    tree = ET.parse(pets_path)
    root = tree.getroot()
    fixed = 0
    for pet in root.findall("pet"):
        cond = pet.get("condition_reward")
        if cond and not cond.isdigit():
            del pet.attrib["condition_reward"]
            fixed += 1
    tree.write(pets_path, encoding="utf-8", xml_declaration=True)
    print(f"Fixed {fixed} pets in {pets_path}")

fix_pets_xml(base_static)
fix_pets_xml(prod_static)
