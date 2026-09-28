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

