"""
DDS Texture Loader and Color Space Manager for Blender.
Provides high-performance O(1) texture deduplication and persistent GPU memory caching.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

import bpy


# Map normalized filepath to image datablock name (string, never raw bpy.types.Image RNA pointer)
_IMAGE_CACHE: Dict[str, str] = {}


def load_texture_image(
    filepath: str | Path,
    *,
    colorspace: str = "sRGB",
    check_existing: bool = True,
) -> Optional[bpy.types.Image]:
    """
    Loads an image from disk and sets its colorspace.
    colorspace can be 'sRGB' or 'Non-Color'.
    Guaranteed safe against StructRNA removal errors across multiple imports.
    Protects loaded images with use_fake_user to prevent viewport streaming drops.
    """
    path_str = str(filepath).strip()
    if not path_str or not os.path.isfile(path_str):
        return None

    norm_path = os.path.normcase(os.path.abspath(path_str))

    # 1. Fast O(1) internal cache lookup
    if check_existing and norm_path in _IMAGE_CACHE:
        img_name = _IMAGE_CACHE[norm_path]
        try:
            img = bpy.data.images.get(img_name)
            if img is not None:
                if img.filepath:
                    existing_path = os.path.normcase(os.path.abspath(bpy.path.abspath(img.filepath)))
                    if existing_path == norm_path:
                        return img
                else:
                    return img
        except (ReferenceError, Exception):
            _IMAGE_CACHE.pop(norm_path, None)

    # 2. Load from disk via Blender API (native check_existing=True is C-accelerated)
    try:
        image = bpy.data.images.load(norm_path, check_existing=check_existing)
    except Exception:
        return None

    if image is None:
        return None

    # Configure color space
    try:
        if colorspace == "Non-Color":
            image.colorspace_settings.name = "Non-Color"
        else:
            image.colorspace_settings.name = "sRGB"
    except Exception:
        pass

    try:
        _IMAGE_CACHE[norm_path] = image.name
    except (ReferenceError, Exception):
        pass

    return image


def clear_texture_cache() -> None:
    _IMAGE_CACHE.clear()


def purge_orphan_datablocks() -> None:
    """Purges unreferenced images and materials from Blender's memory."""
    try:
        # Purge unused images that have no users
        for img in list(bpy.data.images):
            try:
                if img.users == 0 and not img.use_fake_user:
                    bpy.data.images.remove(img)
            except Exception:
                pass
        # Purge unused materials
        for mat in list(bpy.data.materials):
            try:
                if mat.users == 0 and not mat.use_fake_user:
                    bpy.data.materials.remove(mat)
            except Exception:
                pass
    except Exception:
        pass


clear_cache = clear_texture_cache


_PAK_IMAGE_CACHE: Dict[str, str] = {}


def load_texture_from_pak_bytes(
    cache_key: str,
    dds_bytes: bytes,
    *,
    colorspace: str = "sRGB",
    name_hint: str = "AionTex",
) -> Optional[bpy.types.Image]:
    """
    Loads a texture from raw DDS bytes extracted from a PAK archive.
    Uses Blender's packed image API to avoid temp file I/O.
    cache_key: unique identifier for this texture (e.g. normalized PAK path)
    """
    if not dds_bytes:
        return None

    norm_key = cache_key.lower().replace("\\", "/")

    # Check in-memory cache first
    if norm_key in _PAK_IMAGE_CACHE:
        img_name = _PAK_IMAGE_CACHE[norm_key]
        try:
            img = bpy.data.images.get(img_name)
            if img is not None:
                return img
        except (ReferenceError, Exception):
            _PAK_IMAGE_CACHE.pop(norm_key, None)

    try:
        import tempfile
        ext = Path(cache_key).suffix or ".dds"
        safe_stem = Path(cache_key).stem[:40].replace("/", "_").replace("\\", "_")
        fname = f"aion_tex_{safe_stem}{ext}"
        tmp_dir = Path(tempfile.gettempdir()) / "aion_blender_textures"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / fname

        if not tmp_path.is_file():
            tmp_path.write_bytes(dds_bytes)

        image = bpy.data.images.load(str(tmp_path), check_existing=True)
        if image is None:
            return None

        # Configure color space
        try:
            if colorspace == "Non-Color":
                image.colorspace_settings.name = "Non-Color"
            else:
                image.colorspace_settings.name = "sRGB"
        except Exception:
            pass

        _PAK_IMAGE_CACHE[norm_key] = image.name
        # Also register in main cache by disk path
        norm_disk = os.path.normcase(os.path.abspath(str(tmp_path)))
        _IMAGE_CACHE[norm_disk] = image.name
        return image
    except Exception:
        return None

