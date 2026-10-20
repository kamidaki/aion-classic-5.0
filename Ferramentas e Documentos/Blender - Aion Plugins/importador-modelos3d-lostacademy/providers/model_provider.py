"""
Comprehensive Model Provider for Aion Assets.
Orchestrates mesh building, UV mapping, material assignment, skeletal rigging,
and animation setup for viewer and editor modes, plus CGF binary serialization.
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bpy
from mathutils import Matrix, Vector

from .base_provider import IModelProvider
from .texture_provider import TextureProvider
from .material_provider import MaterialProvider
from .skeleton_provider import SkeletonProvider
from .animation_provider import AnimationProvider
from ..core.client_provider import AionClientProvider
from ..core.change_tracker import ChangeTracker
from ..formats.cgf.parser import get_cgf
from ..formats.cgf.writer import write_cgf, patch_cgf
from ..indexer.asset_entry import AssetEntry


def _read_matrix44(matrix_values: List[float]) -> Tuple[Tuple[float, ...], ...]:
    return (
        tuple(matrix_values[0:4]),
        tuple(matrix_values[4:8]),
        tuple(matrix_values[8:12]),
        (
            matrix_values[12] / 100.0,
            matrix_values[13] / 100.0,
            matrix_values[14] / 100.0,
            matrix_values[15],
        ),
    )


def _composed_node_matrix(node: Dict[str, Any], all_nodes: Dict[Any, Any]) -> Matrix:
    chain = []
    current = node
    seen = set()
    while isinstance(current, dict):
        cid = current.get("header", {}).get("chunk_id") if isinstance(current.get("header"), dict) else None
        if cid in seen:
            break
        if cid is not None:
            seen.add(cid)
        chain.append(current)
        parent_id = current.get("parent_id")
        if parent_id in (None, -1, 0xFFFFFFFF):
            break
        current = all_nodes.get(parent_id)

    matrix = Matrix.Identity(4)
    for chain_node in reversed(chain):
        trans = chain_node.get("transform")
        if trans and len(trans) == 16:
            local_mat = Matrix(_read_matrix44(trans)).transposed()
            matrix = matrix @ local_mat
    return matrix


def _safe_uv_idx(idx: int, length: int) -> int:
    return idx if 0 <= idx < length else 0

def _is_collision_or_nodraw_node(node: Dict[str, Any], mat_info: Dict[str, Any]) -> bool:
    name = str(node.get("name", "")).strip()
    if name.startswith("$") or name.startswith("phys_") or name.startswith("collision_"):
        return True

    mat_name = str(mat_info.get("name", "")).lower()
    mat_shader = str(mat_info.get("shader", "")).lower()
    mat_template = str(mat_info.get("material_template", "")).lower()

    if "nodraw" in mat_name or "nodraw" in mat_shader or "mat_nodraw" in mat_template:
        return True

    diffuse = mat_info.get("texture_diffuse")
    has_diffuse = bool(isinstance(diffuse, dict) and (diffuse.get("name") or diffuse.get("long_name")))
    opacity = float(mat_info.get("opacity", 1.0) or 1.0)
    if not has_diffuse and opacity == 0.0:
        return True

    is_primitive_shape = any(name.lower().startswith(p) for p in ("box", "sphere", "cylinder", "capsule", "phys"))
    mtl_flag = mat_info.get("mtl_flag", {}) if isinstance(mat_info.get("mtl_flag"), dict) else {}
    if is_primitive_shape and (mtl_flag.get("physicalize") or mat_info.get("mtl_collide", 0.0) > 0) and not has_diffuse:
        return True

    return False


def detect_mesh_slot(model_path: str, category: str = "") -> str:
    """Classifies an asset into an equipment/body slot for mannequin dressing and replacement."""
    p_lower = model_path.lower().replace("\\", "/")
    fn = p_lower.split("/")[-1]

    # Weapons & Shields
    if "shield" in p_lower or fn.startswith("sh_"):
        return "weapon_sub"
    if category == "WEAPON" or any(k in p_lower for k in ("sword", "dagger", "spear", "mace", "staff", "bow", "gun", "harp", "polearm", "2h", "greatsword", "orb", "book", "cipherblade")):
        return "weapon_main"
    if category == "WINGS" or "wing" in p_lower:
        return "wings"

    # Headgear & Hair
    if "hair" in p_lower:
        return "hair"
    if any(k in p_lower for k in ("cap", "hat", "helm", "helmet", "_hd_", "mask", "glasses", "horn", "tiara", "crown")):
        return "head"

    # Armor slots
    if any(k in p_lower for k in ("body", "torso", "chest", "robe", "shirt", "tunic", "coat", "dress", "swimsuit")) or fn.endswith(("_body.cgf", "_torso.cgf")):
        return "torso"
    if any(k in p_lower for k in ("leg", "pants", "trouser", "skirt")) or fn.endswith(("_leg.cgf", "_pants.cgf")):
        return "legs"
    if any(k in p_lower for k in ("foot", "feet", "boot", "shoe")) or fn.endswith(("_foot.cgf", "_feet.cgf")):
        return "feet"
    if any(k in p_lower for k in ("hand", "glove", "gauntlet", "bracer")) or fn.endswith(("_hand.cgf", "_glove.cgf")):
        return "hands"
    if any(k in p_lower for k in ("shoulder", "pauldron")) or fn.endswith(("_shoulder.cgf",)):
        return "shoulders"

    return "misc"


class ModelProvider(IModelProvider):
    """High-level asset loader and serializer."""

    def __init__(self, client_provider: AionClientProvider):
        self.client_prov = client_provider
        self.tex_prov = TextureProvider(client_provider.catalog, client_provider.root, client_provider)
        self.mat_prov = MaterialProvider(self.tex_prov)
        self.skel_prov = SkeletonProvider()
        self.anim_prov = AnimationProvider()
        self.change_tracker = ChangeTracker.get()

    def load_model(
        self,
        entry: AssetEntry,
        target_collection: bpy.types.Collection,
        load_animation: bool = True,
        target_rig: Optional[bpy.types.Object] = None,
        slot_override: Optional[str] = None,
        replace_slot: bool = True,
    ) -> Optional[bpy.types.Object]:
        """Loads a model asset into Blender with meshes, materials, armature, and idle animation."""
        self.client_prov.ensure_category_paks_indexed(entry.model_path)
        cgf_bytes = self.client_prov.resolve_cgf_bytes(entry.model_path)
        if not cgf_bytes:
            return None

        # Determine equipment slot and remove existing piece in this slot to prevent overlapping
        slot = slot_override or detect_mesh_slot(entry.model_path, getattr(entry, "category", ""))
        if target_rig and replace_slot and slot != "misc":
            for child in list(target_rig.children):
                if child.type == "MESH" and child.get("aion_slot") == slot:
                    bpy.data.objects.remove(child, do_unlink=True)

        # Track baseline for change detection
        self.change_tracker.track(
            asset_id=entry.asset_id,
            asset_name=entry.name,
            source_rel_path=entry.model_path,
            original_bytes=cgf_bytes,
        )

        parsed_cgf = get_cgf(io.BytesIO(cgf_bytes))
        nodes = parsed_cgf.get("nodes", {})
        if not nodes:
            return None

        all_materials = parsed_cgf.get("all_materials", [])
        all_nodes = parsed_cgf.get("all_nodes") or parsed_cgf.get("nodes") or {}

        bone_names = parsed_cgf.get("bone_names", [])
        bone_initial_pos = parsed_cgf.get("bone_initial_pos", [])
        bone_anim = parsed_cgf.get("bone_anim", [])

        # 1. Build or reuse Armature
        rig_obj = target_rig
        if rig_obj is None and bone_names and bone_initial_pos:
            rig_obj = self.skel_prov.build_armature(
                name=entry.name,
                bone_names=bone_names,
                bone_initial_pos=bone_initial_pos,
                bone_anim=bone_anim,
                collection=target_collection,
            )
        elif rig_obj is not None and bone_names and hasattr(rig_obj, "data") and hasattr(rig_obj.data, "bones"):
            # Dynamically add any missing bones into target_rig
            missing_bones = [b for b in bone_names if b not in rig_obj.data.bones]
            if missing_bones:
                bpy.context.view_layer.objects.active = rig_obj
                bpy.ops.object.mode_set(mode="EDIT")
                for i, b_name in enumerate(bone_names):
                    if b_name not in rig_obj.data.edit_bones:
                        eb = rig_obj.data.edit_bones.new(b_name)
                        eb.use_deform = True
                        m = bone_initial_pos[i] if i < len(bone_initial_pos) else None
                        if m and len(m) >= 12:
                            rot_3x3 = Matrix((
                                (m[0], m[3], m[6]),
                                (m[1], m[4], m[7]),
                                (m[2], m[5], m[8]),
                            ))
                            pos = Vector((m[9] / 100.0, m[10] / 100.0, m[11] / 100.0))
                            mat = Matrix.Translation(pos) @ rot_3x3.to_4x4()
                        else:
                            mat = Matrix.Translation(Vector((0.0, 0.0, 1.5)))
                        eb.head = mat.translation
                        bone_dir = mat.to_3x3().col[1].normalized()
                        if bone_dir.length < 0.001:
                            bone_dir = Vector((0.0, 1.0, 0.0))
                        eb.tail = eb.head + bone_dir * 0.05
                        eb.matrix = mat
                        # Hierarchy attachment
                        if "hair" in b_name.lower() and "Bip01 Head" in rig_obj.data.edit_bones:
                            eb.parent = rig_obj.data.edit_bones["Bip01 Head"]
                        elif "wing" in b_name.lower() and "Bip01 Spine2" in rig_obj.data.edit_bones:
                            eb.parent = rig_obj.data.edit_bones["Bip01 Spine2"]
                bpy.ops.object.mode_set(mode="OBJECT")

        # 2. Build Meshes for each Node
        created_objects: List[bpy.types.Object] = []

        for nid, node_data in nodes.items():
            mesh_chunk = node_data.get("mesh")
            if not mesh_chunk:
                continue

            mat_info = node_data.get("material") if isinstance(node_data.get("material"), dict) else {}
            if _is_collision_or_nodraw_node(node_data, mat_info):
                continue

            node_name = node_data.get("name") or f"{entry.name}_Mesh"
            positions = mesh_chunk.get("vertices", {}).get("position", [])
            faces_v = mesh_chunk.get("faces", {}).get("v", [])
            faces_m = mesh_chunk.get("faces", {}).get("material", [])
            smoothing_groups = mesh_chunk.get("faces", {}).get("smoothing_group", [])

            if not positions or not faces_v:
                continue

            m_data = bpy.data.meshes.new(f"{node_name}_Mesh")
            m_data.from_pydata(positions, [], faces_v)

            # Assign Smoothing
            if smoothing_groups and len(smoothing_groups) == len(m_data.polygons):
                for blender_poly, sg in zip(m_data.polygons, smoothing_groups):
                    if sg != 0:
                        blender_poly.use_smooth = True
            else:
                for blender_poly in m_data.polygons:
                    blender_poly.use_smooth = True

            # Assign Material Slots & Polygon Material Indices
            mat_info = node_data.get("material") if isinstance(node_data.get("material"), dict) else {}
            is_multi = mat_info.get("mtl_type") == 2 or bool(mat_info.get("sub_materials"))
            use_mat_ids: List[int] = []
            mat_slot_by_id: Dict[int, int] = {}

            def slot_for(mat_id: int) -> int:
                slot = mat_slot_by_id.get(mat_id)
                if slot is None:
                    slot = len(use_mat_ids)
                    use_mat_ids.append(mat_id)
                    mat_slot_by_id[mat_id] = slot
                return slot

            if faces_m and len(faces_m) == len(m_data.polygons):
                for blender_poly, mat_id in zip(m_data.polygons, faces_m):
                    blender_poly.material_index = slot_for(mat_id)
            else:
                use_mat_ids = [0]

            # Assign UVs (direct u, v matching CryEngine & DDS coordinates)
            uvs_data = mesh_chunk.get("uvs", {}).get("uvs", [])
            uv_faces = mesh_chunk.get("uv_faces", {}).get("face_uvs", [])
            if uvs_data and m_data.polygons:
                uv_layer = m_data.uv_layers.new(name="UVMap")
                flat_uv = [0.0] * (len(m_data.loops) * 2)
                uv_len = len(uvs_data)

                if uv_faces and len(uv_faces) == len(m_data.polygons):
                    for uv_face, blender_poly in zip(uv_faces, m_data.polygons):
                        for face_uvidx, loop_index in zip(uv_face, blender_poly.loop_indices):
                            uv = uvs_data[_safe_uv_idx(face_uvidx, uv_len)]
                            base = loop_index * 2
                            flat_uv[base] = uv[0]
                            flat_uv[base + 1] = uv[1]
                else:
                    for blender_poly in m_data.polygons:
                        for loop_index in blender_poly.loop_indices:
                            vert_idx = m_data.loops[loop_index].vertex_index
                            if vert_idx < uv_len:
                                uv = uvs_data[vert_idx]
                                base = loop_index * 2
                                flat_uv[base] = uv[0]
                                flat_uv[base + 1] = uv[1]

                uv_layer.data.foreach_set("uv", flat_uv)

            m_data.update()
            mesh_obj = bpy.data.objects.new(node_name, m_data)
            mesh_obj["aion_slot"] = slot
            target_collection.objects.link(mesh_obj)
            created_objects.append(mesh_obj)

            # Assign Materials to slots
            if is_multi:
                sub_materials = mat_info.get("sub_materials", [])
                for mat_id in use_mat_ids:
                    m_dict = None
                    if 0 <= mat_id < len(all_materials):
                        m_dict = all_materials[mat_id]
                    elif 0 <= mat_id < len(sub_materials):
                        m_dict = sub_materials[mat_id]
                    else:
                        m_dict = mat_info

                    mat_name = m_dict.get("name") or f"{entry.name}_Mat_{mat_id}"
                    mat = self.mat_prov.create_material(
                        material_name=mat_name,
                        mtl_chunk=m_dict,
                        model_path=entry.model_path,
                    )
                    mesh_obj.data.materials.append(mat)
            elif mat_info:
                mat = self.mat_prov.create_material(
                    material_name=mat_info.get("name", f"{entry.name}_Material"),
                    mtl_chunk=mat_info,
                    model_path=entry.model_path,
                )
                mesh_obj.data.materials.append(mat)

            # Apply Node World Transform & Parenting
            node_mat = _composed_node_matrix(node_data, all_nodes)
            skin_weights = mesh_chunk.get("skin_weights", [])

            if rig_obj and skin_weights:
                self.skel_prov.apply_skin_weights(mesh_obj, bone_names, skin_weights, rig_obj)
                mesh_obj.parent = rig_obj
                mesh_obj.matrix_parent_inverse = rig_obj.matrix_world.inverted()
            elif rig_obj:
                # Unskinned mesh
                equip_bone = None
                is_dressing_room = (target_rig is not None)

                # 1. Check if node has explicit parent bone in CGF node hierarchy
                parent_id = node_data.get("parent_id")
                parent_node = all_nodes.get(parent_id) if parent_id not in (None, -1, 0xFFFFFFFF) else None
                if parent_node and parent_node.get("name") in rig_obj.data.bones:
                    equip_bone = parent_node.get("name")
                elif is_dressing_room:
                    # Equipment bone mapping only for dressing room equips
                    entry_cat = getattr(entry, "category", "")
                    entry_name_lower = (entry.name + " " + (entry.model_path or "")).lower()

                    if any(k in entry_name_lower for k in ("cap", "hat", "helm", "helmet", "_hd_", "mask", "glasses", "horn", "tiara", "crown")):
                        for candidate in ("Bip01 Head", "Head"):
                            if candidate in rig_obj.data.bones:
                                equip_bone = candidate
                                break
                    elif "shield" in entry_name_lower or "sh_" in entry_name_lower or slot == "weapon_sub":
                        for candidate in ("Lhand_bone", "Bip01 L Hand", "Shield", "Dummy_Shield"):
                            if candidate in rig_obj.data.bones:
                                equip_bone = candidate
                                break
                    elif entry_cat == "WEAPON" or slot == "weapon_main" or any(k in entry_name_lower for k in ("sword", "dagger", "spear", "mace", "staff", "bow", "gun", "harp", "wp_", "sw_", "da_", "ts_", "pa_", "st_", "ma_")):
                        for candidate in ("Rhand_bone", "Bip01 R Hand", "Weapon_R", "Dummy_Weapon_R"):
                            if candidate in rig_obj.data.bones:
                                equip_bone = candidate
                                break
                    elif entry_cat == "WINGS" or "wing" in entry_name_lower or slot == "wings":
                        for candidate in ("Bip01 Spine2", "Bip01 Spine1"):
                            if candidate in rig_obj.data.bones:
                                equip_bone = candidate
                                break

                mesh_obj.matrix_world = node_mat

                if equip_bone and equip_bone in rig_obj.pose.bones:
                    mesh_obj.parent = rig_obj
                    mesh_obj.parent_type = "BONE"
                    mesh_obj.parent_bone = equip_bone
                    if equip_bone in ("Rhand_bone", "Lhand_bone"):
                        # Osso de encaixe: a origem do item fica no referencial do osso (o Blender soma o comprimento do osso ao filho)
                        mesh_obj.matrix_parent_inverse = Matrix.Translation((0.0, -rig_obj.data.bones[equip_bone].length, 0.0))
                    else:
                        bone_mat_world = rig_obj.matrix_world @ rig_obj.pose.bones[equip_bone].matrix
                        mesh_obj.matrix_parent_inverse = bone_mat_world.inverted()
                else:
                    mesh_obj.parent = rig_obj
                    mesh_obj.matrix_parent_inverse = rig_obj.matrix_world.inverted()
            else:
                mesh_obj.matrix_world = node_mat

        # 3. Load Idle Animation if requested
        if rig_obj and load_animation and entry.model_path:
            cal_map, caf_bytes = self.client_prov.resolve_animation_asset(entry.model_path)
            if caf_bytes:
                action = self.anim_prov.load_animation(
                    rig_obj=rig_obj,
                    caf_bytes=caf_bytes,
                    action_name=f"{entry.name}_Idle",
                    bone_names=bone_names,
                    bone_anim=bone_anim,
                )
                if action:
                    start = int(action.frame_range[0])
                    end = int(action.frame_range[1])
                    from ..viewers.animation_player import AnimationPlayer
                    AnimationPlayer.set_frame_range(start, end)
                    AnimationPlayer.play()

        # Return root (Rig if present, otherwise first mesh)
        return rig_obj if rig_obj else (created_objects[0] if created_objects else None)

    def serialize_model(
        self,
        root_obj: bpy.types.Object,
        entry: AssetEntry,
    ) -> bytes:
        """Serializes current Blender mesh, materials, and armature state back to CGF bytes."""
        # Find mesh object and armature
        mesh_obj = None
        arm_obj = None

        if root_obj.type == "ARMATURE":
            arm_obj = root_obj
            for child in root_obj.children:
                if child.type == "MESH":
                    mesh_obj = child
                    break
        elif root_obj.type == "MESH":
            mesh_obj = root_obj
            if root_obj.parent and root_obj.parent.type == "ARMATURE":
                arm_obj = root_obj.parent

        if not mesh_obj:
            raise ValueError(f"No mesh object found to serialize for {entry.name}")

        mesh: bpy.types.Mesh = mesh_obj.data
        if hasattr(mesh, "calc_normals"):
            mesh.calc_normals()
        else:
            mesh.update()

        # Extract vertices (in Blender meters)
        vertices = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]
        normals = [(v.normal.x, v.normal.y, v.normal.z) for v in mesh.vertices]

        # Extract triangulated faces
        faces: List[Tuple[int, int, int]] = []
        for poly in mesh.polygons:
            if len(poly.vertices) == 3:
                faces.append(tuple(poly.vertices))
            elif len(poly.vertices) > 3:
                # Fan triangulation
                for i in range(1, len(poly.vertices) - 1):
                    faces.append((poly.vertices[0], poly.vertices[i], poly.vertices[i + 1]))

        # Extract UVs
        uvs: List[Tuple[float, float]] = []
        face_uvs: List[Tuple[int, int, int]] = []
        if mesh.uv_layers.active:
            uv_layer = mesh.uv_layers.active.data
            for poly in mesh.polygons:
                poly_uvs = []
                for loop_idx in poly.loop_indices:
                    uv_coord = uv_layer[loop_idx].uv
                    # Invert V back to CryEngine standard (1.0 - V)
                    u, v = uv_coord.x, 1.0 - uv_coord.y
                    uv_idx = len(uvs)
                    uvs.append((u, v))
                    poly_uvs.append(uv_idx)
                if len(poly_uvs) == 3:
                    face_uvs.append(tuple(poly_uvs))
                elif len(poly_uvs) > 3:
                    for i in range(1, len(poly_uvs) - 1):
                        face_uvs.append((poly_uvs[0], poly_uvs[i], poly_uvs[i + 1]))

        # Extract Skin Weights
        skin_weights: Optional[List[List[Tuple[int, float]]]] = None
        new_bone_names = None
        new_bone_initial_pos = None
        new_bone_anim = None

        if arm_obj:
            b_names, b_pos, b_anim = self.skel_prov.extract_armature(arm_obj)
            new_bone_names = b_names
            new_bone_initial_pos = b_pos
            new_bone_anim = b_anim

            # Map vertex groups to bone indices
            vg_to_bone: Dict[int, int] = {}
            for vg in mesh_obj.vertex_groups:
                if vg.name in b_names:
                    vg_to_bone[vg.index] = b_names.index(vg.name)

            skin_weights = []
            for v in mesh.vertices:
                links = []
                for g in v.groups:
                    if g.group in vg_to_bone and g.weight > 0.0001:
                        links.append((vg_to_bone[g.group], float(g.weight)))
                skin_weights.append(links)

        # Check if original bytes exist in change tracker for non-destructive patching
        tracked = self.change_tracker.get_tracked(entry.asset_id)
        orig_bytes = None
        if tracked:
            cgf_ref = entry.model_path
            orig_bytes = self.client_prov.resolve_cgf_bytes(cgf_ref)

        if orig_bytes:
            # Non-destructively patch existing CGF
            return patch_cgf(
                original_cgf_bytes=orig_bytes,
                new_vertices=vertices,
                new_normals=normals,
                new_faces=faces,
                new_uvs=uvs,
                new_face_uvs=face_uvs if face_uvs else None,
                new_skin_weights=skin_weights,
                new_bone_names=new_bone_names,
                new_bone_initial_pos=new_bone_initial_pos,
                new_bone_anim=new_bone_anim,
            )
        else:
            # Build new CGF from scratch
            return write_cgf(
                vertices=vertices,
                normals=normals,
                faces=faces,
                uvs=uvs,
                face_uvs=face_uvs if face_uvs else None,
                node_name=entry.name,
                material_name=f"{entry.name}_Mat",
                bone_names=new_bone_names,
                bone_initial_pos=new_bone_initial_pos,
                bone_anim=new_bone_anim,
                skin_weights=skin_weights,
            )
