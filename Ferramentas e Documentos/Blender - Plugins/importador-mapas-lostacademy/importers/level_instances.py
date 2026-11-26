import math
from dataclasses import dataclass

from .level_jobs import SOURCE_BRUSH, SOURCE_OBJECT, LevelCgfJob


INVALID_OBJECT_SCALE = "invalid_object_scale"
INVALID_OBJECT_TRANSFORM = "invalid_object_transform"
INVALID_BRUSH_MATRIX = "invalid_brush_matrix"
UNSUPPORTED_SOURCE_TYPE = "unsupported_source_type"


class InvalidPlacementError(ValueError):
    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class PlacementSkip:
    source_type: str
    source_index: int
    cgf_reference: str
    reason_code: str
    reason: str


@dataclass(frozen=True)
class PlacementTransformSummary:
    source_type: str
    source_index: int
    matrix_values: tuple[float, ...]
    translation: tuple[float, float, float]
    scale: float | None
    heading_degrees: float | None
    is_non_default: bool


@dataclass(frozen=True)
class PlacementInstanceBatch:
    instances: tuple
    transform_summaries: tuple[PlacementTransformSummary, ...]
    object_placement_count: int
    brush_placement_count: int
    placement_skips: tuple[PlacementSkip, ...]
    invalid_placements_skipped: int
    invalid_object_scale_count: int
    invalid_brush_matrix_count: int


def iter_merge_static_template_meshes(
    template_collection,
    merged_name: str = "AionMergedTemplate",
    *,
    time_slice_s: float = 0.008,
):
    """
    Time-sliced generator merging multiple static MESH sub-objects inside `template_collection`
    into ONE multi-material mesh datablock using pure bmesh (zero bpy.ops calls).
    Yields `(step_idx, total_steps)` whenever work exceeds `time_slice_s`, and returns the
    single MESH object via StopIteration.value.
    """
    if template_collection is None:
        return None

    import time
    import bpy
    import bmesh
    from mathutils import Matrix

    mesh_objs = [o for o in list(template_collection.objects) if o.type == "MESH" and o.data is not None]
    if len(mesh_objs) <= 1:
        return mesh_objs[0] if mesh_objs else None

    # Never merge rigged or animated sub-meshes
    for obj in mesh_objs:
        if any(m.type == "ARMATURE" for m in obj.modifiers):
            return None
        if getattr(obj, "animation_data", None) is not None and getattr(obj.animation_data, "action", None) is not None:
            return None

    unified_materials = []
    mat_ptr_to_idx = {}
    identity_mat = Matrix.Identity(4)

    merged_bm = bmesh.new()
    tmp_mesh = bpy.data.meshes.new("__aion_merge_scratch__")
    old_meshes = []
    total_objs = len(mesh_objs)
    slice_t0 = time.perf_counter()

    try:
        for idx_m, obj in enumerate(mesh_objs, start=1):
            orig_mesh = obj.data
            old_meshes.append(orig_mesh)
            if len(orig_mesh.vertices) == 0 or len(orig_mesh.polygons) == 0:
                continue

            local_to_unified = {}
            for local_idx, mat in enumerate(orig_mesh.materials):
                if mat is None:
                    local_to_unified[local_idx] = 0
                else:
                    ptr = mat.as_pointer()
                    u_idx = mat_ptr_to_idx.get(ptr)
                    if u_idx is None:
                        u_idx = len(unified_materials)
                        unified_materials.append(mat)
                        mat_ptr_to_idx[ptr] = u_idx
                    local_to_unified[local_idx] = u_idx

            tmp_bm = bmesh.new()
            try:
                tmp_bm.from_mesh(orig_mesh)
                if obj.matrix_world != identity_mat:
                    bmesh.ops.transform(tmp_bm, matrix=obj.matrix_world, verts=tmp_bm.verts)
                if local_to_unified:
                    for face in tmp_bm.faces:
                        face.material_index = local_to_unified.get(face.material_index, 0)
                tmp_bm.to_mesh(tmp_mesh)
                merged_bm.from_mesh(tmp_mesh)
            finally:
                tmp_bm.free()

            if idx_m < total_objs and (time.perf_counter() - slice_t0) >= time_slice_s:
                yield idx_m, total_objs * 2
                slice_t0 = time.perf_counter()

        if len(merged_bm.verts) == 0 or len(merged_bm.faces) == 0:
            merged_bm.free()
            merged_bm = None
            return mesh_objs[0]

        if (time.perf_counter() - slice_t0) >= time_slice_s:
            yield total_objs, total_objs * 2
            slice_t0 = time.perf_counter()

        final_mesh = bpy.data.meshes.new(merged_name)
        merged_bm.to_mesh(final_mesh)
        merged_bm.free()
        merged_bm = None

        for mat in unified_materials:
            final_mesh.materials.append(mat)
        final_mesh.update(calc_edges=False)

        merged_obj = bpy.data.objects.new(merged_name, final_mesh)
        merged_obj.matrix_world = identity_mat
        template_collection.objects.link(merged_obj)

        if hasattr(bpy.data, "batch_remove"):
            try:
                bpy.data.batch_remove(ids=mesh_objs)
            except Exception:
                for obj in mesh_objs:
                    try:
                        bpy.data.objects.remove(obj, do_unlink=True)
                    except Exception:
                        pass

            seen_mesh_ptrs = set()
            unused_meshes = []
            for om in old_meshes:
                try:
                    ptr = om.as_pointer()
                    if ptr not in seen_mesh_ptrs and om.users == 0:
                        seen_mesh_ptrs.add(ptr)
                        unused_meshes.append(om)
                except Exception:
                    pass
            if tmp_mesh is not None:
                try:
                    if tmp_mesh.name in bpy.data.meshes:
                        unused_meshes.append(tmp_mesh)
                        tmp_mesh = None
                except Exception:
                    pass
            if unused_meshes:
                try:
                    bpy.data.batch_remove(ids=unused_meshes)
                except Exception:
                    for om in unused_meshes:
                        try:
                            if om.users == 0:
                                bpy.data.meshes.remove(om)
                        except Exception:
                            pass
        else:
            for idx_rm, obj in enumerate(mesh_objs, start=1):
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass
                if idx_rm < total_objs and (time.perf_counter() - slice_t0) >= time_slice_s:
                    yield total_objs + idx_rm, total_objs * 2
                    slice_t0 = time.perf_counter()

            total_old = len(old_meshes)
            for idx_om, om in enumerate(old_meshes, start=1):
                try:
                    if om.users == 0:
                        bpy.data.meshes.remove(om)
                except Exception:
                    pass
                if idx_om < total_old and (time.perf_counter() - slice_t0) >= time_slice_s:
                    yield total_objs * 2, total_objs * 2
                    slice_t0 = time.perf_counter()

        return merged_obj
    except Exception:
        if merged_bm is not None:
            try:
                merged_bm.free()
            except Exception:
                pass
        return mesh_objs[0]
    finally:
        try:
            if tmp_mesh is not None and tmp_mesh.name in bpy.data.meshes:
                bpy.data.meshes.remove(tmp_mesh)
        except Exception:
            pass


def merge_static_template_meshes(
    template_collection,
    merged_name: str = "AionMergedTemplate",
):
    """
    Synchronous wrapper around `iter_merge_static_template_meshes` merging static MESH
    sub-objects inside a CGF/CGA template collection into ONE multi-material mesh datablock.
    """
    gen = iter_merge_static_template_meshes(
        template_collection,
        merged_name=merged_name,
        time_slice_s=9999.0,
    )
    try:
        while True:
            next(gen)
    except StopIteration as exc:
        return exc.value


def _disable_obj_shadows(obj) -> None:
    if hasattr(obj, "visible_shadow"):
        try:
            obj.visible_shadow = False
        except (AttributeError, TypeError):
            pass


def iter_create_level_cgf_placement_instances(
    target_collection,
    template_collection,
    placements: tuple[LevelCgfJob, ...],
    max_placements: int,
    *,
    use_mesh_instancing: bool = True,
    disable_shadows: bool = False,
    chunk_size: int = 32,
    template_name: str | None = None,
    template_objects=None,
):
    """
    Generator yielding (placed_so_far, total_placements) every chunk_size objects
    and returning PlacementInstanceBatch via StopIteration.value.
    """
    if max_placements < 1:
        raise ValueError("max_placements must be >= 1")

    import bpy
    from mathutils import Matrix
    from editing.roundtrip_tracker import tag_object_instance

    instances = []
    summaries = []
    placement_skips = []

    # Detect if direct mesh instancing is available (hardware GPU instancing)
    source_objs = (
        list(template_objects)
        if template_objects is not None
        else (list(template_collection.objects) if template_collection else [])
    )
    mesh_objs = [o for o in source_objs if o.type == "MESH" and o.data is not None]
    tpl_label = template_name or (template_collection.name if template_collection else "AionTemplate")
    can_use_direct_mesh = use_mesh_instancing and (len(mesh_objs) >= 1)

    # Determine link target collection
    category = getattr(placements[0], "category", "PROPS") if placements else "PROPS"
    if isinstance(target_collection, dict):
        dest_col = target_collection.get(category) or target_collection.get("PROPS") or target_collection.get("ROOT")
        link_target = dest_col
    else:
        link_target = target_collection

    selected_placements = placements[:max_placements]
    total = len(selected_placements)
    step_yield = max(1, int(chunk_size))

    for idx, placement in enumerate(selected_placements, start=1):
        try:
            matrix = _placement_matrix(placement)
        except InvalidPlacementError as exc:
            placement_skips.append(
                PlacementSkip(
                    source_type=placement.source_type,
                    source_index=placement.source_index,
                    cgf_reference=placement.cgf_reference,
                    reason_code=exc.reason_code,
                    reason=str(exc),
                )
            )
            continue
        summary = _summarize_transform(placement, matrix)

        if can_use_direct_mesh:
            if len(mesh_objs) == 1:
                single_mesh = mesh_objs[0]
                instance = bpy.data.objects.new(
                    f"{tpl_label}_{placement.source_type}_{placement.source_index}",
                    single_mesh.data,
                )
                mesh_offset = single_mesh.matrix_world
                instance.matrix_world = matrix @ mesh_offset
                if disable_shadows:
                    _disable_obj_shadows(instance)
                tag_object_instance(
                    instance,
                    source_type=placement.source_type,
                    source_index=placement.source_index,
                    cgf_reference=placement.cgf_reference,
                    matrix=matrix,
                    mesh_offset=mesh_offset,
                )
                link_target.objects.link(instance)
                instances.append(instance)
            else:
                root_instance = bpy.data.objects.new(
                    f"{tpl_label}_{placement.source_type}_{placement.source_index}_0",
                    mesh_objs[0].data,
                )
                mesh_offset = mesh_objs[0].matrix_world
                root_instance.matrix_world = matrix @ mesh_offset
                if disable_shadows:
                    _disable_obj_shadows(root_instance)
                tag_object_instance(
                    root_instance,
                    source_type=placement.source_type,
                    source_index=placement.source_index,
                    cgf_reference=placement.cgf_reference,
                    matrix=matrix,
                    mesh_offset=mesh_offset,
                )
                link_target.objects.link(root_instance)
                instances.append(root_instance)

                try:
                    inv_root_mat = root_instance.matrix_world.inverted()
                except Exception:
                    inv_root_mat = Matrix.Identity(4)

                for sub_idx, sub_mesh in enumerate(mesh_objs[1:], start=1):
                    sub_inst = bpy.data.objects.new(
                        f"{tpl_label}_{placement.source_type}_{placement.source_index}_{sub_idx}",
                        sub_mesh.data,
                    )
                    sub_inst.matrix_world = matrix @ sub_mesh.matrix_world
                    sub_inst.parent = root_instance
                    sub_inst.matrix_parent_inverse = inv_root_mat
                    if disable_shadows:
                        _disable_obj_shadows(sub_inst)
                    link_target.objects.link(sub_inst)
                    instances.append(sub_inst)
        else:
            instance = bpy.data.objects.new(
                f"{tpl_label}_{placement.source_type}_{placement.source_index}",
                None,
            )
            instance.instance_type = "COLLECTION"
            instance.instance_collection = template_collection
            instance.empty_display_size = 0.001
            instance.matrix_world = matrix
            if disable_shadows:
                _disable_obj_shadows(instance)
            tag_object_instance(
                instance,
                source_type=placement.source_type,
                source_index=placement.source_index,
                cgf_reference=placement.cgf_reference,
                matrix=matrix,
            )
            link_target.objects.link(instance)
            instances.append(instance)

        summaries.append(summary)
        if idx % step_yield == 0 and idx < total:
            yield idx, total

    return PlacementInstanceBatch(
        instances=tuple(instances),
        transform_summaries=tuple(summaries),
        object_placement_count=sum(
            summary.source_type == SOURCE_OBJECT for summary in summaries
        ),
        brush_placement_count=sum(
            summary.source_type == SOURCE_BRUSH for summary in summaries
        ),
        placement_skips=tuple(placement_skips),
        invalid_placements_skipped=len(placement_skips),
        invalid_object_scale_count=sum(
            skip.reason_code == INVALID_OBJECT_SCALE
            for skip in placement_skips
        ),
        invalid_brush_matrix_count=sum(
            skip.reason_code == INVALID_BRUSH_MATRIX
            for skip in placement_skips
        ),
    )


def create_level_cgf_placement_instances(
    target_collection,
    template_collection,
    placements: tuple[LevelCgfJob, ...],
    max_placements: int,
    *,
    use_mesh_instancing: bool = True,
    disable_shadows: bool = False,
) -> PlacementInstanceBatch:
    gen = iter_create_level_cgf_placement_instances(
        target_collection,
        template_collection,
        placements,
        max_placements,
        use_mesh_instancing=use_mesh_instancing,
        disable_shadows=disable_shadows,
        chunk_size=max(1, max_placements + 1),
    )
    try:
        while True:
            next(gen)
    except StopIteration as exc:
        return exc.value


def _placement_matrix(placement: LevelCgfJob):
    from mathutils import Matrix

    if placement.source_type == SOURCE_OBJECT:
        if placement.position is None or placement.scale is None or placement.heading_degrees is None:
            raise InvalidPlacementError(
                INVALID_OBJECT_TRANSFORM,
                "object placement requires position, scale, and heading",
            )
        if not math.isfinite(placement.scale) or placement.scale <= 0:
            raise InvalidPlacementError(
                INVALID_OBJECT_SCALE,
                f"object placement scale must be finite and positive: {placement.scale}",
            )
        if not all(math.isfinite(value) for value in placement.position):
            raise InvalidPlacementError(
                INVALID_OBJECT_TRANSFORM,
                f"object placement position must be finite: {placement.position}",
            )
        if not math.isfinite(placement.heading_degrees):
            raise InvalidPlacementError(
                INVALID_OBJECT_TRANSFORM,
                f"object placement heading must be finite: {placement.heading_degrees}",
            )

        sot_matrix = (
            Matrix.Translation(placement.position)
            @ Matrix.Rotation(math.radians(placement.heading_degrees), 4, "Z")
            @ Matrix.Scale(placement.scale, 4)
        )
        return sot_matrix

    if placement.source_type == SOURCE_BRUSH:
        if placement.transform is None or len(placement.transform) != 12:
            raise InvalidPlacementError(
                INVALID_BRUSH_MATRIX,
                "brush placement requires a 12-value transform",
            )
        if not all(math.isfinite(value) for value in placement.transform):
            raise InvalidPlacementError(
                INVALID_BRUSH_MATRIX,
                "brush placement matrix contains NaN or infinity",
            )

        sot_matrix = Matrix(
            (
                placement.transform[0:4],
                placement.transform[4:8],
                placement.transform[8:12],
                (0.0, 0.0, 0.0, 1.0),
            )
        )
        return sot_matrix

    raise InvalidPlacementError(
        UNSUPPORTED_SOURCE_TYPE,
        f"unsupported placement source type: {placement.source_type}",
    )


def _summarize_transform(placement: LevelCgfJob, matrix) -> PlacementTransformSummary:
    matrix_values = tuple(float(value) for row in matrix for value in row)
    if len(matrix_values) != 16:
        raise ValueError(f"placement matrix must contain 16 values, got {len(matrix_values)}")

    identity = (
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    )
    is_non_default = (matrix_values != identity)
    return PlacementTransformSummary(
        source_type=placement.source_type,
        source_index=placement.source_index,
        matrix_values=matrix_values,
        translation=(matrix_values[3], matrix_values[7], matrix_values[11]),
        scale=placement.scale,
        heading_degrees=placement.heading_degrees,
        is_non_default=is_non_default,
    )
