"""
Aion Water and Liquid Animation System.
Applies animated ripple displacement, wave motion, and UV flow drivers.
"""

from __future__ import annotations

from typing import Optional
import bpy


def apply_water_wave_animation(
    water_object: bpy.types.Object,
    *,
    wave_height: float = 0.35,
    wave_speed: float = 0.05,
) -> Optional[bpy.types.Modifier]:
    """
    Applies live wave displacement to the water mesh using Blender's procedural wave modifier.
    Returns the created or existing modifier, or None on failure.
    """
    if water_object is None or water_object.type != "MESH":
        return None

    if "Aion_WaterWaves" in water_object.modifiers:
        return water_object.modifiers["Aion_WaterWaves"]

    try:
        mod = water_object.modifiers.new("Aion_WaterWaves", type="WAVE")
        mod.use_x = True
        mod.use_y = True
        mod.height = wave_height
        mod.width = 25.0
        mod.speed = wave_speed
        mod.narrowness = 2.5
        return mod
    except Exception:
        return None
