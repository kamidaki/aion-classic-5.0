from collections import Counter
from dataclasses import dataclass
import math
from pathlib import Path

from aion_formats.level import CgaEntityCandidate, parse_mission_cga_entities


CGA_ENTITIES_COLLECTION_NAME = "Aion CGA Entities"
CGA_ENTITIES_COORDINATE_VARIANT = "raw_xyz"


@dataclass(frozen=True)
class CgaEntityImportStatus:
    asset_path: str
    resolved_path: str
    entity_id: str
    entity_name: str
    position: tuple[float, float, float] | None
    angles: tuple[float, float, float] | None
    classification: str
    confidence: str
    status: str
    reason: str
    object_name: str
    collection_name: str
    controller_count: int
    timing_present: bool


@dataclass(frozen=True)
class CgaEntitiesImportResult:
    requested: bool
    file_found: bool
    parsed: bool
    candidates_count: int
    created_count: int
    skipped_count: int
    failed_count: int
    angles_applied_count: int
    controller_count_total: int
    timing_present_count: int
    skip_reasons: dict
    failure_reasons: dict
    collection_name: str
    coordinate_variant: str
    candidate_statuses: tuple[CgaEntityImportStatus, ...]


def iter_create_cga_entities(
    context,
    level_dir: str | Path,
    client_root: str | Path,
    *,
    import_mode: str = "VISUAL",
    apply_angles: bool = True,
    apply_smoothing_groups: bool = False,
    animate_texture_sequences: bool = False,
    animate_shader_uv_scroll: bool = False,
    animate_cga_controllers: bool = False,
    texture_animation_fps: int = 10,
    limit: int | None = None,
    load_cgf=None,
    get_cgf_import_report=None,
    simple_shaders: bool = False,
    disable_shadows: bool = False,
    merge_static_meshes: bool = True,
    batch_size: int = 4,
    pre_parsed=None,
    parent_collection=None,
):
    """Linearly yields progress while creating CGA entity instances without UI stalls."""
    level_path = Path(level_dir)
    client_root_path = Path(client_root)
    source_path = level_path / "mission_mission0.xml"
    if import_mode not in {"VISUAL", "COLLISION"}:
        raise ValueError(f"unsupported CGA entity import mode: {import_mode}")
    if import_mode == "COLLISION":
        apply_smoothing_groups = False
        animate_texture_sequences = False
        animate_shader_uv_scroll = False
        animate_cga_controllers = False
    if limit is not None and limit < 1:
        raise ValueError("CGA entities limit must be positive")
    if pre_parsed is None:
        if not source_path.is_file():
            return _result(
                requested=True,
                file_found=False,
                parsed=False,
                skip_reasons={"mission_file_missing": 1},
            )

        parsed = parse_mission_cga_entities(
            source_path,
            client_root=client_root_path,
            level_dir=level_path,
        )
    else:
        parsed = pre_parsed
    if not parsed.valid:
        return _result(
            requested=True,
            file_found=True,
            parsed=False,
            skip_reasons={parsed.reason or "parse_failed": 1},
        )

    candidates = parsed.candidates[:limit] if limit is not None else parsed.candidates
    skip_reasons = Counter(candidate.classification for candidate in parsed.skipped)
    if not candidates:
        return _result(
            requested=True,
            file_found=True,
            parsed=True,
            candidates_count=0,
            created_count=0,
            skipped_count=sum(skip_reasons.values()),
            failed_count=0,
            skip_reasons=dict(skip_reasons),
        )

    if load_cgf is None:
        from . import cgf_importer
        load_cgf = cgf_importer.load
        get_cgf_import_report = cgf_importer.get_last_import_report

    import bpy
    import time
    from .level_instances import merge_static_template_meshes

    host_col = parent_collection if parent_collection is not None else context.scene.collection
    collection = bpy.data.collections.new(CGA_ENTITIES_COLLECTION_NAME)
    host_col.children.link(collection)
    template_cache = {}
    failure_reasons = Counter()
    candidate_statuses = []
    created_count = 0
    angles_applied_count = 0
    controller_count_total = 0
    timing_present_count = 0
    total = len(candidates)
    slice_t0 = time.perf_counter()

    for idx, candidate in enumerate(candidates, start=1):
        template_collection, report, skip_reason, failure_reason = _cga_template_collection(
            context,
            candidate,
            template_cache,
            load_cgf,
            get_cgf_import_report,
            import_mode=import_mode,
            apply_smoothing_groups=apply_smoothing_groups,
            animate_texture_sequences=animate_texture_sequences,
            animate_shader_uv_scroll=animate_shader_uv_scroll,
            animate_cga_controllers=animate_cga_controllers,
            texture_animation_fps=texture_animation_fps,
            client_root=str(client_root_path),
            simple_shaders=simple_shaders,
            merge_static_meshes=merge_static_meshes and not animate_cga_controllers,
            merge_helper=merge_static_template_meshes,
        )
        controller_count = getattr(report, "cga_controller_count", 0) if report else 0
        timing_present = bool(getattr(report, "cga_timing_present", False)) if report else False
        if skip_reason:
            skip_reasons[skip_reason] += 1
            candidate_statuses.append(
                _candidate_status(candidate, "skipped", skip_reason, controller_count, timing_present)
            )
        elif failure_reason:
            failure_reasons[failure_reason] += 1
            candidate_statuses.append(
                _candidate_status(candidate, "failed", failure_reason, controller_count, timing_present)
            )
        else:
            instance = _create_cga_instance(
                bpy,
                candidate,
                template_collection,
                controller_count,
                timing_present,
                getattr(report, "cga_animation_status", "controller_not_decoded"),
                getattr(report, "cga_controller_animations_applied", 0),
                import_mode=import_mode,
                apply_angles=apply_angles,
                use_direct_mesh=not animate_cga_controllers,
                disable_shadows=disable_shadows,
            )
            collection.objects.link(instance)
            candidate_statuses.append(
                _candidate_status(
                    candidate,
                    "created",
                    "",
                    controller_count,
                    timing_present,
                    object_name=instance.name,
                    collection_name=collection.name,
                )
            )
            created_count += 1
            controller_count_total += controller_count
            if timing_present:
                timing_present_count += 1
            if instance.get("aion_cga_angles_used"):
                angles_applied_count += 1
        if idx < total and (idx % max(1, batch_size) == 0 or (time.perf_counter() - slice_t0) >= 0.008):
            yield idx, total
            slice_t0 = time.perf_counter()

    if created_count == 0 and len(collection.objects) == 0 and len(collection.children) == 0:
        if collection.name in host_col.children.keys():
            host_col.children.unlink(collection)
        bpy.data.collections.remove(collection)

    return _result(
        requested=True,
        file_found=True,
        parsed=True,
        candidates_count=len(candidates),
        created_count=created_count,
        skipped_count=sum(skip_reasons.values()),
        failed_count=sum(failure_reasons.values()),
        angles_applied_count=angles_applied_count,
        controller_count_total=controller_count_total,
        timing_present_count=timing_present_count,
        skip_reasons=dict(skip_reasons),
        failure_reasons=dict(failure_reasons),
        candidate_statuses=tuple(candidate_statuses),
    )


def create_cga_entities(
    context,
    level_dir: str | Path,
    client_root: str | Path,
    *,
    import_mode: str = "VISUAL",
    apply_angles: bool = True,
    apply_smoothing_groups: bool = False,
    animate_texture_sequences: bool = False,
    animate_shader_uv_scroll: bool = False,
    animate_cga_controllers: bool = False,
    texture_animation_fps: int = 10,
    limit: int | None = None,
    load_cgf=None,
    get_cgf_import_report=None,
    simple_shaders: bool = False,
    disable_shadows: bool = False,
) -> CgaEntitiesImportResult:
    gen = iter_create_cga_entities(
        context,
        level_dir,
        client_root,
        import_mode=import_mode,
        apply_angles=apply_angles,
        apply_smoothing_groups=apply_smoothing_groups,
        animate_texture_sequences=animate_texture_sequences,
        animate_shader_uv_scroll=animate_shader_uv_scroll,
        animate_cga_controllers=animate_cga_controllers,
        texture_animation_fps=texture_animation_fps,
        limit=limit,
        load_cgf=load_cgf,
        get_cgf_import_report=get_cgf_import_report,
        simple_shaders=simple_shaders,
        disable_shadows=disable_shadows,
        batch_size=100000,
    )
    try:
        while True:
            next(gen)
    except StopIteration as exc:
        return exc.value


def _cga_template_collection(
    context,
    candidate: CgaEntityCandidate,
    template_cache,
    load_cgf,
    get_cgf_import_report,
    *,
    import_mode: str,
    apply_smoothing_groups: bool,
    animate_texture_sequences: bool,
    animate_shader_uv_scroll: bool,
    animate_cga_controllers: bool,
    texture_animation_fps: int,
    client_root: str | None = None,
    simple_shaders: bool = False,
    merge_static_meshes: bool = False,
    merge_helper=None,
):
    key = (str(candidate.resolved_path), import_mode)
    cached = template_cache.get(key)
    if cached is not None:
        return cached

    import bpy

    collections_before = set(bpy.data.collections)
    try:
        try:
            result = load_cgf(
                context,
                str(candidate.resolved_path),
                import_mode=import_mode,
                apply_smoothing_groups=apply_smoothing_groups,
                animate_texture_sequences=animate_texture_sequences,
                animate_shader_uv_scroll=animate_shader_uv_scroll,
                animate_cga_controllers=animate_cga_controllers,
                texture_animation_fps=texture_animation_fps,
                client_root=client_root,
                simple_shaders=simple_shaders,
                link_to_scene=False,
            )
        except TypeError:
            try:
                result = load_cgf(
                    context,
                    str(candidate.resolved_path),
                    import_mode=import_mode,
                    apply_smoothing_groups=apply_smoothing_groups,
                    animate_texture_sequences=animate_texture_sequences,
                    animate_shader_uv_scroll=animate_shader_uv_scroll,
                    animate_cga_controllers=animate_cga_controllers,
                    texture_animation_fps=texture_animation_fps,
                    client_root=client_root,
                    simple_shaders=simple_shaders,
                )
            except TypeError:
                try:
                    result = load_cgf(
                        context,
                        str(candidate.resolved_path),
                        import_mode=import_mode,
                        apply_smoothing_groups=apply_smoothing_groups,
                        animate_texture_sequences=animate_texture_sequences,
                        animate_shader_uv_scroll=animate_shader_uv_scroll,
                        animate_cga_controllers=animate_cga_controllers,
                        texture_animation_fps=texture_animation_fps,
                        client_root=client_root,
                    )
                except TypeError:
                    result = load_cgf(
                        context,
                        str(candidate.resolved_path),
                        import_mode=import_mode,
                        apply_smoothing_groups=apply_smoothing_groups,
                        animate_texture_sequences=animate_texture_sequences,
                        animate_shader_uv_scroll=animate_shader_uv_scroll,
                        animate_cga_controllers=animate_cga_controllers,
                        texture_animation_fps=texture_animation_fps,
                    )
    except Exception as exc:
        return None, None, None, f"cga_error_{type(exc).__name__}"
    report = get_cgf_import_report() if get_cgf_import_report is not None else None
    if result != {"FINISHED"}:
        reason_code = getattr(report, "reason_code", None) or "unknown"
        if reason_code in {"empty_mesh", "no_geometry_for_mode"}:
            return None, report, reason_code, None
        return None, report, None, reason_code

    new_collections = tuple(
        collection for collection in bpy.data.collections if collection not in collections_before
    )
    template_collection = _find_imported_collection(new_collections)
    if template_collection is None:
        return None, report, "no_template_collection", None
    if merge_static_meshes and merge_helper is not None:
        try:
            merge_helper(template_collection, f"CGA_{Path(candidate.resolved_path).stem}")
        except Exception:
            pass
    _unlink_from_scene_root(context, template_collection)
    template_cache[key] = (template_collection, report, None, None)
    return template_cache[key]


def _create_cga_instance(
    bpy,
    candidate,
    template_collection,
    controller_count,
    timing_present,
    animation_status,
    animations_applied,
    *,
    import_mode,
    apply_angles,
    use_direct_mesh: bool = False,
    disable_shadows: bool = False,
):
    mesh_objs = [o for o in template_collection.objects if o.type == "MESH" and o.data is not None] if template_collection else []
    if use_direct_mesh and len(mesh_objs) == 1:
        obj = bpy.data.objects.new(_object_name(candidate), mesh_objs[0].data)
    else:
        obj = bpy.data.objects.new(_object_name(candidate), None)
        obj.instance_type = "COLLECTION"
        obj.instance_collection = template_collection
        obj.empty_display_size = 0.001
    if disable_shadows and hasattr(obj, "visible_shadow"):
        try:
            obj.visible_shadow = False
        except (AttributeError, TypeError):
            pass
    obj.location = _raw_position(candidate.position)
    angles_used = False
    if apply_angles and candidate.angles is not None:
        obj.rotation_euler = tuple(math.radians(value) for value in candidate.angles)
        angles_used = True
    _assign_custom_properties(
        obj,
        candidate,
        controller_count,
        timing_present,
        animation_status,
        animations_applied,
        import_mode,
        angles_used,
    )
    return obj


def _assign_custom_properties(
    obj,
    candidate,
    controller_count,
    timing_present,
    animation_status,
    animations_applied,
    import_mode,
    angles_used,
):
    obj["aion_cga_entity"] = True
    obj["aion_source_extension"] = ".cga"
    obj["aion_cga_static_import"] = True
    obj["aion_cga_controller_count"] = int(controller_count)
    obj["aion_cga_timing_present"] = bool(timing_present)
    obj["aion_cga_animation_status"] = str(animation_status or "controller_not_decoded")
    obj["aion_cga_controller_animations_applied"] = int(animations_applied or 0)
    obj["aion_import_mode"] = str(import_mode)
    obj["aion_source_file"] = candidate.source_file
    obj["aion_entity_id"] = candidate.entity_id
    obj["aion_entity_name"] = candidate.entity_name
    obj["aion_entity_class"] = candidate.entity_class
    obj["aion_asset_ref"] = candidate.asset_path
    obj["aion_raw_pos"] = tuple(float(value) for value in candidate.position)
    obj["aion_angles"] = tuple(float(value) for value in candidate.angles) if candidate.angles else ()
    obj["aion_cga_angles_used"] = bool(angles_used)
    obj["aion_scale_used"] = False
    obj["aion_coordinate_variant"] = CGA_ENTITIES_COORDINATE_VARIANT
    obj["aion_placement_confidence"] = candidate.confidence
    obj["aion_classification"] = candidate.classification
    obj["aion_cga_animation_name"] = candidate.animation_name
    obj["aion_cga_animation_loop"] = bool(candidate.animation_loop)
    obj["aion_cga_animation_playing"] = bool(candidate.animation_playing)


def _raw_position(position):
    if position is None:
        raise ValueError("CGA entity position is missing")
    values = tuple(float(value) for value in position)
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise ValueError(f"invalid CGA entity position: {position}")
    return values


def _object_name(candidate):
    base = candidate.entity_name or Path(candidate.asset_path).stem or "CgaEntity"
    return f"AION_CGAEntity_{base}"


def _candidate_status(
    candidate,
    status,
    reason,
    controller_count,
    timing_present,
    *,
    object_name="",
    collection_name="",
):
    return CgaEntityImportStatus(
        asset_path=candidate.asset_path,
        resolved_path=str(candidate.resolved_path) if candidate.resolved_path else "",
        entity_id=candidate.entity_id,
        entity_name=candidate.entity_name,
        position=tuple(candidate.position) if candidate.position else None,
        angles=tuple(candidate.angles) if candidate.angles else None,
        classification=candidate.classification,
        confidence=candidate.confidence,
        status=status,
        reason=reason,
        object_name=object_name,
        collection_name=collection_name,
        controller_count=int(controller_count),
        timing_present=bool(timing_present),
    )


def _find_imported_collection(new_collections):
    candidates = tuple(new_collections)
    if len(candidates) == 1:
        return candidates[0]
    return candidates[-1] if candidates else None


def _unlink_from_scene_root(context, collection):
    root_children = context.scene.collection.children
    if collection.name in root_children.keys():
        root_children.unlink(collection)


def _result(
    *,
    requested,
    file_found,
    parsed,
    candidates_count=0,
    created_count=0,
    skipped_count=0,
    failed_count=0,
    angles_applied_count=0,
    controller_count_total=0,
    timing_present_count=0,
    skip_reasons=None,
    failure_reasons=None,
    candidate_statuses=(),
):
    return CgaEntitiesImportResult(
        requested=bool(requested),
        file_found=bool(file_found),
        parsed=bool(parsed),
        candidates_count=int(candidates_count),
        created_count=int(created_count),
        skipped_count=int(skipped_count),
        failed_count=int(failed_count),
        angles_applied_count=int(angles_applied_count),
        controller_count_total=int(controller_count_total),
        timing_present_count=int(timing_present_count),
        skip_reasons=dict(skip_reasons or {}),
        failure_reasons=dict(failure_reasons or {}),
        collection_name=CGA_ENTITIES_COLLECTION_NAME,
        coordinate_variant=CGA_ENTITIES_COORDINATE_VARIANT,
        candidate_statuses=tuple(candidate_statuses),
    )
