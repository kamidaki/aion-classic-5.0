"""
Asset Change Tracking and Modification State Manager.
Tracks original content hashes, modification state, dirty flags, and affected dependencies.
"""

from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class TrackedAsset:
    """Tracks state and modifications for a single loaded Aion asset."""

    def __init__(
        self,
        asset_id: str,
        asset_name: str,
        source_rel_path: str,
        original_bytes: bytes,
        pak_path: Optional[Path] = None,
    ):
        self.asset_id = asset_id
        self.asset_name = asset_name
        self.source_rel_path = source_rel_path.replace("\\", "/").strip().lstrip("/")
        self.pak_path = Path(pak_path).resolve() if pak_path else None
        self.original_hash = hashlib.sha256(original_bytes).hexdigest()
        self.current_hash = self.original_hash
        self.is_dirty: bool = False
        self.modified_fields: Set[str] = set()
        self.modified_bytes: Optional[bytes] = None
        self.dependencies: List[str] = []

    def mark_modified(self, field_name: str, new_bytes: bytes) -> None:
        """Records a modification on a specific subsystem (mesh, skeleton, material, anim)."""
        self.modified_fields.add(field_name)
        self.modified_bytes = new_bytes
        self.current_hash = hashlib.sha256(new_bytes).hexdigest()
        self.is_dirty = (self.current_hash != self.original_hash)

    def revert(self, original_bytes: bytes) -> None:
        """Reverts modifications back to original."""
        self.modified_fields.clear()
        self.modified_bytes = None
        self.current_hash = self.original_hash
        self.is_dirty = False

    def commit(self) -> None:
        """Marks current modified state as the new baseline after saving."""
        if self.modified_bytes:
            self.original_hash = self.current_hash
        self.modified_fields.clear()
        self.modified_bytes = None
        self.is_dirty = False


class ChangeTracker:
    """Singleton tracker for all open and modified assets in the Blender session."""

    _instance: Optional["ChangeTracker"] = None

    def __init__(self):
        self._tracked: Dict[str, TrackedAsset] = {}

    @classmethod
    def get(cls) -> "ChangeTracker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def track(
        self,
        asset_id: str,
        asset_name: str,
        source_rel_path: str,
        original_bytes: bytes,
        pak_path: Optional[Path] = None,
    ) -> TrackedAsset:
        tracked = TrackedAsset(asset_id, asset_name, source_rel_path, original_bytes, pak_path)
        self._tracked[asset_id] = tracked
        return tracked

    def get_tracked(self, asset_id: str) -> Optional[TrackedAsset]:
        return self._tracked.get(asset_id)

    def mark_dirty(self, asset_id: str, field_name: str, new_bytes: bytes) -> None:
        tracked = self._tracked.get(asset_id)
        if tracked:
            tracked.mark_modified(field_name, new_bytes)

    def get_dirty_assets(self) -> List[TrackedAsset]:
        return [t for t in self._tracked.values() if t.is_dirty]

    def clear(self) -> None:
        self._tracked.clear()
