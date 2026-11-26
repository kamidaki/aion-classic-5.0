"""
Export and Direct-Save Operators for Aion Blender Toolkit.
"""

from __future__ import annotations

from pathlib import Path
import bpy
from bpy.props import BoolProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from exporters.level_exporter import export_and_save_level


class AION_OT_direct_save(bpy.types.Operator):
    """Save all scene edits directly back into Aion level files and Level.pak archive."""

    bl_idname = "aion.direct_save"
    bl_label = "Direct Save Map"
    bl_description = "Serialize all scene changes (brushes, vegetation, terrain, placeables) and repack Level.pak ready for the game client"
    bl_options = {"REGISTER", "UNDO"}

    create_backup: BoolProperty(
        name="Create Backup (.pak.bak)",
        description="Keep a safe backup of the original Level.pak before replacing it",
        default=True,
    )

    def execute(self, context):
        settings = getattr(context.scene, "aion_settings", None)
        loaded_dir = getattr(settings, "loaded_level_dir", "") if settings else ""

        if not loaded_dir or not Path(loaded_dir).is_dir():
            # If not tracked, try looking at level_path
            alt_path = getattr(settings, "level_path", "") if settings else ""
            if alt_path and Path(alt_path).exists():
                loaded_dir = str(Path(alt_path).parent if Path(alt_path).is_file() else Path(alt_path))
            else:
                self.report(
                    {"ERROR"},
                    "No active Aion level loaded. Please import a level first or use 'Export Level' to choose a directory.",
                )
                return {"CANCELLED"}

        level_path = Path(loaded_dir).resolve()
        self.report({"INFO"}, f"Direct saving level at '{level_path}'...")

        result = export_and_save_level(
            context.scene,
            level_path,
            create_backup=self.create_backup,
            repack_pak=True,
        )

        if result.success:
            if settings:
                settings.status_message = result.message
            self.report({"INFO"}, result.message)
            return {"FINISHED"}
        else:
            if settings:
                settings.status_message = f"Error: {result.message}"
            self.report({"ERROR"}, f"Direct save failed: {result.message}")
            return {"CANCELLED"}


class AION_OT_export_level(bpy.types.Operator):
    """Serialize scene edits and repack an Aion Level folder or Level.pak."""

    bl_idname = "export_scene.aion_level"
    bl_label = "Export Aion Level"
    bl_description = "Serialize scene edits and repack into Level.pak with automatic backup"
    bl_options = {"REGISTER", "UNDO"}

    directory: StringProperty(
        name="Level Directory",
        description="Select the level folder (e.g. levels/dc1 or Level.pak)",
        subtype="DIR_PATH",
    )

    create_backup: BoolProperty(
        name="Create Backup (.pak.bak)",
        description="Keep a safe backup of the original Level.pak before replacing it",
        default=True,
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.directory:
            self.report({"ERROR"}, "No level directory selected.")
            return {"CANCELLED"}

        level_path = Path(self.directory).resolve()
        if level_path.is_file():
            level_path = level_path.parent

        result = export_and_save_level(
            context.scene,
            level_path,
            create_backup=self.create_backup,
            repack_pak=True,
        )

        if result.success:
            self.report({"INFO"}, result.message)
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, f"Export failed: {result.message}")
            return {"CANCELLED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "create_backup")


# Backwards compatibility alias for older menus/scripts
class AION_OT_repack_level(AION_OT_export_level):
    bl_idname = "export_scene.aion_level_pak"
    bl_label = "Export / Repack Aion Level (.pak)"
