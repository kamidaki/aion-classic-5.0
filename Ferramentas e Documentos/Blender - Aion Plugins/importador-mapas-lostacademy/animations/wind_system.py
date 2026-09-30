"""
Aion Vegetation Wind Sway — Static Deform System.

DESIGN DECISION:
    Python expression drivers (sin(frame * ...)) were the root cause of the Blender
    PLAY/SPACE freeze. Blender evaluates every Python driver on every object on every
    frame in the main thread. With 500+ vegetation instances this blocks the UI completely.

    This module now uses ONLY static SIMPLE_DEFORM modifiers with a fixed angle.
    No drivers. No keyframes per object. No per-frame Python evaluation.
    Wind "visual effect" is achieved purely by the geometry deformation — static but
    believable for a viewport preview. For animated wind, users can manually add a
    single NLA action on the 'Aion_Wind_Controller' empty if desired.
"""

from __future__ import annotations

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


def clean_python_wind_drivers(scene=None) -> int:
    """
    Removes any Python expression drivers matching the wind pattern from ALL objects.
    Call this once on existing scenes that were imported with the old driver system.
    Returns the number of drivers removed.
    """
    removed = 0
    target_objects = list(bpy.data.objects) if scene is None else list(scene.objects)
    for obj in target_objects:
        if not obj.animation_data or not obj.animation_data.drivers:
            continue
        to_remove = []
        for drv in obj.animation_data.drivers:
            expr = drv.driver.expression if drv.driver else ""
            if "sin(frame" in expr or "Aion_Wind" in (drv.data_path or ""):
                to_remove.append(drv)
        for drv in to_remove:
            try:
                obj.animation_data.drivers.remove(drv)
                removed += 1
            except Exception:
                pass
        # Also clean up empty animation_data to prevent depsgraph overhead
        try:
            if obj.animation_data and not obj.animation_data.action and not obj.animation_data.drivers:
                obj.animation_data_clear()
        except Exception:
            pass
    return removed


def apply_vegetation_wind_sway(
    target: Union[bpy.types.Collection, bpy.types.Object],
    model_reference: str = "vegetation",
    *,
    wind_strength: float = 0.05,
    wind_speed: float = 0.045,  # Kept for API compatibility, unused
) -> Union[Optional[bpy.types.Modifier], int]:
    """
    Applies a static SIMPLE_DEFORM BEND modifier to vegetation meshes.

    NO Python drivers. NO per-object keyframes. NO per-frame evaluation.
    This guarantees zero overhead during PLAY/SPACE timeline playback.

    The static bend angle gives a subtle natural lean that serves as a
    viewport wind preview without any runtime cost.
    """
    if not is_vegetation_reference(model_reference) or target is None:
        return 0

    if isinstance(target, bpy.types.Object):
        objs = [target]
    else:
        objs = [o for o in target.all_objects if o.type == "MESH"]

    applied_mod = None
    applied_count = 0

    for obj in objs:
        if obj.type != "MESH":
            continue

        # Skip if already applied
        if "Aion_Wind" in obj.modifiers:
            continue

        try:
            mod = obj.modifiers.new("Aion_Wind", type="SIMPLE_DEFORM")
            mod.deform_method = "BEND"
            mod.deform_axis = "X"
            mod.angle = wind_strength  # Static angle — no driver, no keyframe

            # Limit to upper canopy so base/roots stay anchored
            try:
                mod.limits[0] = 0.2
                mod.limits[1] = 1.0
            except Exception:
                pass

            # IMPORTANT: Do NOT call driver_add() or keyframe_insert() here.
            # Any Python driver or keyframe causes per-frame main-thread evaluation.

            applied_count += 1
            applied_mod = mod
        except Exception:
            pass

    if isinstance(target, bpy.types.Object):
        return applied_mod
    return applied_count
