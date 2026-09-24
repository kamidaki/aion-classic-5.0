import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import aion_unpak

data_dir = r"D:\GameForge\aionclassic\data"

paks_to_check = [
    os.path.join(data_dir, "world", "world.pak"),
    os.path.join(data_dir, "Quest", "Quest.pak"),
    os.path.join(data_dir, "npcs", "npcs.pak"),
    os.path.join(data_dir, "dialogs", "dialogs.pak"),
]

for p in paks_to_check:
    print(f"\n==================== {os.path.basename(p)} ====================")
    with open(p, "rb") as f:
        zf = aion_unpak.unpak_stream(f.read())
    names = zf.namelist()
    print(f"Total files: {len(names)}")
    tutorial_files = [n for n in names if any(k in n.lower() for k in ["tutorial", "telos", "poeta", "ishalgen", "11003", "11004", "22007", "reaper", "start"])]
    print(f"Tutorial/Start related files ({len(tutorial_files)}):")
    for tf in tutorial_files[:30]:
        print("  -", tf)
