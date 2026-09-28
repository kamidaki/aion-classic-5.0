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


def create_level_cgf_placement_instances(
    target_collection,
    template_collection,
    placements: tuple[LevelCgfJob, ...],
    max_placements: int,
    *,
    use_mesh_instancing: bool = True,
) -> PlacementInstanceBatch:
    if max_placements < 1:
        raise ValueError("max_placements must be >= 1")

    import bpy
    from mathutils import Matrix
    from editing.roundtrip_tracker import tag_object_instance

    instances = []
    summaries = []
    placement_skips = []

    # Detect if direct mesh instancing is available (hardware GPU instancing)
    mesh_objs = [o for o in template_collection.objects if o.type == "MESH"] if template_collection else []
    can_use_direct_mesh = use_mesh_instancing and (len(mesh_objs) >= 1)

    for placement in placements[:max_placements]:
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

        category = getattr(placement, "category", "PROPS")
        if isinstance(target_collection, dict):
            dest_col = target_collection.get(category) or target_collection.get("PROPS") or target_collection.get("ROOT")
        else:
            dest_col = target_collection

        if can_use_direct_mesh:
            if len(mesh_objs) == 1:
                # Single-mesh template: share vertex/index buffers directly
                single_mesh = mesh_objs[0]
                instance = bpy.data.objects.new(
                    f"{template_collection.name}_{placement.source_type}_{placement.source_index}",
                    single_mesh.data,
                )
                mesh_offset = single_mesh.matrix_world
                instance.matrix_world = matrix @ mesh_offset
                tag_object_instance(
                    instance,
                    source_type=placement.source_type,
                    source_index=placement.source_index,
                    cgf_reference=placement.cgf_reference,
                    matrix=matrix,
                    mesh_offset=mesh_offset,
                )
                dest_col.objects.link(instance)
                instances.append(instance)
            else:
                # Multi-mesh template: direct GPU mesh instancing for all sub-meshes
                # Completely eliminates heavy COLLECTION instancing that freezes the Blender depsgraph
                root_instance = bpy.data.objects.new(
                    f"{template_collection.name}_{placement.source_type}_{placement.source_index}_0",
                    mesh_objs[0].data,
                )
                mesh_offset = mesh_objs[0].matrix_world
                root_instance.matrix_world = matrix @ mesh_offset
                tag_object_instance(
                    root_instance,
                    source_type=placement.source_type,
                    source_index=placement.source_index,
                    cgf_reference=placement.cgf_reference,
                    matrix=matrix,
                    mesh_offset=mesh_offset,
                )
                dest_col.objects.link(root_instance)
                instances.append(root_instance)

                try:
                    inv_root_mat = root_instance.matrix_world.inverted()
                except Exception:
                    inv_root_mat = Matrix.Identity(4)

                for sub_idx, sub_mesh in enumerate(mesh_objs[1:], start=1):
                    sub_inst = bpy.data.objects.new(
                        f"{template_collection.name}_{placement.source_type}_{placement.source_index}_{sub_idx}",
                        sub_mesh.data,
                    )
                    sub_inst.matrix_world = matrix @ sub_mesh.matrix_world
                    sub_inst.parent = root_instance
                    sub_inst.matrix_parent_inverse = inv_root_mat
                    dest_col.objects.link(sub_inst)
                    instances.append(sub_inst)
        else:
            instance = bpy.data.objects.new(
                f"{template_collection.name}_{placement.source_type}_{placement.source_index}",
                None,
            )
            instance.instance_type = "COLLECTION"
            instance.instance_collection = template_collection
            instance.empty_display_size = 0.001
            instance.matrix_world = matrix
            tag_object_instance(
                instance,
                source_type=placement.source_type,
                source_index=placement.source_index,
                cgf_reference=placement.cgf_reference,
                matrix=matrix,
            )
            dest_col.objects.link(instance)
            instances.append(instance)

        summaries.append(summary)

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
