"""
Interactive Object Editing and Placement Tools for Aion Blender Toolkit.
Supports snapping to terrain, randomizing transforms for natural vegetation, and cloning.
"""

from __future__ import annotations

import math
import random
from typing import Iterable, List, Optional

import bpy
from mathutils import Matrix, Vector

from .roundtrip_tracker import tag_object_instance


def snap_objects_to_terrain(
    objects: Iterable[bpy.types.Object],
    terrain_obj: Optional[bpy.types.Object] = None,
) -> int:
    """
    Snaps selected objects down onto the terrain surface using raycasting.
    """
    if terrain_obj is None:
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH" and ("aion_blend_shader_enabled" in obj or "terrain" in obj.name.lower()):
                terrain_obj = obj
                break

    if terrain_obj is None:
        return 0

    snapped_count = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    terrain_eval = terrain_obj.evaluated_get(depsgraph)

    for obj in objects:
        if obj == terrain_obj:
            continue

        world_pos = obj.matrix_world.translation
        # Cast ray from 500 units above down along Z axis
        ray_origin = Vector((world_pos.x, world_pos.y, world_pos.z + 500.0))
        ray_dir = Vector((0.0, 0.0, -1.0))

        # Transform ray into terrain local space
        terrain_mat_inv = terrain_eval.matrix_world.inverted()
        local_origin = terrain_mat_inv @ ray_origin
        local_dir = terrain_mat_inv.to_3x3() @ ray_dir

        success, hit_loc, normal, face_idx = terrain_eval.ray_cast(local_origin, local_dir)
        if success:
            world_hit = terrain_eval.matrix_world @ hit_loc
            obj.location.z = world_hit.z
            snapped_count += 1

    return snapped_count


def randomize_object_transforms(
    objects: Iterable[bpy.types.Object],
    *,
    min_scale: float = 0.85,
    max_scale: float = 1.15,
    random_yaw: bool = True,
) -> int:
    """Randomizes scale and Z rotation for natural vegetation scattering."""
    count = 0
    for obj in objects:
        if obj.type not in ("MESH", "EMPTY"):
            continue

        scale_factor = random.uniform(min_scale, max_scale)
        obj.scale = (obj.scale.x * scale_factor, obj.scale.y * scale_factor, obj.scale.z * scale_factor)

        if random_yaw:
            yaw_angle = random.uniform(0.0, math.tau)
            obj.rotation_euler.z = yaw_angle

        count += 1
    return count
