import os
import sys
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
import aion_unpak

data_dir = r"D:\GameForge\aionclassic\data"

# Unpack PC.pak
pc_pak = os.path.join(data_dir, "PC", "PC.pak")
with open(pc_pak, "rb") as f:
    zf = aion_unpak.unpak_stream(f.read())

print("=== PC.pak files ===")
for name in zf.namelist():
    print(" ", name)

if "client_character_class_info.xml" in zf.namelist():
    data = zf.read("client_character_class_info.xml").decode("utf-8", errors="replace")
    with open(os.path.join(PROJECT_ROOT, "6 - Ferramentas", "client_character_class_info.xml"), "w", encoding="utf-8") as out:
        out.write(data)
    print("\nSaved client_character_class_info.xml (len:", len(data), ")")

# Check other files in PC.pak or other paks for stats and experience
for fn in zf.namelist():
    if "stat" in fn.lower() or "level" in fn.lower() or "exp" in fn.lower() or "class" in fn.lower():
        print(f"Interesting in PC.pak: {fn}")
        content = zf.read(fn).decode("utf-8", errors="replace")
        with open(os.path.join(os.path.join(PROJECT_ROOT, "6 - Ferramentas"), fn), "w", encoding="utf-8") as out:
            out.write(content)
