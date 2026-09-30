"""
Level Serializer for Aion Blender Toolkit.
Applies Blender scene modifications directly into client-ready Aion map files.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import bpy
from mathutils import Matrix

from formats.level.brush import BrushNodePlacement, parse_brush_lst, write_brush_lst
from formats.level.leveldata import parse_leveldata, write_leveldata
from formats.level.mission_placeables import update_mission_placeables_xml
from formats.level.objects import ObjectPlacement, parse_objects_lst, write_objects_lst
from .roundtrip_tracker import (
    SOURCE_BRUSH,
    SOURCE_MISSION,
    SOURCE_OBJECT,
    collect_scene_changes,
)
from .terrain_editor import find_terrain_object, sync_sculpted_terrain_to_land_map


@dataclass(frozen=True)
class LevelSerializationReport:
    level_dir: Path
    target_dir: Path
    brushes_modified: int
    objects_modified: int
    mission_placeables_modified: int
    terrain_samples_modified: int
    files_updated: tuple[str, ...]
    success: bool
    message: str


def serialize_scene_to_level_files(
    scene: bpy.types.Scene,
    level_dir: str | Path,
) -> LevelSerializationReport:
    """
    Scans the Blender scene for edits and serializes them into the Aion level files.
    Updates brush.lst, objects.lst, mission_mission0.xml, and terrain/land_map.h32.
    """
    level_path = Path(level_dir).resolve()
    if level_path.is_file():
        level_path = level_path.parent

    # Determine target directory (prefer .aion_cache if it exists)
    cache_dir = level_path / ".aion_cache"
    target_dir = cache_dir if cache_dir.is_dir() else level_path

    files_updated = []
    brushes_modified = 0
    objects_modified = 0
    mission_modified = 0
    terrain_modified = 0

    changes = collect_scene_changes(scene)

    # 1. Update brush.lst (World structures, props, buildings)
    brush_path = target_dir / "brush.lst"
    brush_records = changes.get(SOURCE_BRUSH, [])
    mod_brushes = [r for r in brush_records if r.is_modified and r.source_index >= 0]

    if mod_brushes and brush_path.is_file():
        brush_list = parse_brush_lst(brush_path)
        nodes_list = list(brush_list.nodes)

        for rec in mod_brushes:
            idx = rec.source_index
            if 0 <= idx < len(nodes_list):
                mat = rec.current_matrix
                # Convert 4x4 matrix to 3x4 row-major 12 floats
                new_transform = (
                    float(mat[0][0]), float(mat[0][1]), float(mat[0][2]), float(mat[0][3]),
                    float(mat[1][0]), float(mat[1][1]), float(mat[1][2]), float(mat[1][3]),
                    float(mat[2][0]), float(mat[2][1]), float(mat[2][2]), float(mat[2][3]),
                )
                orig_node = nodes_list[idx]
                nodes_list[idx] = BrushNodePlacement(
                    index=orig_node.index,
                    delimiter_1=orig_node.delimiter_1,
                    node_size=orig_node.node_size,
                    mesh_index=orig_node.mesh_index,
                    mesh_file_name=orig_node.mesh_file_name,
                    unknown_id=orig_node.unknown_id,
                    node_flags=orig_node.node_flags,
                    delimiter_2=orig_node.delimiter_2,
                    transform=new_transform,
                    unknown_51=orig_node.unknown_51,
                    unknown_52=orig_node.unknown_52,
                    unknown_53=orig_node.unknown_53,
                    event_type=orig_node.event_type,
                    unknown_6=orig_node.unknown_6,
                    extra_bytes=orig_node.extra_bytes,
                )
                brushes_modified += 1

        new_brush_list = type(brush_list)(
            signature=brush_list.signature,
            version=brush_list.version,
            mesh_block_size=brush_list.mesh_block_size,
            titles=brush_list.titles,
            meshes=brush_list.meshes,
            nodes=tuple(nodes_list),
            trailing_bytes=brush_list.trailing_bytes,
        )
        write_brush_lst(brush_path, new_brush_list)
        files_updated.append("brush.lst")

    # 2. Update objects.lst (Vegetation, trees, plants)
    objects_path = target_dir / "objects.lst"
    leveldata_path = target_dir / "leveldata.xml"
    object_records = changes.get(SOURCE_OBJECT, [])
    mod_objects = [r for r in object_records if r.is_modified and r.source_index >= 0]

    if mod_objects and objects_path.is_file() and leveldata_path.is_file():
        level_data = parse_leveldata(leveldata_path)
        objects_list = parse_objects_lst(objects_path, level_data)
        placements_list = list(objects_list.placements)

        for rec in mod_objects:
            idx = rec.source_index
            if 0 <= idx < len(placements_list):
                mat = rec.current_matrix
                pos = (float(mat.translation.x), float(mat.translation.y), float(mat.translation.z))
                scale = float((mat.to_scale().x + mat.to_scale().y + mat.to_scale().z) / 3.0)
                heading = float(math.degrees(mat.to_euler().z)) % 360.0

                orig_p = placements_list[idx]
                placements_list[idx] = ObjectPlacement(
                    vegetation_index=orig_p.vegetation_index,
                    vegetation_file=orig_p.vegetation_file,
                    raw_position=None,
                    position=pos,
                    scale=scale,
                    heading_raw=int(round(heading * 255.0 / 360.0)) & 0xFFFFFFFF,
                    heading_degrees=heading,
                    unknown_byte=orig_p.unknown_byte,
                )
                objects_modified += 1

        new_objects_list = type(objects_list)(
            header=objects_list.header,
            placements=tuple(placements_list),
            trailing_bytes=objects_list.trailing_bytes,
        )
        write_objects_lst(objects_path, new_objects_list, level_data)
        files_updated.append("objects.lst")

    # 3. Update mission_mission0.xml (Placeables)
    mission_path = target_dir / "mission_mission0.xml"
    mission_records = changes.get(SOURCE_MISSION, [])
    mod_mission = [r for r in mission_records if r.is_modified]

    if mod_mission and mission_path.is_file():
        mod_entities = {}
        for rec in mod_mission:
            el_id = rec.obj.get("aion_entity_id") or rec.obj.name
            mat = rec.current_matrix
            pos = (mat.translation.x, mat.translation.y, mat.translation.z)
            angles = tuple(math.degrees(a) for a in mat.to_euler())
            mod_entities[el_id] = {"position": pos, "angles": angles}

        mission_modified = update_mission_placeables_xml(mission_path, mod_entities)
        if mission_modified > 0:
            files_updated.append("mission_mission0.xml")

    # 4. Update terrain heightfield if sculpted
    terrain_obj = find_terrain_object(scene)
    terrain_h32_path = target_dir / "terrain" / "land_map.h32"
    if terrain_obj and terrain_h32_path.is_file():
        try:
            mod_samples, _ = sync_sculpted_terrain_to_land_map(
                terrain_obj,
                terrain_h32_path,
                terrain_h32_path,
            )
            if mod_samples > 0:
                terrain_modified = mod_samples
                files_updated.append("terrain/land_map.h32")
        except Exception:
            pass

    # Mark modified objects clean with new base matrix
    for rec in (*mod_brushes, *mod_objects, *mod_mission):
        rec.obj["aion_orig_matrix"] = [float(v) for row in rec.current_matrix for v in row]

    total_changes = brushes_modified + objects_modified + mission_modified + terrain_modified
    msg = (
        f"Level files updated: {brushes_modified} brushes, "
        f"{objects_modified} vegetation objects, "
        f"{mission_modified} mission entities, "
        f"{terrain_modified} terrain samples. Files: {', '.join(files_updated) if files_updated else 'none'}"
    )

    return LevelSerializationReport(
        level_dir=level_path,
        target_dir=target_dir,
        brushes_modified=brushes_modified,
        objects_modified=objects_modified,
        mission_placeables_modified=mission_modified,
        terrain_samples_modified=terrain_modified,
        files_updated=tuple(files_updated),
        success=True,
        message=msg,
    )
