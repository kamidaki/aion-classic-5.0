"""
Model Creator for LostAcademy Aion Model Library.
Creates brand new Aion-compatible CGF models from arbitrary selected Blender geometry
with UVs, materials, and optional skeletal rigging.
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import Optional, Tuple

import bpy
from ..formats.cgf.writer import write_cgf
from ..indexer.asset_entry import AssetEntry
from ..indexer.asset_database import AssetDatabase
from ..core.transaction_manager import TransactionManager, TransactionResult


class ModelCreator:
    """Creates new Aion CGF assets from Blender scene objects."""

    @staticmethod
    def create_model_from_selected(
        obj: bpy.types.Object,
        asset_name: str,
        category: str = "OBJECT",
        target_relative_path: str = "",
        client_root: Optional[Path] = None,
        allow_client_write: bool = False,
    ) -> Tuple[Optional[AssetEntry], TransactionResult]:
        """
        Converts the active Blender mesh into an Aion CGF asset and registers it in the library.
        """
        if not obj or obj.type != "MESH":
            return None, TransactionResult(False, "Selected object is not a valid Mesh.")

        mesh: bpy.types.Mesh = obj.data
        if hasattr(mesh, "calc_normals"):
            mesh.calc_normals()
        else:
            mesh.update()

        # 1. Extract vertices, normals, faces
        vertices = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]
        normals = [(v.normal.x, v.normal.y, v.normal.z) for v in mesh.vertices]

        faces = []
        for p in mesh.polygons:
            if len(p.vertices) == 3:
                faces.append(tuple(p.vertices))
            elif len(p.vertices) > 3:
                for i in range(1, len(p.vertices) - 1):
                    faces.append((p.vertices[0], p.vertices[i], p.vertices[i + 1]))

        # 2. Extract UVs
        uvs = []
        face_uvs = []
        if mesh.uv_layers.active:
            uv_layer = mesh.uv_layers.active.data
            for p in mesh.polygons:
                p_uvs = []
                for loop_idx in p.loop_indices:
                    uv = uv_layer[loop_idx].uv
                    uv_idx = len(uvs)
                    uvs.append((uv.x, 1.0 - uv.y))
                    p_uvs.append(uv_idx)
                if len(p_uvs) == 3:
                    face_uvs.append(tuple(p_uvs))
                elif len(p_uvs) > 3:
                    for i in range(1, len(p_uvs) - 1):
                        face_uvs.append((p_uvs[0], p_uvs[i], p_uvs[i + 1]))
        else:
            # Fallback zero UVs
            uvs = [(0.0, 0.0)] * len(vertices)
            face_uvs = faces

        # 3. Handle Armature if parented
        bone_names = None
        bone_pos = None
        bone_anim = None
        skin_weights = None

        if obj.parent and obj.parent.type == "ARMATURE":
            arm: bpy.types.Armature = obj.parent.data
            bone_names = [b.name for b in arm.bones]
            bone_pos = []
            bone_anim = []
            for idx, b in enumerate(arm.bones):
                m = b.matrix_local
                mat_12 = (
                    m[0][0], m[0][1], m[0][2],
                    m[1][0], m[1][1], m[1][2],
                    m[2][0], m[2][1], m[2][2],
                    b.head_local.x * 100.0,
                    b.head_local.y * 100.0,
                    b.head_local.z * 100.0,
                )
                bone_pos.append(mat_12)
                pid = bone_names.index(b.parent.name) if b.parent and b.parent.name in bone_names else -1
                bone_anim.append({
                    "bone_id": idx,
                    "parent_id": pid,
                    "num_children": len(b.children),
                    "ctrl_id": abs(hash(b.name)) % 0xFFFFFFFF,
                })

            vg_map = {vg.name: vg.index for vg in obj.vertex_groups}
            skin_weights = []
            for v in mesh.vertices:
                links = []
                for g in v.groups:
                    for b_idx, b_name in enumerate(bone_names):
                        if vg_map.get(b_name) == g.group and g.weight > 0.001:
                            links.append((b_idx, float(g.weight)))
                skin_weights.append(links)

        # 4. Generate CGF Binary
        clean_name = asset_name.strip() or "Custom_Model"
        clean_slug = clean_name.lower().replace(" ", "_")
        if not target_relative_path:
            cat_folder = category.lower()
            target_relative_path = f"objects/{cat_folder}/{clean_slug}/{clean_slug}.cgf"

        cgf_bytes = write_cgf(
            vertices=vertices,
            normals=normals,
            faces=faces,
            uvs=uvs,
            face_uvs=face_uvs if face_uvs else None,
            node_name=clean_slug,
            material_name=f"{clean_slug}_mat",
            bone_names=bone_names,
            bone_initial_pos=bone_pos,
            bone_anim=bone_anim,
            skin_weights=skin_weights,
        )

        # 5. Create AssetEntry
        asset_id = f"custom_{int(time.time())}"
        entry = AssetEntry(
            asset_id=asset_id,
            name=clean_name,
            category=category,
            model_path=target_relative_path,
            has_skeleton=bool(bone_names),
            bone_count=len(bone_names) if bone_names else 0,
            skeleton_path=target_relative_path if bone_names else None,
            vertex_count=len(vertices),
            triangle_count=len(faces),
            file_size=len(cgf_bytes),
            is_loose=True,
        )

        # 6. Save via TransactionManager
        tx_result = TransactionResult(True, "Created in memory.")
        if client_root:
            tx_result = TransactionManager.save_assets(
                client_root=client_root,
                asset_updates={target_relative_path: cgf_bytes},
                allow_client_write=allow_client_write,
            )

        # Register in AssetDatabase
        AssetDatabase.get().add_entry(entry)

        return entry, tx_result
