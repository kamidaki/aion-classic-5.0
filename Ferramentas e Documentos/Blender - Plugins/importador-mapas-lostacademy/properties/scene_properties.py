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

from config.settings import (
    DEFAULT_WIND_SPEED,
    DEFAULT_WIND_STRENGTH,
    DEFAULT_WATER_FLOW_SPEED,
    get_default_client_root,
)


class AionSceneSettings(bpy.types.PropertyGroup):
    """Global Aion toolkit settings stored on the Blender Scene."""

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

    terrain_lod: EnumProperty(
        name="Terrain LOD",
        description="Detail level for terrain mesh generation",
        items=(
            ("2", "LOD 2 (Fast - Recommended)", "512x512 grid - High performance, smooth in viewport"),
            ("1", "LOD 1 (Full 100% Quality)", "1024x1024 grid - Highest detail, heavier on memory"),
            ("4", "LOD 4 (Preview)", "256x256 grid - Ultra fast"),
        ),
        default="2",
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
        name="CGA Dynamic Entities",
        description="Import dynamic entities and animation controllers",
        default=True,
    )
    animate_cga_controllers: BoolProperty(
        name="Animate CGA Controllers",
        description="Apply rotational keyframe animations to CGA entities",
        default=True,
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
    target_model_lod: EnumProperty(
        name="Model LOD",
        description="Target Level-of-Detail for 3D models (resolves _lod1, _lod2, _lod3 companion assets)",
        items=(
            ("0", "LOD 0 (High Detail)", "Base full mesh detail"),
            ("1", "LOD 1 (Medium Detail)", "Companion _lod1.cgf geometry"),
            ("2", "LOD 2 (Low Detail)", "Companion _lod2.cgf geometry"),
            ("3", "LOD 3 (Distant Detail)", "Companion _lod3.cgf geometry"),
        ),
        default="0",
    )

    import_nameplates: BoolProperty(
        name="NPC 3D Nameplates",
        description="Create 3D floating billboard nameplates with localized name and NPC ID above heads",
        default=True,
    )

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

    # Live Animation settings
    live_wind: BoolProperty(
        name="Live Wind Sway",
        description="Enable procedural wind swaying on vegetation when playing timeline",
        default=True,
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
        description="Automatically mark imported models as Blender assets with 3D preview generation",
        default=True,
    )


def register():
    bpy.utils.register_class(AionSceneSettings)
    bpy.types.Scene.aion_settings = PointerProperty(type=AionSceneSettings)


def unregister():
    if hasattr(bpy.types.Scene, "aion_settings"):
        del bpy.types.Scene.aion_settings
    bpy.utils.unregister_class(AionSceneSettings)
