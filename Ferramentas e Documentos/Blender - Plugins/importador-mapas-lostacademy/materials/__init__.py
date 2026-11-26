"""
Aion Materials Package.
Handles shader interpretation, texture loading, material caching, terrain & water materials.
"""

from .texture_loader import load_texture_image, clear_texture_cache
from .shader_interpreter import (
    interpret_and_build_material_graph,
    safe_set_blend_method,
    safe_set_two_sided,
)
from .material_manager import (
    get_or_create_aion_material,
    resolve_texture_slot,
    clean_material_cache,
)
from .terrain_materials import (
    create_terrain_materials,
    resolve_terrain_detail_texture,
    TerrainMaterialSlot,
    TerrainDetailTextureReference,
)
from .water_materials import create_liquid_material

__all__ = [
    "load_texture_image",
    "clear_texture_cache",
    "interpret_and_build_material_graph",
    "safe_set_blend_method",
    "safe_set_two_sided",
    "get_or_create_aion_material",
    "resolve_texture_slot",
    "clean_material_cache",
    "create_terrain_materials",
    "resolve_terrain_detail_texture",
    "TerrainMaterialSlot",
    "TerrainDetailTextureReference",
    "create_liquid_material",
]
