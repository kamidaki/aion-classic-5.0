"""
Texture Provider for Aion Assets.
Resolves, extracts, deduplicates, and binds DDS textures to Blender material nodes.
"""

from __future__ import annotations
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

import bpy
from .base_provider import ITextureProvider
from ..core.pak_engine import AionCatalogIndex


class TextureProvider(ITextureProvider):
    """Manages DDS texture resolution and image datablock caching."""

    def __init__(self, catalog: AionCatalogIndex, client_root: Path, client_provider: Any = None):
        self.catalog = catalog
        self.client_root = client_root
        self.client_prov = client_provider
        self._image_cache: Dict[str, bpy.types.Image] = {}
        self._path_cache: Dict[str, Path] = {}
        self._indexed_texture_dirs: set[str] = set()
        self._temp_extracted_dir = Path(tempfile.mkdtemp(prefix="aion_tex_cache_"))

    def _ensure_texture_paks_indexed(self, rel_path: str) -> None:
        """Dynamically indexes texture PAKs (objects/monster, objects/npc, levels/common, Effects) on demand."""
        clean_lower = rel_path.lower().replace("\\", "/")
        candidate_folders: list[Path] = []

        if "monster" in clean_lower:
            candidate_folders.append(self.client_root / "objects" / "monster")
        if any(k in clean_lower for k in ("npc", "human", "pc")):
            candidate_folders.append(self.client_root / "objects" / "npc")
        if "effect" in clean_lower:
            candidate_folders.append(self.client_root / "Effects")

        # Always check common levels and general textures
        candidate_folders.append(self.client_root / "levels" / "common")
        candidate_folders.append(self.client_root / "data" / "cutscene" / "Textures")

        for c_dir in candidate_folders:
            key = str(c_dir).lower()
            if key not in self._indexed_texture_dirs and c_dir.is_dir():
                self._indexed_texture_dirs.add(key)
                for pak_p in c_dir.glob("*texture*.pak"):
                    try:
                        self.catalog.index_pak(pak_p)
                    except Exception:
                        pass
                for pak_p in c_dir.glob("*Texture*.pak"):
                    try:
                        self.catalog.index_pak(pak_p)
                    except Exception:
                        pass

    def resolve_texture_file(self, rel_path: str) -> Optional[Path]:
        """Resolves a texture path to an accessible file on disk (extracting from PAK if needed)."""
        if not rel_path:
            return None

        clean_rel = rel_path.replace("\\", "/").strip().lstrip("/")
        clean_key = clean_rel.lower()

        # Check path cache first
        if clean_key in self._path_cache:
            p = self._path_cache[clean_key]
            if p.is_file():
                return p

        # 1. Check loose file
        loose_cand = self.client_root / clean_rel
        if loose_cand.is_file():
            self._path_cache[clean_key] = loose_cand
            return loose_cand

        # 2. Check catalog
        entry_info = self.catalog.find_file(clean_rel)
        if not entry_info:
            entry_info = self.catalog.find_file(Path(clean_rel).name)

        if not entry_info:
            self._ensure_texture_paks_indexed(clean_rel)
            entry_info = self.catalog.find_file(clean_rel) or self.catalog.find_file(Path(clean_rel).name)

        if not entry_info and self.client_prov and hasattr(self.client_prov, "ensure_category_paks_indexed"):
            self.client_prov.ensure_category_paks_indexed(clean_rel)
            entry_info = self.catalog.find_file(clean_rel) or self.catalog.find_file(Path(clean_rel).name)

        if entry_info:
            pak_path, entry = entry_info
            dest_file = self._temp_extracted_dir / Path(clean_rel).name
            if dest_file.is_file():
                self._path_cache[clean_key] = dest_file
                return dest_file

            data = self.catalog.extract_file(entry.name)
            if data:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                dest_file.write_bytes(data)
                self._path_cache[clean_key] = dest_file
                return dest_file

        return None

    def get_texture_image(self, rel_path: str) -> Optional[bpy.types.Image]:
        """Loads or returns a cached bpy.types.Image for the given relative texture path."""
        if not rel_path:
            return None

        clean_key = rel_path.lower().replace("\\", "/").strip().lstrip("/")
        img_name = Path(clean_key).name

        # Safe cache lookup
        cached = self._image_cache.get(clean_key)
        if cached:
            try:
                if cached.name in bpy.data.images and cached.has_data:
                    return cached
            except ReferenceError:
                self._image_cache.pop(clean_key, None)

        existing_img = bpy.data.images.get(img_name)
        if existing_img:
            try:
                if existing_img.name and existing_img.has_data:
                    self._image_cache[clean_key] = existing_img
                    return existing_img
            except ReferenceError:
                pass

        file_path = self.resolve_texture_file(rel_path)
        if not file_path or not file_path.is_file():
            return None

        try:
            img = bpy.data.images.load(str(file_path), check_existing=True)
            img.name = img_name
            self._image_cache[clean_key] = img
            return img
        except Exception:
            return None

    def clear_cache(self) -> None:
        """Clears stale in-memory image references."""
        self._image_cache.clear()

    def cleanup(self) -> None:
        import shutil
        self.clear_cache()
        self._path_cache.clear()
        shutil.rmtree(self._temp_extracted_dir, ignore_errors=True)

