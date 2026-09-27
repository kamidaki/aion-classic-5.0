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
        """Removes previously inspected model objects and orphan data to completely eliminate duplicate meshes and flickering."""
        col = ViewerStage.get_or_create_stage_collection()
        to_delete = set()

        for obj in list(col.objects):
            if obj.type not in ("LIGHT", "CAMERA"):
                to_delete.add(obj)
                for child in getattr(obj, "children_recursive", []):
                    to_delete.add(child)

        # Also search active scene for any lingering Aion preview objects or rigs
        scene = bpy.context.scene
        for obj in list(scene.objects):
            if obj.type not in ("LIGHT", "CAMERA") and obj.name.startswith(("Aion_", "mannequin_", "auto_")):
                to_delete.add(obj)

        for obj in to_delete:
            try:
                # Clear animation action
                if obj.animation_data and obj.animation_data.action:
                    act = obj.animation_data.action
                    obj.animation_data.action = None
                    if act.users == 0:
                        bpy.data.actions.remove(act)

                # Unlink from all collections
                for c in list(obj.users_collection):
                    c.objects.unlink(obj)

                m_data = obj.data if obj.type == "MESH" else None
                a_data = obj.data if obj.type == "ARMATURE" else None

                bpy.data.objects.remove(obj, do_unlink=True)

                if m_data and m_data.users == 0:
                    bpy.data.meshes.remove(m_data)
                if a_data and a_data.users == 0:
                    bpy.data.armatures.remove(a_data)
            except Exception:
                pass

        try:
            bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        except Exception:
            pass

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
