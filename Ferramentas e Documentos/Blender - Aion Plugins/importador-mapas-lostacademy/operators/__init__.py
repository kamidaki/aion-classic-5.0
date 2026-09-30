"""
Blender operators for the Aion importer and editor toolkit.
"""

from __future__ import annotations

import bpy

from .cleanup_operators import (
    AION_OT_clean_wind_drivers,
    AION_OT_purge_unused_data,
)
from .editing_operators import (
    AION_OT_randomize_transforms,
    AION_OT_snap_to_terrain,
    AION_OT_sync_terrain,
    AION_OT_toggle_animation,
)
from .export_level import (
    AION_OT_direct_save,
    AION_OT_export_level,
    AION_OT_repack_level,
)
from .import_cgf import AION_OT_import_cgf
from .import_level import AION_OT_import_level_folder

CLASSES = (
    AION_OT_import_cgf,
    AION_OT_import_level_folder,
    AION_OT_export_level,
    AION_OT_repack_level,
    AION_OT_direct_save,
    AION_OT_snap_to_terrain,
    AION_OT_randomize_transforms,
    AION_OT_sync_terrain,
    AION_OT_toggle_animation,
    AION_OT_clean_wind_drivers,
    AION_OT_purge_unused_data,
)


def register():
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass


def unregister():
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
