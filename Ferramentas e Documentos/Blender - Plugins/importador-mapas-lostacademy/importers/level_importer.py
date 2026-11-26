from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path
import threading
import time
from typing import Callable, Iterable

from config.performance_profiles import (
    apply_viewport_60fps_optimization,
    frame_viewport_on_map,
    normalize_performance_profile,
    resolve_profile_settings,
)
from formats.level import (
    LIQUID_KIND_AUTO,
    LIQUID_PRESET_AUTO,
    build_liquid_surface_recipe,
    extract_liquid_references,
    parse_brush_lst,
    parse_land_map_h32,
    parse_leveldata,
    parse_objects_lst,
)

from .cga_entities_importer import (
    CgaEntitiesImportResult,
    create_cga_entities,
    iter_create_cga_entities,
)
from .level_instances import (
    INVALID_BRUSH_MATRIX,
    INVALID_OBJECT_SCALE,
    PlacementSkip,
    PlacementTransformSummary,
    create_level_cgf_placement_instances,
    iter_create_level_cgf_placement_instances,
    iter_merge_static_template_meshes,
    merge_static_template_meshes,
)
from .level_jobs import collect_level_cgf_jobs
from .environment_importer import SkyboxImportResult, create_skybox_preview, create_environment_lighting_preview
from .level_summary import LevelImportExecutionSummary
from .level_templates import LevelCgfTemplate, group_level_cgf_templates
from .liquid_surface_importer import (
    LiquidSurfaceMaterialResult,
    apply_liquid_surface_material,
    skipped_liquid_surface_result,
)
from .mission_placeables_importer import (
    MissionPlaceablesImportResult,
    create_mission_placeables,
    iter_create_mission_placeables,
)
from .particle_effects_importer import (
    ParticleEffectsImportResult,
    create_particle_effects,
    iter_create_particle_effects,
    prepare_particle_effects_stage_data,
)
from core.resource_resolver import (
    LevelCgfResolutionResult,
    ResolvedLevelCgfJob,
    resolve_level_cgf_jobs,
)
from core.pak_engine import AionLevelUnpacker
from animations.wind_system import apply_vegetation_wind_sway
from animations.water_animation import apply_water_wave_animation
from .static_lights_importer import (
    DEFAULT_STATIC_LIGHT_POWER,
    STATIC_LIGHTS_MODE_POINT_LIGHT,
    StaticLightsImportResult,
    create_static_deferred_lights,
)
from .terrain_importer import (
    DEFAULT_XY_SCALE,
    TerrainMeshResult,
    create_terrain_mesh,
    iter_create_terrain_mesh,
    prepare_terrain_stage_data,
)
from .water_importer import WaterPlaneResult, create_water_plane, create_water_volumes



LEVEL_COLLECTION_NAME = "Aion Level Import"
PREVIEW_COLLECTION_NAME = "Aion Level Import Preview"


@dataclass(frozen=True)
class LevelCgfImportFailure:
    normalized_reference: str
    resolved_path: Path
    import_mode: str
    reason_code: str
    reason: str
    parser_node_count: int = 0
    parser_mesh_node_count: int = 0
    parser_material_count: int = 0
    candidate_mesh_node_count: int = 0
    parser_coverage_counts: dict | None = None
    unsupported_chunks: dict | None = None
    unused_material_fields: dict | None = None


@dataclass(frozen=True)
class LevelCgfImportSkip:
    normalized_reference: str
    resolved_path: Path
    import_mode: str
    reason_code: str
    reason: str
    parser_node_count: int = 0
    parser_mesh_node_count: int = 0
    parser_material_count: int = 0
    candidate_mesh_node_count: int = 0
    parser_coverage_counts: dict | None = None
    unsupported_chunks: dict | None = None
    unused_material_fields: dict | None = None


@dataclass(frozen=True)
class LevelTemplatePlacementStats:
    normalized_reference: str
    import_mode: str
    available_placement_count: int
    created_placement_count: int


@dataclass(frozen=True)
class LevelImportProgress:
    stage: str
    message: str
    completed: int
    total: int

    @property
    def fraction(self) -> float:
        if self.total < 1:
            return 0.0
        return min(max(self.completed / self.total, 0.0), 1.0)


@dataclass(frozen=True)
class LevelImportResult:
    level_dir: Path
    client_root: Path
    import_mode: str
    limited_preview: bool
    max_unique_cgfs: int
    max_placements_per_template: int
    resolved_job_count: int
    missing_resource_count: int
    total_template_count: int
    max_available_placements_per_template: int
    selected_template_count: int
    imported_template_count: int
    skipped_template_count: int
    failed_template_count: int
    selected_placement_count: int
    placement_objects_created: int
    object_placement_count: int
    brush_placement_count: int
    non_default_transform_count: int
    invalid_placements_skipped: int
    invalid_object_scale_count: int
    invalid_brush_matrix_count: int
    first_invalid_placement: PlacementSkip | None
    transform_summaries: tuple[PlacementTransformSummary, ...]
    per_template_placement_counts: tuple[LevelTemplatePlacementStats, ...]
    terrain_mesh_result: TerrainMeshResult | None
    water_result: WaterPlaneResult | None
    liquid_surface_result: LiquidSurfaceMaterialResult | None
    static_lights_result: StaticLightsImportResult | None
    mission_placeables_result: MissionPlaceablesImportResult | None
    particle_effects_result: ParticleEffectsImportResult | None
    cga_entities_result: CgaEntitiesImportResult | None
    summary: LevelImportExecutionSummary
    objects_created: int
    meshes_created: int
    failures: tuple[LevelCgfImportFailure, ...]
    skipped_templates: tuple[LevelCgfImportSkip, ...]
    skybox_result: SkyboxImportResult | None = None
    environment_lighting_result: SkyboxImportResult | None = None
    npc_result: object | None = None





def select_level_cgf_templates(
    templates: Iterable[LevelCgfTemplate],
    max_unique_cgfs: int,
) -> tuple[LevelCgfTemplate, ...]:
    if max_unique_cgfs < 1:
        raise ValueError("max_unique_cgfs must be >= 1")

    selected = []
    for template in sorted(
        templates,
        key=lambda item: item.placement_count,
        reverse=True,
    ):
        selected.append(template)
        if len(selected) >= max_unique_cgfs:
            break

    return tuple(selected)


def _resolve_cgf_chunk_worker(
    resolver,
    chunk_pairs: list[tuple[str, str]],
    target_lod: int,
    cancel_event: threading.Event | None = None,
) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    if resolver is None:
        return resolved
    for norm, orig in chunk_pairs:
        if cancel_event is not None and cancel_event.is_set():
            break
        res_path = resolver.resolve_resource(orig, target_lod=target_lod)
        if res_path and res_path.is_file():
            resolved[norm] = res_path
    return resolved


def _ensure_catalog_worker(
    client_root: str | Path,
    preload_shaders: bool = True,
    cancel_event: threading.Event | None = None,
):
    from core.pak_engine import get_pak_resolver
    resolver = get_pak_resolver(client_root)
    if resolver:
        resolver.ensure_catalog(cancel_event=cancel_event)
        if preload_shaders and not (cancel_event is not None and cancel_event.is_set()):
            try:
                from formats.cgf.shader_semantics import _ensure_shader_cache
                _ensure_shader_cache(Path(client_root))
            except Exception:
                pass
        return resolver, resolver.catalog
    return None, None


def _parse_stage3_worker(
    level_path: Path,
    terrain_path: Path,
    read_terrain: bool,
    terrain_lod: int,
    client_root: str | Path | None,
    visual_mode: bool,
    compute_blend: bool,
    cancel_event: threading.Event | None = None,
):
    if cancel_event is not None and cancel_event.is_set():
        return None, None, None, None, None
    level_data, objects, brush = _parse_level_cgf_sources(level_path)
    if cancel_event is not None and cancel_event.is_set():
        return level_data, objects, brush, None, None
    land_map = parse_land_map_h32(terrain_path) if (read_terrain and terrain_path.is_file()) else None
    precomputed_terrain = None
    if land_map is not None and not (cancel_event is not None and cancel_event.is_set()):
        precomputed_terrain = prepare_terrain_stage_data(
            land_map,
            level_data=level_data if visual_mode else None,
            client_root=client_root if visual_mode else None,
            lod=terrain_lod,
            compute_blend=compute_blend,
        )
    return level_data, objects, brush, land_map, precomputed_terrain


def _prepare_stage4_worker(
    level_path: Path,
    client_root_path: Path,
    level_data,
    liquid_kind: str,
    liquid_preset: str,
    skybox_time_option: str,
    want_liquid_recipe: bool,
    want_env: bool,
    cancel_event: threading.Event | None = None,
):
    liquid_recipe = None
    env_report = None
    if want_liquid_recipe and not (cancel_event is not None and cancel_event.is_set()):
        reference_texts = extract_liquid_references(
            (
                level_path / "materials.xml",
                level_path / "mission_mission0.xml",
                level_path / "objects.lst",
                level_path / "brush.lst",
            )
        )
        liquid_recipe = build_liquid_surface_recipe(
            client_root_path,
            level_data,
            level_dir=level_path,
            requested_kind=liquid_kind,
            requested_preset=liquid_preset,
            reference_texts=reference_texts,
        )
    if want_env and not (cancel_event is not None and cancel_event.is_set()):
        mission_xml = level_path / "mission_mission0.xml"
        if mission_xml.is_file():
            try:
                from formats.level.environment import resolve_level_environment
                env_report = resolve_level_environment(
                    mission_xml, client_root_path, time_option=skybox_time_option,
                )
            except Exception:
                try:
                    from aion_formats.level.environment import resolve_level_environment
                    env_report = resolve_level_environment(
                        mission_xml, client_root_path, time_option=skybox_time_option,
                    )
                except Exception:
                    env_report = None
    return liquid_recipe, env_report


def _parse_cga_stage6_worker(
    level_path: Path,
    client_root_path: Path,
    cancel_event: threading.Event | None = None,
):
    if cancel_event is not None and cancel_event.is_set():
        return None
    source_path = level_path / "mission_mission0.xml"
    if not source_path.is_file():
        return None
    try:
        from formats.level import parse_mission_cga_entities
        return parse_mission_cga_entities(
            source_path,
            client_root=client_root_path,
            level_dir=level_path,
        )
    except Exception:
        return None


def _collect_stage5_jobs_worker(
    objects,
    brush,
    collect_kwargs: dict,
    cancel_event: threading.Event | None = None,
):
    jobs = collect_level_cgf_jobs(objects, brush, **collect_kwargs)
    unique_refs: dict[str, str] = {}
    job_norms: list[tuple[object, str]] = []
    for job in jobs.jobs:
        if cancel_event is not None and cancel_event.is_set():
            break
        ref = getattr(job, "cgf_reference", "")
        norm = str(ref).replace("\\", "/").strip().lstrip("/") if ref else ""
        if norm and norm not in unique_refs:
            unique_refs[norm] = str(ref)
        job_norms.append((job, norm))
    return unique_refs, job_norms


def import_level_generator(
    context,
    level_dir: str | Path,
    client_root: str | Path,
    import_mode: str = "VISUAL",
    limited_preview: bool = False,
    max_unique_cgfs: int = 10,
    max_placements_per_template: int = 3,
    import_terrain: bool = True,
    import_terrain_textures: bool = True,
    import_terrain_blend_attributes: bool = True,
    import_terrain_blend_shader: bool = True,
    import_terrain_shadows: bool = True,
    import_buildings: bool = True,
    import_structures: bool = True,
    import_doors_portals: bool = True,
    import_props: bool = True,
    import_rocks: bool = True,
    import_interactive_objects: bool = True,
    import_vegetation: bool = True,
    import_trees: bool = True,
    import_grass: bool = True,
    import_bushes_flowers: bool = True,
    import_water: bool = True,
    import_textured_liquid_surface: bool = True,
    liquid_kind: str = LIQUID_KIND_AUTO,
    liquid_preset: str = LIQUID_PRESET_AUTO,
    import_static_lights: bool = True,
    static_lights_mode: str = STATIC_LIGHTS_MODE_POINT_LIGHT,
    static_lights_power: float = DEFAULT_STATIC_LIGHT_POWER,
    import_mission_placeables: bool = True,
    apply_mission_angles: bool = True,
    mission_placeables_limit: int | None = None,
    import_particle_effects: bool = True,
    import_cga_entities: bool = True,
    animate_cga_controllers: bool = False,
    apply_smoothing_groups: bool = False,
    animate_texture_sequences: bool = False,
    animate_shader_uv_scroll: bool = False,
    texture_animation_fps: int = 10,
    load_cgf: Callable | None = None,
    get_cgf_import_report: Callable | None = None,
    progress_callback: Callable[[LevelImportProgress], None] | None = None,
    import_skybox: bool = True,
    skybox_time_option: str = "Daylight",
    import_environment_lighting: bool = True,
    environment_sun_energy: float = 2.0,
    environment_ambient_strength: float = 0.3,
    terrain_lod: int | None = None,
    import_collision: bool = False,
    import_npcs: bool = True,
    import_npc_models: bool = True,
    animate_npcs: bool = True,
    import_monsters: bool = True,
    import_friendly_npcs: bool = True,
    import_ambient_creatures: bool = True,
    import_nameplates: bool = True,
    emulator_data_dir: str | Path | None = None,
    import_lod0: bool = True,
    import_lod1: bool = True,
    import_lod2: bool = True,
    import_lod3: bool = True,
    use_mesh_instancing: bool = True,
    optimize_material_preview: bool = True,
    multithreaded_io: bool = True,
    performance_profile: str | None = None,
    simple_shaders: bool | None = None,
    max_terrain_blend_layers: int | None = None,
    disable_dynamic_shadows: bool | None = None,
    merge_template_submeshes: bool | None = None,
    animate_water: bool = False,
    cancel_event: threading.Event | None = None,
) -> LevelImportResult:
    """
    Strictly linear, non-blocking 8-stage async importer:
      Stage 1/8: Prepare/unpack Level.pak (background worker)
      Stage 2/8: Index client PAK catalog (background worker)
      Stage 3/8: Parse level metadata & build terrain mesh
      Stage 4/8: Create lightweight water, liquid shader, lighting & optional skybox
      Stage 5/8: Resolve CGFs linearly in chunks, merge static meshes & place 1 template at a time
      Stage 6/8: Optional lights, mission placeables, particles & CGA entities
      Stage 7/8: Optional authoritative NPCs (only after map geometry finishes!)
      Stage 8/8: Prune empty collections, apply 60+ FPS Eevee tuning & finalize
    """
    if not client_root:
        raise ValueError("client_root is required for level CGF import")
    if import_mode not in {"VISUAL", "COLLISION"}:
        raise ValueError(f"unsupported import mode: {import_mode}")
    if limited_preview and max_placements_per_template < 1:
        raise ValueError("max_placements_per_template must be >= 1")

    profile_key = normalize_performance_profile(performance_profile) if performance_profile else "LOW"
    profile_cfg = resolve_profile_settings(profile_key)

    effective_terrain_lod = int(terrain_lod) if terrain_lod is not None else int(profile_cfg["terrain_lod"])
    effective_target_lod = int(profile_cfg["target_model_lod"])
    if performance_profile is None:
        if import_lod3 and not import_lod0:
            effective_target_lod = 3
        elif import_lod2 and not import_lod0:
            effective_target_lod = 2
        elif import_lod1 and not import_lod0:
            effective_target_lod = 1
        elif import_lod0:
            effective_target_lod = 0

    effective_simple_shaders = (
        bool(simple_shaders)
        if simple_shaders is not None
        else (bool(profile_cfg["simple_shaders"]) if performance_profile is not None else False)
    )
    effective_max_blend_layers = (
        int(max_terrain_blend_layers)
        if max_terrain_blend_layers is not None
        else int(profile_cfg["max_terrain_blend_layers"])
    )
    effective_disable_shadows = (
        bool(disable_dynamic_shadows)
        if disable_dynamic_shadows is not None
        else bool(profile_cfg["disable_dynamic_shadows"])
    )
    effective_merge_submeshes = (
        bool(merge_template_submeshes)
        if merge_template_submeshes is not None
        else bool(profile_cfg["merge_template_submeshes"])
    )
    effective_lightweight_water = bool(profile_cfg["lightweight_water"])

    visual_mode = import_mode == "VISUAL"
    if not visual_mode:
        import_skybox = False
        import_environment_lighting = False
        import_terrain = True
        import_terrain_textures = False
        import_terrain_blend_attributes = False
        import_terrain_blend_shader = False
        import_terrain_shadows = False
        import_water = False
        import_textured_liquid_surface = False
        import_static_lights = False
        import_mission_placeables = False
        import_particle_effects = False
        import_cga_entities = True
        animate_cga_controllers = False
        animate_texture_sequences = False
        animate_shader_uv_scroll = False
        import_npcs = False
        import_collision = True

    from materials.material_manager import clean_material_cache, set_session_pak_catalog
    from materials.texture_loader import clear_texture_cache, purge_orphan_datablocks

    clean_material_cache()
    clear_texture_cache()
    purge_orphan_datablocks()

    try:
        from .armature_importer import ArmatureCache
        ArmatureCache.get().clear()
    except Exception:
        pass

    prewarm_cgf = None
    iter_load_cgf_fn = None
    uses_native_cgf = False
    if load_cgf is None:
        from . import cgf_importer
        load_cgf = cgf_importer.load
        get_cgf_import_report = cgf_importer.get_last_import_report
        prewarm_cgf = cgf_importer.prewarm_cgf_and_textures
        iter_load_cgf_fn = cgf_importer.iter_load_cgf
        uses_native_cgf = True

    cancel_ev = cancel_event if cancel_event is not None else threading.Event()
    client_root_path = Path(client_root)
    executor = ThreadPoolExecutor(max_workers=1)
    pending_future = None
    resolver = None
    completed_ok = False

    try:
        # ------------------------------------------------------------------
        # STAGE 1/8: Prepare / unpack Level.pak off the main thread
        # ------------------------------------------------------------------
        from core.pak_engine import AionLevelUnpacker
        yield (0.01, "[1/8] Preparando diretório do mapa (Level.pak)...")
        pending_future = executor.submit(AionLevelUnpacker.prepare_level_directory, level_dir, cancel_ev)
        while not pending_future.done():
            if cancel_ev.is_set():
                return None
            yield (0.03, "[1/8] Extraindo Level.pak em segundo plano...")
        if cancel_ev.is_set():
            return None
        try:
            level_path = pending_future.result()
        except Exception:
            level_path = Path(level_dir)
        pending_future = None

        context.scene["aion_active_level_path"] = str(level_path)
        terrain_path = level_path / "terrain" / "land_map.h32"
        if import_terrain and not terrain_path.is_file():
            raise FileNotFoundError(f"terrain preview requested but file is missing: {terrain_path}")
        yield (0.08, "[1/8] Mapa preparado.")

        # ------------------------------------------------------------------
        # STAGE 2/8: Index client PAK catalog off the main thread
        # ------------------------------------------------------------------
        if cancel_ev.is_set():
            return None
        yield (0.09, "[2/8] Indexando catálogo de PAKs...")
        pending_future = executor.submit(_ensure_catalog_worker, client_root, True, cancel_ev)
        while not pending_future.done():
            if cancel_ev.is_set():
                return None
            yield (0.12, "[2/8] Indexando catálogo de PAKs...")
        if cancel_ev.is_set():
            return None
        try:
            resolver, pak_catalog = pending_future.result()
            if pak_catalog is not None:
                set_session_pak_catalog(pak_catalog)
        except Exception:
            resolver = None
        pending_future = None
        yield (0.16, "[2/8] Catálogo pronto.")

        # ------------------------------------------------------------------
        # STAGE 3/8: Parse level binaries & precompute terrain off main thread
        # ------------------------------------------------------------------
        if cancel_ev.is_set():
            return None
        _emit_progress(
            progress_callback,
            stage="discover",
            message="Reading level sources",
            completed=0,
            total=1,
        )
        yield (0.17, "[3/8] Lendo leveldata.xml, terreno e weights em segundo plano...")
        pending_future = executor.submit(
            _parse_stage3_worker,
            level_path,
            terrain_path,
            import_terrain,
            effective_terrain_lod,
            client_root_path,
            visual_mode,
            import_terrain_blend_attributes or import_terrain_blend_shader,
            cancel_ev,
        )
        while not pending_future.done():
            if cancel_ev.is_set():
                return None
            yield (0.19, "[3/8] Processando terreno em segundo plano...")
        if cancel_ev.is_set():
            return None
        level_data, objects, brush, land_map, precomputed_terrain = pending_future.result()
        pending_future = None
        if level_data is None:
            return None

        import bpy

        root_collection = context.scene.collection
        collection_name = (
            PREVIEW_COLLECTION_NAME
            if limited_preview
            else LEVEL_COLLECTION_NAME
        )
        preview_collection = bpy.data.collections.new(collection_name)
        root_collection.children.link(preview_collection)

        category_collections = {
            "ROOT": preview_collection,
            "TERRAIN": bpy.data.collections.new("TERRAIN"),
            "BUILDINGS": bpy.data.collections.new("BUILDINGS"),
            "PROPS": bpy.data.collections.new("PROPS"),
            "VEGETATION": bpy.data.collections.new("VEGETATION"),
            "ROCKS": bpy.data.collections.new("ROCKS"),
            "WATER": bpy.data.collections.new("WATER"),
            "LIGHTING": bpy.data.collections.new("LIGHTING"),
            "SKYBOX": bpy.data.collections.new("SKYBOX"),
            "PLACEABLES": bpy.data.collections.new("PLACEABLES"),
            "NPCS": bpy.data.collections.new("NPCS"),
            "EFFECTS": bpy.data.collections.new("EFFECTS"),
            "COLLISION": bpy.data.collections.new("COLLISION"),
            ".TEMPLATES": bpy.data.collections.new(".TEMPLATES"),
        }
        for cat_name, cat_col in category_collections.items():
            if cat_name != "ROOT":
                preview_collection.children.link(cat_col)

        veg_root_col = category_collections["VEGETATION"]
        for veg_sub in ("Trees & Forest", "Bushes & Flowers", "Grass & Cover"):
            sub_col = bpy.data.collections.new(veg_sub)
            veg_root_col.children.link(sub_col)
            category_collections[veg_sub] = sub_col

        templates_col = category_collections[".TEMPLATES"]
        templates_col.hide_viewport = True
        templates_col.hide_render = True

        def _exclude_layer_col(layer_col, target_col):
            if layer_col.collection == target_col:
                layer_col.exclude = True
                return True
            for child in layer_col.children:
                if _exclude_layer_col(child, target_col):
                    return True
            return False

        if hasattr(context, "view_layer") and context.view_layer and hasattr(context.view_layer, "layer_collection"):
            try:
                _exclude_layer_col(context.view_layer.layer_collection, templates_col)
            except Exception:
                pass

        objects_before = len(bpy.data.objects)
        meshes_before = len(bpy.data.meshes)
        terrain_mesh_result = None

        if import_terrain and land_map is not None:
            yield (0.22, f"[3/8] Construindo terreno (LOD {effective_terrain_lod})...")
            terrain_gen = iter_create_terrain_mesh(
                context,
                land_map,
                level_data=level_data if visual_mode else None,
                client_root=client_root_path if visual_mode else None,
                import_terrain_textures=import_terrain_textures,
                import_terrain_blend_attributes=import_terrain_blend_attributes,
                import_terrain_blend_shader=import_terrain_blend_shader,
                import_terrain_shadows=import_terrain_shadows,
                level_dir=level_path,
                lod=effective_terrain_lod,
                max_blend_materials=effective_max_blend_layers,
                simple_shader=effective_simple_shaders,
                disable_shadows=effective_disable_shadows,
                precomputed=precomputed_terrain,
                target_collection=category_collections["TERRAIN"],
            )
            try:
                while True:
                    if cancel_ev.is_set():
                        return None
                    t_frac, t_msg = next(terrain_gen)
                    yield (0.22 + 0.07 * t_frac, f"[3/8] {t_msg}")
            except StopIteration as exc_ter:
                terrain_mesh_result = exc_ter.value
        terrain_height_grid = None
        if import_npcs and precomputed_terrain is not None and precomputed_terrain.get("grid_z") is not None:
            terrain_height_grid = (
                precomputed_terrain["grid_row_xs"],
                precomputed_terrain["grid_col_ys"],
                precomputed_terrain["grid_z"],
                precomputed_terrain["grid_h"],
                precomputed_terrain["grid_w"],
            )
        precomputed_terrain = None
        land_map = None  # Free height samples immediately before object phase
        if terrain_mesh_result is not None:
            try:
                apply_viewport_60fps_optimization(context, profile_key)
                cx = float(terrain_mesh_result.width) * float(terrain_mesh_result.xy_scale) * 0.5
                cy = float(terrain_mesh_result.height) * float(terrain_mesh_result.xy_scale) * 0.5
                cz = (float(terrain_mesh_result.min_height) + float(terrain_mesh_result.max_height)) * 0.5
                span = max(
                    float(terrain_mesh_result.width) * float(terrain_mesh_result.xy_scale),
                    float(terrain_mesh_result.height) * float(terrain_mesh_result.xy_scale),
                )
                frame_viewport_on_map((cx, cy, cz), distance=max(900.0, span * 0.55))
            except Exception:
                pass
        yield (0.30, "[3/8] Terreno concluído.")

        # ------------------------------------------------------------------
        # STAGE 4/8: Water, Liquid Surface, Lighting & Skybox
        # ------------------------------------------------------------------
        if cancel_ev.is_set():
            return None
        water_result = None
        liquid_surface_result = None
        skybox_result = None
        environment_lighting_result = None

        want_liquid_recipe = bool(import_textured_liquid_surface and import_water)
        want_env_parse = bool(import_environment_lighting or import_skybox)
        liquid_recipe = None
        env_report = None

        if want_liquid_recipe or want_env_parse:
            yield (0.305, "[4/8] Analisando iluminação e líquidos em segundo plano...")
            pending_future = executor.submit(
                _prepare_stage4_worker,
                level_path,
                client_root_path,
                level_data,
                liquid_kind,
                liquid_preset,
                skybox_time_option,
                want_liquid_recipe,
                want_env_parse,
                cancel_ev,
            )
            while not pending_future.done():
                if cancel_ev.is_set():
                    return None
                yield (0.31, "[4/8] Lendo ambiente e líquidos em segundo plano...")
            if cancel_ev.is_set():
                return None
            liquid_recipe, env_report = pending_future.result()
            pending_future = None

        if import_water:
            yield (0.315, "[4/8] Criando plano e volumes de água...")
            want_water_waves = bool(animate_water and not effective_lightweight_water and not effective_simple_shaders)
            water_result = create_water_plane(
                context,
                level_data.level_info,
                xy_scale=(
                    terrain_mesh_result.xy_scale
                    if terrain_mesh_result is not None
                    else DEFAULT_XY_SCALE
                ),
                subdivide_water=want_water_waves,
                disable_shadows=effective_disable_shadows,
                target_collection=category_collections["WATER"],
            )
            if water_result and water_result.object and want_water_waves:
                apply_water_wave_animation(water_result.object)

        if import_textured_liquid_surface:
            yield (0.325, "[4/8] Aplicando shader de água...")
            if not import_water:
                liquid_surface_result = skipped_liquid_surface_result(
                    requested=True,
                    selected_kind=liquid_kind,
                    selected_preset=liquid_preset,
                    reason="textured liquid surface requires Import Water Plane",
                )
            else:
                if liquid_recipe is None:
                    reference_texts = extract_liquid_references(
                        (
                            level_path / "materials.xml",
                            level_path / "mission_mission0.xml",
                            level_path / "objects.lst",
                            level_path / "brush.lst",
                        )
                    )
                    liquid_recipe = build_liquid_surface_recipe(
                        client_root_path,
                        level_data,
                        level_dir=level_path,
                        requested_kind=liquid_kind,
                        requested_preset=liquid_preset,
                        reference_texts=reference_texts,
                    )
                liquid_surface_result = apply_liquid_surface_material(
                    water_result,
                    liquid_recipe,
                    animate_liquid=bool(animate_water and animate_shader_uv_scroll and not effective_simple_shaders),
                    simple_shader=effective_simple_shaders or optimize_material_preview,
                )

        if import_water:
            try:
                water_mat = (
                    water_result.object.active_material
                    if water_result is not None and getattr(water_result, "object", None) is not None
                    else None
                )
                create_water_volumes(
                    context,
                    level_path / "mission_mission0.xml",
                    client_root_path,
                    water_material=water_mat,
                    disable_shadows=effective_disable_shadows,
                    simple_shaders=effective_simple_shaders,
                    target_collection=category_collections["WATER"],
                )
            except Exception as exc_wv:
                print(f"[Aion] WaterVolume warning: {exc_wv}")

        if import_environment_lighting:
            yield (0.335, "[4/8] Configurando iluminação ambiente...")
            environment_lighting_result = create_environment_lighting_preview(
                context.scene,
                level_path,
                client_root_path,
                time_option=skybox_time_option,
                sun_energy=environment_sun_energy,
                ambient_strength=environment_ambient_strength,
                use_shadow=not effective_disable_shadows,
                pre_resolved_report=env_report,
                target_collection=category_collections["LIGHTING"],
            )

        if import_skybox:
            yield (0.342, "[4/8] Configurando Skybox...")
            skybox_result = create_skybox_preview(
                context.scene,
                level_path,
                client_root_path,
                time_option=skybox_time_option,
                pre_resolved_report=env_report,
            )
            try:
                from .environment_importer import create_physical_skydome
                center_x = (terrain_mesh_result.width * terrain_mesh_result.xy_scale / 2.0) if terrain_mesh_result else 1536.0
                center_y = (terrain_mesh_result.height * terrain_mesh_result.xy_scale / 2.0) if terrain_mesh_result else 1536.0
                min_z = float(terrain_mesh_result.min_height) if terrain_mesh_result else 0.0
                create_physical_skydome(
                    context,
                    client_root_path,
                    center=(center_x, center_y, min_z),
                    animate_clouds=bool(animate_shader_uv_scroll and not effective_simple_shaders),
                    override_viewport_shading=False,
                    target_collection=category_collections["SKYBOX"],
                )
            except Exception:
                pass
        env_report = None
        liquid_recipe = None
        yield (0.35, "[4/8] Água e ambiente concluídos.")

        # ------------------------------------------------------------------
        # STAGE 5/8: Collect & Resolve CGFs linearly, then Import 1 by 1
        # ------------------------------------------------------------------
        collect_kwargs = dict(
            import_mode=import_mode,
            import_buildings=import_buildings,
            import_structures=import_structures,
            import_doors_portals=import_doors_portals,
            import_props=import_props,
            import_rocks=import_rocks,
            import_interactive_objects=import_interactive_objects,
            import_vegetation=import_vegetation,
            import_trees=import_trees,
            import_grass=import_grass,
            import_bushes_flowers=import_bushes_flowers,
            import_effects=import_particle_effects,
            import_collision=import_collision,
            import_lod0=import_lod0,
            import_lod1=import_lod1,
            import_lod2=import_lod2,
            import_lod3=import_lod3,
        )
        pending_future = executor.submit(
            _collect_stage5_jobs_worker,
            objects,
            brush,
            collect_kwargs,
            cancel_ev,
        )
        while not pending_future.done():
            if cancel_ev.is_set():
                return None
            yield (0.35, "[5/8] Filtrando objetos do mapa...")
        if cancel_ev.is_set():
            return None
        unique_refs, job_norms = pending_future.result()
        pending_future = None
        # Release raw lists now that CGF jobs are extracted
        objects = None
        brush = None

        resolved_paths_map: dict[str, Path] = {}
        unique_items = list(unique_refs.items())
        total_unique = len(unique_items)
        if resolver is not None and total_unique > 0:
            chunk_sz = 20
            for start in range(0, total_unique, chunk_sz):
                if cancel_ev.is_set():
                    return None
                chunk = unique_items[start : start + chunk_sz]
                done_count = min(start + len(chunk), total_unique)
                msg = f"[5/8] Extraindo modelos CGF ({done_count}/{total_unique})..."
                frac = 0.35 + 0.12 * (start / max(1, total_unique))
                pending_future = executor.submit(
                    _resolve_cgf_chunk_worker, resolver, chunk, effective_target_lod, cancel_ev
                )
                while not pending_future.done():
                    if cancel_ev.is_set():
                        return None
                    yield (frac, msg)
                if cancel_ev.is_set():
                    return None
                resolved_paths_map.update(pending_future.result())
                pending_future = None
                yield (0.35 + 0.12 * (done_count / max(1, total_unique)), msg)

        resolved_jobs = []
        missing_jobs = []
        for job, norm in job_norms:
            r_path = resolved_paths_map.get(norm)
            if norm and r_path is not None:
                resolved_jobs.append(
                    ResolvedLevelCgfJob(job=job, resolved_path=r_path, normalized_reference=norm)
                )
            else:
                missing_jobs.append(job)
        resolution = LevelCgfResolutionResult(
            resolved=tuple(resolved_jobs), missing=tuple(missing_jobs)
        )
        template_collection = group_level_cgf_templates(resolution.resolved)
        selected_templates = (
            select_level_cgf_templates(
                template_collection.templates,
                max_unique_cgfs,
            )
            if limited_preview
            else template_collection.templates
        )

        optional_stage_count = sum(
            (
                import_skybox,
                import_environment_lighting,
                import_terrain,
                import_water,
                import_textured_liquid_surface,
                import_static_lights,
                import_mission_placeables,
                import_particle_effects,
                import_cga_entities,
                import_npcs,
            )
        )
        progress_total = 2 + len(selected_templates) + optional_stage_count
        progress_completed = 1
        _emit_progress(
            progress_callback,
            stage="discover",
            message=(
                f"Resolved {len(selected_templates)} of "
                f"{len(template_collection.templates)} CGF templates"
            ),
            completed=progress_completed,
            total=progress_total,
        )

        def advance_progress(stage: str, message: str) -> None:
            nonlocal progress_completed
            progress_completed += 1
            _emit_progress(
                progress_callback,
                stage=stage,
                message=message,
                completed=progress_completed,
                total=progress_total,
            )

        imported_template_count = 0
        selected_placement_count = 0
        placement_objects_created = 0
        object_placement_count = 0
        brush_placement_count = 0
        transform_summaries = []
        placement_skips = []
        per_template_placement_counts = []
        failures = []
        skipped_templates = []
        texture_sequences_applied = 0
        texture_sequences_skipped = 0
        texture_sequence_missing_frames = 0
        shader_uv_scroll_applied = 0
        shader_uv_scroll_skipped = 0

        total_tpl = len(selected_templates)
        for template_index, template in enumerate(selected_templates, start=1):
            if cancel_ev.is_set():
                return None
            frac = 0.47 + 0.31 * ((template_index - 1) / max(1, total_tpl))
            yield (
                frac,
                f"[5/8] Modelo {template_index}/{total_tpl}: {template.resolved_path.name}",
            )
            _emit_progress(
                progress_callback,
                stage="cgf_templates",
                message=(
                    f"Importing CGF template {template_index}/{total_tpl}: "
                    f"{template.resolved_path.name}"
                ),
                completed=progress_completed,
                total=progress_total,
            )
            preparsed_cgf = None
            if prewarm_cgf is not None:
                pending_future = executor.submit(
                    prewarm_cgf,
                    str(template.resolved_path),
                    client_root=str(client_root),
                    simple_shaders=effective_simple_shaders,
                    cancel_event=cancel_ev,
                )
                while not pending_future.done():
                    if cancel_ev.is_set():
                        return None
                    yield (
                        frac,
                        f"[5/8] Lendo modelo {template_index}/{total_tpl}: {template.resolved_path.name}",
                    )
                if cancel_ev.is_set():
                    return None
                preparsed_cgf = pending_future.result()
                pending_future = None

            collections_before = set(bpy.data.collections)
            imported_collection = None
            try:
                if uses_native_cgf and iter_load_cgf_fn is not None:
                    cgf_gen = iter_load_cgf_fn(
                        context,
                        str(template.resolved_path),
                        import_mode=template.import_mode,
                        apply_smoothing_groups=apply_smoothing_groups,
                        animate_texture_sequences=animate_texture_sequences,
                        animate_shader_uv_scroll=animate_shader_uv_scroll,
                        texture_animation_fps=texture_animation_fps,
                        client_root=str(client_root),
                        optimize_material_preview=optimize_material_preview,
                        simple_shaders=effective_simple_shaders,
                        preparsed_cgf=preparsed_cgf,
                        target_collection=None,
                        link_to_scene=False,
                        time_slice_s=0.006,
                        cancel_event=cancel_ev,
                    )
                    try:
                        while True:
                            if cancel_ev.is_set():
                                return None
                            n_done, n_tot = next(cgf_gen)
                            yield (
                                frac,
                                f"[5/8] Construindo {template.resolved_path.name} ({n_done}/{n_tot})...",
                            )
                    except StopIteration as exc_cgf:
                        result, imported_collection = exc_cgf.value
                else:
                    try:
                        result = load_cgf(
                            context,
                            str(template.resolved_path),
                            import_mode=template.import_mode,
                            apply_smoothing_groups=apply_smoothing_groups,
                            animate_texture_sequences=animate_texture_sequences,
                            animate_shader_uv_scroll=animate_shader_uv_scroll,
                            texture_animation_fps=texture_animation_fps,
                            client_root=str(client_root),
                            optimize_material_preview=optimize_material_preview,
                            simple_shaders=effective_simple_shaders,
                            preparsed_cgf=preparsed_cgf,
                            link_to_scene=False,
                        )
                    except TypeError:
                        try:
                            result = load_cgf(
                                context,
                                str(template.resolved_path),
                                import_mode=template.import_mode,
                                apply_smoothing_groups=apply_smoothing_groups,
                                animate_texture_sequences=animate_texture_sequences,
                                animate_shader_uv_scroll=animate_shader_uv_scroll,
                                texture_animation_fps=texture_animation_fps,
                                client_root=str(client_root),
                                optimize_material_preview=optimize_material_preview,
                            )
                        except TypeError:
                            result = load_cgf(
                                context,
                                str(template.resolved_path),
                                import_mode=template.import_mode,
                                apply_smoothing_groups=apply_smoothing_groups,
                                animate_texture_sequences=animate_texture_sequences,
                                animate_shader_uv_scroll=animate_shader_uv_scroll,
                                texture_animation_fps=texture_animation_fps,
                            )
            except Exception:
                result = {"CANCELLED"}
            finally:
                preparsed_cgf = None

            if cancel_ev.is_set():
                return None

            import_report = (
                get_cgf_import_report()
                if get_cgf_import_report is not None
                else None
            )
            if import_report is not None:
                texture_sequences_applied += getattr(import_report, "texture_sequences_applied", 0)
                texture_sequences_skipped += getattr(import_report, "texture_sequences_skipped", 0)
                texture_sequence_missing_frames += getattr(
                    import_report,
                    "texture_sequence_missing_frames",
                    0,
                )
                shader_uv_scroll_applied += getattr(import_report, "shader_uv_scroll_applied", 0)
                shader_uv_scroll_skipped += getattr(import_report, "shader_uv_scroll_skipped", 0)

            if result != {"FINISHED"}:
                reason_code = (
                    import_report.reason_code
                    if import_report and import_report.reason_code
                    else "unknown"
                )
                reason = (
                    import_report.reason
                    if import_report and import_report.reason
                    else f"CGF importer returned {result}"
                )
                failure_kwargs = {
                    "normalized_reference": template.normalized_reference,
                    "resolved_path": template.resolved_path,
                    "import_mode": template.import_mode,
                    "reason_code": reason_code,
                    "reason": reason,
                    "parser_node_count": import_report.parser_node_count if import_report else 0,
                    "parser_mesh_node_count": import_report.parser_mesh_node_count if import_report else 0,
                    "parser_material_count": import_report.parser_material_count if import_report else 0,
                    "candidate_mesh_node_count": (
                        import_report.candidate_mesh_node_count if import_report else 0
                    ),
                    "parser_coverage_counts": (
                        getattr(import_report, "parser_coverage_counts", {}) if import_report else {}
                    ),
                    "unsupported_chunks": (
                        getattr(import_report, "unsupported_chunks", {}) if import_report else {}
                    ),
                    "unused_material_fields": (
                        getattr(import_report, "unused_material_fields", {}) if import_report else {}
                    ),
                }
                if _is_expected_cgf_skip(reason_code):
                    skipped_templates.append(LevelCgfImportSkip(**failure_kwargs))
                else:
                    failures.append(LevelCgfImportFailure(**failure_kwargs))
                advance_progress(
                    "cgf_templates",
                    f"Processed CGF template {template_index}/{total_tpl}",
                )
                continue

            new_collections = tuple(
                collection for collection in bpy.data.collections if collection not in collections_before
            )
            if imported_collection is None:
                imported_collection = _find_imported_template_collection(
                    new_collections,
                    preview_collection,
                )

            # Merge static sub-meshes of the template into 1 multi-material GPU mesh (time-sliced)
            if effective_merge_submeshes:
                try:
                    merge_gen = iter_merge_static_template_meshes(
                        imported_collection,
                        merged_name=f"Tpl_{template.resolved_path.stem}",
                        time_slice_s=0.006,
                    )
                    try:
                        while True:
                            if cancel_ev.is_set():
                                return None
                            m_done, m_tot = next(merge_gen)
                            yield (
                                0.47 + 0.31 * ((template_index - 0.6) / max(1, total_tpl)),
                                f"[5/8] Mesclando {template.resolved_path.name} ({m_done}/{m_tot})...",
                            )
                    except StopIteration:
                        pass
                except Exception:
                    pass

            # Yield right after template mesh construction before instancing its copies
            yield (
                0.47 + 0.31 * ((template_index - 0.5) / max(1, total_tpl)),
                f"[5/8] Posicionando cópias: {template.resolved_path.name}",
            )

            col_objs = list(imported_collection.objects) if imported_collection is not None else []
            mesh_objs = [o for o in col_objs if o.type == "MESH" and o.data is not None]
            flattened_tpl_obj = None
            if (
                use_mesh_instancing
                and len(col_objs) == 1
                and len(mesh_objs) == 1
                and imported_collection is not None
                and len(imported_collection.children) == 0
            ):
                flattened_tpl_obj = mesh_objs[0]
                flattened_tpl_obj["aion_reference"] = template.normalized_reference
                flattened_tpl_obj["aion_source_type"] = "brush"
                imported_collection.objects.unlink(flattened_tpl_obj)
                templates_col.objects.link(flattened_tpl_obj)
                if imported_collection.name in root_collection.children.keys():
                    root_collection.children.unlink(imported_collection)
                new_collections = tuple(c for c in new_collections if c != imported_collection)
                bpy.data.collections.remove(imported_collection)
                imported_collection = None

            placement_limit = (
                max_placements_per_template
                if limited_preview
                else template.placement_count
            )
            inst_gen = iter_create_level_cgf_placement_instances(
                category_collections,
                imported_collection,
                template.placements,
                placement_limit,
                use_mesh_instancing=use_mesh_instancing,
                disable_shadows=effective_disable_shadows,
                chunk_size=24,
                template_name=template.resolved_path.name,
                template_objects=(flattened_tpl_obj,) if flattened_tpl_obj is not None else None,
            )
            try:
                while True:
                    if cancel_ev.is_set():
                        return None
                    placed_n, tot_n = next(inst_gen)
                    yield (
                        0.47 + 0.31 * (template_index / max(1, total_tpl)),
                        f"[5/8] {template.resolved_path.name} ({placed_n}/{tot_n})",
                    )
            except StopIteration as exc_inst:
                instance_batch = exc_inst.value

            imported_template_count += 1
            selected_placement_count += placement_limit
            placement_objects_created += len(instance_batch.instances)
            object_placement_count += instance_batch.object_placement_count
            brush_placement_count += instance_batch.brush_placement_count
            transform_summaries.extend(instance_batch.transform_summaries)
            placement_skips.extend(instance_batch.placement_skips)
            per_template_placement_counts.append(
                LevelTemplatePlacementStats(
                    normalized_reference=template.normalized_reference,
                    import_mode=template.import_mode,
                    available_placement_count=template.placement_count,
                    created_placement_count=len(instance_batch.instances),
                )
            )
            if imported_collection is not None:
                if imported_collection.name != preview_collection.name and imported_collection.name not in templates_col.children.keys():
                    templates_col.children.link(imported_collection)
                _detach_template_collections_from_scene(
                    root_collection,
                    (imported_collection,),
                )
            elif new_collections:
                _detach_template_collections_from_scene(
                    root_collection,
                    new_collections,
                )
            advance_progress(
                "cgf_templates",
                f"Processed CGF template {template_index}/{total_tpl}",
            )

        yield (0.78, "[5/8] Modelos e instâncias concluídos.")

        # ------------------------------------------------------------------
        # STAGE 6/8: Optional Static Lights, Placeables, FX & CGA Entities
        # ------------------------------------------------------------------
        if cancel_ev.is_set():
            return None
        static_lights_result = None
        mission_placeables_result = None
        particle_effects_result = None
        cga_entities_result = None

        if import_static_lights:
            yield (0.79, "[6/8] Importando luzes estáticas...")
            static_lights_result = create_static_deferred_lights(
                context,
                level_path,
                mode=static_lights_mode,
                power=static_lights_power,
                target_collection=category_collections["LIGHTING"],
            )
            advance_progress("static_lights", "Static lights processed")

        if import_mission_placeables:
            yield (0.80, "[6/8] Importando objetos de missão...")
            place_gen = iter_create_mission_placeables(
                context,
                level_path,
                client_root_path,
                apply_angles=apply_mission_angles,
                apply_smoothing_groups=apply_smoothing_groups,
                animate_texture_sequences=animate_texture_sequences,
                animate_shader_uv_scroll=animate_shader_uv_scroll,
                texture_animation_fps=texture_animation_fps,
                limit=mission_placeables_limit,
                load_cgf=load_cgf,
                get_cgf_import_report=get_cgf_import_report,
                target_collection=category_collections["PLACEABLES"],
                disable_shadows=effective_disable_shadows,
                simple_shaders=effective_simple_shaders,
                batch_size=1,
            )
            try:
                while True:
                    if cancel_ev.is_set():
                        return None
                    p_done, p_tot = next(place_gen)
                    yield (
                        0.80 + 0.009 * (p_done / max(1, p_tot)),
                        f"[6/8] Objetos de missão ({p_done}/{p_tot})...",
                    )
            except StopIteration as exc_pl:
                mission_placeables_result = exc_pl.value
            advance_progress("mission_placeables", "Mission placeables processed")

        if import_particle_effects:
            yield (0.81, "[6/8] Lendo efeitos (.prt/.dds) em segundo plano...")
            pending_future = executor.submit(
                prepare_particle_effects_stage_data,
                level_path,
                client_root_path,
                level_data=level_data,
            )
            while not pending_future.done():
                if cancel_ev.is_set():
                    return None
                yield (0.812, "[6/8] Extraindo efeitos de partículas (.prt/.dds)...")
            if cancel_ev.is_set():
                return None
            fx_pre_prepared = pending_future.result()
            pending_future = None

            fx_gen = iter_create_particle_effects(
                context,
                level_path,
                client_root_path,
                level_data=level_data,
                pre_prepared=fx_pre_prepared,
                target_collection=category_collections["EFFECTS"],
                disable_shadows=effective_disable_shadows,
                batch_size=24,
            )
            try:
                while True:
                    if cancel_ev.is_set():
                        return None
                    fx_done, fx_tot = next(fx_gen)
                    yield (
                        0.812 + 0.008 * (fx_done / max(1, fx_tot)),
                        f"[6/8] Criando partículas ({fx_done}/{fx_tot})...",
                    )
            except StopIteration as exc_fx:
                particle_effects_result = exc_fx.value
            advance_progress("particle_effects", "Particle effects processed")

        if import_cga_entities:
            yield (0.815, "[6/8] Lendo entidades CGA em segundo plano...")
            cga_pre_parsed = None
            pending_future = executor.submit(
                _parse_cga_stage6_worker,
                level_path,
                client_root_path,
                cancel_ev,
            )
            while not pending_future.done():
                if cancel_ev.is_set():
                    return None
                yield (0.82, "[6/8] Lendo mission_mission0.xml (CGA)...")
            if cancel_ev.is_set():
                return None
            cga_pre_parsed = pending_future.result()
            pending_future = None

            cga_gen = iter_create_cga_entities(
                context,
                level_path,
                client_root_path,
                import_mode=import_mode,
                apply_angles=True,
                apply_smoothing_groups=apply_smoothing_groups,
                animate_texture_sequences=animate_texture_sequences,
                animate_shader_uv_scroll=animate_shader_uv_scroll,
                animate_cga_controllers=animate_cga_controllers,
                texture_animation_fps=texture_animation_fps,
                load_cgf=load_cgf,
                get_cgf_import_report=get_cgf_import_report,
                simple_shaders=effective_simple_shaders,
                disable_shadows=effective_disable_shadows,
                merge_static_meshes=effective_merge_submeshes,
                batch_size=2,
                pre_parsed=cga_pre_parsed,
                parent_collection=preview_collection,
            )
            try:
                while True:
                    if cancel_ev.is_set():
                        return None
                    cga_done, cga_total = next(cga_gen)
                    yield (
                        0.82 + 0.02 * (cga_done / max(1, cga_total)),
                        f"[6/8] Entidades CGA ({cga_done}/{cga_total})...",
                    )
            except StopIteration as exc_cga:
                cga_entities_result = exc_cga.value
            advance_progress("cga_entities", "CGA entities processed")

        # ------------------------------------------------------------------
        # STAGE 7/8: Authoritative NPCs (strictly AFTER map finishes!)
        # ------------------------------------------------------------------
        if cancel_ev.is_set():
            return None
        npc_result = None
        if visual_mode and import_npcs:
            yield (0.85, "[7/8] Carregando NPCs de forma linear...")
            advance_progress("npcs", "Spawning authoritative NPCs from client_world XML")
            try:
                from .npc_importer import iter_create_world_npcs
                npc_gen = iter_create_world_npcs(
                    context,
                    level_dir=level_path,
                    client_root=client_root_path,
                    parent_collection=category_collections["NPCS"],
                    terrain_obj=terrain_mesh_result.object if terrain_mesh_result else None,
                    import_models=import_npc_models,
                    animate_npcs=animate_npcs,
                    import_monsters=import_monsters,
                    import_friendly=import_friendly_npcs,
                    import_ambient=import_ambient_creatures,
                    import_nameplates=import_nameplates,
                    disable_shadows=effective_disable_shadows,
                    batch_size=6,
                    executor=executor,
                    cancel_event=cancel_ev,
                    terrain_grid=terrain_height_grid,
                    emulator_data_dir=emulator_data_dir,
                )
                while True:
                    if cancel_ev.is_set():
                        return None
                    npc_frac, npc_msg = next(npc_gen)
                    yield (0.85 + 0.11 * npc_frac, f"[7/8] {npc_msg}")
            except StopIteration as exc_npc:
                npc_result = exc_npc.value
            except Exception as exc:
                print(f"[Aion] NPC Spawning warning: {exc}")
            terrain_height_grid = None

        # ------------------------------------------------------------------
        # STAGE 8/8: Finalize, prune & tune Eevee/Viewport for 60+ FPS
        # ------------------------------------------------------------------
        if cancel_ev.is_set():
            return None
        yield (0.97, "[8/8] Limpando coleções vazias...")
        objects_created = len(bpy.data.objects) - objects_before
        meshes_created = len(bpy.data.meshes) - meshes_before
        summary = _build_execution_summary(
            total_template_count=len(template_collection.templates),
            selected_template_count=len(selected_templates),
            imported_template_count=imported_template_count,
            failed_template_count=len(failures),
            skipped_template_count=len(skipped_templates),
            placement_objects_created=placement_objects_created,
            invalid_placements_skipped=len(placement_skips),
            invalid_object_scale_count=sum(
                skip.reason_code == INVALID_OBJECT_SCALE
                for skip in placement_skips
            ),
            invalid_brush_matrix_count=sum(
                skip.reason_code == INVALID_BRUSH_MATRIX
                for skip in placement_skips
            ),
            first_invalid_placement=placement_skips[0] if placement_skips else None,
            limited_preview=limited_preview,
            import_terrain=import_terrain,
            import_terrain_textures=import_terrain_textures,
            import_terrain_blend_attributes=import_terrain_blend_attributes,
            import_terrain_blend_shader=import_terrain_blend_shader,
            import_water=import_water,
            import_static_lights=import_static_lights,
            static_lights_mode=static_lights_mode,
            static_lights_power=static_lights_power,
            import_mission_placeables=import_mission_placeables,
            mission_placeables_result=mission_placeables_result,
            import_particle_effects=import_particle_effects,
            particle_effects_result=particle_effects_result,
            import_cga_entities=import_cga_entities,
            cga_entities_result=cga_entities_result,
            terrain_mesh_result=terrain_mesh_result,
            water_result=water_result,
            liquid_surface_result=liquid_surface_result,
            static_lights_result=static_lights_result,
            animate_texture_sequences=animate_texture_sequences,
            animate_shader_uv_scroll=animate_shader_uv_scroll,
            texture_sequences_applied=texture_sequences_applied,
            texture_sequences_skipped=texture_sequences_skipped,
            texture_sequence_missing_frames=texture_sequence_missing_frames,
            shader_uv_scroll_applied=shader_uv_scroll_applied,
            shader_uv_scroll_skipped=shader_uv_scroll_skipped,
            npc_result=npc_result,
        )

        if skybox_result:
            summary = replace(
                summary, skybox_status="applied" if skybox_result.applied else skybox_result.reason,
                skybox_profile=skybox_result.profile,
            )

        if environment_lighting_result:
            summary = replace(
                summary, environment_lighting_status=(
                    f"preview:{environment_lighting_result.reason}" if environment_lighting_result.applied else environment_lighting_result.reason
                ),
            )

        # Prune empty subcollections (vegetation children first, then top-level categories)
        veg_parent = category_collections.get("VEGETATION")
        veg_sub_names = ("Trees & Forest", "Bushes & Flowers", "Grass & Cover")
        for veg_sub in veg_sub_names:
            sub_col = category_collections.pop(veg_sub, None)
            if sub_col is not None and len(sub_col.objects) == 0 and len(sub_col.children) == 0:
                if veg_parent is not None and sub_col.name in veg_parent.children.keys():
                    veg_parent.children.unlink(sub_col)
                bpy.data.collections.remove(sub_col)

        for cat_name, cat_col in list(category_collections.items()):
            if cat_name != "ROOT" and len(cat_col.objects) == 0 and len(cat_col.children) == 0:
                if cat_col.name in preview_collection.children.keys():
                    preview_collection.children.unlink(cat_col)
                bpy.data.collections.remove(cat_col)

        if (
            imported_template_count == 0
            and terrain_mesh_result is None
            and water_result is None
            and not (npc_result and npc_result.spawned_count)
            and static_lights_result is None
            and mission_placeables_result is None
            and particle_effects_result is None
            and cga_entities_result is None
        ):
            if preview_collection.name in root_collection.children.keys():
                root_collection.children.unlink(preview_collection)
            bpy.data.collections.remove(preview_collection)

        yield (0.985, "[8/8] Otimizando viewport (60+ FPS)...")
        apply_viewport_60fps_optimization(context, profile_key)
        if terrain_mesh_result is not None:
            try:
                cx = float(terrain_mesh_result.width) * float(terrain_mesh_result.xy_scale) * 0.5
                cy = float(terrain_mesh_result.height) * float(terrain_mesh_result.xy_scale) * 0.5
                cz = (float(terrain_mesh_result.min_height) + float(terrain_mesh_result.max_height)) * 0.5
                span = max(
                    float(terrain_mesh_result.width) * float(terrain_mesh_result.xy_scale),
                    float(terrain_mesh_result.height) * float(terrain_mesh_result.xy_scale),
                )
                frame_viewport_on_map((cx, cy, cz), distance=max(900.0, span * 0.55))
            except Exception:
                pass
        advance_progress("complete", "Level import complete")
        try:
            from importers.asset_catalog import invalidate_asset_catalog_cache
            invalidate_asset_catalog_cache()
        except Exception:
            pass
        yield (0.995, "[8/8] Liberando handles e caches...")
        if resolver is not None:
            try:
                resolver.close()
            except Exception:
                pass
        try:
            from materials.material_manager import set_session_pak_catalog
            set_session_pak_catalog(None)
        except Exception:
            pass
        import gc
        gc.collect(0)
        completed_ok = True
        return LevelImportResult(
            level_dir=level_path,
            client_root=client_root_path,
            import_mode=import_mode,
            limited_preview=limited_preview,
            max_unique_cgfs=max_unique_cgfs,
            max_placements_per_template=max_placements_per_template,
            resolved_job_count=len(resolution.resolved),
            missing_resource_count=len(resolution.missing),
            total_template_count=len(template_collection.templates),
            max_available_placements_per_template=template_collection.max_placements_per_template,
            selected_template_count=len(selected_templates),
            imported_template_count=imported_template_count,
            failed_template_count=len(failures),
            skipped_template_count=len(skipped_templates),
            selected_placement_count=selected_placement_count,
            placement_objects_created=placement_objects_created,
            object_placement_count=object_placement_count,
            brush_placement_count=brush_placement_count,
            non_default_transform_count=sum(
                summary.is_non_default for summary in transform_summaries
            ),
            invalid_placements_skipped=len(placement_skips),
            invalid_object_scale_count=sum(
                skip.reason_code == INVALID_OBJECT_SCALE
                for skip in placement_skips
            ),
            invalid_brush_matrix_count=sum(
                skip.reason_code == INVALID_BRUSH_MATRIX
                for skip in placement_skips
            ),
            first_invalid_placement=placement_skips[0] if placement_skips else None,
            transform_summaries=tuple(transform_summaries),
            per_template_placement_counts=tuple(per_template_placement_counts),
            terrain_mesh_result=terrain_mesh_result,
            water_result=water_result,
            liquid_surface_result=liquid_surface_result,
            static_lights_result=static_lights_result,
            mission_placeables_result=mission_placeables_result,
            particle_effects_result=particle_effects_result,
            cga_entities_result=cga_entities_result,
            summary=summary,
            objects_created=objects_created,
            meshes_created=meshes_created,
            failures=tuple(failures),
            skipped_templates=tuple(skipped_templates),
            skybox_result=skybox_result,
            environment_lighting_result=environment_lighting_result,
            npc_result=npc_result,
        )
    finally:
        if not completed_ok:
            cancel_ev.set()
        if pending_future is not None:
            try:
                pending_future.cancel()
            except Exception:
                pass
        executor.shutdown(wait=False, cancel_futures=True)
        if resolver is not None:
            try:
                resolver.close()
            except Exception:
                pass


def _emit_progress(
    callback: Callable[[LevelImportProgress], None] | None,
    *,
    stage: str,
    message: str,
    completed: int,
    total: int,
) -> None:
    if callback is None:
        return
    callback(
        LevelImportProgress(
            stage=stage,
            message=message,
            completed=completed,
            total=total,
        )
    )


def _build_execution_summary(
    *,
    total_template_count: int,
    selected_template_count: int,
    imported_template_count: int,
    failed_template_count: int,
    skipped_template_count: int,
    placement_objects_created: int,
    invalid_placements_skipped: int,
    invalid_object_scale_count: int,
    invalid_brush_matrix_count: int,
    first_invalid_placement: PlacementSkip | None,
    limited_preview: bool,
    import_terrain: bool,
    import_terrain_textures: bool,
    import_terrain_blend_attributes: bool,
    import_terrain_blend_shader: bool,
    import_water: bool,
    import_static_lights: bool,
    static_lights_mode: str,
    static_lights_power: float,
    import_mission_placeables: bool,
    mission_placeables_result: MissionPlaceablesImportResult | None,
    import_particle_effects: bool,
    particle_effects_result: ParticleEffectsImportResult | None,
    import_cga_entities: bool,
    cga_entities_result: CgaEntitiesImportResult | None,
    terrain_mesh_result: TerrainMeshResult | None,
    water_result: WaterPlaneResult | None,
    liquid_surface_result: LiquidSurfaceMaterialResult | None,
    static_lights_result: StaticLightsImportResult | None,
    animate_texture_sequences: bool,
    animate_shader_uv_scroll: bool,
    texture_sequences_applied: int,
    texture_sequences_skipped: int,
    texture_sequence_missing_frames: int,
    shader_uv_scroll_applied: int,
    shader_uv_scroll_skipped: int,
    npc_result: object | None = None,
) -> LevelImportExecutionSummary:
    terrain = terrain_mesh_result
    return LevelImportExecutionSummary(
        import_scope="limited preview" if limited_preview else "full",
        cgf_total=total_template_count,
        cgf_selected=selected_template_count,
        cgf_imported=imported_template_count,
        cgf_failed=failed_template_count,
        cgf_skipped_expected=skipped_template_count,
        placements_created=placement_objects_created,
        invalid_placements_skipped=invalid_placements_skipped,
        invalid_object_scale_count=invalid_object_scale_count,
        invalid_brush_matrix_count=invalid_brush_matrix_count,
        invalid_placement_sample=(
            f"{first_invalid_placement.source_type}[{first_invalid_placement.source_index}] "
            f"{first_invalid_placement.cgf_reference}: {first_invalid_placement.reason}"
            if first_invalid_placement
            else None
        ),
        terrain_enabled=import_terrain,
        terrain_created=terrain is not None,
        terrain_vertices=terrain.vertex_count if terrain else 0,
        terrain_faces=terrain.face_count if terrain else 0,
        terrain_materials=terrain.material_slot_count if terrain else 0,
        terrain_uv_loops=terrain.uv_loop_count if terrain else 0,
        detail_textures_total=terrain.detail_texture_count if terrain else 0,
        detail_textures_existing=terrain.existing_detail_texture_count if terrain else 0,
        detail_textures_missing=terrain.missing_detail_texture_count if terrain else 0,
        texture_preview_requested=import_terrain and import_terrain_textures,
        texture_images_loaded=terrain.texture_images_loaded if terrain else 0,
        texture_images_failed=terrain.texture_images_failed if terrain else 0,
        texture_nodes_created=terrain.texture_nodes_created if terrain else 0,
        blend_attributes_requested=(
            import_terrain and (import_terrain_blend_attributes or import_terrain_blend_shader)
        ),
        blend_attribute_layers_created=getattr(terrain, "blend_attribute_layers_created", 0) if terrain else 0,
        blend_weight_material_count=getattr(terrain, "blend_weight_material_count", 0) if terrain else 0,
        blend_boundary_sample_count=getattr(terrain, "blend_boundary_sample_count", 0) if terrain else 0,
        blend_invalid_weight_count=getattr(terrain, "blend_invalid_weight_count", 0) if terrain else 0,
        blend_shader_requested=import_terrain and import_terrain_blend_shader,
        blend_shader_graph_created=getattr(terrain, "blend_shader_graph_created", False) if terrain else False,
        blend_shader_material_count=getattr(terrain, "blend_shader_material_count", 0) if terrain else 0,
        blend_shader_included_materials=",".join(
            str(index)
            for index in (getattr(terrain, "blend_shader_included_material_indices", ()) if terrain else ())
        ),
        blend_shader_texture_images_loaded=getattr(terrain, "blend_shader_texture_images_loaded", 0) if terrain else 0,
        blend_shader_texture_images_failed=getattr(terrain, "blend_shader_texture_images_failed", 0) if terrain else 0,
        blend_shader_texture_nodes_created=getattr(terrain, "blend_shader_texture_nodes_created", 0) if terrain else 0,
        blend_shader_skipped_material_count=len(getattr(terrain, "blend_shader_skipped_material_indices", ())) if terrain else 0,
        blend_shader_skipped_sample_counts=",".join(
            f"{index}:{count}"
            for index, count in (
                getattr(terrain, "blend_shader_skipped_material_sample_counts", ())
                if terrain
                else ()
            )
        ),
        blend_shader_skipped_reasons=",".join(
            f"{index}:{reason}:{count}"
            for index, reason, count in (
                getattr(terrain, "blend_shader_skipped_material_reasons", ())
                if terrain
                else ()
            )
        ),
        blend_shader_projection_mode=getattr(terrain, "blend_shader_projection_mode", "") if terrain else "",
        blend_shader_warnings="; ".join(getattr(terrain, "blend_shader_warnings", ())) if terrain else "",
        water_enabled=import_water,
        water_created=bool(water_result and water_result.created),
        water_level=water_result.water_level if water_result else None,
        water_width=water_result.width if water_result else 0.0,
        water_height=water_result.height if water_result else 0.0,
        water_skip_reason=water_result.skip_reason if water_result else None,
        liquid_surface_requested=liquid_surface_result.requested if liquid_surface_result else False,
        liquid_surface_applied=liquid_surface_result.applied if liquid_surface_result else False,
        liquid_surface_kind=liquid_surface_result.selected_kind if liquid_surface_result else "",
        liquid_surface_inferred_kind=liquid_surface_result.inferred_kind if liquid_surface_result else "",
        liquid_surface_preset=liquid_surface_result.selected_preset if liquid_surface_result else "",
        liquid_surface_textures_loaded=liquid_surface_result.textures_loaded if liquid_surface_result else 0,
        liquid_surface_textures_used=liquid_surface_result.textures_used if liquid_surface_result else 0,
        liquid_surface_material_name=liquid_surface_result.material_name if liquid_surface_result else "",
        liquid_surface_skip_reason=liquid_surface_result.skip_reason if liquid_surface_result else None,
        liquid_surface_warnings="; ".join(liquid_surface_result.warnings) if liquid_surface_result else "",
        static_lights_enabled=import_static_lights,
        static_lights_file_found=static_lights_result.file_found if static_lights_result else False,
        static_lights_created=static_lights_result.created if static_lights_result else False,
        static_lights_count=static_lights_result.light_count if static_lights_result else 0,
        static_lights_created_count=static_lights_result.created_count if static_lights_result else 0,
        static_lights_failed_count=static_lights_result.failed_count if static_lights_result else 0,
        static_lights_mode=static_lights_result.mode if static_lights_result else static_lights_mode if import_static_lights else "",
        static_lights_power=static_lights_result.power if static_lights_result else static_lights_power if import_static_lights else 0.0,
        static_lights_skip_reason=static_lights_result.skip_reason if static_lights_result else None,
        mission_placeables_enabled=import_mission_placeables,
        mission_placeables_file_found=mission_placeables_result.file_found if mission_placeables_result else False,
        mission_placeables_created=mission_placeables_result.created_count > 0 if mission_placeables_result else False,
        mission_placeables_candidates=mission_placeables_result.candidates_count if mission_placeables_result else 0,
        mission_placeables_created_count=mission_placeables_result.created_count if mission_placeables_result else 0,
        mission_placeables_skipped_count=mission_placeables_result.skipped_count if mission_placeables_result else 0,
        mission_placeables_failed_count=mission_placeables_result.failed_count if mission_placeables_result else 0,
        mission_placeables_angles_applied_count=mission_placeables_result.angles_applied_count if mission_placeables_result else 0,
        mission_placeables_skip_reasons=_format_reason_counts(
            mission_placeables_result.skip_reasons if mission_placeables_result else {}
        ),
        mission_placeables_failure_reasons=_format_reason_counts(
            mission_placeables_result.failure_reasons if mission_placeables_result else {}
        ),
        particle_effects_enabled=import_particle_effects,
        particle_effects_files_scanned=particle_effects_result.files_scanned if particle_effects_result else 0,
        particle_effects_records_found=particle_effects_result.records_found if particle_effects_result else 0,
        particle_effects_definitions_found=particle_effects_result.definitions_found if particle_effects_result else 0,
        particle_effects_textures_resolved=particle_effects_result.textures_resolved if particle_effects_result else 0,
        particle_effects_sprites_created=particle_effects_result.sprite_visuals_created if particle_effects_result else 0,
        particle_effects_markers_created=particle_effects_result.marker_fallback_created if particle_effects_result else 0,
        particle_effects_skipped_invalid=particle_effects_result.skipped_invalid_placements if particle_effects_result else 0,
        particle_effects_unsupported_count=particle_effects_result.unsupported_effects if particle_effects_result else 0,
        particle_effects_skip_reasons=_format_reason_counts(
            particle_effects_result.skip_reasons if particle_effects_result else {}
        ),
        cga_entities_enabled=import_cga_entities,
        cga_entities_file_found=cga_entities_result.file_found if cga_entities_result else False,
        cga_entities_created=cga_entities_result.created_count > 0 if cga_entities_result else False,
        cga_entities_candidates=cga_entities_result.candidates_count if cga_entities_result else 0,
        cga_entities_created_count=cga_entities_result.created_count if cga_entities_result else 0,
        cga_entities_skipped_count=cga_entities_result.skipped_count if cga_entities_result else 0,
        cga_entities_failed_count=cga_entities_result.failed_count if cga_entities_result else 0,
        cga_entities_angles_applied_count=cga_entities_result.angles_applied_count if cga_entities_result else 0,
        cga_entities_controller_count=cga_entities_result.controller_count_total if cga_entities_result else 0,
        cga_entities_timing_present_count=cga_entities_result.timing_present_count if cga_entities_result else 0,
        cga_entities_skip_reasons=_format_reason_counts(
            cga_entities_result.skip_reasons if cga_entities_result else {}
        ),
        cga_entities_failure_reasons=_format_reason_counts(
            cga_entities_result.failure_reasons if cga_entities_result else {}
        ),
        texture_sequences_requested=animate_texture_sequences,
        texture_sequences_applied=texture_sequences_applied,
        texture_sequences_skipped=texture_sequences_skipped,
        texture_sequence_missing_frames=texture_sequence_missing_frames,
        shader_uv_scroll_requested=animate_shader_uv_scroll,
        shader_uv_scroll_applied=shader_uv_scroll_applied,
        shader_uv_scroll_skipped=shader_uv_scroll_skipped,
        npcs_spawned=npc_result.spawned_count if npc_result else 0,
        npc_models_loaded=npc_result.models_loaded_count if npc_result else 0,
    )


def _format_reason_counts(reason_counts: dict) -> str:
    return ",".join(
        f"{reason}:{count}"
        for reason, count in sorted((reason_counts or {}).items())
    )


def _parse_level_cgf_sources(level_path: Path):
    leveldata_path = level_path / "leveldata.xml"
    if not leveldata_path.is_file():
        raise FileNotFoundError(f"leveldata.xml is required: {leveldata_path}")

    level_data = parse_leveldata(leveldata_path)

    objects_path = level_path / "objects.lst"
    objects = parse_objects_lst(objects_path, level_data) if objects_path.is_file() else None

    brush_path = level_path / "brush.lst"
    brush = parse_brush_lst(brush_path) if brush_path.is_file() else None

    return level_data, objects, brush


def _is_expected_cgf_skip(reason_code: str) -> bool:
    return reason_code in {"empty_mesh", "no_geometry_for_mode"}


def _detach_template_collections_from_scene(root_collection, new_collections):
    for collection in new_collections:
        if collection.name in root_collection.children.keys():
            root_collection.children.unlink(collection)


def _find_imported_template_collection(new_collections, preview_collection):
    imported = tuple(collection for collection in new_collections if collection != preview_collection)
    if len(imported) != 1:
        raise RuntimeError(f"CGF import created {len(imported)} collections; expected exactly one")
    return imported[0]



def import_level(
    context,
    level_dir: Path | str,
    client_root: Path | str,
    **kwargs,
) -> LevelImportResult:
    """
    Synchronous wrapper for import_level_generator.
    Drives the generator to completion and calls progress_callback if provided.
    Guarantees backwards compatibility for CLI and automated testing.
    """
    progress_callback = kwargs.get("progress_callback")
    gen = import_level_generator(context, level_dir, client_root, **kwargs)
    last_state = None
    try:
        while True:
            frac, msg = next(gen)
            state = (frac, msg)
            if state == last_state:
                time.sleep(0.002)
            else:
                last_state = state
                if progress_callback:
                    progress_callback(
                        LevelImportProgress(
                            stage="import",
                            message=msg,
                            completed=int(frac * 100),
                            total=100,
                        )
                    )
    except StopIteration as exc:
        return exc.value
