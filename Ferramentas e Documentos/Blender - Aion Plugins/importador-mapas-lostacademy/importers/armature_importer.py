"""
Armature & Character Animation Importer for Aion Blender Toolkit.
Constructs Blender Armatures from CryEngine skeleton chunks,
assigns skin weights, and creates looping idle Actions from CAF animation data.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bpy
import mathutils
from mathutils import Matrix, Quaternion, Vector

from formats.cgf.caf_parser import parse_caf
from formats.cgf.cal_parser import parse_cal, find_default_idle_animation


class ArmatureCache:
    """Caches created Armature datablocks and Actions for instanced NPCs."""

    _instance: Optional["ArmatureCache"] = None

    def __init__(self):
        self._armatures: Dict[str, bpy.types.Armature] = {}
        self._actions: Dict[str, bpy.types.Action] = {}

    @classmethod
    def get(cls) -> "ArmatureCache":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def clear(self) -> None:
        self._armatures.clear()
        self._actions.clear()


def build_npc_armature(
    npc_name: str,
    bone_names: List[str],
    bone_initial_pos: List[Tuple[float, ...]],
    bone_anim: List[Dict[str, Any]],
    collection: bpy.types.Collection,
) -> Optional[bpy.types.Object]:
    """
    Builds a Blender Armature object matching the CryEngine skeleton hierarchy.
    Transforms metric cm coordinates to Blender meters (/ 100).
    """
    if not bone_names or not bone_initial_pos:
        return None

    cache = ArmatureCache.get()
    cache_key = f"arm_{npc_name}_{len(bone_names)}"

    arm_data = cache._armatures.get(cache_key)
    if arm_data is None or arm_data.name not in bpy.data.armatures:
        arm_data = bpy.data.armatures.new(f"{npc_name}_Armature")
        cache._armatures[cache_key] = arm_data

        # Temporary object to edit bones
        temp_obj = bpy.data.objects.new(f"{npc_name}_Rig_Temp", arm_data)
        collection.objects.link(temp_obj)
        bpy.context.view_layer.objects.active = temp_obj

        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones: Dict[int, bpy.types.EditBone] = {}

        # 1. Create all bones with head positions
        for i, b_name in enumerate(bone_names):
            eb = arm_data.edit_bones.new(b_name)
            eb.use_deform = True
            m = bone_initial_pos[i] if i < len(bone_initial_pos) else None
            if m and len(m) >= 12:
                # floats 9, 10, 11 are bone position in cm
                head_pos = Vector((m[9] / 100.0, m[10] / 100.0, m[11] / 100.0))
            else:
                head_pos = Vector((0.0, 0.0, float(i) * 0.05))

            eb.head = head_pos
            eb.tail = head_pos + Vector((0.0, 0.0, 0.05))
            edit_bones[i] = eb

        # 2. Configure parent-child relationships and tail pointing
        for i, b_info in enumerate(bone_anim):
            pid = b_info.get("parent_id", -1)
            if pid >= 0 and pid in edit_bones:
                eb = edit_bones[i]
                parent_eb = edit_bones[pid]
                eb.parent = parent_eb

                # Orient parent tail toward child head if distance > 1mm
                dist = (eb.head - parent_eb.head).length
                if dist > 0.005:
                    parent_eb.tail = eb.head

        bpy.ops.object.mode_set(mode="OBJECT")
        collection.objects.unlink(temp_obj)
        bpy.data.objects.remove(temp_obj, do_unlink=True)

    # Create scene object using the cached armature datablock
    rig_obj = bpy.data.objects.new(f"{npc_name}_Rig", arm_data)
    collection.objects.link(rig_obj)
    return rig_obj


def apply_skin_weights(
    mesh_obj: bpy.types.Object,
    bone_names: List[str],
    skin_weights: List[List[Tuple[int, float]]],
    rig_obj: Optional[bpy.types.Object] = None,
) -> None:
    """
    Creates vertex groups on the mesh object and assigns skinning weights.
    Adds an ARMATURE modifier pointing to rig_obj.
    """
    if not bone_names or not skin_weights:
        return

    # Create vertex groups
    for b_name in bone_names:
        if b_name not in mesh_obj.vertex_groups:
            mesh_obj.vertex_groups.new(name=b_name)

    # Assign weights
    for vert_idx, links in enumerate(skin_weights):
        for bone_id, weight in links:
            if 0 <= bone_id < len(bone_names) and weight > 0.0001:
                b_name = bone_names[bone_id]
                mesh_obj.vertex_groups[b_name].add([vert_idx], weight, "REPLACE")

    # Add Armature modifier if rig is provided
    if rig_obj is not None:
        has_arm_mod = any(mod.type == "ARMATURE" for mod in mesh_obj.modifiers)
        if not has_arm_mod:
            mod = mesh_obj.modifiers.new(name="Aion_Armature", type="ARMATURE")
            mod.object = rig_obj
            mod.use_vertex_groups = True


def apply_caf_animation(
    rig_obj: bpy.types.Object,
    caf_data: bytes,
    bone_names: List[str],
    bone_anim: List[Dict[str, Any]],
    action_name: str = "Aion_NPC_Idle",
) -> Optional[bpy.types.Action]:
    """
    Parses a CAF animation file and assigns a looping Action to rig_obj.
    Keyframes are inserted for location and rotation_quaternion across bones.
    Supports both Blender 4.x and Blender 5.x layered/slotted action architectures.
    """
    if not caf_data:
        return None

    parsed = parse_caf(caf_data)
    if not parsed or not parsed.get("controllers"):
        return None

    cache = ArmatureCache.get()
    if action_name in cache._actions and cache._actions[action_name].name in bpy.data.actions:
        action = cache._actions[action_name]
        rig_obj.animation_data_create()
        rig_obj.animation_data.action = action
        return action

    controllers = parsed["controllers"]
    timing = parsed.get("timing", {})
    frame_end = timing.get("frame_end", 60)

    # Ensure pose is initialized in Blender 5.2 LTS
    if rig_obj.pose is None:
        try:
            bpy.context.view_layer.update()
        except Exception:
            pass

    # Map controller IDs to bone names
    ctrl_to_bone: Dict[int, str] = {}
    for i, b_info in enumerate(bone_anim):
        cid = b_info.get("ctrl_id")
        if cid is not None and i < len(bone_names):
            ctrl_to_bone[cid] = bone_names[i]

    action = bpy.data.actions.new(action_name)
    rig_obj.animation_data_create()
    rig_obj.animation_data.action = action

    # Configure pose bones and insert keyframes
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

    # Configure cyclic playback
    try:
        action.use_cyclic = True
    except AttributeError:
        pass

    if hasattr(action, "fcurves"):
        for fc in action.fcurves:
            has_cycles = any(m.type == "CYCLES" for m in fc.modifiers)
            if not has_cycles:
                fc.modifiers.new(type="CYCLES")

    cache._actions[action_name] = action
    return action
