"""
LostAcademy Aion Model Library - Configuration & Settings Constants.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Tuple

# Client detection paths provided optionally via environment variables
_ENV_CLIENT_ROOT = os.environ.get("AION_CLIENT_ROOT", "").strip()
DEFAULT_CLIENT_PATHS: List[str] = [_ENV_CLIENT_ROOT] if _ENV_CLIENT_ROOT else []

# Cache directories and filenames
INDEX_CACHE_FILENAME = ".aion_model_index.json"
THUMBNAIL_CACHE_DIRNAME = ".aion_model_thumbs"
DEFAULT_THUMBNAIL_SIZE: Tuple[int, int] = (160, 160)

# Safety settings
SAFETY_ALLOW_CLIENT_WRITE_DEFAULT: bool = False
BACKUP_SUFFIX: str = ".bak"

# Model Library Asset Categories (Categorias de Modelos)
KNOWN_CATEGORIES: List[Tuple[str, str, str]] = [
    ("ALL", "Todos os Modelos", "Todos os recursos indexados"),
    ("NPC", "NPCs", "Personagens não jogáveis e humanoides"),
    ("MONSTER", "Monstros & Chefes", "Criaturas agressivas, fauna e chefes"),
    ("CHARACTER", "Personagens de Jogadores", "Corpos base e customizações de jogadores"),
    ("WEAPON", "Armas & Escudos", "Espadas, adagas, arcos, cajados, orbes e escudos"),
    ("ARMOR", "Armaduras & Roupas", "Capacetes, peitorais, calças, luvas, botas e ombreiras"),
    ("WINGS", "Asas", "Asas e aparatos de voo"),
    ("PET_MOUNT", "Mascotes & Montarias", "Minions, familiares e montarias"),
    ("BUILDING", "Construções & Estruturas", "Castelos, fortalezas, casas e torres"),
    ("PROP", "Objetos de Cenário & Móveis", "Baús, móveis, barris e estandartes"),
    ("VEGETATION", "Vegetação & Natureza", "Árvores, flores, arbustos, rochas e terrenos"),
    ("OBJECT", "Objetos Interativos", "Portais, interruptores, portões e armadilhas"),
    ("EFFECT", "Efeitos & Luzes", "Âncoras visuais mágicas e emissores de partículas"),
]

# Supported Client Generations / Flavors
FLAVOR_GAMEFORGE = "GAMEFORGE_CLASSIC"
FLAVOR_LIVE_CLASSICO = "LIVE_CLASSICO_SA"
FLAVOR_AION_39 = "AION_39_LEGACY"
FLAVOR_GENERIC = "AION_GENERIC"
