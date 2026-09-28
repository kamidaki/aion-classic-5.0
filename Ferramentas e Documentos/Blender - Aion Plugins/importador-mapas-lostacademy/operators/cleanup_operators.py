"""
Cleanup and Scene Optimization Operators for Aion Blender Toolkit.
Purges leftover Python drivers and unused datablocks to restore 100% responsiveness.
"""

from __future__ import annotations

import bpy
from animations.wind_system import clean_python_wind_drivers
from materials.texture_loader import purge_orphan_datablocks


class AION_OT_clean_wind_drivers(bpy.types.Operator):
    """Purge legacy Python expression drivers that lock the viewport during animation playback."""

    bl_idname = "aion.clean_wind_drivers"
    bl_label = "Clean Wind Drivers (Fix Freeze)"
    bl_description = "Removes any legacy per-object Python drivers that cause Blender to freeze during PLAY"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        removed = clean_python_wind_drivers(context.scene)
        purge_orphan_datablocks()
        self.report({"INFO"}, f"Cleaned {removed} Python drivers. Viewport responsiveness restored.")
        return {"FINISHED"}


class AION_OT_purge_unused_data(bpy.types.Operator):
    """Purge unreferenced images, materials, and meshes to free RAM and eliminate lag."""

    bl_idname = "aion.purge_unused_data"
    bl_label = "Purge Unused Data (Free RAM)"
    bl_description = "Purges unreferenced textures, materials, and mesh buffers from Blender memory"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from materials.material_manager import clean_material_cache
        from materials.texture_loader import clear_texture_cache

        clean_material_cache()
        clear_texture_cache()
        purge_orphan_datablocks()

        # Blender native purge operator if available
        try:
            bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        except Exception:
            pass

        self.report({"INFO"}, "Purged unused datablocks from memory.")
        return {"FINISHED"}
