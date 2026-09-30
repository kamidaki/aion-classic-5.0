"""
Shader UV Scroll Animation System for Blender.
Animates texture mapping nodes using CryEngine TexShift speed parameters.
"""

from __future__ import annotations

from typing import Optional

import bpy


def animate_mapping_location(
    mapping_node: bpy.types.Node,
    speed_x: float,
    speed_y: float,
    fps: int = 10,
    *,
    base_x: float = 0.0,
    base_y: float = 0.0,
) -> bool:
    """Adds scripted drivers to a Mapping node's Location inputs for continuous UV scrolling."""
    if mapping_node is None:
        return False

    try:
        if speed_x != 0.0:
            drv_x = mapping_node.inputs["Location"].driver_add("default_value", 0)
            drv_x.driver.type = "SCRIPTED"
            drv_x.driver.expression = f"{base_x:.6f} + (frame / {fps}) * {speed_x:.6f}"

        if speed_y != 0.0:
            drv_y = mapping_node.inputs["Location"].driver_add("default_value", 1)
            drv_y.driver.type = "SCRIPTED"
            drv_y.driver.expression = f"{base_y:.6f} + (frame / {fps}) * {speed_y:.6f}"

        return True
    except Exception:
        return False
