from pathlib import Path

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy_extras.io_utils import ImportHelper

from aion_formats.level import (
    LIQUID_KIND_AUTO,
    LIQUID_KIND_LAVA,
    LIQUID_KIND_UNKNOWN,
    LIQUID_KIND_WATER,
    LIQUID_PRESET_AUTO,
    LIQUID_PRESET_LAVA_EMISSIVE,
    LIQUID_PRESET_NORMAL,
    LIQUID_PRESET_TRANSPARENT,
)

import time
from importers.level_importer import import_level, import_level_generator
from importers.level_summary import format_level_import_report
from importers.static_lights_importer import (
    DEFAULT_STATIC_LIGHT_POWER,
    STATIC_LIGHTS_MODE_EMPTY,
    STATIC_LIGHTS_MODE_POINT_LIGHT,
)


class AION_OT_import_level_folder(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.aion_level_folder"
    bl_label = "Import Aion Level Folder"
    bl_description = "Import an unpacked Aion level locally"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ""
    use_filter_folder = True

    directory: StringProperty(
        name="Folder",
        description="Level folder or directory",
        subtype="DIR_PATH",
        options={"HIDDEN"},
    )

    filter_glob: StringProperty(
        default="*.pak;*.xml;*.lst;*.h32;*.dat",
        options={"HIDDEN"},
    )

    import_mode: EnumProperty(
        name="Import Mode",
        description="What to import from resolved level CGF references",
        items=(
            ("VISUAL", "Visual", "Import visual level content"),
            (
                "COLLISION",
                "Collision",
                "Import terrain heightfield plus collision geometry from CGF and placed CGA entities",
            ),
        ),
        default="VISUAL",
    )

    client_root: StringProperty(
        name="Client Root",
        description="Aion client root folder (auto-detected or configured)",
        subtype="DIR_PATH",
        default="",
    )

    terrain_lod: EnumProperty(
        name="Terrain LOD",
        description="Terrain mesh detail level. LOD 2 = fast recommended (512x512) renders in ~1.5s, LOD 1 = full (1024x1024)",
        items=(
            ("2", "LOD 2 (Fast - Recommended)", "Half vertex density (512x512) - Renders in ~1.5s, consumes 75% less RAM"),
            ("1", "LOD 1 (Full 100% Quality)", "Full vertex density (1024x1024) - Very heavy on huge maps"),
            ("4", "LOD 4 (Ultra Fast / Preview)", "Quarter vertex density (256x256) - Renders in <1s"),
        ),
        default="2",
    )

    limited_preview: BoolProperty(
        name="Limited Preview (Debug)",
        description="Apply template and placement limits for bounded debugging and smoke tests",
        default=False,
    )

    max_unique_cgfs: IntProperty(
        name="Preview Max Unique CGFs",
        description="Maximum unique CGF templates imported only in limited preview mode",
        default=10,
        min=1,
    )

    max_placements_per_template: IntProperty(
        name="Preview Placements per Template",
        description="Maximum placements per template created only in limited preview mode",
        default=3,
        min=1,
    )

    # Terrain
    import_terrain: BoolProperty(
        name="Import Terrain Preview",
        description="Create a terrain mesh preview from terrain/land_map.h32",
        default=True,
    )
    import_terrain_textures: BoolProperty(
        name="Load Terrain Texture Preview",
        description="Explicitly load resolved terrain detail DDS files into simple material texture nodes",
        default=True,
    )
    import_terrain_blend_attributes: BoolProperty(
        name="Smooth Terrain Multi-Layer Blending",
        description="Compute and store smooth terrain material weights as vertex color attributes",
        default=True,
    )
    import_terrain_blend_shader: BoolProperty(
        name="Terrain Blend Shader",
        description="Create a unified multi-layer blended terrain material with smooth transitions between grass, rock, and dirt",
        default=True,
    )
    import_terrain_shadows: BoolProperty(
        name="Terrain Lightmap / Shadows",
        description="Apply terrainlm.pak baked shadow maps to terrain shader",
        default=True,
    )

    # Architecture & Props
    import_buildings: BoolProperty(
        name="Buildings & Architecture",
        description="Import buildings, structures, bridges, and monuments",
        default=True,
    )
    import_structures: BoolProperty(
        name="Structural Geometry",
        description="Import walls, bridges, stairs, and ruins",
        default=True,
    )
    import_doors_portals: BoolProperty(
        name="Doors & Portals",
        description="Import gates, doors, and dimensional portals",
        default=True,
    )
    import_props: BoolProperty(
        name="Props & Decorative Objects",
        description="Import camp items, furniture, barrels, and totems",
        default=True,
    )
    import_rocks: BoolProperty(
        name="Rocks & Natural Formations",
        description="Import boulders, cliffs, stalagmites, and crystals",
        default=True,
    )
    import_interactive_objects: BoolProperty(
        name="Interactive Objects & Signs",
        description="Import milestones, altars, burners, and signboards",
        default=True,
    )

    # Vegetation
    import_vegetation: BoolProperty(
        name="Vegetation",
        description="Master switch for all vegetation elements (can add thousands of objects; enable when needed)",
        default=False,
    )
    import_trees: BoolProperty(
        name="Trees & Forest",
        description="Import trees, trunks, branches, and pines",
        default=True,
    )
    import_grass: BoolProperty(
        name="Grass & Cover",
        description="Import grass fields, weeds, and ground cover (over 10,000 objects on full maps; enable if required)",
        default=False,
    )
    import_bushes_flowers: BoolProperty(
        name="Bushes & Flowers",
        description="Import shrubs, flowers, crops, and aquatic flora",
        default=True,
    )

    # Water & Liquids
    import_water: BoolProperty(
        name="Import Water Plane",
        description="Create a simple water plane from LevelInfo WaterLevel and heightmap dimensions",
        default=True,
    )
    import_textured_liquid_surface: BoolProperty(
        name="Import Textured Liquid Surface",
        description="Apply optional water/lava preview material to the imported liquid plane",
        default=True,
    )
    liquid_kind: EnumProperty(
        name="Liquid Kind",
        description="Select the liquid material family or infer it from level data",
        items=(
            (LIQUID_KIND_AUTO, "Auto", "Infer water/lava from level data and texture references"),
            (LIQUID_KIND_WATER, "Water", "Use water-like liquid material selection"),
            (LIQUID_KIND_LAVA, "Lava", "Use lava-like emissive liquid material selection"),
            (LIQUID_KIND_UNKNOWN, "Unknown", "Use fallback liquid material selection"),
        ),
        default=LIQUID_KIND_AUTO,
    )
    liquid_preset: EnumProperty(
        name="Liquid Preset",
        description="Choose a simple liquid material preset",
        items=(
            (LIQUID_PRESET_AUTO, "Auto", "Choose a conservative preset from liquid kind"),
            (LIQUID_PRESET_NORMAL, "Normal", "Water-style material with diffuse/normal candidates"),
            (LIQUID_PRESET_TRANSPARENT, "Transparent", "More transparent water-style material"),
            (LIQUID_PRESET_LAVA_EMISSIVE, "Lava Emissive", "Emissive lava-style material"),
        ),
        default=LIQUID_PRESET_AUTO,
    )

    # Environment, Sky & Lighting
    import_skybox: BoolProperty(
        name="Static Skybox Background (Experimental)",
        description="Camera-only upper sky; preserves lighting. Reference orientation, no atmosphere or clouds",
        default=False,
    )
    import_environment_lighting: BoolProperty(
        name="Environment Lighting Preview (Experimental)",
        description="Static Lighting_000 SunVector reference + profile ambient; not calibrated game daylight",
        default=True,
    )
    environment_sun_energy: FloatProperty(
        name="Sun Strength (Preview)", default=2.0, min=0.0,
        description="Blender Sun energy, not a conversion of Aion lighting units",
    )
    environment_ambient_strength: FloatProperty(
        name="Ambient Strength (Preview)", default=0.3, min=0.0,
        description="World ambient; Eevee requires indirect light probes for diffuse ambient",
    )
    skybox_time_option: StringProperty(
        name="Sky Time Profile",
        description="Exact TimeEnvOption name from the mission; no automatic time/weather selection",
        default="Daylight",
    )
    import_static_lights: BoolProperty(
        name="Import Static Lights",
        description="Create optional point lights from staticdeferredlights.lst using confirmed raw coordinates",
        default=False,
    )
    static_lights_mode: EnumProperty(
        name="Static Lights Mode",
        description="Preview staticdeferredlights.lst as markers or Blender point lights",
        items=(
            (
                STATIC_LIGHTS_MODE_POINT_LIGHT,
                "Point Lights",
                "Create conservative Blender point lights",
            ),
            (
                STATIC_LIGHTS_MODE_EMPTY,
                "Markers",
                "Create non-rendering empty markers",
            ),
        ),
        default=STATIC_LIGHTS_MODE_POINT_LIGHT,
    )
    static_lights_power: FloatProperty(
        name="Static Light Power",
        description="Energy assigned to each imported static deferred point light",
        default=DEFAULT_STATIC_LIGHT_POWER,
        min=1.0,
        soft_max=5000.0,
    )

    # Dynamics, Placeables & Collision
    import_mission_placeables: BoolProperty(
        name="Import Obelisks & Placeables",
        description="Import hardcoded client Obelisks, pedestals, client NPCs (fauna/critters), and placeables from mission_mission0.xml",
        default=False,
    )
    apply_mission_angles: BoolProperty(
        name="Apply Mission Angles",
        description="Apply Entity.Angles rotation for imported mission PlaceableObject previews",
        default=True,
    )
    import_particle_effects: BoolProperty(
        name="Import Particle Effects",
        description="Create ParticleEffect markers/sprites from entitycontexts*.lst and matching .prt libraries",
        default=False,
    )
    import_cga_entities: BoolProperty(
        name="Import CGA Entities",
        description="Import static mesh content from BasicEntity .cga references",
        default=True,
    )
    animate_cga_controllers: BoolProperty(
        name="Animate CGA Controllers",
        description="Apply decoded CGA rotation controller keyframes for imported CGA entities",
        default=True,
    )
    apply_smoothing_groups: BoolProperty(
        name="Apply CGF Smoothing Groups",
        description="Set imported CGF polygons smooth when the parsed face smoothing group is nonzero",
        default=False,
    )
    import_collision: BoolProperty(
        name="Collision Geometry",
        description="Import invisible collision walls and walk obstacles (recommended False for visual scene editing)",
        default=False,
    )

    # NPCs & World Spawns (Section 7)
    import_npcs: BoolProperty(
        name="NPCs & World Spawns",
        description="Import authoritative NPC spawns from client_world XML",
        default=False,
    )
    import_npc_models: BoolProperty(
        name="Resolve & Load 3D NPC Models",
        description="Load 3D CGF meshes for monsters, humanoids, and Shugos",
        default=False,
    )
    animate_npcs: BoolProperty(
        name="Animate NPCs (Armatures & Idle CAF)",
        description="Build armature rigs, assign vertex skinning, and play looping idle animations on NPCs",
        default=False,
    )
    import_monsters: BoolProperty(
        name="Monsters & Hostiles",
        description="Spawn monsters, wild creatures, and enemy mobs",
        default=True,
    )
    import_friendly_npcs: BoolProperty(
        name="Friendly NPCs & Merchants",
        description="Spawn town NPCs, quest givers, and merchants",
        default=True,
    )
    import_ambient_creatures: BoolProperty(
        name="Ambient Critters & Fauna",
        description="Spawn ambient fauna, birds, and critters",
        default=True,
    )

    # LOD Levels (Section 8)
    import_lod0: BoolProperty(
        name="LOD 0 (Full High Detail)",
        description="Import base full-detail models",
        default=True,
    )
    import_lod1: BoolProperty(
        name="LOD 1 (Medium Detail)",
        description="Import level-of-detail 1 models (disabled by default to prevent overlapping duplicates)",
        default=False,
    )
    import_lod2: BoolProperty(
        name="LOD 2 (Low Detail)",
        description="Import level-of-detail 2 models",
        default=False,
    )
    import_lod3: BoolProperty(
        name="LOD 3 (Distant Detail)",
        description="Import level-of-detail 3 models",
        default=False,
    )

    # Engine Performance Options
    use_mesh_instancing: BoolProperty(
        name="Hardware Mesh Instancing (100+ FPS)",
        description="Direct GPU mesh datablock sharing instead of collection instances. Drastically lowers draw calls and Material Preview lag",
        default=True,
    )
    optimize_material_preview: BoolProperty(
        name="Optimize Material Preview (EEVEE Next)",
        description="Dithered alpha clip and global material deduplication for smooth navigation",
        default=True,
    )
    multithreaded_io: BoolProperty(
        name="Multi-threaded Asset Decompression",
        description="Fast background PAK decompression using CPU worker threads",
        default=True,
    )

    # Shaders & Animations
    animate_texture_sequences: BoolProperty(
        name="Animate Texture Sequences",
        description="Use confirmed diffuse texture frame sequences as Blender image sequences for imported CGFs",
        default=True,
    )
    animate_shader_uv_scroll: BoolProperty(
        name="Animate Shader UV Scroll",
        description="Use confirmed client shader TexShift semantics to animate supported imported CGF material UVs",
        default=True,
    )
    texture_animation_fps: IntProperty(
        name="Texture Sequence FPS",
        description="Playback FPS for imported texture image sequences; shader UV scroll uses shader speed and scene time",
        default=10,
        min=1,
        max=60,
    )

    def invoke(self, context, event):
        settings = getattr(context.scene, "aion_settings", None)
        if settings:
            for prop_name in (
                "client_root", "terrain_lod",
                "import_terrain", "import_terrain_textures", "import_terrain_blend_attributes",
                "import_terrain_blend_shader", "import_terrain_shadows",
                "import_buildings", "import_structures", "import_doors_portals",
                "import_props", "import_rocks", "import_interactive_objects",
                "import_vegetation", "import_trees", "import_grass", "import_bushes_flowers",
                "import_water", "import_textured_liquid_surface",
                "import_lighting", "import_environment_lighting", "import_skybox", "import_static_lights",
                "import_collision", "import_npcs", "import_npc_models", "animate_npcs",
                "import_monsters", "import_friendly_npcs", "import_ambient_creatures",
                "import_lod0", "import_lod1", "import_lod2", "import_lod3",
                "use_mesh_instancing", "optimize_material_preview", "multithreaded_io",
            ):
                if hasattr(settings, prop_name) and hasattr(self, prop_name):
                    try:
                        setattr(self, prop_name, getattr(settings, prop_name))
                    except Exception:
                        pass
        return super().invoke(context, event)

    def execute(self, context):
        raw_path = str(self.filepath).strip() if getattr(self, "filepath", None) else ""
        raw_dir = str(self.directory).strip() if getattr(self, "directory", None) else ""

        target_level_dir = None
        if raw_path:
            p = Path(raw_path)
            if p.is_file():
                target_level_dir = p.parent
            elif p.is_dir():
                target_level_dir = p

        if target_level_dir is None and raw_dir:
            p = Path(raw_dir)
            if p.is_dir():
                target_level_dir = p

        if target_level_dir is None and raw_path:
            target_level_dir = Path(raw_path)

        if target_level_dir is None:
            self.report({"ERROR"}, "Selecione a pasta do mapa ou o arquivo Level.pak")
            return {"CANCELLED"}

        client_root = self.client_root.strip()
        if not client_root or not Path(client_root).is_dir():
            for parent in target_level_dir.parents:
                if (parent / "levels").is_dir() or (parent / "L10N").is_dir() or (parent / "system.cfg").is_file():
                    client_root = str(parent)
                    break
            if not client_root:
                try:
                    from ..config.settings import get_default_client_root
                except ImportError:
                    from config.settings import get_default_client_root
                client_root = get_default_client_root()

        if not client_root or not Path(client_root).is_dir():
            self.report({"ERROR"}, f"Pasta Client Root do Aion não encontrada: '{client_root}'")
            return {"CANCELLED"}

        from materials.material_manager import clean_material_cache
        from materials.texture_loader import clear_texture_cache, purge_orphan_datablocks

        clean_material_cache()
        clear_texture_cache()
        purge_orphan_datablocks()

        visual_mode = self.import_mode == "VISUAL"
        effective_import_terrain = self.import_terrain if visual_mode else True
        effective_import_terrain_textures = (
            visual_mode and effective_import_terrain and self.import_terrain_textures
        )
        effective_import_terrain_blend_attributes = (
            visual_mode and effective_import_terrain and self.import_terrain_blend_attributes
        )
        effective_import_terrain_blend_shader = (
            visual_mode and effective_import_terrain and self.import_terrain_blend_shader
        )
        effective_import_terrain_shadows = (
            visual_mode and effective_import_terrain and self.import_terrain_shadows
        )
        effective_import_water = visual_mode and self.import_water
        effective_import_textured_liquid_surface = (
            effective_import_water and self.import_textured_liquid_surface
        )
        effective_import_static_lights = visual_mode and self.import_static_lights
        effective_import_mission_placeables = visual_mode and self.import_mission_placeables
        effective_import_particle_effects = visual_mode and self.import_particle_effects
        effective_import_cga_entities = self.import_cga_entities if visual_mode else True
        effective_animate_cga_controllers = (
            visual_mode and effective_import_cga_entities and self.animate_cga_controllers
        )
        effective_animate_texture_sequences = visual_mode and self.animate_texture_sequences
        effective_animate_shader_uv_scroll = visual_mode and self.animate_shader_uv_scroll

        from core.pak_engine import AionLevelUnpacker
        try:
            effective_level_dir = AionLevelUnpacker.prepare_level_directory(target_level_dir)
        except Exception:
            effective_level_dir = Path(target_level_dir)

        terrain_path = effective_level_dir / "terrain" / "land_map.h32"
        if effective_import_terrain and not terrain_path.is_file():
            self.report({"ERROR"}, f"Arquivo de terreno não encontrado: {terrain_path}")
            return {"CANCELLED"}

        import_kwargs = dict(
            terrain_lod=int(self.terrain_lod),
            import_mode=self.import_mode,
            import_skybox=visual_mode and self.import_skybox,
            skybox_time_option=self.skybox_time_option,
            import_environment_lighting=visual_mode and self.import_environment_lighting,
            environment_sun_energy=self.environment_sun_energy,
            environment_ambient_strength=self.environment_ambient_strength,
            limited_preview=self.limited_preview,
            max_unique_cgfs=self.max_unique_cgfs,
            max_placements_per_template=self.max_placements_per_template,
            import_terrain=effective_import_terrain,
            import_terrain_textures=effective_import_terrain_textures,
            import_terrain_blend_attributes=effective_import_terrain_blend_attributes,
            import_terrain_blend_shader=effective_import_terrain_blend_shader,
            import_terrain_shadows=effective_import_terrain_shadows,
            import_buildings=visual_mode and self.import_buildings,
            import_structures=visual_mode and self.import_structures,
            import_doors_portals=visual_mode and self.import_doors_portals,
            import_props=visual_mode and self.import_props,
            import_rocks=visual_mode and self.import_rocks,
            import_interactive_objects=visual_mode and self.import_interactive_objects,
            import_vegetation=visual_mode and self.import_vegetation,
            import_trees=visual_mode and self.import_trees,
            import_grass=visual_mode and self.import_grass,
            import_bushes_flowers=visual_mode and self.import_bushes_flowers,
            import_water=effective_import_water,
            import_textured_liquid_surface=effective_import_textured_liquid_surface,
            liquid_kind=self.liquid_kind,
            liquid_preset=self.liquid_preset,
            import_static_lights=effective_import_static_lights,
            static_lights_mode=self.static_lights_mode,
            static_lights_power=self.static_lights_power,
            import_mission_placeables=effective_import_mission_placeables,
            apply_mission_angles=self.apply_mission_angles,
            import_particle_effects=effective_import_particle_effects,
            import_cga_entities=effective_import_cga_entities,
            animate_cga_controllers=effective_animate_cga_controllers,
            apply_smoothing_groups=self.apply_smoothing_groups,
            animate_texture_sequences=effective_animate_texture_sequences,
            animate_shader_uv_scroll=effective_animate_shader_uv_scroll,
            texture_animation_fps=self.texture_animation_fps,
            import_collision=self.import_collision if visual_mode else True,
            import_npcs=visual_mode and self.import_npcs,
            import_npc_models=visual_mode and self.import_npc_models,
            animate_npcs=visual_mode and self.animate_npcs,
            import_monsters=visual_mode and self.import_monsters,
            import_friendly_npcs=visual_mode and self.import_friendly_npcs,
            import_ambient_creatures=visual_mode and self.import_ambient_creatures,
            import_lod0=self.import_lod0,
            import_lod1=self.import_lod1,
            import_lod2=self.import_lod2,
            import_lod3=self.import_lod3,
            use_mesh_instancing=self.use_mesh_instancing,
            optimize_material_preview=self.optimize_material_preview,
            multithreaded_io=self.multithreaded_io,
        )

        self._target_level_dir = target_level_dir
        self._client_root = client_root
        self._effective_import_water = effective_import_water
        self._effective_import_textured_liquid_surface = effective_import_textured_liquid_surface
        self._effective_import_static_lights = effective_import_static_lights
        self._effective_import_mission_placeables = effective_import_mission_placeables
        self._effective_import_cga_entities = effective_import_cga_entities

        # Headless mode (CLI testing, benchmarks): run synchronously
        if bpy.app.background:
            result = import_level(context, target_level_dir, client_root, **import_kwargs)
            return self._finish_import(context, result)

        # Interactive GUI mode: run non-blocking modal timer loop
        self._generator = import_level_generator(context, target_level_dir, client_root, **import_kwargs)
        self._start_time = time.perf_counter()
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.016, window=context.window)
        wm.modal_handler_add(self)
        wm.progress_begin(0, 100)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "ESC":
            self._cleanup(context)
            self.report({"WARNING"}, "Aion level import cancelled by user.")
            return {"CANCELLED"}

        if event.type == "TIMER":
            t0 = time.perf_counter()
            # Process steps within a 15ms frame budget to keep Blender 100% responsive
            while time.perf_counter() - t0 < 0.015:
                try:
                    frac, msg = next(self._generator)
                    context.window_manager.progress_update(round(frac * 100))
                    context.workspace.status_text_set(f"Aion Import: {msg} ({round(frac * 100)}%)")
                except StopIteration as exc:
                    self._cleanup(context)
                    elapsed = time.perf_counter() - self._start_time
                    res = self._finish_import(context, exc.value)
                    context.workspace.status_text_set(f"Aion: Imported in {elapsed:.2f}s")
                    return res
                except Exception as exc:
                    self._cleanup(context)
                    self.report({"ERROR"}, f"Aion level import failed: {exc}")
                    return {"CANCELLED"}

            return {"PASS_THROUGH"}

        return {"PASS_THROUGH"}

    def _cleanup(self, context):
        if getattr(self, "_timer", None) is not None:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except Exception:
                pass
            self._timer = None
        try:
            context.window_manager.progress_end()
            context.workspace.status_text_set(None)
        except Exception:
            pass

    def _finish_import(self, context, result):
        target_level_dir = self._target_level_dir
        client_root = self._client_root
        effective_import_water = self._effective_import_water
        effective_import_textured_liquid_surface = self._effective_import_textured_liquid_surface
        effective_import_static_lights = self._effective_import_static_lights
        effective_import_mission_placeables = self._effective_import_mission_placeables
        effective_import_cga_entities = self._effective_import_cga_entities

        failure_samples = _format_cgf_issues(result.failures)
        skip_samples = _format_cgf_issues(result.skipped_templates)
        water_failure = (
            f", water={result.water_result.skip_reason}"
            if result.water_result and result.water_result.skip_reason
            else ""
        )
        if (
            result.imported_template_count == 0
            and result.terrain_mesh_result is None
            and not (result.skybox_result and result.skybox_result.applied)
            and not (result.environment_lighting_result and result.environment_lighting_result.applied)
            and not (result.water_result and result.water_result.created)
            and not (result.liquid_surface_result and result.liquid_surface_result.applied)
            and not (result.static_lights_result and result.static_lights_result.created)
            and not (
                result.mission_placeables_result
                and result.mission_placeables_result.created_count
            )
            and not (
                result.particle_effects_result
                and (
                    result.particle_effects_result.sprite_visuals_created
                    or result.particle_effects_result.marker_fallback_created
                )
            )
            and not (
                result.cga_entities_result
                and result.cga_entities_result.created_count
            )
            and not (
                result.npc_result
                and result.npc_result.spawned_count
            )
        ):
            self.report(
                {"ERROR"},
                "Aion level import failed: "
                f"selected={result.selected_template_count}, failed={result.failed_template_count}"
                f", skipped={result.skipped_template_count}"
                f"{failure_samples}{skip_samples}{water_failure}",
            )
            return {"CANCELLED"}

        report_type = (
            {"WARNING"}
            if result.failed_template_count
            or (result.skybox_result and not result.skybox_result.applied)
            or (result.environment_lighting_result and not result.environment_lighting_result.applied)
            or (effective_import_water and not result.summary.water_created)
            or (
                effective_import_textured_liquid_surface
                and result.liquid_surface_result
                and not result.liquid_surface_result.applied
            )
            or (
                effective_import_static_lights
                and result.static_lights_result
                and result.static_lights_result.failed_count
            )
            or (
                effective_import_mission_placeables
                and result.mission_placeables_result
                and result.mission_placeables_result.failed_count
            )
            or (
                effective_import_cga_entities
                and result.cga_entities_result
                and result.cga_entities_result.failed_count
            )
            else {"INFO"}
        )
        settings = getattr(context.scene, "aion_settings", None)
        if settings:
            settings.loaded_level_dir = str(target_level_dir)
            settings.level_path = str(target_level_dir)
            settings.client_root = str(client_root)
            settings.status_message = f"Loaded {target_level_dir.name}"

        self.report(
            report_type,
            format_level_import_report(result.summary) + failure_samples + skip_samples,
        )
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        box_main = layout.box()
        box_main.label(text="Import Configuration", icon="SETTINGS")
        box_main.prop(self, "import_mode")
        box_main.prop(self, "client_root")

        if self.import_mode != "VISUAL":
            return

        # Optimization & Viewport
        box_perf = layout.box()
        box_perf.label(text="Engine & Viewport Optimizations", icon="SHADING_RENDERED")
        box_perf.prop(self, "use_mesh_instancing")
        box_perf.prop(self, "optimize_material_preview")
        box_perf.prop(self, "multithreaded_io")

        # LOD Controls
        box_lod = layout.box()
        box_lod.label(text="LOD Level Controls", icon="LOD")
        row = box_lod.row(align=True)
        row.prop(self, "import_lod0", text="LOD 0")
        row.prop(self, "import_lod1", text="LOD 1")
        row.prop(self, "import_lod2", text="LOD 2")
        row.prop(self, "import_lod3", text="LOD 3")

        # Terrain & Material Blending
        box_terrain = layout.box()
        box_terrain.prop(self, "import_terrain", text="Terrain Heightfield", icon="LANDSCAPE")
        if self.import_terrain:
            col = box_terrain.column()
            col.prop(self, "terrain_lod")
            col.prop(self, "import_terrain_textures")
            col.prop(self, "import_terrain_blend_shader")
            col.prop(self, "import_terrain_blend_attributes")
            col.prop(self, "import_terrain_shadows")

        # Architecture & Props
        box_bldg = layout.box()
        box_bldg.prop(self, "import_buildings", text="Buildings & Structures", icon="HOME")
        if self.import_buildings:
            col = box_bldg.column()
            col.prop(self, "import_structures")
            col.prop(self, "import_doors_portals")

        box_props = layout.box()
        box_props.prop(self, "import_props", text="Props & Decorative", icon="OBJECT_DATAMODE")
        if self.import_props:
            col = box_props.column()
            col.prop(self, "import_rocks")
            col.prop(self, "import_interactive_objects")

        # Vegetation
        box_veg = layout.box()
        box_veg.prop(self, "import_vegetation", text="Vegetation", icon="OUTLINER_OB_CURVE")
        if self.import_vegetation:
            col = box_veg.column()
            col.prop(self, "import_trees")
            col.prop(self, "import_grass")
            col.prop(self, "import_bushes_flowers")

        # NPCs & World Spawns (Section 7)
        box_npcs = layout.box()
        box_npcs.prop(self, "import_npcs", text="NPCs & World Spawns", icon="COMMUNITY")
        if self.import_npcs:
            col = box_npcs.column()
            col.prop(self, "import_npc_models")
            col.prop(self, "animate_npcs")
            col.prop(self, "import_monsters")
            col.prop(self, "import_friendly_npcs")
            col.prop(self, "import_ambient_creatures")

        # Water & Liquids
        box_water = layout.box()
        box_water.prop(self, "import_water", text="Water & Ocean Planes", icon="FORCE_FLUID")
        if self.import_water:
            col = box_water.column()
            col.prop(self, "import_textured_liquid_surface")
            if self.import_textured_liquid_surface:
                col.prop(self, "liquid_kind")
                col.prop(self, "liquid_preset")

        # Environment, Sky & Lighting
        box_env = layout.box()
        box_env.label(text="Environment & Lighting", icon="LIGHT")
        box_env.prop(self, "import_environment_lighting")
        if self.import_environment_lighting:
            col = box_env.column()
            col.prop(self, "environment_sun_energy")
            col.prop(self, "environment_ambient_strength")
        box_env.prop(self, "import_skybox")
        if self.import_skybox:
            box_env.prop(self, "skybox_time_option")
        box_env.prop(self, "import_static_lights")
        if self.import_static_lights:
            col = box_env.column()
            col.prop(self, "static_lights_mode")
            col.prop(self, "static_lights_power")

        # Dynamics & Placeables
        box_dyn = layout.box()
        box_dyn.label(text="Dynamics & Placeables", icon="PHYSICS")
        box_dyn.prop(self, "import_cga_entities")
        if self.import_cga_entities:
            box_dyn.prop(self, "animate_cga_controllers")
        box_dyn.prop(self, "import_mission_placeables")
        if self.import_mission_placeables:
            box_dyn.prop(self, "apply_mission_angles")
        box_dyn.prop(self, "import_particle_effects")
        box_dyn.prop(self, "import_collision")

        # Shaders & Animations
        box_anim = layout.box()
        box_anim.label(text="Texture & Shader Animation", icon="ANIM_DATA")
        box_anim.prop(self, "animate_texture_sequences")
        box_anim.prop(self, "animate_shader_uv_scroll")
        if self.animate_texture_sequences:
            box_anim.prop(self, "texture_animation_fps")


def _format_cgf_issues(issues, limit=3):
    if not issues:
        return ""
    samples = "; ".join(
        f"{issue.resolved_path.name}:{issue.reason_code}"
        for issue in issues[:limit]
    )
    more = f"; +{len(issues) - limit} more" if len(issues) > limit else ""
    label = "failures" if issues[0].__class__.__name__.endswith("Failure") else "skips"
    return f"; {label}={samples}{more}"
