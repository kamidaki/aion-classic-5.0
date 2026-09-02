import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PARSERS_DIR))
import os
import xml.etree.ElementTree as ET
import backup_manager

# Read client pcexp_table.xml if exists, or use client data
client_exp_path = os.path.join(PROJECT_ROOT, "Cliente Classic 4.5\Data\Dump\PC\pcexp_table.xml")

for base_dir in [
    os.path.join(PROJECT_ROOT, "1 - Código Fonte [Emulador]", "GameServer", "data", "static_data"),
    os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data")
]:
    exp_file = os.path.join(base_dir, "player_experience_table.xml")
    backup_manager.backup_file_before_modification(exp_file)
    if os.path.exists(client_exp_path):
        c_tree = ET.parse(client_exp_path)
        root = ET.Element("player_experience_table", {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "player_experience_table.xsd"
        })
        for entry in c_tree.getroot():
            exp_val = entry.findtext("exp", "0")
            elem = ET.SubElement(root, "exp")
            elem.text = exp_val
        tree = ET.ElementTree(root)
        tree.write(exp_file, encoding="utf-8", xml_declaration=True)
        print(f"Wrote {len(root)} levels from client pcexp_table to {exp_file}")
    else:
        # If client xml not found, convert current file's exp attribute to text
        tree = ET.parse(exp_file)
        root = tree.getroot()
        new_root = ET.Element("player_experience_table", {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "player_experience_table.xsd"
        })
        for elem in root.findall("exp"):
            val = elem.get("exp") or elem.text or "0"
            new_elem = ET.SubElement(new_root, "exp")
            new_elem.text = val
        tree = ET.ElementTree(new_root)
        tree.write(exp_file, encoding="utf-8", xml_declaration=True)
        print(f"Converted {len(new_root)} levels to text in {exp_file}")
