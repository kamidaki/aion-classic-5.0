import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(PARSERS_DIR)))
import os

LEGACY_FILES = [
    "battle-master-templates.xml",
    "mage-templates.xml",
    "martial-artist-templates.xml",
    "monk-templates.xml",
    "priest-templates.xml",
    "reaper-templates.xml",
    "scout-templates.xml",
    "soul_reaper-templates.xml",
    "thunderer-templates.xml",
    "warrior-templates.xml"
]

for base_dir in [
    os.path.join(PROJECT_ROOT, "Código Fonte - Emulador", "GameServer", "data", "static_data", "stats\player"),
    os.path.join(PROJECT_ROOT, "Emulador - Produto Final", "GameServer", "data", "static_data", "stats\player")
]:
    for f in LEGACY_FILES:
        fp = os.path.join(base_dir, f)
        if os.path.exists(fp):
            os.remove(fp)
            print(f"Removed legacy file: {fp}")
