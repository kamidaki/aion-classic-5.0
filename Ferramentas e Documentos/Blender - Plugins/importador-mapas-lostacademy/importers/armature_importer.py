"""
Armature and Character Animation Importer for Aion Blender Toolkit.
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
        self._armatures: Dict[str, str] = {}
        self._actions: Dict[str, str] = {}

    @classmethod
    def get(cls) -> "ArmatureCache":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def clear(self) -> None:
        self._armatures.clear()
        self._actions.clear()

    clear_cache = clear

    def get_armature(self, key: str) -> Optional[bpy.types.Armature]:
        name = self._armatures.get(key)
        if not name:
            return None
        try:
            arm = bpy.data.armatures.get(name)
            if arm is not None and arm.name == name:
                return arm
        except (ReferenceError, Exception):
            pass
        self._armatures.pop(key, None)
        return None

    def set_armature(self, key: str, arm: bpy.types.Armature) -> None:
        try:
            self._armatures[key] = arm.name
        except (ReferenceError, Exception):
            pass

    def get_action(self, key: str) -> Optional[bpy.types.Action]:
        name = self._actions.get(key)
        if not name:
            return None
        try:
            act = bpy.data.actions.get(name)
            if act is not None and act.name == name:
                return act
        except (ReferenceError, Exception):
            pass
        self._actions.pop(key, None)
        return None

    def set_action(self, key: str, act: bpy.types.Action) -> None:
        try:
            self._actions[key] = act.name
        except (ReferenceError, Exception):
            pass


def build_npc_armature(
    npc_name: str,
    bone_names: List[str],
    bone_initial_pos: List[Tuple[float, ...]],
    bone_anim: List[Dict[str, Any]],
    collection: Optional[bpy.types.Collection] = None,
) -> Any:
    """
    Builds a Blender Armature matching the CryEngine skeleton hierarchy.
    Transforms metric cm coordinates to Blender meters (/ 100).
    Safely uses a temporary object linked to the scene root collection
    to build edit bones, with guaranteed cleanup and mode restoration.
    """
    if not bone_names or not bone_initial_pos:
        return None

    cache = ArmatureCache.get()
    cache_key = f"arm_{npc_name}_{len(bone_names)}"

    arm_data = cache.get_armature(cache_key)
    if arm_data is None:
        arm_data = bpy.data.armatures.new(f"{npc_name}_Armature")

        scene_col = bpy.context.scene.collection
        view_layer = bpy.context.view_layer
        temp_name = f"__aion_temp_rig_{npc_name}__"
        temp_obj = bpy.data.objects.new(temp_name, arm_data)
        scene_col.objects.link(temp_obj)
        view_layer.update()

        prev_active = getattr(view_layer.objects, "active", None)
        edit_failed = False
        try:
            view_layer.objects.active = temp_obj
            temp_obj.select_set(True)

            win = None
            screen = None
            area = None
            for wm in getattr(bpy.data, "window_managers", ()):
                for w in getattr(wm, "windows", ()):
                    win = w
                    screen = getattr(w, "screen", None)
                    if screen:
                        area = next((a for a in screen.areas if a.type == "VIEW_3D"), None)
                    break
                if win:
                    break

            override_kwargs = {
                "scene": bpy.context.scene,
                "view_layer": view_layer,
                "object": temp_obj,
                "active_object": temp_obj,
                "selected_objects": [temp_obj],
                "selected_editable_objects": [temp_obj],
            }
            if win and screen:
                override_kwargs["window"] = win
                override_kwargs["screen"] = screen
            if area:
                override_kwargs["area"] = area

            with bpy.context.temp_override(**override_kwargs):
                bpy.ops.object.mode_set(mode="EDIT")
                edit_bones: Dict[int, bpy.types.EditBone] = {}

                # 1. Create all bones with head positions
                for i, b_name in enumerate(bone_names):
                    eb = arm_data.edit_bones.new(b_name)
                    eb.use_deform = True
                    m = bone_initial_pos[i] if i < len(bone_initial_pos) else None
                    if m and len(m) >= 12:
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

                        dist = (eb.head - parent_eb.head).length
                        if dist > 0.005:
                            parent_eb.tail = eb.head
        except Exception as exc:
            edit_failed = True
            print(f"[AION NPC] Edit-mode armature skipped ({npc_name}): {exc}")
        finally:
            try:
                if temp_obj.mode != "OBJECT":
                    with bpy.context.temp_override(scene=bpy.context.scene, view_layer=view_layer, object=temp_obj, active_object=temp_obj):
                        bpy.ops.object.mode_set(mode="OBJECT")
            except Exception:
                pass
            if temp_obj.name in scene_col.objects:
                scene_col.objects.unlink(temp_obj)
            if temp_obj.name in bpy.data.objects:
                bpy.data.objects.remove(temp_obj, do_unlink=True)
            if prev_active and prev_active.name in bpy.data.objects:
                try:
                    view_layer.objects.active = prev_active
                except Exception:
                    pass
        if edit_failed:
            cache._armatures.pop(cache_key, None)
            try:
                bpy.data.armatures.remove(arm_data)
            except Exception:
                pass
            return None
        cache.set_armature(cache_key, arm_data)

    if collection is not None:
        rig_obj = bpy.data.objects.new(f"{npc_name}_Rig", arm_data)
        collection.objects.link(rig_obj)
        return rig_obj

    return arm_data


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

    # Pre-create vertex groups
    vgs = []
    for b_name in bone_names:
        if b_name in mesh_obj.vertex_groups:
            vgs.append(mesh_obj.vertex_groups[b_name])
        else:
            vgs.append(mesh_obj.vertex_groups.new(name=b_name))

    # Assign weights
    for vert_idx, links in enumerate(skin_weights):
        for bone_id, weight in links:
            if 0 <= bone_id < len(vgs) and weight > 0.0001:
                vgs[bone_id].add([vert_idx], weight, "REPLACE")

    # Add Armature modifier if rig is provided
    if rig_obj is not None:
        has_arm_mod = any(mod.type == "ARMATURE" for mod in mesh_obj.modifiers)
        if not has_arm_mod:
            mod = mesh_obj.modifiers.new(name="Aion_Armature", type="ARMATURE")
            mod.object = rig_obj
            mod.use_vertex_groups = True


def iter_apply_caf_animation(
    rig_obj: bpy.types.Object,
    caf_data: bytes | Dict[str, Any],
    bone_names: List[str],
    bone_anim: List[Dict[str, Any]],
    action_name: str = "Aion_NPC_Idle",
    *,
    bones_per_yield: int = 6,
):
    """
    Time-sliced generator creating a looping CAF Action on `rig_obj`.
    Accepts either raw CAF bytes or pre-parsed CAF dict from worker threads.
    Yields `(done_bones, total_bones)` every `bones_per_yield` bones and returns the Action.
    """
    if not caf_data:
        return None

    cache = ArmatureCache.get()
    cached_action = cache.get_action(action_name)
    if cached_action is not None:
        rig_obj.animation_data_create()
        rig_obj.animation_data.action = cached_action
        return cached_action

    parsed = caf_data if isinstance(caf_data, dict) else parse_caf(caf_data)
    if not parsed or not parsed.get("controllers"):
        return None

    controllers = parsed["controllers"]

    # Ensure pose is initialized in Blender view layer
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

    step_yield = max(1, int(bones_per_yield))
    total_ctrls = len(controllers)
    processed = 0

    # Configure pose bones and insert keyframes in time-sliced bone chunks
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

            processed += 1
            if processed % step_yield == 0 and processed < total_ctrls:
                yield (processed, total_ctrls)

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
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for bag in getattr(strip, "channelbags", ()):
                for fc in getattr(bag, "fcurves", ()):
                    if not any(m.type == "CYCLES" for m in fc.modifiers):
                        fc.modifiers.new(type="CYCLES")

    cache.set_action(action_name, action)
    return action


def apply_caf_animation(
    rig_obj: bpy.types.Object,
    caf_data: bytes | Dict[str, Any],
    bone_names: List[str],
    bone_anim: List[Dict[str, Any]],
    action_name: str = "Aion_NPC_Idle",
) -> Optional[bpy.types.Action]:
    """
    Synchronous wrapper around `iter_apply_caf_animation` assigning a looping CAF Action.
    """
    gen = iter_apply_caf_animation(
        rig_obj,
        caf_data,
        bone_names,
        bone_anim,
        action_name=action_name,
        bones_per_yield=999999,
    )
    try:
        while True:
            next(gen)
    except StopIteration as exc:
        return exc.value
