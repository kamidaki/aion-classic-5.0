"""
CGF Mesh Importer for Aion Blender Toolkit.
Constructs meshes, assigns materials with full shader/texture semantics, and handles animations.
"""

from __future__ import annotations

from array import array
import math
import os
import threading
import time
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
    simple_shaders: bool = False,
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

    num_polys = len(mesh.polygons)
    if faces_m and num_polys > 0:
        if len(faces_m) >= num_polys:
            poly_mat_indices = [slot_for(mat_id) for mat_id in faces_m[:num_polys]]
        else:
            poly_mat_indices = [slot_for(mat_id) for mat_id in faces_m] + [0] * (num_polys - len(faces_m))
        mesh.polygons.foreach_set("material_index", poly_mat_indices)

    if apply_smoothing_groups and smoothing_groups and num_polys > 0:
        if len(smoothing_groups) >= num_polys:
            smooth_flags = [sg != 0 for sg in smoothing_groups[:num_polys]]
        else:
            smooth_flags = [sg != 0 for sg in smoothing_groups] + [False] * (num_polys - len(smoothing_groups))
        mesh.polygons.foreach_set("use_smooth", smooth_flags)

    if verts_tex and uv_faces and mesh.uv_layers.active:
        uv_layer = mesh.uv_layers.active
        flat_uv = array("f", [0.0]) * (len(mesh.loops) * 2)
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
            simple_shaders=simple_shaders,
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
                simple_shaders=simple_shaders,
            )
            mesh.materials.append(mat)

    mesh.update(calc_edges=False)
    obj = bpy.data.objects.new(mesh.name, mesh)
    return obj


def prewarm_cgf_and_textures(
    filepath: str | Path,
    *,
    client_root: Optional[str] = None,
    simple_shaders: bool = False,
    cancel_event: Optional[threading.Event] = None,
) -> Optional[dict]:
    """
    Pure-Python background worker helper:
    parses CGF binary geometry/materials and pre-extracts required DDS textures from PAKs to disk cache
    without touching bpy.*, eliminating main-thread I/O spikes during template creation.
    """
    if cancel_event is not None and cancel_event.is_set():
        return None
    path = Path(filepath)
    if not path.is_file():
        return None
    try:
        with open(path, "rb") as f:
            cgf_file = get_cgf(f, diagnostics=True, file_path=str(path))
    except Exception:
        return None

    if not isinstance(cgf_file, dict) or cgf_file.get("error"):
        return cgf_file

    if client_root and not (cancel_event is not None and cancel_event.is_set()):
        try:
            from core.pak_engine import get_pak_resolver
            resolver = get_pak_resolver(client_root)
            if resolver:
                slots = ("texture_diffuse", "texture_opacity") if simple_shaders else (
                    "texture_diffuse",
                    "texture_opacity",
                    "texture_bump",
                    "texture_gloss",
                    "texture_filter",
                )
                seen_refs = set()
                candidate_mats = list(cgf_file.get("all_materials", []))
                for n_data in (cgf_file.get("nodes") or {}).values():
                    if isinstance(n_data, dict) and isinstance(n_data.get("material"), dict):
                        candidate_mats.append(n_data["material"])
                for m_dict in candidate_mats:
                    if cancel_event is not None and cancel_event.is_set():
                        return None
                    if not isinstance(m_dict, dict):
                        continue
                    for slot_key in slots:
                        t_info = m_dict.get(slot_key)
                        if not isinstance(t_info, dict):
                            continue
                        for k in ("long_name", "name"):
                            raw = str(t_info.get(k) or "").strip().strip("\x00")
                            if raw and raw not in seen_refs:
                                if cancel_event is not None and cancel_event.is_set():
                                    return None
                                seen_refs.add(raw)
                                resolver.resolve_resource(raw)
        except Exception:
            pass

    return cgf_file


def _record_report(
    *,
    filepath: str,
    import_mode: str,
    result: str,
    reason_code: Optional[str],
    reason: Optional[str],
    file_exists: bool,
    parser_node_count: int = 0,
    parser_mesh_node_count: int = 0,
    parser_material_count: int = 0,
    candidate_mesh_node_count: int = 0,
    objects_created: int = 0,
    diag: Optional[dict] = None,
) -> CgfImportReport:
    global _LAST_IMPORT_REPORT
    diag = diag if isinstance(diag, dict) else {}
    report = CgfImportReport(
        filepath=filepath,
        import_mode=import_mode,
        result=result,
        reason_code=reason_code,
        reason=reason,
        file_exists=file_exists,
        parser_node_count=parser_node_count,
        parser_mesh_node_count=parser_mesh_node_count,
        parser_material_count=parser_material_count,
        candidate_mesh_node_count=candidate_mesh_node_count,
        objects_created=objects_created,
        parser_coverage_counts=dict(diag.get("coverage_counts") or {}),
        unsupported_chunks=dict(diag.get("unsupported_chunks") or {}),
        unused_material_fields=dict(diag.get("unused_material_fields") or {}),
    )
    _LAST_IMPORT_REPORT = report
    return report


def iter_load_cgf(
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
    simple_shaders: bool = False,
    preparsed_cgf: Optional[dict] = None,
    target_collection: Optional[bpy.types.Collection] = None,
    link_to_scene: bool = True,
    time_slice_s: float = 0.008,
    cancel_event: Optional[threading.Event] = None,
):
    """
    Time-sliced generator loader for CGF/CGA files.
    Yields `(node_idx, total_nodes)` when building multi-part meshes exceeds `time_slice_s`.
    Always sets `_LAST_IMPORT_REPORT` cleanly and returns `(status_set, collection_or_None)`.
    """
    path = Path(filepath)
    if not path.is_file():
        _record_report(
            filepath=str(path),
            import_mode=import_mode,
            result="CANCELLED",
            reason_code="file_missing",
            reason=f"CGF file not found: {path}",
            file_exists=False,
        )
        return {"CANCELLED"}, None

    if cancel_event is not None and cancel_event.is_set():
        _record_report(
            filepath=str(path),
            import_mode=import_mode,
            result="CANCELLED",
            reason_code="cancelled",
            reason="Cancelled by user",
            file_exists=True,
        )
        return {"CANCELLED"}, None

    file_name = path.name

    if preparsed_cgf is not None:
        cgf_file = preparsed_cgf
    else:
        try:
            with open(path, "rb") as f:
                cgf_file = get_cgf(f, diagnostics=True, file_path=str(path))
        except Exception as exc:
            _record_report(
                filepath=str(path),
                import_mode=import_mode,
                result="ERROR",
                reason_code="parse_exception",
                reason=str(exc),
                file_exists=True,
            )
            return {"CANCELLED"}, None

    if not isinstance(cgf_file, dict) or cgf_file.get("error"):
        err_msg = str(cgf_file.get("error") if isinstance(cgf_file, dict) else "Invalid CGF data")
        _record_report(
            filepath=str(path),
            import_mode=import_mode,
            result="ERROR",
            reason_code="parse_error",
            reason=err_msg,
            file_exists=True,
        )
        return {"CANCELLED"}, None

    materials = cgf_file.get("all_materials", [])
    nodes = tuple((cgf_file.get("nodes") or {}).values())
    all_nodes = cgf_file.get("all_nodes") or cgf_file.get("nodes") or {}
    diag = cgf_file.get("diagnostics") if isinstance(cgf_file.get("diagnostics"), dict) else {}

    parser_node_count = len(all_nodes)
    parser_mesh_node_count = sum(1 for n in nodes if isinstance(n, dict) and n.get("mesh"))
    parser_material_count = len(materials)
    candidate_mesh_nodes = 0
    filtered_by_mode = 0

    own_col = target_collection is None
    cgf_col = target_collection if target_collection is not None else bpy.data.collections.new(name=file_name)
    objects_created = 0
    total_nodes = len(nodes)
    slice_start = time.perf_counter()

    def _cleanup_cancelled():
        if own_col and cgf_col.name in bpy.data.collections:
            for o in list(cgf_col.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(cgf_col)
        _record_report(
            filepath=str(path),
            import_mode=import_mode,
            result="CANCELLED",
            reason_code="cancelled",
            reason="Cancelled by user",
            file_exists=True,
            parser_node_count=parser_node_count,
            parser_mesh_node_count=parser_mesh_node_count,
            parser_material_count=parser_material_count,
            candidate_mesh_node_count=candidate_mesh_nodes,
            objects_created=0,
            diag=diag,
        )
        return {"CANCELLED"}, None

    for idx_n, node in enumerate(nodes, start=1):
        if cancel_event is not None and cancel_event.is_set():
            return _cleanup_cancelled()

        mesh_chunk = node.get("mesh") if isinstance(node, dict) else None
        if not mesh_chunk:
            continue

        mat_info = node.get("material") if isinstance(node.get("material"), dict) else {}
        verts_loc = mesh_chunk.get("vertices", {}).get("position", [])
        faces = mesh_chunk.get("faces", {}).get("v", [])
        if verts_loc and faces:
            if import_mode == "VISUAL" and _is_collision_or_nodraw_node(node, mat_info):
                filtered_by_mode += 1
                continue
            candidate_mesh_nodes += 1

        if mat_info.get("mtl_type") == 2 and faces:
            faces_m = mesh_chunk.get("faces", {}).get("material", [])
            if faces_m:
                seen_mat_ids = set()
                for mat_id in faces_m[:len(faces)]:
                    if mat_id in seen_mat_ids:
                        continue
                    seen_mat_ids.add(mat_id)
                    if cancel_event is not None and cancel_event.is_set():
                        return _cleanup_cancelled()
                    m_dict = materials[mat_id] if 0 <= mat_id < len(materials) else mat_info
                    get_or_create_aion_material(
                        m_dict,
                        str(path),
                        client_root=client_root,
                        animate_texture_sequences=animate_texture_sequences,
                        texture_animation_fps=texture_animation_fps,
                        animate_shader_uv_scroll=animate_shader_uv_scroll,
                        optimize_material_preview=optimize_material_preview,
                        simple_shaders=simple_shaders,
                    )
                    if (time.perf_counter() - slice_start) >= time_slice_s:
                        yield idx_n, total_nodes
                        slice_start = time.perf_counter()

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
            simple_shaders=simple_shaders,
        )
        if obj is None:
            continue

        obj.matrix_world = _composed_node_matrix(node, all_nodes)
        if animate_cga_controllers:
            apply_cga_controller_animation(obj, node, cgf_file, enabled=True)

        cgf_col.objects.link(obj)
        objects_created += 1

        if idx_n < total_nodes and (time.perf_counter() - slice_start) >= time_slice_s:
            yield idx_n, total_nodes
            slice_start = time.perf_counter()

    if objects_created > 0:
        if link_to_scene and own_col:
            root_col = context.scene.collection
            if cgf_col.name not in root_col.children.keys():
                root_col.children.link(cgf_col)
        _record_report(
            filepath=str(path),
            import_mode=import_mode,
            result="FINISHED",
            reason_code=None,
            reason=None,
            file_exists=True,
            parser_node_count=parser_node_count,
            parser_mesh_node_count=parser_mesh_node_count,
            parser_material_count=parser_material_count,
            candidate_mesh_node_count=candidate_mesh_nodes,
            objects_created=objects_created,
            diag=diag,
        )
        return {"FINISHED"}, cgf_col

    if own_col and cgf_col.name in bpy.data.collections:
        bpy.data.collections.remove(cgf_col)

    if filtered_by_mode > 0:
        reason_code = "no_geometry_for_mode"
        reason = f"All {filtered_by_mode} mesh node(s) excluded as collision/nodraw in {import_mode} mode"
    else:
        reason_code = "empty_mesh"
        reason = "CGF contains no buildable geometry"

    _record_report(
        filepath=str(path),
        import_mode=import_mode,
        result="CANCELLED",
        reason_code=reason_code,
        reason=reason,
        file_exists=True,
        parser_node_count=parser_node_count,
        parser_mesh_node_count=parser_mesh_node_count,
        parser_material_count=parser_material_count,
        candidate_mesh_node_count=candidate_mesh_nodes,
        objects_created=0,
        diag=diag,
    )
    return {"CANCELLED"}, None


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
    simple_shaders: bool = False,
    preparsed_cgf: Optional[dict] = None,
    target_collection: Optional[bpy.types.Collection] = None,
    link_to_scene: bool = True,
) -> dict:
    gen = iter_load_cgf(
        context,
        filepath,
        import_mode=import_mode,
        apply_smoothing_groups=apply_smoothing_groups,
        animate_texture_sequences=animate_texture_sequences,
        texture_animation_fps=texture_animation_fps,
        animate_shader_uv_scroll=animate_shader_uv_scroll,
        animate_cga_controllers=animate_cga_controllers,
        client_root=client_root,
        optimize_material_preview=optimize_material_preview,
        simple_shaders=simple_shaders,
        preparsed_cgf=preparsed_cgf,
        target_collection=target_collection,
        link_to_scene=link_to_scene,
        time_slice_s=9999.0,
    )
    try:
        while True:
            next(gen)
    except StopIteration as exc:
        status_set, _ = exc.value
        return status_set
