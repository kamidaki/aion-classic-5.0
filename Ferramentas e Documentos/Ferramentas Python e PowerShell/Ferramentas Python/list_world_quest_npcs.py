import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import aion_unpak

data_dir = r"D:\GameForge\aionclassic\data"

paks_to_check = [
    ("world.pak", os.path.join(data_dir, "world", "world.pak")),
    ("Quest.pak", os.path.join(data_dir, "Quest", "Quest.pak")),
    ("npcs.pak", os.path.join(data_dir, "npcs", "npcs.pak")),
]

for title, p in paks_to_check:
    print(f"\n==================== {title} ====================")
    with open(p, "rb") as f:
        zf = aion_unpak.unpak_stream(f.read())
    for name in zf.namelist():
        print(" ", name)
