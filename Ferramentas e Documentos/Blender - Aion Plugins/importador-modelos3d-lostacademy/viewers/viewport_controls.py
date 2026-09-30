"""
Viewport Camera Navigation and Preset Controls.
Provides fast perspective changes (Front, Side, Top, Ortho/Persp, Focus, Reset).
"""

from __future__ import annotations
import bpy


def view_preset_axis(axis: str = "FRONT") -> None:
    """Sets the 3D viewport camera to standard orthographic/perspective projection axes."""
    axis_map = {
        "FRONT": "FRONT",
        "BACK": "BACK",
        "LEFT": "LEFT",
        "RIGHT": "RIGHT",
        "TOP": "TOP",
        "BOTTOM": "BOTTOM",
    }
    view_type = axis_map.get(axis.upper(), "FRONT")

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                for region in area.regions:
                    if region.type == "WINDOW":
                        ctx = {
                            "window": window,
                            "screen": window.screen,
                            "area": area,
                            "region": region,
                        }
                        try:
                            with bpy.context.temp_override(**ctx):
                                bpy.ops.view3d.view_axis(type=view_type)
                        except Exception:
                            pass


def toggle_persp_ortho() -> None:
    """Toggles 3D viewport between perspective and orthographic projection."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                for region in area.regions:
                    if region.type == "WINDOW":
                        ctx = {
                            "window": window,
                            "screen": window.screen,
                            "area": area,
                            "region": region,
                        }
                        try:
                            with bpy.context.temp_override(**ctx):
                                bpy.ops.view3d.view_persportho()
                        except Exception:
                            pass


def reset_view() -> None:
    """Resets the 3D Viewport camera to default 3/4 perspective view."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                if space and space.type == "VIEW_3D":
                    space.region_3d.view_perspective = "PERSP"
                    space.region_3d.view_distance = 3.5
                    space.region_3d.view_location = (0.0, 0.0, 1.0)
                    space.region_3d.view_rotation = (0.785, 0.35, 0.0, 0.5)
