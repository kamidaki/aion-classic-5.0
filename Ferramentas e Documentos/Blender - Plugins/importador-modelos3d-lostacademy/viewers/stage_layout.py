"""
Stage Layout Manager for LostAcademy Aion Model Library.
Handles automatic positioning of multiple models side-by-side in the viewport.
"""
from __future__ import annotations
from typing import List

import bpy
from mathutils import Vector

from .viewer_stage import ViewerStage


SAFE_MARGIN = 1.0  # meters between models


def get_stage_models() -> List[bpy.types.Object]:
    """Returns all armature root objects currently in the viewer stage."""
    stage_col = ViewerStage.get_or_create_stage_collection()
    return [o for o in stage_col.objects if o.type == 'ARMATURE']


def get_model_bounds_x(obj: bpy.types.Object) -> tuple:
    """Returns (min_x, max_x) bounds of obj and all its mesh children in world space."""
    min_x = float('inf')
    max_x = float('-inf')

    def process_obj(o: bpy.types.Object) -> None:
        nonlocal min_x, max_x
        if o.type == 'MESH':
            for corner in o.bound_box:
                world_corner = o.matrix_world @ Vector(corner)
                min_x = min(min_x, world_corner.x)
                max_x = max(max_x, world_corner.x)
        for child in o.children:
            process_obj(child)

    process_obj(obj)
    if min_x == float('inf'):
        return (obj.location.x, obj.location.x)
    return (min_x, max_x)


def calculate_next_model_x_offset(exclude_obj: Optional[bpy.types.Object] = None) -> float:
    """Calculates X position for the next model in the lineup.

    Scans all existing armature roots in the stage collection (excluding
    *exclude_obj*, if given), finds the rightmost world-space X bound among
    them, and returns that value plus SAFE_MARGIN so the new model is placed
    immediately to the right without overlapping.
    """
    existing = [o for o in get_stage_models() if o != exclude_obj]
    if not existing:
        return 0.0

    rightmost_x = float('-inf')
    for rig in existing:
        _, max_x = get_model_bounds_x(rig)
        rightmost_x = max(rightmost_x, max_x)

    if rightmost_x == float('-inf'):
        return 0.0

    # Account for half-width of the new model so origin placement maintains safe margin
    new_half_width = 0.0
    if exclude_obj is not None:
        min_nx, max_nx = get_model_bounds_x(exclude_obj)
        width = max_nx - min_nx
        if 0.0 < width < 50.0:
            new_half_width = width * 0.5

    return rightmost_x + SAFE_MARGIN + new_half_width


def apply_lineup_offset(root_obj: bpy.types.Object, mode: str = 'FOCUS') -> None:
    """Positions *root_obj* according to the current stage layout mode.

    Args:
        root_obj: The top-level object (usually an ARMATURE) that was just
            imported into the stage collection.
        mode: One of:

            ``'FOCUS'``
                Centre model at the world origin.  Clearing of pre-existing
                objects is handled externally by
                :meth:`~viewers.viewer_stage.ViewerStage.clear_stage_objects`
                before this function is called.

            ``'LINEUP'``
                Place the model to the right of all existing stage models,
                separated by :data:`SAFE_MARGIN`.
    """
    if mode == 'LINEUP':
        x_offset = calculate_next_model_x_offset(exclude_obj=root_obj)
        root_obj.location.x = x_offset
    else:
        # FOCUS mode: stage is already cleared by the caller
        root_obj.location.x = 0.0

    root_obj.location.y = 0.0
    root_obj.location.z = 0.0

