from collections import Counter
from dataclasses import dataclass, replace
import math
from pathlib import Path

from formats.level import MissionPlaceableCandidate, parse_mission_placeables


MISSION_PLACEABLES_COLLECTION_NAME = "AION Mission Placeables"
MISSION_PLACEABLES_COORDINATE_VARIANT = "raw_xyz"


@dataclass(frozen=True)
class MissionPlaceableImportStatus:
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


@dataclass(frozen=True)
class MissionPlaceablesImportResult:
    requested: bool
    file_found: bool
    parsed: bool
    candidates_count: int
    created_count: int
    skipped_count: int
    failed_count: int
    angles_applied_count: int
    skip_reasons: dict
    failure_reasons: dict
    collection_name: str
    coordinate_variant: str
    candidate_statuses: tuple[MissionPlaceableImportStatus, ...]


def iter_create_mission_placeables(
    context,
    level_dir: str | Path,
    client_root: str | Path,
    *,
    apply_angles: bool = True,
    apply_smoothing_groups: bool = False,
    animate_texture_sequences: bool = False,
    animate_shader_uv_scroll: bool = False,
    texture_animation_fps: int = 10,
    limit: int | None = None,
    load_cgf=None,
    get_cgf_import_report=None,
    target_collection=None,
    disable_shadows: bool = True,
    simple_shaders: bool = False,
    batch_size: int = 8,
):
    """Time-sliced generator creating mission placeables without stalling the Blender UI thread."""
    level_path = Path(level_dir)
    client_root_path = Path(client_root)
    source_path = level_path / "mission_mission0.xml"
    if limit is not None and limit < 1:
        raise ValueError("mission placeables limit must be positive")
    if not source_path.is_file():
        return _result(
            requested=True,
            file_found=False,
            parsed=False,
            skip_reasons={"mission_file_missing": 1},
        )

    parsed = parse_mission_placeables(
        source_path,
        client_root=client_root_path,
        level_dir=level_path,
    )
    if not parsed.valid:
        return _result(
            requested=True,
            file_found=True,
            parsed=False,
            skip_reasons={parsed.reason or "parse_failed": 1},
        )

    if load_cgf is None:
        from . import cgf_importer
        load_cgf = cgf_importer.load
        get_cgf_import_report = cgf_importer.get_last_import_report

    import bpy

    try:
        from core.pak_engine import get_pak_resolver
        resolver = get_pak_resolver(client_root_path)
    except Exception:
        resolver = None

    raw_candidates = list(parsed.candidates)
    # Include PAK-backed candidates if filesystem probe left resolved_path None
    if not raw_candidates and hasattr(parsed, "skipped"):
        raw_candidates = [
            c for c in parsed.skipped
            if c.classification in {"cgf_missing", "asset_missing"} and c.asset_path
        ]
    candidates = raw_candidates[:limit] if limit is not None else raw_candidates

    collection = target_collection if target_collection is not None else bpy.data.collections.new(MISSION_PLACEABLES_COLLECTION_NAME)
    if target_collection is None:
        context.scene.collection.children.link(collection)

    col_obelisks = bpy.data.collections.new("Aion Obelisks & Binding Stones")
    collection.children.link(col_obelisks)

    col_npcs = bpy.data.collections.new("Aion Client NPCs")
    collection.children.link(col_npcs)

    col_spawns = bpy.data.collections.new("Aion NPC Spawns")
    collection.children.link(col_spawns)

    col_furniture = bpy.data.collections.new("Aion World Furniture & Milestones")
    collection.children.link(col_furniture)

    col_misc = bpy.data.collections.new("Aion General Placeables")
    collection.children.link(col_misc)

    template_cache = {}
    skip_reasons = Counter(candidate.classification for candidate in parsed.skipped)
    failure_reasons = Counter()
    candidate_statuses = []
    created_count = 0
    angles_applied_count = 0
    total = len(candidates)
    step_yield = max(1, int(batch_size))

    for idx, candidate in enumerate(candidates, start=1):
        resolved_path = candidate.resolved_path
        if (resolved_path is None or not Path(resolved_path).is_file()) and resolver is not None and candidate.asset_path:
            pak_hit = resolver.resolve_resource(candidate.asset_path)
            if pak_hit and pak_hit.is_file():
                candidate = replace(candidate, resolved_path=pak_hit)

        if candidate.resolved_path is None or not Path(candidate.resolved_path).is_file():
            skip_reasons["cgf_missing"] += 1
            candidate_statuses.append(_candidate_status(candidate, "skipped", "cgf_missing"))
            continue

        template_collection, skip_reason, failure_reason = _mission_template_collection(
            context,
            candidate,
            template_cache,
            load_cgf,
            get_cgf_import_report,
            apply_smoothing_groups=apply_smoothing_groups,
            animate_texture_sequences=animate_texture_sequences,
            animate_shader_uv_scroll=animate_shader_uv_scroll,
            texture_animation_fps=texture_animation_fps,
            client_root=str(client_root_path),
            disable_shadows=disable_shadows,
            simple_shaders=simple_shaders,
        )
        if skip_reason:
            skip_reasons[skip_reason] += 1
            candidate_statuses.append(_candidate_status(candidate, "skipped", skip_reason))
            continue
        if failure_reason:
            failure_reasons[failure_reason] += 1
            candidate_statuses.append(_candidate_status(candidate, "failed", failure_reason))
            continue
        instance = _create_placeable_instance(
            bpy,
            candidate,
            template_collection,
            apply_angles=apply_angles,
            disable_shadows=disable_shadows,
        )

        # Route to appropriate subcollection
        if candidate.category == "obelisk":
            target_col = col_obelisks
        elif candidate.category == "client_npc":
            target_col = col_npcs
        elif candidate.category == "npc_spawn":
            target_col = col_spawns
        elif candidate.category == "furniture":
            target_col = col_furniture
        else:
            target_col = col_misc

        target_col.objects.link(instance)
        candidate_statuses.append(
            _candidate_status(
                candidate,
                "created",
                "",
                object_name=instance.name,
                collection_name=target_col.name,
            )
        )
        created_count += 1
        if instance.get("aion_rotation_used"):
            angles_applied_count += 1
        if idx % step_yield == 0 and idx < total:
            yield idx, total

    # Prune empty subcollections
    for sub in (col_obelisks, col_npcs, col_spawns, col_furniture, col_misc):
        if not sub.objects and not sub.children:
            try:
                collection.children.unlink(sub)
                bpy.data.collections.remove(sub)
            except Exception:
                pass

    return _result(
        requested=True,
        file_found=True,
        parsed=True,
        candidates_count=len(candidates),
        created_count=created_count,
        skipped_count=sum(skip_reasons.values()),
        failed_count=sum(failure_reasons.values()),
        angles_applied_count=angles_applied_count,
        skip_reasons=dict(skip_reasons),
        failure_reasons=dict(failure_reasons),
        candidate_statuses=tuple(candidate_statuses),
    )


def create_mission_placeables(
    context,
    level_dir: str | Path,
    client_root: str | Path,
    *,
    apply_angles: bool = True,
    apply_smoothing_groups: bool = False,
    animate_texture_sequences: bool = False,
    animate_shader_uv_scroll: bool = False,
    texture_animation_fps: int = 10,
    limit: int | None = None,
    load_cgf=None,
    get_cgf_import_report=None,
    target_collection=None,
    disable_shadows: bool = True,
    simple_shaders: bool = False,
) -> MissionPlaceablesImportResult:
    gen = iter_create_mission_placeables(
        context,
        level_dir,
        client_root,
        apply_angles=apply_angles,
        apply_smoothing_groups=apply_smoothing_groups,
        animate_texture_sequences=animate_texture_sequences,
        animate_shader_uv_scroll=animate_shader_uv_scroll,
        texture_animation_fps=texture_animation_fps,
        limit=limit,
        load_cgf=load_cgf,
        get_cgf_import_report=get_cgf_import_report,
        target_collection=target_collection,
        disable_shadows=disable_shadows,
        simple_shaders=simple_shaders,
        batch_size=999999,
    )
    try:
        while True:
            next(gen)
    except StopIteration as exc:
        return exc.value


def _mission_template_collection(
    context,
    candidate: MissionPlaceableCandidate,
    template_cache,
    load_cgf,
    get_cgf_import_report,
    *,
    apply_smoothing_groups: bool,
    animate_texture_sequences: bool,
    animate_shader_uv_scroll: bool,
    texture_animation_fps: int,
    client_root: str | None = None,
    disable_shadows: bool = True,
    simple_shaders: bool = False,
):
    key = str(candidate.resolved_path)
    cached = template_cache.get(key)
    if cached is not None:
        return cached, None, None

    import bpy

    collections_before = set(bpy.data.collections)
    try:
        try:
            result = load_cgf(
                context,
                str(candidate.resolved_path),
                import_mode="VISUAL",
                apply_smoothing_groups=apply_smoothing_groups,
                animate_texture_sequences=animate_texture_sequences,
                animate_shader_uv_scroll=animate_shader_uv_scroll,
                texture_animation_fps=texture_animation_fps,
                client_root=client_root,
                simple_shaders=simple_shaders,
            )
        except TypeError:
            try:
                result = load_cgf(
                    context,
                    str(candidate.resolved_path),
                    import_mode="VISUAL",
                    apply_smoothing_groups=apply_smoothing_groups,
                    animate_texture_sequences=animate_texture_sequences,
                    animate_shader_uv_scroll=animate_shader_uv_scroll,
                    texture_animation_fps=texture_animation_fps,
                    client_root=client_root,
                )
            except TypeError:
                result = load_cgf(
                    context,
                    str(candidate.resolved_path),
                    import_mode="VISUAL",
                    apply_smoothing_groups=apply_smoothing_groups,
                    animate_texture_sequences=animate_texture_sequences,
                    animate_shader_uv_scroll=animate_shader_uv_scroll,
                    texture_animation_fps=texture_animation_fps,
                )
    except Exception as exc:
        return None, None, f"cgf_error_{type(exc).__name__}"
    report = get_cgf_import_report() if get_cgf_import_report is not None else None
    if result != {"FINISHED"}:
        reason_code = getattr(report, "reason_code", None) or "unknown"
        if reason_code in {"empty_mesh", "no_geometry_for_mode"}:
            return None, reason_code, None
        return None, None, reason_code

    new_collections = tuple(
        collection for collection in bpy.data.collections if collection not in collections_before
    )
    template_collection = _find_imported_collection(new_collections)
    if template_collection is None:
        return None, "no_template_collection", None
    if disable_shadows:
        for t_obj in template_collection.objects:
            if hasattr(t_obj, "visible_shadow"):
                try:
                    t_obj.visible_shadow = False
                except (AttributeError, TypeError):
                    pass
    _unlink_from_scene_root(context, template_collection)
    template_cache[key] = template_collection
    return template_collection, None, None


def _create_placeable_instance(bpy, candidate, template_collection, *, apply_angles, disable_shadows: bool = True):
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
    rotation_used = False
    if apply_angles and candidate.angles is not None:
        obj.rotation_euler = tuple(math.radians(value) for value in candidate.angles)
        rotation_used = True
    if candidate.scale is not None:
        obj.scale = candidate.scale
    _assign_custom_properties(obj, candidate, rotation_used)
    return obj


def _assign_custom_properties(obj, candidate, rotation_used):
    obj["aion_mission_placeable"] = True
    obj["aion_source_file"] = candidate.source_file
    obj["aion_entity_id"] = candidate.entity_id
    obj["aion_entity_name"] = candidate.entity_name
    obj["aion_asset_ref"] = candidate.asset_path
    obj["aion_raw_pos"] = tuple(float(value) for value in candidate.position)
    obj["aion_angles"] = tuple(float(value) for value in candidate.angles) if candidate.angles else ()
    obj["aion_rotation_used"] = bool(rotation_used)
    obj["aion_scale_used"] = bool(candidate.scale is not None)
    obj["aion_coordinate_variant"] = MISSION_PLACEABLES_COORDINATE_VARIANT
    obj["aion_placement_confidence"] = candidate.confidence
    obj["aion_classification"] = candidate.classification
    obj["aion_category"] = candidate.category
    obj["aion_is_obelisk"] = (candidate.category == "obelisk")
    obj["aion_is_client_npc"] = (candidate.category == "client_npc")


def _raw_position(position):
    if position is None:
        raise ValueError("mission placeable position is missing")
    values = tuple(float(value) for value in position)
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise ValueError(f"invalid mission placeable position: {position}")
    return values


def _object_name(candidate):
    prefix = "AION_Placeable"
    if candidate.category == "obelisk":
        prefix = "AION_Obelisk"
    elif candidate.category == "client_npc":
        prefix = "AION_ClientNPC"
    elif candidate.category == "npc_spawn":
        prefix = "AION_Spawn"
    elif candidate.category == "furniture":
        prefix = "AION_Prop"
    base = candidate.entity_name or Path(candidate.asset_path).stem or "Object"
    return f"{prefix}_{base}"


def _candidate_status(
    candidate,
    status,
    reason,
    *,
    object_name="",
    collection_name="",
):
    return MissionPlaceableImportStatus(
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
    skip_reasons=None,
    failure_reasons=None,
    candidate_statuses=(),
):
    return MissionPlaceablesImportResult(
        requested=bool(requested),
        file_found=bool(file_found),
        parsed=bool(parsed),
        candidates_count=int(candidates_count),
        created_count=int(created_count),
        skipped_count=int(skipped_count),
        failed_count=int(failed_count),
        angles_applied_count=int(angles_applied_count),
        skip_reasons=dict(skip_reasons or {}),
        failure_reasons=dict(failure_reasons or {}),
        collection_name=MISSION_PLACEABLES_COLLECTION_NAME,
        coordinate_variant=MISSION_PLACEABLES_COORDINATE_VARIANT,
        candidate_statuses=tuple(candidate_statuses),
    )
