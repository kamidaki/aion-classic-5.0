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

    def __init__(self, catalog: AionCatalogIndex, client_root: Path):
        self.catalog = catalog
        self.client_root = client_root
        self._image_cache: Dict[str, bpy.types.Image] = {}
        self._temp_extracted_dir = Path(tempfile.mkdtemp(prefix="aion_tex_cache_"))

    def resolve_texture_file(self, rel_path: str) -> Optional[Path]:
        """Resolves a texture path to an accessible file on disk (extracting from PAK if needed)."""
        if not rel_path:
            return None

        clean_rel = rel_path.replace("\\", "/").strip().lstrip("/")

        # 1. Check loose file
        loose_cand = self.client_root / clean_rel
        if loose_cand.is_file():
            return loose_cand

        # 2. Check catalog
        entry_info = self.catalog.find_file(clean_rel)
        if not entry_info:
            entry_info = self.catalog.find_file(Path(clean_rel).name)

        if entry_info:
            pak_path, entry = entry_info
            dest_file = self._temp_extracted_dir / clean_rel
            if dest_file.is_file():
                return dest_file

            data = self.catalog.extract_file(entry.name)
            if data:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                dest_file.write_bytes(data)
                return dest_file

        return None

    def get_texture_image(self, rel_path: str) -> Optional[bpy.types.Image]:
        """Loads or returns a cached bpy.types.Image for the given relative texture path."""
        if not rel_path:
            return None

        clean_key = rel_path.lower().replace("\\", "/").strip().lstrip("/")
        cached = self._image_cache.get(clean_key)
        if cached and cached.name in bpy.data.images:
            return cached

        file_path = self.resolve_texture_file(rel_path)
        if not file_path or not file_path.is_file():
            return None

        try:
            img_name = Path(clean_key).name
            img = bpy.data.images.load(str(file_path), check_existing=True)
            img.name = img_name
            self._image_cache[clean_key] = img
            return img
        except Exception:
            return None

    def cleanup(self) -> None:
        import shutil
        shutil.rmtree(self._temp_extracted_dir, ignore_errors=True)
