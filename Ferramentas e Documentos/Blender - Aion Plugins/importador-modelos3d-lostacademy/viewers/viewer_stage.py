"""
Dedicated 3D Viewer Staging Environment for LostAcademy Aion Model Library.
Creates a professional staging collection with studio 3-point lighting and automated camera framing.
"""

from __future__ import annotations
from typing import Optional, Tuple

import bpy
from mathutils import Vector

VIEWER_COLLECTION_NAME = "Aion_Model_Viewer"
STAGE_LIGHTS_COLLECTION_NAME = ".Viewer_Studio_Lights"


class ViewerStage:
    """Manages the isolated 3D Viewport inspection stage."""

    @staticmethod
    def get_or_create_stage_collection() -> bpy.types.Collection:
        """Returns or creates the dedicated viewer collection in the active scene."""
        scene = bpy.context.scene
        for c in scene.collection.children:
            if c.name == VIEWER_COLLECTION_NAME:
                return c

        col = bpy.data.collections.new(VIEWER_COLLECTION_NAME)
        scene.collection.children.link(col)
        return col

    @staticmethod
    def clear_stage_objects() -> None:
        """Removes previously inspected model objects from the viewer stage."""
        col = ViewerStage.get_or_create_stage_collection()
        for obj in list(col.objects):
            # Do not delete lights or cameras
            if obj.type not in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(obj, do_unlink=True)

    @classmethod
    def setup_studio_lighting(cls) -> None:
        """Sets up neutral 3-point studio lighting for optimal Material Preview."""
        scene = bpy.context.scene
        # Find or create lights collection
        lights_col = None
        for c in scene.collection.children:
            if c.name == STAGE_LIGHTS_COLLECTION_NAME:
                lights_col = c
                break

        if not lights_col:
            lights_col = bpy.data.collections.new(STAGE_LIGHTS_COLLECTION_NAME)
            scene.collection.children.link(lights_col)

        # Clear existing stage lights
        for o in list(lights_col.objects):
            bpy.data.objects.remove(o, do_unlink=True)

        # 1. Key Light (Sun / Warm)
        key_data = bpy.data.lights.new(name="Aion_Key_Light", type="SUN")
        key_data.energy = 2.5
        key_data.color = (1.0, 0.98, 0.95)
        key_obj = bpy.data.objects.new("Aion_Key_Light", key_data)
        key_obj.location = (5.0, -5.0, 8.0)
        key_obj.rotation_euler = (0.785, 0.35, 0.61)  # Angled down
        lights_col.objects.link(key_obj)

        # 2. Fill Light (Area / Cool)
        fill_data = bpy.data.lights.new(name="Aion_Fill_Light", type="SUN")
        fill_data.energy = 1.0
        fill_data.color = (0.9, 0.95, 1.0)
        fill_obj = bpy.data.objects.new("Aion_Fill_Light", fill_data)
        fill_obj.location = (-5.0, 5.0, 4.0)
        fill_obj.rotation_euler = (-0.5, -0.3, -2.2)
        lights_col.objects.link(fill_obj)

        # 3. Rim Light (Sun / Neutral)
        rim_data = bpy.data.lights.new(name="Aion_Rim_Light", type="SUN")
        rim_data.energy = 1.5
        rim_data.color = (1.0, 1.0, 1.0)
        rim_obj = bpy.data.objects.new("Aion_Rim_Light", rim_data)
        rim_obj.location = (0.0, 6.0, 5.0)
        rim_obj.rotation_euler = (-1.0, 0.0, 3.1415)
        lights_col.objects.link(rim_obj)

    @classmethod
    def frame_object(cls, target_obj: bpy.types.Object) -> None:
        """Centers view and frames camera on the loaded asset."""
        if not target_obj:
            return

        # Select target object
        bpy.ops.object.select_all(action="DESELECT")
        target_obj.select_set(True)
        bpy.context.view_layer.objects.active = target_obj

        # Frame in all 3D viewports
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                    win_regions = [r for r in area.regions if r.type == "WINDOW"]
                    if not win_regions:
                        continue
                    ctx = {
                        "window": window,
                        "screen": window.screen,
                        "area": area,
                        "region": win_regions[0],
                        "active_object": target_obj,
                        "selected_objects": [target_obj],
                    }
                    try:
                        with bpy.context.temp_override(**ctx):
                            bpy.ops.view3d.view_selected()
                    except Exception:
                        pass
