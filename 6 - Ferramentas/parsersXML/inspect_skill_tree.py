import os
import xml.etree.ElementTree as ET

tree_xml = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data\skill_tree\skill_tree.xml"
tree = ET.parse(tree_xml)
root = tree.getroot()

classes = set()
null_class_count = 0
for s in root.findall("skill"):
    c = s.get("classId")
    if not c:
        null_class_count += 1
    else:
        classes.add(c)

print(f"Total skills: {len(root)}")
print(f"Skills without classId: {null_class_count}")
print(f"ClassId values: {classes}")
