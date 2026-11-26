from array import array
import colorsys
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from aion_formats.level import (
    LandMap,
    LevelData,
    SurfaceType,
    TerrainMaterialInventory,
    build_terrain_preview_blend_weights,
    build_terrain_material_inventory,
)

from .terrain_blend_attributes import (
    TerrainBlendAttributeResult,
    apply_precomputed_terrain_blend_attributes,
    create_fast_subsampled_terrain_blend_attributes,
    create_terrain_blend_attributes,
    prepare_subsampled_terrain_blend_data,
)
from .terrain_blend_nodes import (
    TerrainBlendShaderResult,
    create_terrain_blend_shader,
    iter_create_terrain_blend_shader,
)
from .terrain_textures import resolve_terrain_detail_texture
from .terrain_material_nodes import TerrainTextureNodeResult, create_terrain_texture_nodes


DEFAULT_TERRAIN_NAME = "Aion Terrain"
DEFAULT_XY_SCALE = 2.0


@dataclass(frozen=True)
class TerrainMeshResult:
    object: object
    mesh: object
    width: int
    height: int
    vertex_count: int
    face_count: int
    min_height: float
    max_height: float
    xy_scale: float
    material_slot_count: int = 0
    assigned_material_index_count: int = 0
    uv_layer_count: int = 0
    uv_loop_count: int = 0
    image_count_delta: int = 0
    detail_texture_count: int = 0
    resolved_detail_texture_count: int = 0
    existing_detail_texture_count: int = 0
    missing_detail_texture_count: int = 0
    texture_load_requested: bool = False
    texture_images_loaded: int = 0
    texture_images_failed: int = 0
    texture_nodes_created: int = 0
    blend_attributes_requested: bool = False
    blend_attribute_layers_created: int = 0
    blend_weight_material_count: int = 0
    blend_boundary_sample_count: int = 0
    blend_invalid_weight_count: int = 0
    blend_shader_enabled: bool = False
    blend_shader_graph_created: bool = False
    blend_shader_material_count: int = 0
    blend_shader_included_material_indices: tuple[int, ...] = ()
    blend_shader_texture_images_loaded: int = 0
    blend_shader_texture_images_failed: int = 0
    blend_shader_texture_nodes_created: int = 0
    blend_shader_skipped_material_indices: tuple[int, ...] = ()
    blend_shader_skipped_material_sample_counts: tuple[tuple[int, int], ...] = ()
    blend_shader_skipped_material_reasons: tuple[tuple[int, str, int], ...] = ()
    blend_shader_projection_mode: str = ""
    blend_shader_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class TerrainMaterialSlot:
    terrain_material_index: int
    slot_index: int
    name: str
    surface_type: SurfaceType | None
    material: object | None = None


def build_terrain_geometry(
    land_map: LandMap,
    xy_scale: float = DEFAULT_XY_SCALE,
    lod: int = 1,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int, int]]]:
    if land_map.sample_count != land_map.width * land_map.height:
        raise ValueError("LandMap sample count does not match width * height")
    if not math.isfinite(xy_scale) or xy_scale <= 0:
        raise ValueError("terrain XY scale must be finite and positive")

    step = max(1, int(lod))
    w = land_map.width
    h = land_map.height
    samples = land_map.samples

    if step == 1:
        vertices = []
        vertices_append = vertices.append
        for row in range(h):
            rx = float(row) * xy_scale
            row_off = row * w
            for col in range(w):
                vertices_append((rx, float(col) * xy_scale, samples[row_off + col].height))
        faces = [
            (
                row * w + col,
                (row + 1) * w + col,
                (row + 1) * w + col + 1,
                row * w + col + 1,
            )
            for row in range(h - 1)
            for col in range(w - 1)
        ]
    else:
        rows = list(range(0, h, step))
        if rows[-1] != h - 1:
            rows.append(h - 1)
        cols = list(range(0, w, step))
        if cols[-1] != w - 1:
            cols.append(w - 1)

        new_h = len(rows)
        new_w = len(cols)
        vertices = []
        for r in rows:
            r_scale = float(r) * xy_scale
            r_off = r * w
            for c in cols:
                c_scale = float(c) * xy_scale
                vertices.append((r_scale, c_scale, samples[r_off + c].height))

        faces = [
            (
                r_idx * new_w + c_idx,
                (r_idx + 1) * new_w + c_idx,
                (r_idx + 1) * new_w + c_idx + 1,
                r_idx * new_w + c_idx + 1,
            )
            for r_idx in range(new_h - 1)
            for c_idx in range(new_w - 1)
        ]

    return vertices, faces


def prepare_terrain_stage_data(
    land_map: LandMap,
    level_data: LevelData | None = None,
    client_root: str | Path | None = None,
    *,
    xy_scale: float = DEFAULT_XY_SCALE,
    lod: int = 1,
    compute_blend: bool = True,
) -> dict:
    """
    Pure-Python terrain precomputation safe for background worker thread:
    builds flat foreach_set mesh buffers, subsampled blend weights, face material indices,
    UV buffers, and pre-extracts detail DDS files without touching any Blender state.
    """
    if land_map.sample_count != land_map.width * land_map.height:
        raise ValueError("LandMap sample count does not match width * height")
    if not math.isfinite(xy_scale) or xy_scale <= 0:
        raise ValueError("terrain XY scale must be finite and positive")

    w = land_map.width
    h = land_map.height
    samples = land_map.samples
    rows, cols = _grid_subsamples(w, h, lod)
    new_h = len(rows)
    new_w = len(cols)
    num_verts = new_h * new_w
    num_faces = max(0, (new_h - 1) * (new_w - 1))

    flat_co = array("f", [0.0]) * (num_verts * 3)
    grid_row_xs = [float(r) * xy_scale for r in rows]
    grid_col_ys = [float(c) * xy_scale for c in cols]
    grid_z = array("f", [0.0]) * num_verts
    v_off = 0
    z_idx = 0
    for r in rows:
        rx = float(r) * xy_scale
        row_off = r * w
        for c in cols:
            h_val = float(samples[row_off + c].height)
            flat_co[v_off] = rx
            flat_co[v_off + 1] = float(c) * xy_scale
            flat_co[v_off + 2] = h_val
            grid_z[z_idx] = h_val
            v_off += 3
            z_idx += 1

    flat_loop_verts = array("I", [0]) * (num_faces * 4)
    l_off = 0
    for r_idx in range(new_h - 1):
        base0 = r_idx * new_w
        base1 = (r_idx + 1) * new_w
        for c_idx in range(new_w - 1):
            flat_loop_verts[l_off] = base0 + c_idx
            flat_loop_verts[l_off + 1] = base1 + c_idx
            flat_loop_verts[l_off + 2] = base1 + c_idx + 1
            flat_loop_verts[l_off + 3] = base0 + c_idx + 1
            l_off += 4

    loop_starts = array("I", range(0, num_faces * 4, 4))
    loop_totals = array("I", [4]) * num_faces

    blend_radius = max(1, min(2, int(lod) // 2))
    blend_data = (
        prepare_subsampled_terrain_blend_data(land_map, lod=lod, radius=blend_radius)
        if compute_blend
        else None
    )
    resolved_textures: dict[int, object] = {}
    inventory = None
    face_mat_indices = None
    assigned_mat_count = 0
    preview_uvs = None

    if level_data is not None:
        inventory = build_terrain_material_inventory(land_map, level_data)
        slot_by_tmat = {}
        surface_params = {}
        for slot_idx, usage in enumerate(inventory.used_material_indices):
            slot_by_tmat[usage.index] = slot_idx
            st = usage.surface_type
            if st is not None:
                resolved_textures[usage.index] = resolve_terrain_detail_texture(
                    client_root, st.detail_texture
                )
                sx = float(st.detail_scale_x) if st.detail_scale_x is not None else 1.0
                sy = float(st.detail_scale_y) if st.detail_scale_y is not None else 1.0
                ou = float(st.offset_u) if st.offset_u is not None else 0.0
                ov = float(st.offset_v) if st.offset_v is not None else 0.0
                surface_params[usage.index] = (sx, sy, ou, ov)
            else:
                surface_params[usage.index] = (1.0, 1.0, 0.0, 0.0)

        if num_faces > 0:
            face_mat_indices = array("i", [0]) * num_faces
            preview_uvs = array("f", [0.0]) * (num_faces * 8)
            assigned_set = set()
            poly_idx = 0
            uv_off = 0
            for r_idx in range(new_h - 1):
                r0 = rows[r_idx]
                r1 = rows[r_idx + 1]
                sample_off = r0 * w
                for c_idx in range(new_w - 1):
                    c0 = cols[c_idx]
                    c1 = cols[c_idx + 1]
                    t_mat = samples[sample_off + c0].color
                    s_idx = slot_by_tmat.get(t_mat)
                    if s_idx is not None:
                        face_mat_indices[poly_idx] = s_idx
                        assigned_set.add(s_idx)
                    sx, sy, ou, ov = surface_params.get(t_mat, (1.0, 1.0, 0.0, 0.0))
                    f_c0, f_r0, f_c1, f_r1 = float(c0), float(r0), float(c1), float(r1)
                    preview_uvs[uv_off] = f_c0 * sx + ou
                    preview_uvs[uv_off + 1] = f_r0 * sy + ov
                    preview_uvs[uv_off + 2] = f_c0 * sx + ou
                    preview_uvs[uv_off + 3] = f_r1 * sy + ov
                    preview_uvs[uv_off + 4] = f_c1 * sx + ou
                    preview_uvs[uv_off + 5] = f_r1 * sy + ov
                    preview_uvs[uv_off + 6] = f_c1 * sx + ou
                    preview_uvs[uv_off + 7] = f_r0 * sy + ov
                    poly_idx += 1
                    uv_off += 8
            assigned_mat_count = len(assigned_set)

    return {
        "num_verts": num_verts,
        "num_faces": num_faces,
        "grid_h": new_h,
        "grid_w": new_w,
        "grid_row_xs": grid_row_xs,
        "grid_col_ys": grid_col_ys,
        "grid_z": grid_z,
        "flat_co": flat_co,
        "flat_loop_verts": flat_loop_verts,
        "loop_starts": loop_starts,
        "loop_totals": loop_totals,
        "blend_data": blend_data,
        "inventory": inventory,
        "resolved_textures": resolved_textures,
        "face_mat_indices": face_mat_indices,
        "assigned_mat_count": assigned_mat_count,
        "preview_uvs": preview_uvs,
    }


def iter_create_terrain_mesh(
    context,
    land_map: LandMap,
    level_data: LevelData | None = None,
    client_root: str | Path | None = None,
    import_terrain_textures: bool = False,
    import_terrain_blend_attributes: bool = False,
    import_terrain_blend_shader: bool = False,
    import_terrain_shadows: bool = True,
    level_dir: Path | str | None = None,
    name: str = DEFAULT_TERRAIN_NAME,
    xy_scale: float = DEFAULT_XY_SCALE,
    lod: int = 1,
    max_blend_materials: int = 8,
    simple_shader: bool = False,
    disable_shadows: bool = False,
    precomputed: dict | None = None,
    target_collection=None,
):
    """Yields incrementally while creating the terrain mesh and blend shader."""
    import bpy

    images_before = len(bpy.data.images)
    mesh = bpy.data.meshes.new(name)
    if precomputed is not None and "flat_co" in precomputed:
        num_verts = int(precomputed["num_verts"])
        num_faces = int(precomputed["num_faces"])
        if num_verts > 0:
            mesh.vertices.add(num_verts)
            mesh.vertices.foreach_set("co", precomputed["flat_co"])
        if num_faces > 0:
            mesh.loops.add(num_faces * 4)
            mesh.loops.foreach_set("vertex_index", precomputed["flat_loop_verts"])
            mesh.polygons.add(num_faces)
            mesh.polygons.foreach_set("loop_start", precomputed["loop_starts"])
            mesh.polygons.foreach_set("loop_total", precomputed["loop_totals"])
        mesh.update(calc_edges=True)
    else:
        if precomputed is not None and "vertices" in precomputed:
            vertices = precomputed["vertices"]
            faces = precomputed["faces"]
        else:
            vertices, faces = build_terrain_geometry(land_map, xy_scale=xy_scale, lod=lod)
        num_verts = len(vertices)
        num_faces = len(faces)
        mesh.from_pydata(vertices, (), faces)
        mesh.update(calc_edges=False)
    yield (0.25, "Malha do terreno criada")

    material_slots = ()
    assigned_material_index_count = 0
    texture_node_result = TerrainTextureNodeResult(
        texture_load_requested=False,
        texture_images_loaded=0,
        texture_images_failed=0,
        texture_nodes_created=0,
    )
    blend_attribute_result = TerrainBlendAttributeResult(
        attribute_layers_created=0,
        material_count=0,
        layer_names=(),
    )
    subsampled_sample_counts: dict[int, int] | None = None
    blend_boundary_sample_count = 0
    blend_invalid_weight_count = 0
    if import_terrain_blend_attributes or import_terrain_blend_shader:
        if precomputed is not None and precomputed.get("blend_data") is not None:
            blend_attribute_result, subsampled_sample_counts, blend_boundary_sample_count = (
                apply_precomputed_terrain_blend_attributes(mesh, precomputed["blend_data"])
            )
        else:
            blend_radius = max(1, min(2, int(lod) // 2))
            blend_attribute_result, subsampled_sample_counts, blend_boundary_sample_count = (
                create_fast_subsampled_terrain_blend_attributes(
                    mesh,
                    land_map,
                    lod=lod,
                    radius=blend_radius,
                )
            )
        yield (0.45, "Pesos de blend do terreno aplicados")

    blend_shader_result = TerrainBlendShaderResult(
        enabled=False,
        graph_created=False,
        material_count=0,
        included_material_indices=(),
        texture_images_loaded=0,
        texture_images_failed=0,
        texture_nodes_created=0,
        skipped_material_indices=(),
        skipped_material_sample_counts=(),
        skipped_material_reasons=(),
        projection_mode="",
        warnings=(),
    )

    if level_data is not None:
        inventory = (
            precomputed.get("inventory")
            if precomputed is not None and precomputed.get("inventory") is not None
            else build_terrain_material_inventory(land_map, level_data)
        )
        resolved_map = precomputed.get("resolved_textures") if precomputed is not None else None
        load_slot_nodes = import_terrain_textures and not import_terrain_blend_shader
        material_slots = _create_terrain_materials(
            bpy,
            mesh,
            inventory,
            client_root,
            load_detail_nodes=load_slot_nodes,
            pre_resolved_textures=resolved_map,
        )
        if precomputed is not None and precomputed.get("face_mat_indices") is not None:
            if len(mesh.polygons) > 0:
                mesh.polygons.foreach_set("material_index", precomputed["face_mat_indices"])
            assigned_material_index_count = int(precomputed.get("assigned_mat_count", 0))
            if precomputed.get("preview_uvs") is not None and len(mesh.loops) > 0:
                uv_layer = mesh.uv_layers.new(name="Aion Terrain Preview UV")
                uv_layer.data.foreach_set("uv", precomputed["preview_uvs"])
        else:
            assigned_material_index_count = _assign_face_material_indices(
                mesh,
                land_map,
                material_slots,
                lod=lod,
            )
            _assign_preview_uvs(mesh, land_map, material_slots, lod=lod)
        yield (0.65, "Slots e UVs do terreno atribuídos")

        if load_slot_nodes:
            texture_node_result = create_terrain_texture_nodes(bpy, mesh.materials)
        if import_terrain_blend_shader:
            shadow_path = None
            if import_terrain_shadows and level_dir:
                ld = Path(level_dir)
                for cand in (
                    ld / "terrain" / "cover_low_shadow.dds",
                    ld / "newterrain" / "cover_low_shadow.dds",
                    ld / ".aion_cache" / "terrain" / "cover_low_shadow.dds",
                    ld / ".aion_cache" / "newterrain" / "cover_low_shadow.dds",
                ):
                    if cand.is_file():
                        shadow_path = cand
                        break
            sample_counts = (
                subsampled_sample_counts
                if subsampled_sample_counts is not None
                else _terrain_material_sample_counts(land_map)
            )
            shader_gen = iter_create_terrain_blend_shader(
                bpy,
                mesh,
                material_slots,
                material_sample_counts=sample_counts,
                load_textures=import_terrain_textures,
                material_limit=max_blend_materials,
                simple_shader=simple_shader,
                shadow_texture_path=shadow_path,
            )
            try:
                while True:
                    sh_idx, sh_tot = next(shader_gen)
                    yield (
                        0.65 + 0.30 * (sh_idx / max(1, sh_tot)),
                        f"Carregando shader de terreno ({sh_idx}/{sh_tot})...",
                    )
            except StopIteration as exc_sh:
                blend_shader_result = exc_sh.value

            # Strip the 28 unused slot preview materials so Eevee compiles ONLY 1 terrain shader (no post-load freeze).
            if blend_shader_result.graph_created and len(mesh.materials) > 1:
                blend_mat = mesh.materials[-1]
                old_slot_mats = [m for m in mesh.materials if m is not None and m is not blend_mat]
                mesh.materials.clear()
                mesh.materials.append(blend_mat)
                if len(mesh.polygons) > 0:
                    mesh.polygons.foreach_set("material_index", array("i", [0]) * len(mesh.polygons))
                unused_mats = [m for m in old_slot_mats if m.users == 0]
                if unused_mats:
                    try:
                        bpy.data.batch_remove(ids=unused_mats)
                    except Exception:
                        for om in unused_mats:
                            try:
                                if om.users == 0:
                                    bpy.data.materials.remove(om)
                            except Exception:
                                pass

    terrain_object = bpy.data.objects.new(name, mesh)
    if disable_shadows and hasattr(terrain_object, "visible_shadow"):
        try:
            terrain_object.visible_shadow = False
        except (AttributeError, TypeError):
            pass
    terrain_object["aion_blend_shader_enabled"] = blend_shader_result.enabled
    terrain_object["aion_blend_shader_material_count"] = blend_shader_result.material_count
    terrain_object["aion_blend_shader_included_materials"] = ",".join(
        str(index) for index in blend_shader_result.included_material_indices
    )
    terrain_object["aion_blend_attribute_layers"] = ",".join(blend_attribute_result.layer_names)
    terrain_object["aion_blend_shader_skipped_materials"] = ",".join(
        str(index) for index in blend_shader_result.skipped_material_indices
    )
    terrain_object["aion_blend_shader_skipped_sample_counts"] = ",".join(
        f"{index}:{count}"
        for index, count in blend_shader_result.skipped_material_sample_counts
    )
    terrain_object["aion_blend_shader_skipped_reasons"] = ",".join(
        f"{index}:{reason}:{count}"
        for index, reason, count in blend_shader_result.skipped_material_reasons
    )
    terrain_object["aion_blend_shader_projection"] = blend_shader_result.projection_mode
    terrain_object["aion_blend_shader_warnings"] = "; ".join(blend_shader_result.warnings)
    if precomputed is not None and "grid_h" in precomputed and "grid_w" in precomputed:
        terrain_object["aion_terrain_grid_h"] = int(precomputed["grid_h"])
        terrain_object["aion_terrain_grid_w"] = int(precomputed["grid_w"])
    else:
        g_rows, g_cols = _grid_subsamples(land_map.width, land_map.height, lod)
        terrain_object["aion_terrain_grid_h"] = len(g_rows)
        terrain_object["aion_terrain_grid_w"] = len(g_cols)
    yield (0.96, "Vinculando terreno na cena...")
    dest_col = target_collection if target_collection is not None else context.scene.collection
    dest_col.objects.link(terrain_object)
    return TerrainMeshResult(
        object=terrain_object,
        mesh=mesh,
        width=land_map.width,
        height=land_map.height,
        vertex_count=num_verts,
        face_count=num_faces,
        min_height=land_map.min_height,
        max_height=land_map.max_height,
        xy_scale=xy_scale,
        material_slot_count=len(material_slots),
        assigned_material_index_count=assigned_material_index_count,
        uv_layer_count=len(mesh.uv_layers),
        uv_loop_count=len(mesh.uv_layers.active.data) if mesh.uv_layers.active else 0,
        image_count_delta=len(bpy.data.images) - images_before,
        detail_texture_count=_count_materials_with_property(mesh, "aion_detail_texture"),
        resolved_detail_texture_count=_count_materials_with_property(mesh, "aion_detail_texture_resolved"),
        existing_detail_texture_count=_count_materials_with_existing_detail_texture(mesh, True),
        missing_detail_texture_count=_count_materials_with_existing_detail_texture(mesh, False),
        texture_load_requested=texture_node_result.texture_load_requested,
        texture_images_loaded=texture_node_result.texture_images_loaded,
        texture_images_failed=texture_node_result.texture_images_failed,
        texture_nodes_created=texture_node_result.texture_nodes_created,
        blend_attributes_requested=import_terrain_blend_attributes or import_terrain_blend_shader,
        blend_attribute_layers_created=blend_attribute_result.attribute_layers_created,
        blend_weight_material_count=blend_attribute_result.material_count,
        blend_boundary_sample_count=blend_boundary_sample_count,
        blend_invalid_weight_count=blend_invalid_weight_count,
        blend_shader_enabled=blend_shader_result.enabled,
        blend_shader_graph_created=blend_shader_result.graph_created,
        blend_shader_material_count=blend_shader_result.material_count,
        blend_shader_included_material_indices=blend_shader_result.included_material_indices,
        blend_shader_texture_images_loaded=blend_shader_result.texture_images_loaded,
        blend_shader_texture_images_failed=blend_shader_result.texture_images_failed,
        blend_shader_texture_nodes_created=blend_shader_result.texture_nodes_created,
        blend_shader_skipped_material_indices=blend_shader_result.skipped_material_indices,
        blend_shader_skipped_material_sample_counts=blend_shader_result.skipped_material_sample_counts,
        blend_shader_skipped_material_reasons=blend_shader_result.skipped_material_reasons,
        blend_shader_projection_mode=blend_shader_result.projection_mode,
        blend_shader_warnings=blend_shader_result.warnings,
    )


def create_terrain_mesh(
    context,
    land_map: LandMap,
    level_data: LevelData | None = None,
    client_root: str | Path | None = None,
    import_terrain_textures: bool = False,
    import_terrain_blend_attributes: bool = False,
    import_terrain_blend_shader: bool = False,
    import_terrain_shadows: bool = True,
    level_dir: Path | str | None = None,
    name: str = DEFAULT_TERRAIN_NAME,
    xy_scale: float = DEFAULT_XY_SCALE,
    lod: int = 1,
    max_blend_materials: int = 8,
    simple_shader: bool = False,
    disable_shadows: bool = False,
    precomputed: dict | None = None,
) -> TerrainMeshResult:
    gen = iter_create_terrain_mesh(
        context,
        land_map,
        level_data=level_data,
        client_root=client_root,
        import_terrain_textures=import_terrain_textures,
        import_terrain_blend_attributes=import_terrain_blend_attributes,
        import_terrain_blend_shader=import_terrain_blend_shader,
        import_terrain_shadows=import_terrain_shadows,
        level_dir=level_dir,
        name=name,
        xy_scale=xy_scale,
        lod=lod,
        max_blend_materials=max_blend_materials,
        simple_shader=simple_shader,
        disable_shadows=disable_shadows,
        precomputed=precomputed,
    )
    try:
        while True:
            next(gen)
    except StopIteration as exc:
        return exc.value


def _safe_surface_scale(value: float | None) -> float:
    return value if value is not None and value > 0 else 1.0


def _create_terrain_materials(
    bpy,
    mesh,
    inventory: TerrainMaterialInventory,
    client_root: str | Path | None,
    *,
    load_detail_nodes: bool = True,
    pre_resolved_textures: dict[int, object] | None = None,
) -> tuple[TerrainMaterialSlot, ...]:
    slots = []
    for usage in inventory.used_material_indices:
        material_name = _terrain_material_name(usage.index, usage.surface_type)
        material = bpy.data.materials.new(material_name)
        material.use_nodes = load_detail_nodes
        if load_detail_nodes:
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            nodes.clear()

            output = nodes.new("ShaderNodeOutputMaterial")
            output.location = (400, 0)
            bsdf = nodes.new("ShaderNodeBsdfPrincipled")
            bsdf.location = (100, 0)
            links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

            base_color = _terrain_material_color(usage.index)
            bsdf.inputs["Base Color"].default_value = base_color
            bsdf.inputs["Roughness"].default_value = 0.85
        else:
            base_color = _terrain_material_color(usage.index)
        material.diffuse_color = base_color
        material["aion_terrain_material_index"] = usage.index

        if usage.surface_type is not None:
            material["aion_surface_name"] = usage.surface_type.name or ""
            texture_ref = (
                pre_resolved_textures.get(usage.index)
                if pre_resolved_textures is not None
                else None
            ) or resolve_terrain_detail_texture(
                client_root,
                usage.surface_type.detail_texture,
            )
            material["aion_detail_texture"] = texture_ref.raw_path
            material["aion_detail_texture_normalized"] = texture_ref.normalized_relative_path
            material["aion_detail_texture_resolved"] = texture_ref.resolved_path or ""
            material["aion_detail_texture_exists"] = texture_ref.exists

            if load_detail_nodes and texture_ref.exists and texture_ref.resolved_path:
                from materials.texture_loader import load_texture_image
                img = load_texture_image(texture_ref.resolved_path, colorspace="sRGB")
                if img is not None:
                    tex_node = nodes.new("ShaderNodeTexImage")
                    tex_node.location = (-250, 0)
                    tex_node.image = img

                    tex_coord = nodes.new("ShaderNodeTexCoord")
                    tex_coord.location = (-650, 0)
                    mapping = nodes.new("ShaderNodeMapping")
                    mapping.location = (-450, 0)

                    scale_x = _safe_surface_scale(usage.surface_type.detail_scale_x) * 32.0
                    scale_y = _safe_surface_scale(usage.surface_type.detail_scale_y) * 32.0
                    mapping.inputs["Scale"].default_value = (scale_x, scale_y, 1.0)

                    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])
                    links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])
                    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
        else:
            material["aion_surface_missing"] = True

        slot = TerrainMaterialSlot(
            terrain_material_index=usage.index,
            slot_index=len(mesh.materials),
            name=material_name,
            surface_type=usage.surface_type,
            material=material,
        )
        mesh.materials.append(material)
        slots.append(slot)

    return tuple(slots)


def _grid_subsamples(width: int, height: int, lod: int = 1):
    step = max(1, int(lod))
    if step <= 1:
        return list(range(height)), list(range(width))
    rows = list(range(0, height, step))
    if rows[-1] != height - 1:
        rows.append(height - 1)
    cols = list(range(0, width, step))
    if cols[-1] != width - 1:
        cols.append(width - 1)
    return rows, cols


def _assign_face_material_indices(
    mesh,
    land_map: LandMap,
    material_slots: tuple[TerrainMaterialSlot, ...],
    lod: int = 1,
) -> int:
    slot_by_terrain_index = {
        slot.terrain_material_index: slot.slot_index
        for slot in material_slots
    }
    assigned_indices = set()
    num_polys = len(mesh.polygons)
    if num_polys == 0:
        return 0

    mat_indices = [0] * num_polys
    rows, cols = _grid_subsamples(land_map.width, land_map.height, lod)
    new_h = len(rows)
    new_w = len(cols)
    w = land_map.width
    samples = land_map.samples
    poly_idx = 0

    for r_idx in range(new_h - 1):
        r = rows[r_idx]
        sample_offset = r * w
        for c_idx in range(new_w - 1):
            if poly_idx >= num_polys:
                break
            c = cols[c_idx]
            terrain_material_index = samples[sample_offset + c].color
            slot_index = slot_by_terrain_index.get(terrain_material_index)
            if slot_index is not None:
                mat_indices[poly_idx] = slot_index
                assigned_indices.add(slot_index)
            poly_idx += 1

    mesh.polygons.foreach_set("material_index", mat_indices)
    return len(assigned_indices)


def _assign_preview_uvs(
    mesh,
    land_map: LandMap,
    material_slots: tuple[TerrainMaterialSlot, ...],
    lod: int = 1,
) -> None:
    num_loops = len(mesh.loops)
    if num_loops == 0:
        return

    uv_layer = mesh.uv_layers.new(name="Aion Terrain Preview UV")
    from array import array

    surface_params = {}
    for slot in material_slots:
        st = slot.surface_type
        if st is not None:
            sx = float(st.detail_scale_x) if st.detail_scale_x is not None else 1.0
            sy = float(st.detail_scale_y) if st.detail_scale_y is not None else 1.0
            ou = float(st.offset_u) if st.offset_u is not None else 0.0
            ov = float(st.offset_v) if st.offset_v is not None else 0.0
            surface_params[slot.terrain_material_index] = (sx, sy, ou, ov)
        else:
            surface_params[slot.terrain_material_index] = (1.0, 1.0, 0.0, 0.0)

    uvs = array("f", [0.0]) * (num_loops * 2)
    rows, cols = _grid_subsamples(land_map.width, land_map.height, lod)
    new_h = len(rows)
    new_w = len(cols)
    w = land_map.width
    samples = land_map.samples
    loop_idx = 0
    max_loops = num_loops

    for r_idx in range(new_h - 1):
        r0 = rows[r_idx]
        r1 = rows[r_idx + 1]
        sample_offset = r0 * w
        for c_idx in range(new_w - 1):
            if loop_idx + 8 > max_loops * 2:
                break
            c0 = cols[c_idx]
            c1 = cols[c_idx + 1]
            t_mat = samples[sample_offset + c0].color
            sx, sy, ou, ov = surface_params.get(t_mat, (1.0, 1.0, 0.0, 0.0))

            v0_col, v0_row = c0, r0
            v1_col, v1_row = c0, r1
            v2_col, v2_row = c1, r1
            v3_col, v3_row = c1, r0

            uvs[loop_idx] = float(v0_col) * sx + ou
            uvs[loop_idx + 1] = float(v0_row) * sy + ov

            uvs[loop_idx + 2] = float(v1_col) * sx + ou
            uvs[loop_idx + 3] = float(v1_row) * sy + ov

            uvs[loop_idx + 4] = float(v2_col) * sx + ou
            uvs[loop_idx + 5] = float(v2_row) * sy + ov

            uvs[loop_idx + 6] = float(v3_col) * sx + ou
            uvs[loop_idx + 7] = float(v3_row) * sy + ov

            loop_idx += 8

    uv_layer.data.foreach_set("uv", uvs)


def _preview_uv_for_grid(
    column: int,
    row: int,
    surface_type: SurfaceType | None,
) -> tuple[float, float]:
    scale_x = surface_type.detail_scale_x if surface_type and surface_type.detail_scale_x is not None else 1.0
    scale_y = surface_type.detail_scale_y if surface_type and surface_type.detail_scale_y is not None else 1.0
    offset_u = surface_type.offset_u if surface_type and surface_type.offset_u is not None else 0.0
    offset_v = surface_type.offset_v if surface_type and surface_type.offset_v is not None else 0.0
    return (
        float(column) * scale_x + offset_u,
        float(row) * scale_y + offset_v,
    )


def _terrain_material_name(index: int, surface_type: SurfaceType | None) -> str:
    label = None
    if surface_type is not None:
        label = surface_type.name or (
            PureWindowsPath(surface_type.detail_texture).name
            if surface_type.detail_texture
            else None
        )
    return f"Terrain Surface {index}: {label or 'Unknown'}"


def _terrain_material_color(index: int) -> tuple[float, float, float, float]:
    hue = (index * 0.137) % 1.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.45, 0.85)
    return (red, green, blue, 1.0)


def _count_materials_with_property(mesh, property_name: str) -> int:
    return sum(1 for material in mesh.materials if bool(material.get(property_name)))


def _count_materials_with_existing_detail_texture(mesh, exists: bool) -> int:
    return sum(
        1
        for material in mesh.materials
        if bool(material.get("aion_detail_texture")) and material.get("aion_detail_texture_exists") is exists
    )


def _terrain_material_sample_counts(land_map: LandMap) -> dict[int, int]:
    return dict(Counter(sample.color for sample in land_map.samples))
