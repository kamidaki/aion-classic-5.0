"""
Editing and Environment Operators for Aion Blender Toolkit.
"""

from __future__ import annotations

from pathlib import Path
import bpy
from bpy.props import BoolProperty, FloatProperty

from editing.object_editor import randomize_object_transforms, snap_objects_to_terrain
from editing.terrain_editor import find_terrain_object, sync_sculpted_terrain_to_land_map


class AION_OT_snap_to_terrain(bpy.types.Operator):
    """Snap selected objects down to the surface of the Aion terrain mesh."""

    bl_idname = "aion.snap_to_terrain"
    bl_label = "Snap to Terrain"
    bl_description = "Raycast selected objects down onto the underlying terrain heightfield"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        terrain_obj = find_terrain_object(context.scene)
        if not terrain_obj:
            self.report({"ERROR"}, "No terrain mesh found in scene.")
            return {"CANCELLED"}

        snapped = snap_objects_to_terrain(context.selected_objects, terrain_obj)
        self.report({"INFO"}, f"Snapped {snapped} objects onto terrain.")
        return {"FINISHED"}


class AION_OT_randomize_transforms(bpy.types.Operator):
    """Randomize rotation and scale of selected vegetation/decorations for natural scattering."""

    bl_idname = "aion.randomize_transforms"
    bl_label = "Randomize Jitter"
    bl_description = "Apply random yaw rotation and subtle scale variation to selected objects"
    bl_options = {"REGISTER", "UNDO"}

    min_scale: FloatProperty(
        name="Min Scale",
        description="Minimum scale multiplier",
        default=0.85,
        min=0.1,
        max=2.0,
    )

    max_scale: FloatProperty(
        name="Max Scale",
        description="Maximum scale multiplier",
        default=1.15,
        min=0.1,
        max=3.0,
    )

    random_yaw: BoolProperty(
        name="Random Yaw (Z-axis)",
        description="Apply full random 360-degree rotation around Z",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        count = randomize_object_transforms(
            context.selected_objects,
            min_scale=self.min_scale,
            max_scale=self.max_scale,
            random_yaw=self.random_yaw,
        )
        self.report({"INFO"}, f"Randomized transforms for {count} objects.")
        return {"FINISHED"}


class AION_OT_sync_terrain(bpy.types.Operator):
    """Synchronize sculpted terrain mesh elevations into the active level's land_map.h32."""

    bl_idname = "aion.sync_terrain"
    bl_label = "Sync Sculpted Terrain"
    bl_description = "Write vertex elevations from the sculpted Blender terrain mesh back into land_map.h32"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        terrain_obj = find_terrain_object(context.scene)
        if not terrain_obj:
            self.report({"ERROR"}, "No terrain mesh found in scene.")
            return {"CANCELLED"}

        settings = getattr(context.scene, "aion_settings", None)
        loaded_dir = getattr(settings, "loaded_level_dir", "") if settings else ""
        if not loaded_dir or not Path(loaded_dir).is_dir():
            self.report({"ERROR"}, "No active level directory known. Please load a level first.")
            return {"CANCELLED"}

        level_path = Path(loaded_dir)
        h32_path = level_path / "terrain" / "land_map.h32"
        if not h32_path.is_file():
            cache_h32 = level_path / ".aion_cache" / "terrain" / "land_map.h32"
            if cache_h32.is_file():
                h32_path = cache_h32

        if not h32_path.is_file():
            self.report({"ERROR"}, f"land_map.h32 not found in {level_path}")
            return {"CANCELLED"}

        try:
            modified_count, total = sync_sculpted_terrain_to_land_map(
                terrain_obj,
                h32_path,
                h32_path,
            )
            msg = f"Synced terrain: {modified_count} samples updated in land_map.h32 (Total: {total})."
            self.report({"INFO"}, msg)
            if settings:
                settings.status_message = msg
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to sync terrain: {exc}")
            return {"CANCELLED"}


class AION_OT_toggle_animation(bpy.types.Operator):
    """Play or Pause live environmental animations (water ripples, wind sway, UV scrolling)."""

    bl_idname = "aion.toggle_animation"
    bl_label = "Play / Pause Live Environment"
    bl_description = "Toggle live playback of environmental animations in the viewport"
    bl_options = {"REGISTER"}

    def execute(self, context):
        wm = context.window_manager
        screen = context.screen
        if screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
            self.report({"INFO"}, "Animation paused.")
        else:
            bpy.ops.screen.animation_play()
            self.report({"INFO"}, "Animation playing (Space to pause).")
        return {"FINISHED"}


class AION_OT_toggle_npc_names(bpy.types.Operator):
    """Toggle visibility of 3D floating NPC Nameplates in the 3D Viewport."""

    bl_idname = "aion.toggle_npc_names"
    bl_label = "Toggle NPC Nameplates"
    bl_description = "Show or hide 3D billboard nameplates for all world NPCs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        names_col = bpy.data.collections.get("NPC_NAMES")
        if not names_col:
            npcs_col = bpy.data.collections.get("NPCS")
            if npcs_col:
                names_col = npcs_col.children.get("NPC_NAMES")

        if not names_col:
            self.report({"WARNING"}, "No NPC_NAMES collection found in scene.")
            return {"CANCELLED"}

        new_state = not names_col.hide_viewport
        names_col.hide_viewport = new_state
        state_str = "Hidden" if new_state else "Visible"
        self.report({"INFO"}, f"NPC Nameplates: {state_str}")
        return {"FINISHED"}
