"""
AssetEntry Data Model.
Represents lightweight metadata for indexed Aion assets without loading mesh geometry into memory.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AssetEntry:
    """Lightweight metadata descriptor for an Aion asset in the library index."""

    asset_id: str
    name: str
    category: str  # NPC, MONSTER, CHARACTER, WEAPON, ARMOR, WINGS, PET_MOUNT, BUILDING, PROP, VEGETATION, OBJECT, EFFECT
    model_path: str  # Relative client path (e.g. 'objects/npc/shugomale/shugomale.cgf')
    client_flavor: str = "GENERIC"
    source_pak: Optional[str] = None  # PAK filename if packed, None if loose
    is_loose: bool = False

    # Skeleton & Animation Metadata
    has_skeleton: bool = False
    bone_count: int = 0
    skeleton_path: Optional[str] = None
    cal_path: Optional[str] = None
    idle_animation: Optional[str] = None
    animations: List[str] = field(default_factory=list)
    animation_count: int = 0

    # Geometry & Materials Metadata
    vertex_count: int = 0
    triangle_count: int = 0
    bounding_box: Tuple[float, float, float] = (1.0, 1.0, 1.0)  # Dimensions (X, Y, Z) in meters
    materials: List[str] = field(default_factory=list)
    textures: List[str] = field(default_factory=list)

    # State & Audit
    thumbnail_path: Optional[str] = None
    content_hash: str = ""
    file_size: int = 0
    last_modified: float = 0.0
    is_modified: bool = False
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["bounding_box"] = list(self.bounding_box)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetEntry":
        d = dict(data)
        if "bounding_box" in d and isinstance(d["bounding_box"], list):
            d["bounding_box"] = tuple(d["bounding_box"])
        return cls(**d)

    @property
    def display_label(self) -> str:
        """User-friendly label shown in grids and list views."""
        if self.name and self.name != Path(self.model_path).stem:
            return f"{self.name} ({Path(self.model_path).stem})"
        return Path(self.model_path).stem or self.name

    @property
    def search_string(self) -> str:
        """Precomputed lowercase string for instantaneous search matching."""
        terms = [
            self.asset_id,
            self.name,
            self.category,
            self.model_path,
            Path(self.model_path).name,
            self.idle_animation or "",
            "skeleton" if self.has_skeleton else "static",
        ]
        terms.extend(self.animations[:5])
        return " ".join(t.lower() for t in terms if t)
