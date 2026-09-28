"""
Terrain Editor and Heightfield Synchronization for Aion Blender Toolkit.
Syncs sculpted Blender terrain mesh heights back into land_map.h32 format.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional, Tuple

import bpy

from config.settings import DEFAULT_XY_SCALE, LAND_MAP_HEIGHT_SCALE
from formats.level.terrain import LandMap, LandMapSample, parse_land_map_h32, write_land_map_h32


def find_terrain_object(scene: bpy.types.Scene) -> Optional[bpy.types.Object]:
    """Locates the active Aion terrain mesh object in the scene."""
    for obj in scene.objects:
        if obj.type == "MESH" and ("aion_blend_shader_enabled" in obj or "terrain" in obj.name.lower()):
            return obj
    return None


def sync_sculpted_terrain_to_land_map(
    terrain_obj: bpy.types.Object,
    original_h32_path: str | Path,
    output_h32_path: str | Path,
    *,
    xy_scale: float = DEFAULT_XY_SCALE,
) -> Tuple[int, int]:
    """
    Reads vertex Z heights from a sculpted Blender terrain mesh
    and serializes them into the destination land_map.h32 file.
    Returns (modified_sample_count, total_samples_written).
    """
    orig_path = Path(original_h32_path)
    if not orig_path.is_file():
        raise FileNotFoundError(f"Original land_map.h32 not found: {orig_path}")

    orig_land_map = parse_land_map_h32(orig_path)
    mesh = terrain_obj.data
    vertices = mesh.vertices
    w = orig_land_map.width
    h = orig_land_map.height
    total_samples = orig_land_map.sample_count

    # If vertex count matches exactly (LOD 1)
    if len(vertices) == total_samples:
        new_samples = []
        modified_count = 0
        scale = orig_land_map.height_scale or LAND_MAP_HEIGHT_SCALE

        for idx, s in enumerate(orig_land_map.samples):
            v_z = vertices[idx].co.z
            h_raw = max(0, min(65535, int(round(v_z * scale))))
            if abs(v_z - s.height) > 0.01:
                modified_count += 1
            new_samples.append(
                LandMapSample(
                    height_raw=h_raw,
                    height=float(v_z),
                    color=s.color,
                )
            )

        new_land_map = LandMap(
            width=w,
            height=h,
            sample_count=total_samples,
            bytes_per_sample=orig_land_map.bytes_per_sample,
            height_scale=scale,
            samples=tuple(new_samples),
            min_height=min(s.height for s in new_samples),
            max_height=max(s.height for s in new_samples),
            trailing_bytes=orig_land_map.trailing_bytes,
        )
        write_land_map_h32(output_h32_path, new_land_map)
        return modified_count, total_samples

    # If LOD mesh (e.g. LOD 2 or LOD 4), interpolate back into the grid
    scale = orig_land_map.height_scale or LAND_MAP_HEIGHT_SCALE
    new_samples = list(orig_land_map.samples)
    modified_count = 0

    # Raycast or nearest vertex mapping from LOD vertices
    for v in vertices:
        r = int(round(v.co.x / xy_scale))
        c = int(round(v.co.y / xy_scale))
        if 0 <= r < h and 0 <= c < w:
            idx = r * w + c
            orig_s = new_samples[idx]
            v_z = v.co.z
            if abs(v_z - orig_s.height) > 0.01:
                modified_count += 1
                h_raw = max(0, min(65535, int(round(v_z * scale))))
                new_samples[idx] = LandMapSample(
                    height_raw=h_raw,
                    height=float(v_z),
                    color=orig_s.color,
                )

    new_land_map = LandMap(
        width=w,
        height=h,
        sample_count=total_samples,
        bytes_per_sample=orig_land_map.bytes_per_sample,
        height_scale=scale,
        samples=tuple(new_samples),
        min_height=min(s.height for s in new_samples),
        max_height=max(s.height for s in new_samples),
        trailing_bytes=orig_land_map.trailing_bytes,
    )
    write_land_map_h32(output_h32_path, new_land_map)
    return modified_count, total_samples
