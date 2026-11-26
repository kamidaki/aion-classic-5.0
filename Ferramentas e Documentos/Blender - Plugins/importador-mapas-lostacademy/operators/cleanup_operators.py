"""
Cleanup and Scene Optimization Operators for Aion Blender Toolkit.
Purges leftover Python drivers and unused datablocks to restore 100% responsiveness.
"""

from __future__ import annotations

import bpy
from config.performance_profiles import apply_viewport_60fps_optimization
from animations.wind_system import clean_python_wind_drivers
from materials.texture_loader import purge_orphan_datablocks


class AION_OT_optimize_viewport_60fps(bpy.types.Operator):
    """Apply aggressive Eevee & 3D viewport tuning for 60+ FPS on weak GPUs."""

    bl_idname = "aion.optimize_viewport_60fps"
    bl_label = "Otimizar Viewport (60+ FPS)"
    bl_description = "Configura Eevee, sombras, simplificação e clip da cena atual para rodar leve em PCs e GPUs fracas"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = getattr(context.scene, "aion_settings", None)
        profile = getattr(settings, "performance_profile", "LOW") if settings else "LOW"
        result = apply_viewport_60fps_optimization(context, profile)
        self.report(
            {"INFO"},
            f"Viewport otimizada (Perfil={result['profile']}, TAA={result.get('taa_samples', 1)}, Sombras={'ON' if result.get('eevee_shadows') else 'OFF'}).",
        )
        return {"FINISHED"}


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
