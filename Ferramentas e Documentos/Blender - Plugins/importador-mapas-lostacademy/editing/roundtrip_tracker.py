"""
Round-trip Change Tracking and Metadata Management for Aion Level Objects.
Tracks objects imported from brush.lst, objects.lst, and mission_mission0.xml.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import bpy
from mathutils import Matrix, Vector

SOURCE_BRUSH = "brush"
SOURCE_OBJECT = "object"
SOURCE_MISSION = "mission"
SOURCE_NPC = "npc"


@dataclass
class ObjectChangeRecord:
    obj: bpy.types.Object
    source_type: str
    source_index: int
    cgf_reference: str
    is_modified: bool
    current_matrix: Matrix
    original_matrix: Optional[Matrix]
    is_new: bool = False


def tag_object_instance(
    obj: bpy.types.Object,
    source_type: str,
    source_index: int = 0,
    cgf_reference: str = "",
    matrix: Optional[Matrix] = None,
    *,
    reference: Optional[str] = None,
    original_matrix: Optional[Matrix] = None,
    mesh_offset: Optional[Matrix] = None,
) -> None:
    """Tags a Blender object with metadata for round-trip tracking."""
    ref = reference or cgf_reference or ""
    mat = original_matrix if original_matrix is not None else (matrix if matrix is not None else obj.matrix_world)

    obj["aion_source_type"] = str(source_type).strip().lower()
    obj["aion_source_index"] = source_index
    obj["aion_reference"] = ref
    obj["aion_orig_matrix"] = [float(v) for row in mat for v in row]
    if mesh_offset is not None:
        obj["aion_mesh_offset"] = [float(v) for row in mesh_offset for v in row]


def get_object_metadata(obj: bpy.types.Object) -> Optional[dict]:
    """Retrieves Aion source metadata from a Blender object if present."""
    if "aion_source_type" not in obj:
        return None
    return {
        "source_type": str(obj["aion_source_type"]).strip().lower(),
        "source_index": int(obj.get("aion_source_index", -1)),
        "reference": str(obj.get("aion_reference", "")),
        "orig_matrix": obj.get("aion_orig_matrix"),
        "mesh_offset": obj.get("aion_mesh_offset"),
    }


def matrix_has_changed(current: Matrix, original_values: list[float], tolerance: float = 1e-4) -> bool:
    """Checks if a matrix has deviated from its recorded original values."""
    if not original_values or len(original_values) != 16:
        return True
    curr_flat = [float(v) for row in current for v in row]
    for c, o in zip(curr_flat, original_values):
        if abs(c - o) > tolerance:
            return True
    return False


def collect_scene_changes(scene: bpy.types.Scene) -> dict[str, list[ObjectChangeRecord]]:
    """
    Scans the scene for all Aion objects and classifies them into:
    - brush changes (modifications, new additions, deletions)
    - object (vegetation) changes (modifications, new additions, deletions)
    - mission placeable changes
    - NPC spawn changes
    """
    try:
        if bpy.context and hasattr(bpy.context, "view_layer") and bpy.context.view_layer:
            bpy.context.view_layer.update()
    except Exception:
        pass

    results: dict[str, list[ObjectChangeRecord]] = {
        SOURCE_BRUSH: [],
        SOURCE_OBJECT: [],
        SOURCE_MISSION: [],
        SOURCE_NPC: [],
    }

    seen_indices: dict[str, set[int]] = {
        SOURCE_BRUSH: set(),
        SOURCE_OBJECT: set(),
        SOURCE_MISSION: set(),
        SOURCE_NPC: set(),
    }

    for obj in scene.objects:
        # Check NPC objects
        stype_raw = str(obj.get("aion_source_type", "")).strip().lower()
        if stype_raw in ("npc", "npc_rig", "npc_marker") and "aion_npc_id" in obj:
            npc_id = str(obj.get("aion_npc_id", ""))
            npc_name = str(obj.get("aion_npc_name", obj.name))
            orig_pos = obj.get("aion_orig_pos")
            curr_pos = (obj.location.x, obj.location.y, obj.location.z)
            is_mod = False
            if orig_pos and len(orig_pos) == 3:
                is_mod = any(abs(c - o) > 0.05 for c, o in zip(curr_pos, orig_pos))
            else:
                is_mod = False  # Not moved if no baseline

            record = ObjectChangeRecord(
                obj=obj,
                source_type=SOURCE_NPC,
                source_index=int(npc_id) if npc_id.isdigit() else -1,
                cgf_reference=npc_name,
                is_modified=is_mod,
                current_matrix=obj.matrix_world.copy(),
                original_matrix=None,
                is_new=orig_pos is None and int(npc_id if npc_id.isdigit() else -1) < 0,
            )
            results[SOURCE_NPC].append(record)
            continue

        meta = get_object_metadata(obj)
        if not meta:
            continue

        stype = meta["source_type"]
        if stype not in results:
            continue

        sidx = meta["source_index"]
        ref = meta["reference"]
        orig_vals = meta.get("orig_matrix")
        mesh_offset_vals = meta.get("mesh_offset")

        # Duplicate detection (Shift+D in Blender copies custom properties)
        is_duplicate = False
        if sidx >= 0:
            if sidx in seen_indices[stype]:
                is_duplicate = True
                sidx = -1
            else:
                seen_indices[stype].add(sidx)

        # If the template submesh had a local transform offset, inverse-multiply it
        # to recover the exact authoritative placement transform:
        if mesh_offset_vals and len(mesh_offset_vals) == 16:
            offset_mat = Matrix(
                (
                    mesh_offset_vals[0:4],
                    mesh_offset_vals[4:8],
                    mesh_offset_vals[8:12],
                    mesh_offset_vals[12:16],
                )
            )
            try:
                curr_mat = obj.matrix_world @ offset_mat.inverted()
            except Exception:
                curr_mat = obj.matrix_world.copy()
        else:
            curr_mat = obj.matrix_world.copy()

        is_mod = matrix_has_changed(curr_mat, orig_vals) if orig_vals else True
        is_new = (sidx < 0) or is_duplicate

        record = ObjectChangeRecord(
            obj=obj,
            source_type=stype,
            source_index=sidx,
            cgf_reference=ref,
            is_modified=is_mod or is_new,
            current_matrix=curr_mat,
            original_matrix=Matrix(
                (orig_vals[0:4], orig_vals[4:8], orig_vals[8:12], orig_vals[12:16])
            )
            if orig_vals and len(orig_vals) == 16
            else None,
            is_new=is_new,
        )
        results[stype].append(record)

    return results
