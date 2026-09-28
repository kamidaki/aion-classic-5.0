"""
Aion CGA Entity Animation Controller.
Decodes rotation and translation controller keyframes for animated world entities.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import bpy
from mathutils import Matrix, Quaternion, Vector


def apply_cga_controller_animation(
    obj: bpy.types.Object,
    node: Dict[str, Any],
    cgf_file: Dict[str, Any],
    *,
    enabled: bool = True,
) -> int:
    """Decodes CGA controller keyframes and applies them as Blender rotation keyframes."""
    if not enabled or not isinstance(cgf_file, dict):
        return 0

    rot_ctrl_id = node.get("rot_ctrl_id")
    if rot_ctrl_id in (None, 0xFFFFFFFF):
        return 0

    parent_id = node.get("parent_id")
    if parent_id not in (None, -1, 0xFFFFFFFF):
        return 0

    controllers = _decoded_controllers(cgf_file)
    controller = controllers.get(int(rot_ctrl_id))
    if not controller or controller.get("controller_component") != "rotation_axis_angle":
        return 0

    keys = tuple(controller.get("controller_keys") or ())
    if len(keys) < 2:
        return 0

    frame_scale = _get_frame_scale(cgf_file)
    obj.rotation_mode = "QUATERNION"
    inserted_keys = 0

    for key in keys:
        axis = key.get("axis")
        angle = key.get("angle_radians")
        time_ticks = key.get("time_ticks")
        if axis is None or angle is None or time_ticks is None:
            continue

        frame = 1.0 + float(time_ticks) * frame_scale
        blender_axis = Vector((float(axis[0]), float(axis[1]), float(axis[2]))).normalized()
        quat = Quaternion(blender_axis, float(angle))

        obj.rotation_quaternion = quat
        obj.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        inserted_keys += 1

    if inserted_keys < 2:
        obj.animation_data_clear()
        return 0

    # Set linear extrapolation for cyclic rotation
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = "LINEAR"

    return inserted_keys


def _decoded_controllers(cgf_file: Dict[str, Any]) -> Dict[int, Any]:
    controllers = {}
    for chunk in cgf_file.values():
        if isinstance(chunk, dict) and chunk.get("chunk_type") == "Controller":
            header = chunk.get("header") or {}
            cid = header.get("chunk_id")
            if cid is not None:
                controllers[cid] = chunk
    return controllers


def _get_frame_scale(cgf_file: Dict[str, Any]) -> float:
    timing = cgf_file.get("Timing") or {}
    ticks_per_sec = float(timing.get("ticks_per_second") or 4800.0)
    fps = 30.0
    return fps / ticks_per_sec if ticks_per_sec > 0 else 1.0 / 160.0
