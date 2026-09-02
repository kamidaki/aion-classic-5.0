import xml.etree.ElementTree as ET

path = r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data\player_initial_data.xml"
tree = ET.parse(path)
root = tree.getroot()

for pd in root.findall("player_data"):
    print(pd.get("class"))
