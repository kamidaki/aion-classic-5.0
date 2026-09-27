"""
Aion Vegetation Wind Sway and Environmental Wind System.
Animates trees, foliage, plants, and leaves when playing the timeline in Blender.
"""

from __future__ import annotations

import zlib
from typing import Optional, Union

import bpy

VEGETATION_KEYWORDS = (
    "tree", "plant", "greens", "grass", "flower", "leaf", "bush",
    "fern", "vine", "weed", "branch", "stem", "foliage", "kelp",
    "vegetation",
)


def is_vegetation_reference(ref_path: str) -> bool:
    clean = ref_path.lower()
    return any(k in clean for k in VEGETATION_KEYWORDS)


def apply_vegetation_wind_sway(
    target: Union[bpy.types.Collection, bpy.types.Object],
    model_reference: str = "vegetation",
    *,
    wind_strength: float = 0.05,
    wind_speed: float = 0.045,
) -> Optional[bpy.types.Modifier] | int:
    """
    Applies natural harmonic wind sway drivers to foliage meshes in the template collection or single object.
    Roots/bases stay grounded while upper canopies sway gracefully.
    """
    if not is_vegetation_reference(model_reference) or target is None:
        return 0

    seed = (zlib.crc32(model_reference.encode("utf-8")) % 1000) / 100.0

    if isinstance(target, bpy.types.Object):
        objs = [target]
    else:
        objs = [o for o in target.all_objects if o.type == "MESH"]

    applied_mod = None
    applied_count = 0

    for obj in objs:
        if obj.type != "MESH":
            continue

        # Check if already applied
        if "Aion_Wind" in obj.modifiers:
            continue

        try:
            # Simple Deform BEND modifier
            mod = obj.modifiers.new("Aion_Wind", type="SIMPLE_DEFORM")
            mod.deform_method = "BEND"
            mod.deform_axis = "X"

            # Limit deformation to upper portion (leaves/branches) so trunk base remains anchored
            try:
                mod.origin = obj
                mod.limits[0] = 0.2
                mod.limits[1] = 1.0
            except Exception:
                pass

            drv = mod.driver_add("angle")
            drv.driver.type = "SCRIPTED"
            # Dual-sine harmonic expression with unique phase seed
            drv.driver.expression = (
                f"sin(frame * {wind_speed:.4f} + {seed:.2f}) * {wind_strength:.4f} + "
                f"sin(frame * {wind_speed * 0.45:.4f} + {seed:.2f}) * {wind_strength * 0.35:.4f}"
            )
            applied_count += 1
            applied_mod = mod
        except Exception:
            pass

    if isinstance(target, bpy.types.Object):
        return applied_mod
    return applied_count
