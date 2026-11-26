"""
Configuration and default settings for the Aion Blender Toolkit.
"""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_CLIENT_ROOT = os.environ.get("AION_CLIENT_ROOT", "")
DEFAULT_CACHE_DIR_NAME = ".aion_cache"
BACKUP_EXTENSION = ".pak.bak"

# Supported Blender versions
SUPPORTED_BLENDER_VERSIONS = ((4, 0, 0), (5, 2, 0))

# Level format constants
DEFAULT_XY_SCALE = 2.0
LAND_MAP_HEIGHT_SCALE = 32
LAND_MAP_BYTES_PER_SAMPLE = 3

# UI Constants
SIDEBAR_CATEGORY = "Aion Map"
TOPBAR_IMPORT_TEXT = "Aion Level (Folder or Level.pak)"
TOPBAR_EXPORT_TEXT = "Aion Level (.pak)"

# Animation defaults
DEFAULT_TEXTURE_ANIMATION_FPS = 10
DEFAULT_WIND_STRENGTH = 0.05
DEFAULT_WIND_SPEED = 0.045
DEFAULT_WATER_FLOW_SPEED = 0.003


def get_default_client_root() -> str:
    """Returns the default Aion client root directory if configured and existing."""
    if DEFAULT_CLIENT_ROOT and os.path.isdir(DEFAULT_CLIENT_ROOT):
        return DEFAULT_CLIENT_ROOT
    return ""
