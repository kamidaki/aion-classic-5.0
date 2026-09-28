"""
Display & Shading Modes Manager.
Toggles shading (Wireframe, Solid, Material, Rendered) and overlays (Bones, In Front, Wireframe, Normals).
"""

from __future__ import annotations
from typing import Optional
import bpy


def set_shading_mode(mode: str = "MATERIAL") -> None:
    """Sets the 3D viewport shading method across active 3D views."""
    shading_type = mode.upper()
    if shading_type == "MATERIAL":
        shading_type = "MATERIAL"
    elif shading_type not in ("WIREFRAME", "SOLID", "MATERIAL", "RENDERED"):
        shading_type = "SOLID"

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = shading_type


def set_bones_display(
    arm_obj: Optional[bpy.types.Object],
    show_bones: bool = True,
    show_names: bool = False,
    in_front: bool = True,
) -> None:
    """Configures skeletal display properties on an Armature object."""
    if not arm_obj or arm_obj.type != "ARMATURE":
        return

    arm_data: bpy.types.Armature = arm_obj.data
    arm_obj.show_in_front = in_front
    arm_obj.hide_viewport = not show_bones
    arm_data.show_names = show_names

    # Set display type to Octahedral or Wire
    arm_data.display_type = "OCTAHEDRAL"


def toggle_wireframe_overlay(enable: bool = True) -> None:
    """Toggles wireframe mesh overlay on 3D viewports."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.overlay.show_wireframes = enable
