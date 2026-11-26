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
        description="Import dense grass fields and weeds (over 10,000 objects on full maps; enable if detailed grass cover is required)",
        default=False,
    )
    import_bushes_flowers: BoolProperty(
        name="Bushes & Flowers",
        description="Import shrubs, flowers, crops, and aquatic flora",
        default=True,
    )

    # Water & Liquids
    import_water: BoolProperty(
        name="Water Planes",
        description="Import water plane and animated surface shaders",
        default=True,
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
    )
    import_environment_lighting: BoolProperty(
        name="Daylight Sun & Ambient",
        description="Import sun orientation and daylight profile",
        default=True,
    )
    import_skybox: BoolProperty(
        name="Skybox Background",
        description="Import camera skybox background and physical skydome",
        default=False,
    )
    import_static_lights: BoolProperty(
        name="Static Deferred Lights",
        description="Import point lights from staticdeferredlights.lst",
        default=False,
    )

    # Effects & Dynamics
    import_particle_effects: BoolProperty(
        name="Particle Effects",
        description="Import particle effects and sprites from entitycontexts",
        default=False,
    )
    import_cga_entities: BoolProperty(
        name="CGA Entities",
        description="Import placed .cga entities as lightweight mesh instances",
        default=True,
    )
    animate_cga_controllers: BoolProperty(
        name="Animate CGA Controllers",
        description="Apply rotational keyframe animations to CGA entities (heavier)",
        default=False,
    )
    import_placeables: BoolProperty(
        name="Obelisks & Placeables",
        description="Import obelisks, pedestals, and mission placeables",
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
        description="Import authoritative NPC spawns linearly after the map finishes",
        default=False,
    )
    import_npc_models: BoolProperty(
        name="Resolve & Load 3D NPC Models",
        description="Load 3D CGF meshes for monsters, humanoids, and Shugos",
        default=True,
    )
    animate_npcs: BoolProperty(
        name="Animate NPCs (Armatures & Idle CAF)",
        description="Build armature rigs and looping animations (heavy on weak CPUs/GPUs)",
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
        description="Create 3D floating text nameplates above NPCs (heavy on GPU with many curves)",
        default=False,
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
