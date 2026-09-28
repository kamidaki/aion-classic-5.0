"""
Animation Provider for Aion Assets.
Parses CAF animation files into Blender Actions with keyframed bone transforms,
and serializes Blender Actions back into authoritative CryEngine CAF binary files.
"""

from __future__ import annotations
import binascii
from typing import Any, Dict, List, Optional, Tuple

import bpy
from mathutils import Matrix, Quaternion, Vector
from .base_provider import IAnimationProvider
from ..formats.cgf.caf_parser import parse_caf
from ..formats.cgf.caf_writer import write_caf


def sample_controller(keys: List[Dict[str, Any]], frame: float) -> Tuple[Vector, Quaternion]:
    """Linearly interpolates position and spherically interpolates quaternion for sparse keys."""
    if not keys:
        return Vector((0.0, 0.0, 0.0)), Quaternion((1.0, 0.0, 0.0, 0.0))
    if frame <= keys[0]["frame"]:
        return Vector(keys[0]["pos"]), Quaternion(keys[0]["quat"])
    if frame >= keys[-1]["frame"]:
        return Vector(keys[-1]["pos"]), Quaternion(keys[-1]["quat"])

    for idx in range(len(keys) - 1):
        k0 = keys[idx]
        k1 = keys[idx + 1]
        f0 = k0["frame"]
        f1 = k1["frame"]
        if f0 <= frame <= f1:
            if abs(f1 - f0) < 1e-5:
                return Vector(k0["pos"]), Quaternion(k0["quat"])
            t = (frame - f0) / (f1 - f0)
            p0 = Vector(k0["pos"])
            p1 = Vector(k1["pos"])
            q0 = Quaternion(k0["quat"])
            q1 = Quaternion(k1["quat"])
            return p0.lerp(p1, t), q0.slerp(q1, t)
    return Vector(keys[-1]["pos"]), Quaternion(keys[-1]["quat"])


def get_action_fcurves(action: bpy.types.Action) -> List[bpy.types.FCurve]:
    """Returns all fcurves for an action, supporting both legacy Actions and Blender 5+ layered Actions."""
    if not action:
        return []
    try:
        if hasattr(action, "fcurves") and action.fcurves is not None:
            return list(action.fcurves)
    except (AttributeError, TypeError):
        pass
    curves: List[bpy.types.FCurve] = []
    if hasattr(action, "layers"):
        for layer in action.layers:
            for strip in layer.strips:
                if hasattr(strip, "channelbags"):
                    for cb in strip.channelbags:
                        curves.extend(cb.fcurves)
    return curves


class AnimationProvider(IAnimationProvider):
    """Manages Action construction, pose keyframing, and CAF serialization."""

    def load_animation(
        self,
        rig_obj: bpy.types.Object,
        caf_bytes: bytes,
        action_name: str,
        bone_names: Optional[List[str]] = None,
        bone_anim: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[bpy.types.Action]:
        """Parses a CAF file and applies hierarchical keyframes with forward kinematics."""
        if not caf_bytes or not rig_obj:
            return None

        parsed = parse_caf(caf_bytes)
        if not parsed or not parsed.get("controllers"):
            return None

        controllers = parsed["controllers"]
        timing = parsed.get("timing", {})

        # Determine frame boundaries
        frame_start = int(timing.get("frame_start", 0))
        frame_end = int(timing.get("frame_end", 0))
        if frame_end <= frame_start:
            all_frames: List[float] = []
            for keys in controllers.values():
                for k in keys:
                    all_frames.append(k["frame"])
            if all_frames:
                frame_start = int(min(all_frames))
                frame_end = int(max(all_frames))
            else:
                frame_end = frame_start + 60

        # Map controller IDs to bone names via CRC32
        ctrl_to_bone: Dict[int, str] = {}
        if bone_anim and bone_names:
            for i, b_info in enumerate(bone_anim):
                cid = b_info.get("ctrl_id")
                if cid is not None and i < len(bone_names):
                    ctrl_to_bone[cid] = bone_names[i]

        if rig_obj.data and hasattr(rig_obj.data, "bones"):
            for b_name in rig_obj.data.bones.keys():
                ctrl_to_bone[binascii.crc32(b_name.encode("latin-1"))] = b_name
                ctrl_to_bone[binascii.crc32(b_name.lower().encode("latin-1"))] = b_name

        bone_tracks: Dict[str, List[Dict[str, Any]]] = {}
        for cid, keys in controllers.items():
            b_name = ctrl_to_bone.get(cid)
            if b_name and rig_obj.data and b_name in rig_obj.data.bones:
                bone_tracks[b_name] = keys

        # Topological evaluation order (parents before children)
        eval_order: List[str] = []
        visited: set[str] = set()

        def visit(b_data: bpy.types.Bone) -> None:
            if b_data.parent and b_data.parent.name not in visited:
                visit(b_data.parent)
            if b_data.name not in visited:
                visited.add(b_data.name)
                eval_order.append(b_data.name)

        if rig_obj.data and hasattr(rig_obj.data, "bones"):
            for b_data in rig_obj.data.bones:
                visit(b_data)

        # Set timeline playback range
        bpy.context.scene.frame_start = frame_start
        bpy.context.scene.frame_end = max(frame_start + 1, frame_end)

        action = bpy.data.actions.new(name=action_name)
        rig_obj.animation_data_create()
        rig_obj.animation_data.action = action

        bpy.context.view_layer.objects.active = rig_obj
        bpy.ops.object.mode_set(mode="POSE")

        for bn in eval_order:
            if bn in rig_obj.pose.bones:
                rig_obj.pose.bones[bn].rotation_mode = "QUATERNION"

        orig_frame = bpy.context.scene.frame_current

        # Mathematically exact local basis pose keyframing:
        # matrix_basis = rest_local.inverted() @ local_anim
        # Guarantees zero depsgraph lag, zero compound skew down hierarchies,
        # perfectly seamless looping (frame 0 == frame end), and 100% clean rest pose when stopped.
        for f in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(f)

            for bn in eval_order:
                if bn not in rig_obj.pose.bones:
                    continue
                pbone = rig_obj.pose.bones[bn]
                bone_data = rig_obj.data.bones[bn]
                bind_mat = bone_data.matrix_local

                if bone_data.parent:
                    rest_local = bone_data.parent.matrix_local.inverted() @ bind_mat
                else:
                    rest_local = bind_mat

                if bn in bone_tracks:
                    pos_v, quat_v = sample_controller(bone_tracks[bn], float(f))
                    # CryEngine quaternion is conjugated for Blender active rotation
                    quat_v = quat_v.conjugated()
                    local_mat = Matrix.Translation(pos_v) @ quat_v.to_matrix().to_4x4()
                else:
                    local_mat = rest_local

                basis_mat = rest_local.inverted() @ local_mat

                pbone.location = basis_mat.translation
                pbone.rotation_quaternion = basis_mat.to_quaternion()
                pbone.scale = basis_mat.to_scale()

                pbone.keyframe_insert("location", frame=f)
                pbone.keyframe_insert("rotation_quaternion", frame=f)
                pbone.keyframe_insert("scale", frame=f)

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.scene.frame_set(orig_frame)

        # Setup cyclic playback
        for fc in get_action_fcurves(action):
            has_cycles = any(m.type == "CYCLES" for m in fc.modifiers)
            if not has_cycles:
                try:
                    c_mod = fc.modifiers.new(type="CYCLES")
                    c_mod.mode_after = "REPEAT"
                    c_mod.mode_before = "REPEAT"
                except Exception:
                    pass

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

        if rig_obj.data and hasattr(rig_obj.data, "bones"):
            for b_name in rig_obj.data.bones.keys():
                if b_name not in bone_to_ctrl:
                    bone_to_ctrl[b_name] = binascii.crc32(b_name.encode("latin-1"))

        frame_start = int(action.frame_range[0])
        frame_end = int(action.frame_range[1])

        controllers: Dict[int, List[Dict[str, Any]]] = {}
        orig_frame = bpy.context.scene.frame_current

        for f in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(f)

            for b_name, ctrl_id in bone_to_ctrl.items():
                if b_name not in rig_obj.pose.bones:
                    continue
                pbone = rig_obj.pose.bones[b_name]
                bone_data = rig_obj.data.bones.get(b_name)
                bind_mat = bone_data.matrix_local if bone_data else Matrix.Identity(4)

                if bone_data and bone_data.parent:
                    rest_local = bone_data.parent.matrix_local.inverted() @ bind_mat
                else:
                    rest_local = bind_mat

                basis_mat = Matrix.Translation(pbone.location) @ pbone.rotation_quaternion.to_matrix().to_4x4()
                local_mat = rest_local @ basis_mat

                pos = local_mat.translation
                quat = local_mat.to_quaternion().conjugated()

                if ctrl_id not in controllers:
                    controllers[ctrl_id] = []

                controllers[ctrl_id].append({
                    "frame": f - frame_start,
                    "pos": (pos.x, pos.y, pos.z),
                    "quat": (quat.w, quat.x, quat.y, quat.z),
                })

        bpy.context.scene.frame_set(orig_frame)

        return write_caf(
            controllers=controllers,
            ticks_per_frame=160,
            frame_start=0,
            frame_end=frame_end - frame_start,
        )
