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
    r"D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data\stats\player",
    r"D:\AION CLASSIC 5.0 - EMULADOR\2 - Emulador [Produto Final]\GameServer\data\static_data\stats\player"
]:
    for f in LEGACY_FILES:
        fp = os.path.join(base_dir, f)
        if os.path.exists(fp):
            os.remove(fp)
            print(f"Removed legacy file: {fp}")
