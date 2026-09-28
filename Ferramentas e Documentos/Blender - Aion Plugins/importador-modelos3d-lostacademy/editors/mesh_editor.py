"""
Mesh & Geometry Editor for Aion Assets.
Bridges Blender mesh editing (vertices, edges, faces, sculpting, normals, UVs)
with Aion CGF data representation.
"""

from __future__ import annotations
from typing import List, Optional, Tuple

import bpy
from ..core.change_tracker import ChangeTracker


class MeshEditor:
    """Manages mesh edit synchronization and validation."""

    @staticmethod
    def enter_edit_mode(mesh_obj: bpy.types.Object) -> None:
        """Sets active object and enters mesh Edit Mode."""
        if not mesh_obj or mesh_obj.type != "MESH":
            return
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")

    @staticmethod
    def enter_sculpt_mode(mesh_obj: bpy.types.Object) -> None:
        """Sets active object and enters Sculpt Mode."""
        if not mesh_obj or mesh_obj.type != "MESH":
            return
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        bpy.ops.object.mode_set(mode="SCULPT")

    @staticmethod
    def return_to_object_mode() -> None:
        """Exits any sub-mode back to Object Mode."""
        if bpy.context.active_object and bpy.context.active_object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    @staticmethod
    def recalculate_normals(mesh_obj: bpy.types.Object) -> None:
        """Recalculates outside normals on mesh geometry."""
        if not mesh_obj or mesh_obj.type != "MESH":
            return
        curr_mode = mesh_obj.mode
        bpy.context.view_layer.objects.active = mesh_obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode=curr_mode)

    @staticmethod
    def extract_geometry_stats(mesh_obj: bpy.types.Object) -> Tuple[int, int, int]:
        """Returns (vertex_count, edge_count, triangle_count)."""
        if not mesh_obj or mesh_obj.type != "MESH":
            return (0, 0, 0)
        mesh: bpy.types.Mesh = mesh_obj.data
        tri_count = sum(len(p.vertices) - 2 for p in mesh.polygons)
        return (len(mesh.vertices), len(mesh.edges), tri_count)
