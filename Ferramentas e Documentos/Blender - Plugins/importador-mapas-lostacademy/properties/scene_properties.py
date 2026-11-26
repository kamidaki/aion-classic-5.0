"""
Scene Properties and Settings for Aion Blender Toolkit.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from config.performance_profiles import resolve_profile_settings
from config.settings import (
    DEFAULT_WIND_SPEED,
    DEFAULT_WIND_STRENGTH,
    DEFAULT_WATER_FLOW_SPEED,
    get_default_client_root,
)


_CATEGORY_COLLECTION_MAP = {
    "import_terrain": ("TERRAIN",),
    "import_buildings": ("BUILDINGS",),
    "import_props": ("PROPS",),
    "import_rocks": ("ROCKS",),
    "import_vegetation": ("VEGETATION",),
    "import_trees": ("Trees & Forest",),
    "import_bushes_flowers": ("Bushes & Flowers",),
    "import_grass": ("Grass & Cover",),
    "import_water": ("WATER",),
    "import_lighting": ("LIGHTING", "AION Static Deferred Lights", "Aion Environment"),
    "import_environment_lighting": ("LIGHTING", "Aion Environment"),
    "import_static_lights": ("AION Static Deferred Lights",),
    "import_skybox": ("SKYBOX", "Aion Sky & Environment"),
    "import_particle_effects": ("EFFECTS", "Aion Particle Effects"),
    "import_cga_entities": ("AION CGA Entities",),
    "import_placeables": ("PLACEABLES", "AION Mission Placeables"),
    "import_npcs": ("NPCS",),
    "import_monsters": ("Monsters & Hostiles",),
    "import_friendly_npcs": ("NPCs - Friendly",),
    "import_ambient_creatures": ("NPCs - Ambient Fauna",),
    "import_nameplates": ("NPC_NAMES",),
    "import_collision": ("COLLISION",),
}


def apply_category_visibility(scene, settings, prop_name: str) -> None:
    """Instantly toggles visibility of imported collections/shaders without reloading."""
    if scene is None or settings is None:
        return
    visible = bool(getattr(settings, prop_name, True))

    if prop_name == "import_terrain_shadows":
        mat = bpy.data.materials.get("Aion Terrain Blend Shader Preview")
        if mat and mat.use_nodes and mat.node_tree:
            mult = mat.node_tree.nodes.get("AION_TerrainShadowMultiply")
            if mult is not None:
                fac = mult.inputs.get("Factor_Float") or mult.inputs.get("Fac") or mult.inputs[0]
                if fac is not None:
                    fac.default_value = 1.0 if visible else 0.0
                mat.node_tree.update_tag()
        return

    target_names = set(_CATEGORY_COLLECTION_MAP.get(prop_name, ()))
    if not target_names:
        return

    def _walk_layer_cols(layer_col):
        col = getattr(layer_col, "collection", None)
        if col is not None and col.name in target_names:
            try:
                layer_col.hide_viewport = not visible
            except Exception:
                pass
        for child in getattr(layer_col, "children", ()):
            _walk_layer_cols(child)

    for col_name in target_names:
        col = bpy.data.collections.get(col_name)
        if col is not None:
            col.hide_viewport = not visible
            col.hide_render = not visible

    view_layer = getattr(bpy.context, "view_layer", None)
    if view_layer is not None and hasattr(view_layer, "layer_collection"):
        _walk_layer_cols(view_layer.layer_collection)

    if prop_name == "import_skybox":
        world = getattr(scene, "world", None)
        if world and world.use_nodes and world.node_tree:
            bg = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
            if bg and "Strength" in bg.inputs:
                bg.inputs["Strength"].default_value = 0.8 if visible else 0.0


def _make_visibility_updater(prop_name: str):
    def _update(self, context):
        if self.get("aion_syncing_visibility"):
            return
        sc = getattr(context, "scene", None) or getattr(bpy.context, "scene", None)
        apply_category_visibility(sc, self, prop_name)

    return _update


def _on_performance_profile_changed(self, context) -> None:
    """Keeps internal legacy LOD properties aligned with the simplified performance profile."""
    cfg = resolve_profile_settings(getattr(self, "performance_profile", "LOW"))
    try:
        self["terrain_lod_syncing"] = True
        self.terrain_lod = str(cfg["terrain_lod"])
        self.target_model_lod = str(cfg["target_model_lod"])
        self.optimize_material_preview = True
        self.use_mesh_instancing = True
    except Exception:
        pass
    finally:
        self.pop("terrain_lod_syncing", None)


class AionSceneSettings(bpy.types.PropertyGroup):
    """Global Aion toolkit settings stored on the Blender Scene."""

    performance_profile: EnumProperty(
        name="Perfil de Desempenho",
        description="Ajusta automaticamente terreno, LOD de modelos, shaders e viewport visando 60+ FPS",
        items=(
            (
                "LOW",
                "PC Fraco / 60+ FPS (Recomendado)",
                "Terreno passo 4, modelos LOD leves, shaders simples e viewport otimizada para GPUs/CPUs fracas",
            ),
            (
                "BALANCED",
                "Equilibrado",
                "Terreno passo 2, modelos LOD1 e mapas normais sem efeitos pesados",
            ),
            (
                "HIGH",
                "Alta Qualidade",
                "Terreno detalhado, modelos LOD0 e texturas PBR completas",
            ),
        ),
        default="LOW",
        update=_on_performance_profile_changed,
    )

    client_root: StringProperty(
        name="Client Root",
        description="Aion game client root directory",
        subtype="DIR_PATH",
        default=get_default_client_root(),
    )

    emulator_data_dir: StringProperty(
        name="Emulator Static Data",
        description="Opcional: pasta static_data do emulador para rotas de caminhada (auto-detectada quando em branco)",
        subtype="DIR_PATH",
        default="",
    )

    level_path: StringProperty(
        name="Level Path",
        description="Path to level folder or Level.pak",
        subtype="FILE_PATH",
        default="",
    )

    loaded_level_dir: StringProperty(
        name="Active Level Directory",
        description="Directory of the currently active/loaded level",
        subtype="DIR_PATH",
        default="",
    )

    status_message: StringProperty(
        name="Status",
        description="Latest status report from Aion Toolkit",
        default="",
    )

    is_importing: BoolProperty(
        name="Importando",
        description="Indica se uma importação assíncrona está em andamento",
        default=False,
        options={"SKIP_SAVE"},
    )

    import_progress: FloatProperty(
        name="Progresso",
        description="Progresso da importação linear do mapa",
        default=0.0,
        min=0.0,
        max=100.0,
        subtype="PERCENTAGE",
        options={"SKIP_SAVE"},
    )

    import_stage_message: StringProperty(
        name="Etapa Atual",
        description="Descrição da etapa atual da importação",
        default="",
        options={"SKIP_SAVE"},
    )

    terrain_lod: EnumProperty(
        name="Terrain LOD",
        description="Detail level for terrain mesh generation (auto-managed by Perfil de Desempenho)",
        items=(
            ("4", "LOD 4 (60+ FPS / Leve)", "256x256 grid - Ultra fast for weak PCs"),
            ("2", "LOD 2 (Equilibrado)", "512x512 grid - Balanced"),
            ("1", "LOD 1 (Full 100% Quality)", "1024x1024 grid - Heavy"),
        ),
        default="4",
        options={"HIDDEN"},
    )

    # Terrain
    import_terrain: BoolProperty(
        name="Import Terrain",
        description="Import terrain heightfield mesh and materials",
        default=True,
        update=_make_visibility_updater("import_terrain"),
    )
    import_terrain_textures: BoolProperty(
        name="Terrain Detail Textures",
        description="Load high-resolution detail ground textures",
        default=True,
    )
    import_terrain_blend_shader: BoolProperty(
        name="Terrain Multi-Layer Blend Shader",
        description="Create smooth multi-texture blend shader graph",
        default=True,
    )
    import_terrain_blend_attributes: BoolProperty(
        name="Terrain Blend Weights (Vertex Colors)",
        description="Compute vertex blend weights for terrain texturing",
        default=True,
    )
    import_terrain_shadows: BoolProperty(
        name="Terrain Lightmap / Baked Shadows",
        description="Apply terrainlm.pak baked shadow maps to terrain shader",
        default=True,
        update=_make_visibility_updater("import_terrain_shadows"),
    )

    # Architecture & Props
    import_buildings: BoolProperty(
        name="Buildings & Architecture",
        description="Import buildings, structures, bridges, and monuments",
        default=True,
        update=_make_visibility_updater("import_buildings"),
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
        update=_make_visibility_updater("import_props"),
    )
    import_rocks: BoolProperty(
        name="Rocks & Natural Formations",
        description="Import boulders, cliffs, stalagmites, and crystals",
        default=True,
        update=_make_visibility_updater("import_rocks"),
    )
    import_interactive_objects: BoolProperty(
        name="Interactive Objects & Signs",
        description="Import milestones, altars, burners, and signboards",
        default=True,
    )

    # Vegetation
    import_vegetation: BoolProperty(
        name="Vegetation",
        description="Master switch for all vegetation elements (instanciado via Geometry Nodes a 60+ FPS)",
        default=True,
        update=_make_visibility_updater("import_vegetation"),
    )
    import_trees: BoolProperty(
        name="Trees & Forest",
        description="Import trees, trunks, branches, and pines",
        default=True,
        update=_make_visibility_updater("import_trees"),
    )
    import_grass: BoolProperty(
        name="Grass & Cover",
        description="Import grass fields, weeds, and ground cover via Geometry Nodes",
        default=True,
        update=_make_visibility_updater("import_grass"),
    )
    import_bushes_flowers: BoolProperty(
        name="Bushes & Flowers",
        description="Import shrubs, flowers, crops, and aquatic flora",
        default=True,
        update=_make_visibility_updater("import_bushes_flowers"),
    )

    # Water & Liquids
    import_water: BoolProperty(
        name="Water Planes & Volumes",
        description="Import water plane, WaterVolumes, and translucent liquid shaders",
        default=True,
        update=_make_visibility_updater("import_water"),
    )
    import_textured_liquid_surface: BoolProperty(
        name="Textured Liquid Surface",
        description="Apply realistic water/lava shader material",
        default=True,
    )

    # Environment, Sky & Lighting
    import_lighting: BoolProperty(
        name="Environment Lighting",
        description="Import environment sun and ambient lighting",
        default=True,
        update=_make_visibility_updater("import_lighting"),
    )
    import_environment_lighting: BoolProperty(
        name="Daylight Sun & Ambient",
        description="Import sun orientation and daylight profile",
        default=True,
        update=_make_visibility_updater("import_environment_lighting"),
    )
    import_skybox: BoolProperty(
        name="Skybox Background",
        description="Import camera skybox background and physical skydome",
        default=True,
        update=_make_visibility_updater("import_skybox"),
    )
    import_static_lights: BoolProperty(
        name="Static Deferred Lights",
        description="Import point lights from staticdeferredlights.lst",
        default=True,
        update=_make_visibility_updater("import_static_lights"),
    )

    # Effects & Dynamics
    import_particle_effects: BoolProperty(
        name="Particle Effects",
        description="Import particle effects and sprites from entitycontexts",
        default=True,
        update=_make_visibility_updater("import_particle_effects"),
    )
    import_cga_entities: BoolProperty(
        name="CGA Entities",
        description="Import placed .cga entities as lightweight mesh instances",
        default=True,
        update=_make_visibility_updater("import_cga_entities"),
    )
    animate_cga_controllers: BoolProperty(
        name="Animate CGA Controllers",
        description="Apply rotational keyframe animations to CGA entities (heavier)",
        default=False,
    )
    import_placeables: BoolProperty(
        name="Obelisks & Placeables",
        description="Import obelisks, pedestals, and mission placeables",
        default=True,
        update=_make_visibility_updater("import_placeables"),
    )
    import_collision: BoolProperty(
        name="Collision Geometry",
        description="Import invisible collision walls and walk obstacles (recommended False for visual scene editing)",
        default=False,
        update=_make_visibility_updater("import_collision"),
    )

    # NPCs & World Spawns (Section 7)
    import_npcs: BoolProperty(
        name="NPCs & World Spawns",
        description="Import authoritative NPC spawns linearly after the map finishes",
        default=True,
        update=_make_visibility_updater("import_npcs"),
    )
    import_npc_models: BoolProperty(
        name="Resolve & Load 3D NPC Models",
        description="Load 3D CGF meshes for monsters, humanoids, and Shugos",
        default=True,
    )
    animate_npcs: BoolProperty(
        name="Animate NPCs (Walk Routes & CAF)",
        description="Build armature rigs, looping CAF animations, and emulator walker patrol routes",
        default=True,
    )
    import_monsters: BoolProperty(
        name="Monsters & Hostiles",
        description="Spawn monsters, wild creatures, and enemy mobs",
        default=True,
        update=_make_visibility_updater("import_monsters"),
    )
    import_friendly_npcs: BoolProperty(
        name="Friendly NPCs & Merchants",
        description="Spawn town NPCs, quest givers, and merchants",
        default=True,
        update=_make_visibility_updater("import_friendly_npcs"),
    )
    import_ambient_creatures: BoolProperty(
        name="Ambient Critters & Fauna",
        description="Spawn ambient fauna, birds, and critters",
        default=True,
        update=_make_visibility_updater("import_ambient_creatures"),
    )

    # Hidden/Legacy LOD properties kept for backwards API compatibility
    target_model_lod: EnumProperty(
        name="Model LOD",
        description="Auto-managed by Perfil de Desempenho",
        items=(
            ("0", "LOD 0", "Base mesh"),
            ("1", "LOD 1", "Companion _lod1.cgf"),
            ("2", "LOD 2", "Companion _lod2.cgf"),
            ("3", "LOD 3", "Companion _lod3.cgf"),
        ),
        default="2",
        options={"HIDDEN"},
    )

    import_nameplates: BoolProperty(
        name="NPC 3D Nameplates",
        description="Create lightweight upright PT-BR 3D nameplates above NPCs",
        default=True,
        update=_make_visibility_updater("import_nameplates"),
    )

    import_lod0: BoolProperty(
        name="LOD 0",
        description="Internal LOD filter (managed by Perfil de Desempenho)",
        default=True,
        options={"HIDDEN"},
    )
    import_lod1: BoolProperty(
        name="LOD 1",
        description="Internal LOD filter (managed by Perfil de Desempenho)",
        default=True,
        options={"HIDDEN"},
    )
    import_lod2: BoolProperty(
        name="LOD 2",
        description="Internal LOD filter (managed by Perfil de Desempenho)",
        default=True,
        options={"HIDDEN"},
    )
    import_lod3: BoolProperty(
        name="LOD 3",
        description="Internal LOD filter (managed by Perfil de Desempenho)",
        default=False,
        options={"HIDDEN"},
    )

    # Engine Performance Options (auto-managed for 60+ FPS)
    use_mesh_instancing: BoolProperty(
        name="Hardware Mesh Instancing",
        description="Direct GPU mesh datablock sharing",
        default=True,
        options={"HIDDEN"},
    )
    optimize_material_preview: BoolProperty(
        name="Optimize Material Preview",
        description="Dithered alpha clip and global material deduplication",
        default=True,
        options={"HIDDEN"},
    )
    multithreaded_io: BoolProperty(
        name="Async Linear PAK Extraction",
        description="Non-blocking sequential worker extraction",
        default=True,
        options={"HIDDEN"},
    )

    # Live Animation settings (OFF by default for 60+ FPS)
    live_wind: BoolProperty(
        name="Live Wind Sway",
        description="Enable procedural wind swaying on vegetation when playing timeline",
        default=False,
    )

    wind_strength: FloatProperty(
        name="Wind Strength",
        description="Vegetation sway deformation amplitude",
        default=DEFAULT_WIND_STRENGTH,
        min=0.0,
        max=0.5,
    )

    wind_speed: FloatProperty(
        name="Wind Speed",
        description="Vegetation sway frequency",
        default=DEFAULT_WIND_SPEED,
        min=0.0,
        max=0.5,
    )

    water_flow_speed: FloatProperty(
        name="Water Speed",
        description="Animated water ripple and flow speed",
        default=DEFAULT_WATER_FLOW_SPEED,
        min=0.0,
        max=0.05,
    )

    # Export settings
    create_backup: BoolProperty(
        name="Create Backup (.pak.bak)",
        description="Safely backup original Level.pak before overwriting",
        default=True,
    )

    # 3D Asset Browser & Model Inventory Grid
    asset_source: EnumProperty(
        name="Asset Source",
        description="Choose whether to browse models in current map or explore client archives",
        items=(
            ("MAP", "Active Map Models", "Models and assets currently loaded in the active scene", "SCENE_DATA", 0),
            ("CLIENT", "Client Library Explorer", "Explore all 3D CGF models across client PAK archives", "FILE_FOLDER", 1),
        ),
        default="MAP",
    )

    asset_category: EnumProperty(
        name="Category Filter",
        description="Filter models by asset category",
        items=(
            ("ALL", "All Categories", "Show all models", "VIEW3D", 0),
            ("ARCHITECTURE", "Architecture", "Buildings, structures, walls, bridges", "HOME", 1),
            ("PROPS", "Props", "Furniture, camp items, barrels, lamps, decorations", "OBJECT_DATAMODE", 2),
            ("VEGETATION", "Vegetation", "Trees, plants, bushes, grass", "OUTLINER_OB_CURVE", 3),
            ("ROCKS", "Rocks", "Cliffs, boulders, stalagmites, crystals", "MOD_TRIANGULATE", 4),
            ("NPCS", "NPCs", "Monsters, creatures, NPCs", "ARMATURE_DATA", 5),
            ("EFFECTS", "Effects", "Particles, placeables, dynamic entities", "PARTICLES", 6),
        ),
        default="ALL",
    )

    asset_search: StringProperty(
        name="Search",
        description="Filter models by name or path query",
        default="",
    )

    asset_snap_terrain: BoolProperty(
        name="Snap to Terrain",
        description="Automatically align spawned assets to terrain height and surface normal",
        default=True,
    )

    asset_auto_catalog: BoolProperty(
        name="Auto-Catalog on Import",
        description="Mark imported models as Blender assets (previews are NOT auto-rendered to avoid freezing)",
        default=False,
    )


def register():
    bpy.utils.register_class(AionSceneSettings)
    bpy.types.Scene.aion_settings = PointerProperty(type=AionSceneSettings)


def unregister():
    if hasattr(bpy.types.Scene, "aion_settings"):
        del bpy.types.Scene.aion_settings
    bpy.utils.unregister_class(AionSceneSettings)
