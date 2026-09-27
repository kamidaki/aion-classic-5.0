"""
Aion Client Discovery and Version Detection.
Scans disks for available Aion game installations and identifies their flavor and asset architecture.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from config.settings import (
        DEFAULT_CLIENT_PATHS,
        FLAVOR_GAMEFORGE,
        FLAVOR_LIVE_CLASSICO,
        FLAVOR_AION_39,
        FLAVOR_GENERIC,
    )
except ImportError:
    from ..config.settings import (
        DEFAULT_CLIENT_PATHS,
        FLAVOR_GAMEFORGE,
        FLAVOR_LIVE_CLASSICO,
        FLAVOR_AION_39,
        FLAVOR_GENERIC,
    )


class ClientInfo:
    """Detailed metadata for a detected Aion client."""

    __slots__ = ("name", "path", "flavor", "is_valid", "levels_count", "has_data", "has_shaders")

    def __init__(
        self,
        name: str,
        path: Path,
        flavor: str,
        is_valid: bool = True,
        levels_count: int = 0,
        has_data: bool = True,
        has_shaders: bool = True,
    ):
        self.name = name
        self.path = path
        self.flavor = flavor
        self.is_valid = is_valid
        self.levels_count = levels_count
        self.has_data = has_data
        self.has_shaders = has_shaders

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "flavor": self.flavor,
            "is_valid": self.is_valid,
            "levels_count": self.levels_count,
            "has_data": self.has_data,
            "has_shaders": self.has_shaders,
        }


def detect_client_flavor(root_path: Path) -> str:
    """Analyzes a client root path to identify its exact generation flavor."""
    root_str = str(root_path).lower()
    if "gameforge" in root_str or "aionclassic" in root_str:
        return FLAVOR_GAMEFORGE
    if "live cl" in root_str or "am" in root_str or "lostacademy" in root_str:
        return FLAVOR_LIVE_CLASSICO
    if "3. 9" in root_str or "3.9" in root_str or "this aion" in root_str:
        return FLAVOR_AION_39

    # Inspect files on disk
    data_p = root_path / "Data" if (root_path / "Data").is_dir() else root_path / "data"
    if data_p.is_dir():
        npcs_p = data_p / "NPCs" if (data_p / "NPCs").is_dir() else data_p / "npcs"
        if npcs_p.is_dir():
            if (npcs_p / "Npcs_LostAcademy.pak").is_file():
                return FLAVOR_LIVE_CLASSICO
            if (npcs_p / "Npcs.pak").is_file():
                return FLAVOR_AION_39

    return FLAVOR_GENERIC


def inspect_client(client_path: str | Path) -> Optional[ClientInfo]:
    """Inspects a single path to see if it is a valid Aion client."""
    p = Path(client_path).resolve()
    if not p.is_dir():
        return None

    # Check for characteristic Aion directories
    has_levels = (p / "levels").is_dir() or (p / "Levels").is_dir()
    has_data = (p / "data").is_dir() or (p / "Data").is_dir()
    has_objects = (p / "objects").is_dir() or (p / "Objects").is_dir()
    has_textures = (p / "textures").is_dir() or (p / "Textures").is_dir()
    has_shaders = (p / "shaders").is_dir() or (p / "Shaders").is_dir()

    # Valid if at least 2 key folders exist
    valid_dirs = sum([has_levels, has_data, has_objects, has_textures, has_shaders])
    if valid_dirs < 2:
        return None

    flavor = detect_client_flavor(p)

    levels_dir = p / "levels" if (p / "levels").is_dir() else p / "Levels"
    levels_count = 0
    if levels_dir.is_dir():
        levels_count = sum(1 for d in levels_dir.iterdir() if d.is_dir() and not d.name.startswith("."))

    name_map = {
        FLAVOR_GAMEFORGE: f"GameForge Classic ({p.name})",
        FLAVOR_LIVE_CLASSICO: f"Aion Live Clássico SA ({p.name})",
        FLAVOR_AION_39: f"This AION Brasil 3.9 ({p.name})",
        FLAVOR_GENERIC: f"Aion Client ({p.name})",
    }
    client_name = name_map.get(flavor, f"Aion Client ({p.name})")

    return ClientInfo(
        name=client_name,
        path=p,
        flavor=flavor,
        is_valid=True,
        levels_count=levels_count,
        has_data=has_data,
        has_shaders=has_shaders,
    )


def discover_available_clients(extra_paths: Optional[List[str]] = None) -> List[ClientInfo]:
    """Discovers all valid Aion clients from default paths and any user-specified extras."""
    candidates = list(DEFAULT_CLIENT_PATHS)
    if extra_paths:
        for ep in extra_paths:
            if ep and ep not in candidates:
                candidates.insert(0, ep)

    clients: List[ClientInfo] = []
    seen_paths = set()

    for cand in candidates:
        info = inspect_client(cand)
        if info and str(info.path) not in seen_paths:
            clients.append(info)
            seen_paths.add(str(info.path))

    return clients


class ClientDetector:
    """Convenience interface for discovering and inspecting clients."""

    @staticmethod
    def detect_client(client_path: str | Path) -> Optional[ClientInfo]:
        return inspect_client(client_path)

    @staticmethod
    def find_clients(extra_paths: Optional[List[str]] = None) -> List[ClientInfo]:
        return discover_available_clients(extra_paths)
