"""
LostAcademy Aion Model Library - Configuration & Settings Constants.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Tuple

# Client detection fallback paths in priority order
DEFAULT_CLIENT_PATHS: List[str] = [
    r"D:\AION CLASSIC 5.0 - EMULADOR",
    r"D:\GameForge\aionclassic",
    r"I:\Aion Live Clássico - América do Sul",
    r"I:\Servidor Aion\CLIENT 3. 9 - THIS AION BRASIL\This AION Brasil",
]

# Cache directories and filenames
INDEX_CACHE_FILENAME = ".aion_model_index.json"
THUMBNAIL_CACHE_DIRNAME = ".aion_model_thumbs"
DEFAULT_THUMBNAIL_SIZE: Tuple[int, int] = (160, 160)

# Safety settings
SAFETY_ALLOW_CLIENT_WRITE_DEFAULT: bool = False
BACKUP_SUFFIX: str = ".bak"

# Model Library Asset Categories
KNOWN_CATEGORIES: List[Tuple[str, str, str]] = [
    ("ALL", "All Assets", "All indexed assets"),
    ("NPC", "NPCs", "Non-player characters & humanoids"),
    ("MONSTER", "Monsters & Bosses", "Aggressive creatures, wildlife, bosses"),
    ("CHARACTER", "Player Characters", "Player race base bodies and customizations"),
    ("WEAPON", "Weapons & Shields", "Swords, daggers, bows, staves, orbs, shields"),
    ("ARMOR", "Armor & Clothing", "Helmets, tops, pants, gloves, boots, pauldrons"),
    ("WINGS", "Wings", "Wings & flight apparitions"),
    ("PET_MOUNT", "Pets & Mounts", "Minions, familiars, rideable mounts"),
    ("BUILDING", "Buildings & Structures", "Castles, fortress pieces, houses, towers"),
    ("PROP", "Props & Furniture", "Chests, clutter, furniture, barrels, banners"),
    ("VEGETATION", "Vegetation & Nature", "Trees, flowers, grasses, roots, rocks"),
    ("OBJECT", "Interactive & World Objects", "Teleporters, switches, gates, traps"),
    ("EFFECT", "Effects & Lights", "Magic visual anchors, particles, fx placeables"),
]

# Supported Client Generations / Flavors
FLAVOR_GAMEFORGE = "GAMEFORGE_CLASSIC"
FLAVOR_LIVE_CLASSICO = "LIVE_CLASSICO_SA"
FLAVOR_AION_39 = "AION_39_LEGACY"
FLAVOR_GENERIC = "AION_GENERIC"
