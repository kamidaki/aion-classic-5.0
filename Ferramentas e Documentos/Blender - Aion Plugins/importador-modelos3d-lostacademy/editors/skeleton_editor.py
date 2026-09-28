"""
Armature & Skeleton Editor for Aion Assets.
Supports adding bones, deleting bones, renaming bones, reparenting, and updating vertex groups.
"""

from __future__ import annotations
from typing import Optional, Tuple

import bpy
from mathutils import Vector


class SkeletonEditor:
    """Manages Armature structural editing in Blender Edit Mode."""

    @staticmethod
    def enter_bone_edit_mode(arm_obj: bpy.types.Object) -> None:
        """Sets active armature and enters Edit Mode."""
        if not arm_obj or arm_obj.type != "ARMATURE":
            return
        bpy.context.view_layer.objects.active = arm_obj
        arm_obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")

    @staticmethod
    def add_bone(
        arm_obj: bpy.types.Object,
        bone_name: str = "New_Bone",
        head_pos: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        tail_pos: Tuple[float, float, float] = (0.0, 0.0, 1.2),
        parent_name: Optional[str] = None,
    ) -> Optional[str]:
        """Creates a new EditBone in the armature."""
        if not arm_obj or arm_obj.type != "ARMATURE":
            return None

        curr_mode = arm_obj.mode
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="EDIT")

        arm_data: bpy.types.Armature = arm_obj.data
        eb = arm_data.edit_bones.new(bone_name)
        eb.head = Vector(head_pos)
        eb.tail = Vector(tail_pos)
        eb.use_deform = True

        if parent_name and parent_name in arm_data.edit_bones:
            eb.parent = arm_data.edit_bones[parent_name]

        actual_name = eb.name
        bpy.ops.object.mode_set(mode=curr_mode)
        return actual_name

    @staticmethod
    def remove_bone(arm_obj: bpy.types.Object, bone_name: str) -> bool:
        """Deletes a bone from the armature hierarchy."""
        if not arm_obj or arm_obj.type != "ARMATURE":
            return False

        curr_mode = arm_obj.mode
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="EDIT")

        arm_data: bpy.types.Armature = arm_obj.data
        if bone_name in arm_data.edit_bones:
            arm_data.edit_bones.remove(arm_data.edit_bones[bone_name])
            success = True
        else:
            success = False

        bpy.ops.object.mode_set(mode=curr_mode)
        return success

    @staticmethod
    def rename_bone(
        arm_obj: bpy.types.Object,
        old_name: str,
        new_name: str,
        mesh_obj: Optional[bpy.types.Object] = None,
    ) -> bool:
        """Renames a bone and updates matching vertex groups on skinned mesh objects."""
        if not arm_obj or arm_obj.type != "ARMATURE":
            return False

        arm_data: bpy.types.Armature = arm_obj.data
        bone = arm_data.bones.get(old_name)
        if not bone:
            return False

        bone.name = new_name

        # Update vertex group on mesh if provided
        if mesh_obj and mesh_obj.type == "MESH":
            vg = mesh_obj.vertex_groups.get(old_name)
            if vg:
                vg.name = new_name

        return True
