import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(PARSERS_DIR)))
import os
import xml.etree.ElementTree as ET
import backup_manager

def clean_spawns(spawns_dir):
    cleaned_files = 0
    total_removed = 0
    for root_dir, _, files in os.walk(spawns_dir):
        for f in files:
            if not f.endswith(".xml"): continue
            fp = os.path.join(root_dir, f)
            try:
                tree = ET.parse(fp)
                root = tree.getroot()
                modified = False
                for spawn in root.iter("spawn"):
                    if "payload" in spawn.attrib:
                        del spawn.attrib["payload"]
                        total_removed += 1
                        modified = True

                if modified:
                    backup_manager.backup_file_before_modification(fp)
                    tree.write(fp, encoding="utf-8", xml_declaration=True)
                    cleaned_files += 1
            except Exception as e:
                print(f"Error parsing {fp}: {e}")
    print(f"Cleaned {cleaned_files} files in {spawns_dir}, removed {total_removed} payload attributes.")

base_spawns = os.path.join(PROJECT_ROOT, "Código Fonte - Emulador", "GameServer", "data", "static_data", "spawns")
prod_spawns = os.path.join(PROJECT_ROOT, "Emulador - Produto Final", "GameServer", "data", "static_data", "spawns")

clean_spawns(base_spawns)
clean_spawns(prod_spawns)
