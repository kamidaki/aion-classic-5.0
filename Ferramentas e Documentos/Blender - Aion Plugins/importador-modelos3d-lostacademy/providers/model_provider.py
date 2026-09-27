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


class ModelProvider(IModelProvider):
    """High-level asset loader and serializer."""

    def __init__(self, client_provider: AionClientProvider):
        self.client_prov = client_provider
        self.tex_prov = TextureProvider(client_provider.catalog, client_provider.root)
        self.mat_prov = MaterialProvider(self.tex_prov)
        self.skel_prov = SkeletonProvider()
        self.anim_prov = AnimationProvider()
        self.change_tracker = ChangeTracker.get()

    def load_model(
        self,
        entry: AssetEntry,
        target_collection: bpy.types.Collection,
        load_animation: bool = True,
    ) -> Optional[bpy.types.Object]:
        """Loads a model asset into Blender with meshes, materials, armature, and idle animation."""
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

        bone_names = parsed_cgf.get("bone_names", [])
        bone_initial_pos = parsed_cgf.get("bone_initial_pos", [])
        bone_anim = parsed_cgf.get("bone_anim", [])

        # 1. Build Armature if skeleton is present
        rig_obj = None
        if bone_names and bone_initial_pos:
            rig_obj = self.skel_prov.build_armature(
                name=entry.name,
                bone_names=bone_names,
                bone_initial_pos=bone_initial_pos,
                bone_anim=bone_anim,
                collection=target_collection,
            )

        # 2. Build Meshes for each Node
        created_objects: List[bpy.types.Object] = []

        for nid, node_data in nodes.items():
            mesh_chunk = node_data.get("mesh")
            if not mesh_chunk:
                continue

            node_name = node_data.get("name") or f"{entry.name}_Mesh"
            positions = mesh_chunk.get("vertices", {}).get("position", [])
            faces_v = mesh_chunk.get("faces", {}).get("v", [])

            if not positions or not faces_v:
                continue

            m_data = bpy.data.meshes.new(f"{node_name}_Mesh")
            m_data.from_pydata(positions, [], faces_v)
            m_data.update()

            # Assign UVs
            uvs_data = mesh_chunk.get("uvs", {}).get("uvs", [])
            uv_faces = mesh_chunk.get("uv_faces", {}).get("face_uvs", [])
            if uvs_data and m_data.polygons:
                uv_layer = m_data.uv_layers.new(name="UVMap")
                for poly_idx, poly in enumerate(m_data.polygons):
                    for loop_idx in poly.loop_indices:
                        vert_idx = m_data.loops[loop_idx].vertex_index
                        if uv_faces and poly_idx < len(uv_faces):
                            # CryEngine Face UV mapping
                            corner_i = list(poly.vertices).index(vert_idx)
                            uv_idx = uv_faces[poly_idx][corner_i]
                            if uv_idx < len(uvs_data):
                                u, v = uvs_data[uv_idx]
                                uv_layer.data[loop_idx].uv = (u, 1.0 - v)
                        elif vert_idx < len(uvs_data):
                            u, v = uvs_data[vert_idx]
                            uv_layer.data[loop_idx].uv = (u, 1.0 - v)

            mesh_obj = bpy.data.objects.new(node_name, m_data)
            target_collection.objects.link(mesh_obj)
            created_objects.append(mesh_obj)

            # Assign Materials
            mtl_chunk = node_data.get("material")
            if mtl_chunk:
                mat = self.mat_prov.create_material(
                    material_name=mtl_chunk.get("name", "Aion_Material"),
                    mtl_chunk=mtl_chunk,
                )
                mesh_obj.data.materials.append(mat)

            # Bind Skin Weights & Armature Modifier
            skin_weights = mesh_chunk.get("skin_weights", [])
            if rig_obj and skin_weights:
                self.skel_prov.apply_skin_weights(mesh_obj, bone_names, skin_weights, rig_obj)
                mesh_obj.parent = rig_obj

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
