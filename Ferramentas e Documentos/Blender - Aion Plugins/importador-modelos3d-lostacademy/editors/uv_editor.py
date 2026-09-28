"""
UV Coordinate Editor for Aion Assets.
Provides unwrapping, island packing, and alignment tools compatible with CryEngine UV mappings.
"""

from __future__ import annotations
import bpy


class UVEditor:
    """Manages UV unwrapping, packing, and coordinate alignment."""

    @staticmethod
    def unwrap_mesh(mesh_obj: bpy.types.Object, method: str = "ANGLE_BASED") -> None:
        """Unwraps the mesh UVs using Blender's unwrap operators."""
        if not mesh_obj or mesh_obj.type != "MESH":
            return
        curr_mode = mesh_obj.mode
        bpy.context.view_layer.objects.active = mesh_obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.unwrap(method=method, margin=0.01)
        bpy.ops.object.mode_set(mode=curr_mode)

    @staticmethod
    def pack_islands(mesh_obj: bpy.types.Object, margin: float = 0.01) -> None:
        """Packs UV islands efficiently inside the 0..1 UV coordinate space."""
        if not mesh_obj or mesh_obj.type != "MESH":
            return
        curr_mode = mesh_obj.mode
        bpy.context.view_layer.objects.active = mesh_obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(margin=margin)
        bpy.ops.object.mode_set(mode=curr_mode)
