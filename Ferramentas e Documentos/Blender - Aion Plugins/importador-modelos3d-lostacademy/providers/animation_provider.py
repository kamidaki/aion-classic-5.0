"""
Animation Provider for Aion Assets.
Parses CAF animation files into Blender Actions with keyframed bone transforms,
and serializes Blender Actions back into authoritative CryEngine CAF binary files.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

import bpy
from .base_provider import IAnimationProvider
from ..formats.cgf.caf_parser import parse_caf
from ..formats.cgf.caf_writer import write_caf


class AnimationProvider(IAnimationProvider):
    """Manages Action construction, pose keyframing, and CAF serialization."""

    def load_animation(
        self,
        rig_obj: bpy.types.Object,
        caf_bytes: bytes,
        action_name: str,
        bone_names: List[str],
        bone_anim: List[Dict[str, Any]],
    ) -> Optional[bpy.types.Action]:
        """Parses a CAF file and applies keyframes to the rig."""
        if not caf_bytes or not rig_obj:
            return None

        parsed = parse_caf(caf_bytes)
        if not parsed or not parsed.get("controllers"):
            return None

        controllers = parsed["controllers"]
        timing = parsed.get("timing", {})
        frame_end = timing.get("frame_end", 60)

        # Map controller IDs to bone names
        ctrl_to_bone: Dict[int, str] = {}
        for i, b_info in enumerate(bone_anim):
            cid = b_info.get("ctrl_id")
            if cid is not None and i < len(bone_names):
                ctrl_to_bone[cid] = bone_names[i]

        action = bpy.data.actions.new(name=action_name)
        rig_obj.animation_data_create()
        rig_obj.animation_data.action = action

        # Set keyframes on pose bones
        if rig_obj.pose and rig_obj.pose.bones:
            for ctrl_id, keys in controllers.items():
                b_name = ctrl_to_bone.get(ctrl_id)
                if not b_name or b_name not in rig_obj.pose.bones:
                    continue

                pbone = rig_obj.pose.bones[b_name]
                pbone.rotation_mode = "QUATERNION"

                for k in keys:
                    frame = k["frame"]
                    pbone.location = k["pos"]
                    pbone.rotation_quaternion = k["quat"]
                    pbone.keyframe_insert("location", frame=frame)
                    pbone.keyframe_insert("rotation_quaternion", frame=frame)

        # Setup cyclic playback
        if hasattr(action, "fcurves"):
            for fc in action.fcurves:
                has_cycles = any(m.type == "CYCLES" for m in fc.modifiers)
                if not has_cycles:
                    fc.modifiers.new(type="CYCLES")

        return action

    def serialize_action(
        self,
        rig_obj: bpy.types.Object,
        action: bpy.types.Action,
        bone_names: List[str],
        bone_anim: List[Dict[str, Any]],
    ) -> bytes:
        """Extracts keyframes from rig pose bones across the action timeline and encodes CAF binary."""
        if not rig_obj or not action:
            return b""

        bone_to_ctrl: Dict[str, int] = {}
        for i, b_info in enumerate(bone_anim):
            cid = b_info.get("ctrl_id")
            if cid is not None and i < len(bone_names):
                bone_to_ctrl[bone_names[i]] = cid

        frame_start = int(action.frame_range[0])
        frame_end = int(action.frame_range[1])

        controllers: Dict[int, List[Dict[str, Any]]] = {}

        # Sample transforms frame by frame
        orig_frame = bpy.context.scene.frame_current

        for f in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(f)
            bpy.context.view_layer.update()

            for b_name, ctrl_id in bone_to_ctrl.items():
                if b_name not in rig_obj.pose.bones:
                    continue
                pbone = rig_obj.pose.bones[b_name]

                if ctrl_id not in controllers:
                    controllers[ctrl_id] = []

                controllers[ctrl_id].append({
                    "frame": f - frame_start,
                    "pos": (pbone.location.x, pbone.location.y, pbone.location.z),
                    "quat": (
                        pbone.rotation_quaternion.w,
                        pbone.rotation_quaternion.x,
                        pbone.rotation_quaternion.y,
                        pbone.rotation_quaternion.z,
                    ),
                })

        bpy.context.scene.frame_set(orig_frame)

        return write_caf(
            controllers=controllers,
            ticks_per_frame=160,
            frame_start=0,
            frame_end=frame_end - frame_start,
        )
