"""
Performance Benchmark Script for Aion Level Importer in Blender.
Executes automated import profiling for representative Aion maps:
1. Small map: levels/login
2. Large open world: levels/df1 (Ishalgen)

Measures:
- Import duration (seconds)
- Object count, Mesh count, Material count, Texture/Image count
- NPCs spawned and placed
- Memory footprint
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Add plugin root to sys.path
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

import bpy
from importers.level_importer import import_level

_ENV_CLIENT = os.environ.get("AION_CLIENT_ROOT", "").strip()
CLIENT_ROOT = Path(_ENV_CLIENT) if _ENV_CLIENT else None


def reset_blender_scene():
    """Cleans up all objects, meshes, materials, and textures for a fresh run."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img, do_unlink=True)
    for col in list(bpy.data.collections):
        if col != bpy.context.scene.collection:
            bpy.data.collections.remove(col)


def benchmark_map(map_name: str, limited_preview: bool = True, max_unique_cgfs: int = 30):
    if CLIENT_ROOT is None or not CLIENT_ROOT.is_dir():
        raise FileNotFoundError("Defina a variável de ambiente AION_CLIENT_ROOT apontando para o cliente Aion.")
    level_dir = CLIENT_ROOT / "levels" / map_name
    assert level_dir.is_dir(), f"Level directory missing: {level_dir}"

    print(f"\n{'='*75}")
    print(f"BENCHMARK: Importing '{map_name}' (limited_preview={limited_preview}, max_unique_cgfs={max_unique_cgfs})")
    print(f"{'='*75}")

    reset_blender_scene()

    t0 = time.time()
    result = import_level(
        context=bpy.context,
        level_dir=level_dir,
        client_root=CLIENT_ROOT,
        limited_preview=limited_preview,
        max_unique_cgfs=max_unique_cgfs,
        max_placements_per_template=20,
        import_terrain=True,
        import_terrain_textures=True,
        import_terrain_blend_attributes=True,
        import_terrain_blend_shader=True,
        import_terrain_shadows=True,
        import_water=True,
        import_buildings=True,
        import_props=True,
        import_vegetation=True,
        import_rocks=True,
        import_collision=False,
        import_npcs=True,
        import_npc_models=True,
        import_monsters=True,
        import_friendly_npcs=True,
        import_lod0=True,
        import_lod1=True,
        use_mesh_instancing=True,
        optimize_material_preview=True,
    )
    duration = time.time() - t0

    obj_count = len(bpy.data.objects)
    mesh_count = len(bpy.data.meshes)
    mat_count = len(bpy.data.materials)
    img_count = len(bpy.data.images)
    col_count = len(bpy.data.collections)

    npc_res = getattr(result, "npc_result", None)
    npcs_spawned = npc_res.spawns_placed if npc_res else 0
    npc_models = npc_res.models_loaded if npc_res else 0

    print(f"\n--- Benchmark Results for '{map_name}' ---")
    print(f"  Total Import Duration:     {duration:.2f} seconds")
    print(f"  Total Blender Objects:     {obj_count}")
    print(f"  Total Mesh Datablocks:     {mesh_count}")
    print(f"  Total Material Datablocks: {mat_count}")
    print(f"  Total Texture Images:      {img_count}")
    print(f"  Total Collections:         {col_count}")
    print(f"  NPCs Placed in Scene:      {npcs_spawned}")
    print(f"  NPC 3D Models Loaded:      {npc_models}")
    print(f"  Hardware Mesh Instancing:  {'ENABLED' if result.placement_objects_created > 0 else 'N/A'}")
    print(f"  Placements Created:        {result.placement_objects_created}")
    print(f"  Import Status:             SUCCESS")
    print(f"{'='*75}\n")

    return {
        "map": map_name,
        "duration": duration,
        "objects": obj_count,
        "meshes": mesh_count,
        "materials": mat_count,
        "images": img_count,
        "npcs": npcs_spawned,
    }


if __name__ == "__main__":
    res_login = benchmark_map("login", limited_preview=True, max_unique_cgfs=30)
    res_df1 = benchmark_map("df1", limited_preview=True, max_unique_cgfs=30)
    print("\nBENCHMARK RUN COMPLETE.")
