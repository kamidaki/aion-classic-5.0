"""
Skeleton Provider for Aion Assets.
Builds Blender Armature rigs from CryEngine bone chunks, binds vertex skinning groups,
and extracts armature hierarchy / bind poses for export.
"""

from __future__ import annotations
import binascii
from typing import Any, Dict, List, Optional, Tuple

import bpy
from mathutils import Matrix, Vector
from .base_provider import ISkeletonProvider


class SkeletonProvider(ISkeletonProvider):
    """Manages Armature construction, vertex skin weight binding, and bone export."""

    def build_armature(
        self,
        name: str,
        bone_names: List[str],
        bone_initial_pos: List[Tuple[float, ...]],
        bone_anim: List[Dict[str, Any]],
        collection: bpy.types.Collection,
    ) -> Optional[bpy.types.Object]:
        """Constructs a Blender Armature object matching the CryEngine skeleton hierarchy."""
        if not bone_names or not bone_initial_pos:
            return None

        arm_data = bpy.data.armatures.new(f"{name}_Armature")
        arm_data.display_type = "WIRE"
        rig_obj = bpy.data.objects.new(f"{name}_Rig", arm_data)
        rig_obj.show_in_front = False
        collection.objects.link(rig_obj)
        bpy.context.view_layer.objects.active = rig_obj

        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones: Dict[int, bpy.types.EditBone] = {}

        # 1. Create bones with head positions (cm -> meters / 100)
        for i, b_name in enumerate(bone_names):
            eb = arm_data.edit_bones.new(b_name)
            eb.use_deform = True
            m = bone_initial_pos[i] if i < len(bone_initial_pos) else None
            if m and len(m) >= 12:
                # floats 9, 10, 11 are bone origin in cm
                head_pos = Vector((m[9] / 100.0, m[10] / 100.0, m[11] / 100.0))
            else:
                head_pos = Vector((0.0, 0.0, float(i) * 0.05))

            eb.head = head_pos
            eb.tail = head_pos + Vector((0.0, 0.0, 0.04))
            edit_bones[i] = eb

        # 2. Configure parent-child relationships and clean tail orientations
        parent_tails_set = set()
        for i, b_info in enumerate(bone_anim):
            pid = b_info.get("parent_id", -1)
            if pid >= 0 and pid in edit_bones:
                eb = edit_bones[i]
                parent_eb = edit_bones[pid]
                eb.parent = parent_eb
                if pid not in parent_tails_set:
                    dist = (eb.head - parent_eb.head).length
                    if dist > 0.005:
                        parent_eb.tail = eb.head
                        parent_tails_set.add(pid)

        # 3. Orient leaf bones along parent bone direction instead of vertical spike
        for i, eb in edit_bones.items():
            if i not in parent_tails_set and eb.parent:
                parent_dir = (eb.parent.tail - eb.parent.head)
                if parent_dir.length > 0.001:
                    eb.tail = eb.head + parent_dir.normalized() * 0.03

        bpy.ops.object.mode_set(mode="OBJECT")
        return rig_obj

    def apply_skin_weights(
        self,
        mesh_obj: bpy.types.Object,
        bone_names: List[str],
        skin_weights: List[List[Tuple[int, float]]],
        rig_obj: Optional[bpy.types.Object] = None,
    ) -> None:
        """Creates vertex groups and binds skin weights."""
        if not bone_names or not skin_weights:
            return

        for b_name in bone_names:
            if b_name not in mesh_obj.vertex_groups:
                mesh_obj.vertex_groups.new(name=b_name)

        for vert_idx, links in enumerate(skin_weights):
            for bone_id, weight in links:
                if 0 <= bone_id < len(bone_names) and weight > 0.0001:
                    b_name = bone_names[bone_id]
                    mesh_obj.vertex_groups[b_name].add([vert_idx], weight, "REPLACE")

        if rig_obj is not None:
            has_arm_mod = any(mod.type == "ARMATURE" for mod in mesh_obj.modifiers)
            if not has_arm_mod:
                mod = mesh_obj.modifiers.new(name="Aion_Armature", type="ARMATURE")
                mod.object = rig_obj
                mod.use_vertex_groups = True

    def extract_armature(
        self, arm_obj: bpy.types.Object
    ) -> Tuple[List[str], List[Tuple[float, ...]], List[Dict[str, Any]]]:
        """Extracts bone names, 4x3 bind pose matrices, and bone hierarchy from a Blender Armature."""
        if not arm_obj or arm_obj.type != "ARMATURE":
            return [], [], []

        arm_data: bpy.types.Armature = arm_obj.data
        bone_names: List[str] = []
        bone_initial_pos: List[Tuple[float, ...]] = []
        bone_anim: List[Dict[str, Any]] = []

        # Name to index mapping
        name_to_idx: Dict[str, int] = {}
        for idx, bone in enumerate(arm_data.bones):
            bone_names.append(bone.name)
            name_to_idx[bone.name] = idx

        for idx, bone in enumerate(arm_data.bones):
            # Matrix in cm (head position at floats 9, 10, 11)
            # Bone matrix in local / rest space
            m = bone.matrix_local
            # 4x3 row major:
            # [m00, m01, m02, m10, m11, m12, m20, m21, m22, pos_x*100, pos_y*100, pos_z*100]
            mat_12 = (
                m[0][0], m[0][1], m[0][2],
                m[1][0], m[1][1], m[1][2],
                m[2][0], m[2][1], m[2][2],
                bone.head_local.x * 100.0,
                bone.head_local.y * 100.0,
                bone.head_local.z * 100.0,
            )
            bone_initial_pos.append(mat_12)

            pid = name_to_idx.get(bone.parent.name, -1) if bone.parent else -1
            nch = len(bone.children)
            ctrl_id = binascii.crc32(bone.name.encode("latin-1"))

            bone_anim.append({
                "bone_id": idx,
                "parent_id": pid,
                "num_children": nch,
                "ctrl_id": ctrl_id,
            })

        return bone_names, bone_initial_pos, bone_anim
