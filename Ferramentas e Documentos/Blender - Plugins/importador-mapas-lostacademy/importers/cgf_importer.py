"""
CGF Mesh Importer for Aion Blender Toolkit.
Constructs meshes, assigns materials with full shader/texture semantics, and handles animations.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bpy
from mathutils import Matrix

from animations.cga_animator import apply_cga_controller_animation
from formats.cgf.parser import get_cgf
from materials.material_manager import get_or_create_aion_material


@dataclass(frozen=True)
class CgfImportReport:
    filepath: str
    import_mode: str
    result: str
    reason_code: Optional[str]
    reason: Optional[str]
    file_exists: bool
    parser_node_count: int
    parser_mesh_node_count: int
    parser_material_count: int
    candidate_mesh_node_count: int
    objects_created: int
    parser_coverage_counts: dict
    unsupported_chunks: dict
    unused_material_fields: dict
    texture_sequences_requested: bool = False
    texture_sequences_applied: int = 0
    texture_sequences_skipped: int = 0
    texture_sequence_missing_frames: int = 0
    shader_uv_scroll_requested: bool = False
    shader_uv_scroll_applied: int = 0
    shader_uv_scroll_skipped: int = 0
    source_extension: str = ""
    cga_static_import: bool = False
    cga_controller_count: int = 0
    cga_timing_present: bool = False
    cga_animation_status: str = ""
    cga_controller_animation_requested: bool = False
    cga_controller_animations_applied: int = 0


_LAST_IMPORT_REPORT: Optional[CgfImportReport] = None


def get_last_import_report() -> Optional[CgfImportReport]:
    return _LAST_IMPORT_REPORT


def read_matrix44(matrix_values):
    return (
        tuple(matrix_values[0:4]),
        tuple(matrix_values[4:8]),
        tuple(matrix_values[8:12]),
        (
            matrix_values[12] / 100,
            matrix_values[13] / 100,
            matrix_values[14] / 100,
            matrix_values[15],
        ),
    )


def _composed_node_matrix(node, all_nodes):
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
            local_mat = Matrix(read_matrix44(trans)).transposed()
            matrix = matrix @ local_mat
    return matrix


def _safe_uv_idx(idx: int, length: int) -> int:
    return idx if 0 <= idx < length else 0


def _is_collision_or_nodraw_node(node: Dict[str, Any], mat_info: Dict[str, Any]) -> bool:
    name = str(node.get("name", "")).strip()
    if name.startswith("$"):
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


def create_mesh_from_node(
    node: Dict[str, Any],
    materials: List[Dict[str, Any]],
    aion_path: str,
    mat_info: Dict[str, Any],
    *,
    client_root: Optional[str] = None,
    import_mode: str = "VISUAL",
    apply_smoothing_groups: bool = True,
    animate_texture_sequences: bool = True,
    texture_animation_fps: int = 10,
    animate_shader_uv_scroll: bool = True,
    optimize_material_preview: bool = True,
) -> Optional[bpy.types.Object]:
    mesh_chunk = node.get("mesh")
    if not mesh_chunk:
        return None

    if import_mode == "VISUAL" and _is_collision_or_nodraw_node(node, mat_info):
        return None

    verts_loc = mesh_chunk.get("vertices", {}).get("position", [])
    verts_tex = mesh_chunk.get("uvs", {}).get("uvs", [])
    faces = mesh_chunk.get("faces", {}).get("v", [])
    faces_m = mesh_chunk.get("faces", {}).get("material", [])
    smoothing_groups = mesh_chunk.get("faces", {}).get("smoothing_group", [])
    uv_faces = mesh_chunk.get("uv_faces", {}).get("face_uvs", [])

    if not verts_loc or not faces:
        return None

    is_multi = mat_info.get("mtl_type") == 2
    mesh_name = node.get("name", "AionMesh")
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(verts_loc, [], faces)

    if verts_tex and mesh.polygons:
        mesh.uv_layers.new()

    use_mat_ids = []
    mat_slot_by_id = {}

    def slot_for(mat_id):
        slot = mat_slot_by_id.get(mat_id)
        if slot is None:
            slot = len(use_mat_ids)
            use_mat_ids.append(mat_id)
            mat_slot_by_id[mat_id] = slot
        return slot

    for blender_poly, mat_id in zip(mesh.polygons, faces_m):
        blender_poly.material_index = slot_for(mat_id)

    if apply_smoothing_groups:
        for blender_poly, sg in zip(mesh.polygons, smoothing_groups):
            if sg != 0:
                blender_poly.use_smooth = True

    if verts_tex and uv_faces and mesh.uv_layers.active:
        uv_layer = mesh.uv_layers.active
        flat_uv = [0.0] * (len(mesh.loops) * 2)
        uv_len = len(verts_tex)

        for uv_face, blender_poly in zip(uv_faces, mesh.polygons):
            for face_uvidx, loop_index in zip(uv_face, blender_poly.loop_indices):
                uv = verts_tex[_safe_uv_idx(face_uvidx, uv_len)]
                base = loop_index * 2
                flat_uv[base] = uv[0]
                flat_uv[base + 1] = uv[1]

        uv_layer.data.foreach_set("uv", flat_uv)

    # Assign materials via Material Manager
    if mat_info.get("mtl_type") == 1:
        mat = get_or_create_aion_material(
            mat_info,
            aion_path,
            client_root=client_root,
            animate_texture_sequences=animate_texture_sequences,
            texture_animation_fps=texture_animation_fps,
            animate_shader_uv_scroll=animate_shader_uv_scroll,
            optimize_material_preview=optimize_material_preview,
        )
        mesh.materials.append(mat)
    elif is_multi:
        for mat_id in use_mat_ids:
            m_dict = materials[mat_id] if 0 <= mat_id < len(materials) else mat_info
            mat = get_or_create_aion_material(
                m_dict,
                aion_path,
                client_root=client_root,
                animate_texture_sequences=animate_texture_sequences,
                texture_animation_fps=texture_animation_fps,
                animate_shader_uv_scroll=animate_shader_uv_scroll,
                optimize_material_preview=optimize_material_preview,
            )
            mesh.materials.append(mat)

    mesh.update(calc_edges=False)
    obj = bpy.data.objects.new(mesh.name, mesh)
    return obj


def load(
    context,
    filepath: str | Path,
    import_mode: str = "VISUAL",
    apply_smoothing_groups: bool = True,
    animate_texture_sequences: bool = True,
    texture_animation_fps: int = 10,
    animate_shader_uv_scroll: bool = True,
    animate_cga_controllers: bool = True,
    client_root: Optional[str] = None,
    optimize_material_preview: bool = True,
) -> dict:
    global _LAST_IMPORT_REPORT
    path = Path(filepath)
    if not path.is_file():
        return {"CANCELLED"}

    file_name = path.name
    aion_path = str(path.parent)

    try:
        with open(path, "rb") as f:
            cgf_file = get_cgf(f, diagnostics=True, file_path=str(path))
    except Exception as exc:
        _LAST_IMPORT_REPORT = CgfImportReport(
            filepath=str(path),
            import_mode=import_mode,
            result="ERROR",
            reason_code="parse_exception",
            reason=str(exc),
            file_exists=True,
            parser_node_count=0,
            parser_mesh_node_count=0,
            parser_material_count=0,
            candidate_mesh_node_count=0,
            objects_created=0,
            parser_coverage_counts={},
            unsupported_chunks={},
            unused_material_fields={},
        )
        return {"CANCELLED"}

    if not isinstance(cgf_file, dict) or cgf_file.get("error"):
        return {"CANCELLED"}

    materials = cgf_file.get("all_materials", [])
    nodes = tuple((cgf_file.get("nodes") or {}).values())
    all_nodes = cgf_file.get("all_nodes") or cgf_file.get("nodes") or {}

    root_col = context.scene.collection
    cgf_col = bpy.data.collections.new(name=file_name)
    objects_created = 0

    for node in nodes:
        mesh_chunk = node.get("mesh")
        if not mesh_chunk:
            continue

        mat_info = node.get("material") if isinstance(node.get("material"), dict) else {}
        obj = create_mesh_from_node(
            node,
            materials,
            str(path),
            mat_info,
            client_root=client_root,
            import_mode=import_mode,
            apply_smoothing_groups=apply_smoothing_groups,
            animate_texture_sequences=animate_texture_sequences,
            texture_animation_fps=texture_animation_fps,
            animate_shader_uv_scroll=animate_shader_uv_scroll,
            optimize_material_preview=optimize_material_preview,
        )
        if obj is None:
            continue

        obj.matrix_world = _composed_node_matrix(node, all_nodes)
        if animate_cga_controllers:
            apply_cga_controller_animation(obj, node, cgf_file, enabled=True)

        cgf_col.objects.link(obj)
        objects_created += 1

    if objects_created > 0:
        root_col.children.link(cgf_col)
        return {"FINISHED"}
    else:
        bpy.data.collections.remove(cgf_col)
        return {"CANCELLED"}
