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
    ) -> Optional[bpy.types.Object]:
        """Loads a model asset into Blender with meshes, materials, armature, and idle animation."""
        self.client_prov.ensure_category_paks_indexed(entry.model_path)
        cgf_bytes = self.client_prov.resolve_cgf_bytes(entry.model_path)
        if not cgf_bytes:
            return None

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
                            head_pos = Vector((m[9] / 100.0, m[10] / 100.0, m[11] / 100.0))
                        else:
                            head_pos = Vector((0.0, 0.0, 1.5))
                        eb.head = head_pos
                        eb.tail = head_pos + Vector((0.0, 0.0, 0.04))
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
                    )
                    mesh_obj.data.materials.append(mat)
            elif mat_info:
                mat = self.mat_prov.create_material(
                    material_name=mat_info.get("name", f"{entry.name}_Material"),
                    mtl_chunk=mat_info,
                )
                mesh_obj.data.materials.append(mat)

            # Apply Node World Transform & Parenting
            node_mat = _composed_node_matrix(node_data, all_nodes)
            skin_weights = mesh_chunk.get("skin_weights", [])

            if rig_obj and skin_weights:
                self.skel_prov.apply_skin_weights(mesh_obj, bone_names, skin_weights, rig_obj)
                mesh_obj.parent = rig_obj
                mesh_obj.matrix_parent_inverse = rig_obj.matrix_world.inverted()
            else:
                mesh_obj.matrix_world = node_mat
                if rig_obj:
                    equip_bone = None
                    entry_cat = getattr(entry, "category", "")
                    entry_name_lower = (entry.name + " " + (entry.model_path or "")).lower()
                    if "shield" in entry_name_lower or "sh_" in entry_name_lower:
                        for candidate in ("Bip01 L Hand", "Shield", "Dummy_Shield", "bip01 l hand"):
                            if hasattr(rig_obj, "data") and candidate in rig_obj.data.bones:
                                equip_bone = candidate
                                break
                    elif entry_cat == "WEAPON" or any(k in entry_name_lower for k in ("sword", "dagger", "spear", "mace", "staff", "bow", "gun", "harp", "wp_", "sw_", "da_", "ts_", "pa_", "st_", "ma_")):
                        for candidate in ("Bip01 R Hand", "Weapon_R", "Dummy_Weapon_R", "bip01 r hand"):
                            if hasattr(rig_obj, "data") and candidate in rig_obj.data.bones:
                                equip_bone = candidate
                                break
                    elif entry_cat == "WINGS" or "wing" in entry_name_lower:
                        for candidate in ("Bip01 Spine2", "Bip01 Spine1", "bip01 spine2"):
                            if hasattr(rig_obj, "data") and candidate in rig_obj.data.bones:
                                equip_bone = candidate
                                break

                    if equip_bone:
                        mesh_obj.parent = rig_obj
                        mesh_obj.parent_type = "BONE"
                        mesh_obj.parent_bone = equip_bone
                    else:
                        mesh_obj.parent = rig_obj
                        mesh_obj.matrix_parent_inverse = rig_obj.matrix_world.inverted()

        # 3. Load Idle Animation if requested
        if rig_obj and load_animation and entry.model_path:
            cal_map, caf_bytes = self.client_prov.resolve_animation_asset(entry.model_path)
            if caf_bytes:
                self.anim_prov.load_animation(
                    rig_obj=rig_obj,
                    caf_bytes=caf_bytes,
                    action_name=f"{entry.name}_Idle",
                    bone_names=bone_names,
                    bone_anim=bone_anim,
                )

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
