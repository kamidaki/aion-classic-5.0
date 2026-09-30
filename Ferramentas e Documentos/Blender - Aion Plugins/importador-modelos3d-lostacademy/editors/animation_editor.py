"""
Animation & Action Editor for Aion Assets.
Supports clip duplication, keyframe authoring, duration scaling, and idle animation reassignment.
"""

from __future__ import annotations
from typing import List, Optional

import bpy


class AnimationEditor:
    """Manages Action authoring and keyframe modifications."""

    @staticmethod
    def duplicate_action(source_action: bpy.types.Action, new_name: str) -> bpy.types.Action:
        """Clones an existing Action datablock with a new name."""
        new_action = source_action.copy()
        new_action.name = new_name
        return new_action

    @staticmethod
    def insert_keyframe_on_selected_bones(arm_obj: bpy.types.Object, frame: int) -> int:
        """Inserts location and rotation keyframes on selected pose bones."""
        if not arm_obj or arm_obj.type != "ARMATURE" or not arm_obj.pose:
            return 0

        count = 0
        for pbone in arm_obj.pose.bones:
            if pbone.bone.select:
                pbone.rotation_mode = "QUATERNION"
                pbone.keyframe_insert("location", frame=frame)
                pbone.keyframe_insert("rotation_quaternion", frame=frame)
                count += 1
        return count

    @staticmethod
    def scale_action_duration(action: bpy.types.Action, scale_factor: float = 1.0) -> None:
        """Scales keyframe times across all fcurves in an Action."""
        if not action or scale_factor <= 0.0 or scale_factor == 1.0:
            return

        if hasattr(action, "fcurves"):
            for fc in action.fcurves:
                for kp in fc.keyframe_points:
                    kp.co[0] *= scale_factor
                    kp.handle_left[0] *= scale_factor
                    kp.handle_right[0] *= scale_factor
