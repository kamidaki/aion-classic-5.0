"""
Blender operators for the Aion importer and editor toolkit.
"""

from __future__ import annotations

import bpy

from .cleanup_operators import (
    AION_OT_clean_wind_drivers,
    AION_OT_optimize_viewport_60fps,
    AION_OT_purge_unused_data,
)
from .editing_operators import (
    AION_OT_catalog_assets,
    AION_OT_open_asset_browser,
    AION_OT_randomize_transforms,
    AION_OT_refresh_client_assets,
    AION_OT_refresh_client_diagnostics,
    AION_OT_select_asset_in_scene,
    AION_OT_snap_to_terrain,
    AION_OT_spawn_asset,
    AION_OT_spawn_client_model,
    AION_OT_sync_terrain,
    AION_OT_toggle_animation,
    AION_OT_toggle_npc_names,
)
from .export_level import (
    AION_OT_direct_save,
    AION_OT_export_level,
    AION_OT_repack_level,
)
from .import_cgf import AION_OT_import_cgf
from .import_level import (
    AION_OT_cancel_level_import,
    AION_OT_import_level_folder,
    register_handlers,
    unregister_handlers,
)

CLASSES = (
    AION_OT_import_cgf,
    AION_OT_import_level_folder,
    AION_OT_cancel_level_import,
    AION_OT_export_level,
    AION_OT_repack_level,
    AION_OT_direct_save,
    AION_OT_snap_to_terrain,
    AION_OT_randomize_transforms,
    AION_OT_sync_terrain,
    AION_OT_toggle_animation,
    AION_OT_toggle_npc_names,
    AION_OT_clean_wind_drivers,
    AION_OT_optimize_viewport_60fps,
    AION_OT_purge_unused_data,
    AION_OT_open_asset_browser,
    AION_OT_catalog_assets,
    AION_OT_refresh_client_assets,
    AION_OT_refresh_client_diagnostics,
    AION_OT_spawn_asset,
    AION_OT_spawn_client_model,
    AION_OT_select_asset_in_scene,
)


def register():
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass
    register_handlers()


def unregister():
    unregister_handlers()
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
