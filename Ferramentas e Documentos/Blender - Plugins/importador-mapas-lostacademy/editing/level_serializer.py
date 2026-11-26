"""
Level Serializer for Aion Blender Toolkit.
Applies Blender scene modifications directly into client-ready Aion map files.
Supports full round-trip editing: Move, Rotate, Scale, Add (Duplicate/New), and Delete.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import bpy
from mathutils import Matrix

from formats.level.brush import BrushList, BrushMeshEntry, BrushNodePlacement, parse_brush_lst, write_brush_lst
from formats.level.leveldata import parse_leveldata, write_leveldata
from formats.level.mission_placeables import update_mission_placeables_xml
from formats.level.objects import ObjectPlacement, ObjectsList, parse_objects_lst, write_objects_lst
from formats.level.npc_spawns import update_world_npc_spawns_xml
from .roundtrip_tracker import (
    SOURCE_BRUSH,
    SOURCE_MISSION,
    SOURCE_NPC,
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
    npcs_modified: int = 0
    brushes_added: int = 0
    brushes_deleted: int = 0
    objects_added: int = 0
    objects_deleted: int = 0


def serialize_scene_to_level_files(
    scene: bpy.types.Scene,
    level_dir: str | Path,
) -> LevelSerializationReport:
    """
    Scans the Blender scene for edits and serializes them into the Aion level files.
    Updates brush.lst, objects.lst, mission_mission0.xml, client_world_<map>.xml, and terrain/land_map.h32.
    """
    level_path = Path(level_dir).resolve()
    if level_path.is_file():
        level_path = level_path.parent

    # Determine target directory (prefer .aion_cache if it exists)
    cache_dir = level_path / ".aion_cache"
    target_dir = cache_dir if cache_dir.is_dir() else level_path

    files_updated = []
    brushes_modified = 0
    brushes_added = 0
    brushes_deleted = 0
    objects_modified = 0
    objects_added = 0
    objects_deleted = 0
    mission_modified = 0
    npcs_modified = 0
    terrain_modified = 0

    changes = collect_scene_changes(scene)

    # 1. Update brush.lst (World structures, props, buildings)
    brush_path = target_dir / "brush.lst"
    brush_records = changes.get(SOURCE_BRUSH, [])

    if brush_path.is_file() and (brush_records or True):
        brush_list = parse_brush_lst(brush_path)
        orig_nodes = list(brush_list.nodes)
        orig_count = len(orig_nodes)

        present_indices = {r.source_index for r in brush_records if not r.is_new and r.source_index >= 0}
        deleted_indices = set(range(orig_count)) - present_indices if present_indices else set()

        # If all nodes were deleted or some deleted
        if present_indices and len(deleted_indices) > 0:
            brushes_deleted = len(deleted_indices)

        mod_by_idx = {r.source_index: r for r in brush_records if r.is_modified and not r.is_new and r.source_index >= 0}
        new_records = [r for r in brush_records if r.is_new]

        if mod_by_idx or new_records or brushes_deleted > 0:
            new_nodes: List[BrushNodePlacement] = []
            for idx, orig_node in enumerate(orig_nodes):
                if idx in deleted_indices:
                    continue
                if idx in mod_by_idx:
                    rec = mod_by_idx[idx]
                    mat = rec.current_matrix
                    new_transform = (
                        float(mat[0][0]), float(mat[0][1]), float(mat[0][2]), float(mat[0][3]),
                        float(mat[1][0]), float(mat[1][1]), float(mat[1][2]), float(mat[1][3]),
                        float(mat[2][0]), float(mat[2][1]), float(mat[2][2]), float(mat[2][3]),
                    )
                    node = BrushNodePlacement(
                        index=len(new_nodes),
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
                else:
                    node = BrushNodePlacement(
                        index=len(new_nodes),
                        delimiter_1=orig_node.delimiter_1,
                        node_size=orig_node.node_size,
                        mesh_index=orig_node.mesh_index,
                        mesh_file_name=orig_node.mesh_file_name,
                        unknown_id=orig_node.unknown_id,
                        node_flags=orig_node.node_flags,
                        delimiter_2=orig_node.delimiter_2,
                        transform=orig_node.transform,
                        unknown_51=orig_node.unknown_51,
                        unknown_52=orig_node.unknown_52,
                        unknown_53=orig_node.unknown_53,
                        event_type=orig_node.event_type,
                        unknown_6=orig_node.unknown_6,
                        extra_bytes=orig_node.extra_bytes,
                    )
                new_nodes.append(node)

            # Append new brushes
            mesh_entries = list(brush_list.meshes)
            mesh_filename_to_idx = {m.file_name.lower().replace("\\", "/"): m.index for m in mesh_entries}

            for rec in new_records:
                ref = rec.cgf_reference or "objects/default/default.cgf"
                ref_norm = ref.lower().replace("\\", "/")
                if ref_norm not in mesh_filename_to_idx:
                    new_mesh_idx = len(mesh_entries)
                    mesh_entry = BrushMeshEntry(
                        index=new_mesh_idx,
                        structure_size=160,
                        file_name=ref,
                        flags=0,
                        bounding_box=(-1.0, -1.0, -1.0, 1.0, 1.0, 1.0),
                    )
                    mesh_entries.append(mesh_entry)
                    mesh_filename_to_idx[ref_norm] = new_mesh_idx
                else:
                    new_mesh_idx = mesh_filename_to_idx[ref_norm]

                mat = rec.current_matrix
                new_transform = (
                    float(mat[0][0]), float(mat[0][1]), float(mat[0][2]), float(mat[0][3]),
                    float(mat[1][0]), float(mat[1][1]), float(mat[1][2]), float(mat[1][3]),
                    float(mat[2][0]), float(mat[2][1]), float(mat[2][2]), float(mat[2][3]),
                )
                sample_node = new_nodes[0] if new_nodes else (orig_nodes[0] if orig_nodes else None)
                extra_size = 4 * (brush_list.mesh_block_size - 16)
                node = BrushNodePlacement(
                    index=len(new_nodes),
                    delimiter_1=0,
                    node_size=sample_node.node_size if sample_node else 88,
                    mesh_index=new_mesh_idx,
                    mesh_file_name=ref,
                    unknown_id=0,
                    node_flags=0,
                    delimiter_2=0,
                    transform=new_transform,
                    unknown_51=0,
                    unknown_52=0,
                    unknown_53=0,
                    event_type=0,
                    unknown_6=0,
                    extra_bytes=sample_node.extra_bytes if sample_node else b"\x00" * extra_size,
                )
                new_nodes.append(node)
                brushes_added += 1

            new_brush_list = BrushList(
                signature=brush_list.signature,
                version=brush_list.version,
                mesh_block_size=brush_list.mesh_block_size,
                titles=brush_list.titles,
                meshes=tuple(mesh_entries),
                nodes=tuple(new_nodes),
                trailing_bytes=brush_list.trailing_bytes,
            )
            write_brush_lst(brush_path, new_brush_list)
            files_updated.append("brush.lst")

    # 2. Update objects.lst (Vegetation, trees, plants)
    objects_path = target_dir / "objects.lst"
    leveldata_path = target_dir / "leveldata.xml"
    object_records = changes.get(SOURCE_OBJECT, [])

    if objects_path.is_file() and leveldata_path.is_file():
        level_data = parse_leveldata(leveldata_path)
        objects_list = parse_objects_lst(objects_path, level_data)
        orig_placements = list(objects_list.placements)
        orig_p_count = len(orig_placements)

        present_obj_indices = {r.source_index for r in object_records if not r.is_new and r.source_index >= 0}
        deleted_obj_indices = set(range(orig_p_count)) - present_obj_indices if present_obj_indices else set()

        if present_obj_indices and len(deleted_obj_indices) > 0:
            objects_deleted = len(deleted_obj_indices)

        mod_obj_by_idx = {r.source_index: r for r in object_records if r.is_modified and not r.is_new and r.source_index >= 0}
        new_obj_records = [r for r in object_records if r.is_new]

        if mod_obj_by_idx or new_obj_records or objects_deleted > 0:
            new_placements: List[ObjectPlacement] = []
            for idx, orig_p in enumerate(orig_placements):
                if idx in deleted_obj_indices:
                    continue
                if idx in mod_obj_by_idx:
                    rec = mod_obj_by_idx[idx]
                    mat = rec.current_matrix
                    pos = (float(mat.translation.x), float(mat.translation.y), float(mat.translation.z))
                    scale = float((mat.to_scale().x + mat.to_scale().y + mat.to_scale().z) / 3.0)
                    heading = float(math.degrees(mat.to_euler().z)) % 360.0

                    p = ObjectPlacement(
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
                else:
                    p = orig_p
                new_placements.append(p)

            # Append new vegetation objects
            veg_files = list(level_data.vegetation_files or [])
            veg_file_to_idx = {fn.lower().replace("\\", "/"): i for i, fn in enumerate(veg_files)}

            for rec in new_obj_records:
                ref = rec.cgf_reference or "objects/vegetation/default.cgf"
                ref_norm = ref.lower().replace("\\", "/")
                if ref_norm not in veg_file_to_idx:
                    new_vidx = len(veg_files)
                    veg_files.append(ref)
                    veg_file_to_idx[ref_norm] = new_vidx
                else:
                    new_vidx = veg_file_to_idx[ref_norm]

                mat = rec.current_matrix
                pos = (float(mat.translation.x), float(mat.translation.y), float(mat.translation.z))
                scale = float((mat.to_scale().x + mat.to_scale().y + mat.to_scale().z) / 3.0)
                heading = float(math.degrees(mat.to_euler().z)) % 360.0

                p = ObjectPlacement(
                    vegetation_index=new_vidx,
                    vegetation_file=ref,
                    raw_position=None,
                    position=pos,
                    scale=scale,
                    heading_raw=int(round(heading * 255.0 / 360.0)) & 0xFFFFFFFF,
                    heading_degrees=heading,
                    unknown_byte=0,
                )
                new_placements.append(p)
                objects_added += 1

            new_objects_list = ObjectsList(
                header=objects_list.header,
                placements=tuple(new_placements),
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

    # 4. Update NPCs in client_world_<map>.xml
    npc_records = changes.get(SOURCE_NPC, [])
    mod_npcs = [r for r in npc_records if r.is_modified]
    if mod_npcs:
        map_name = level_path.name.lower()
        if map_name.endswith(".pak"):
            map_name = level_path.stem.lower()
        if map_name == ".aion_cache":
            map_name = level_path.parent.name.lower()
        world_xml_path = target_dir / f"client_world_{map_name}.xml"

        npc_dict = {}
        for rec in mod_npcs:
            nid = str(rec.source_index)
            if nid != "-1":
                npc_dict[nid] = (rec.obj.location.x, rec.obj.location.y, rec.obj.location.z)

        if npc_dict:
            upd = update_world_npc_spawns_xml(world_xml_path, npc_dict)
            if upd > 0:
                npcs_modified = upd
                files_updated.append(world_xml_path.name)

    # 5. Update terrain heightfield if sculpted
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
    for rec in (*brush_records, *object_records, *mission_records):
        rec.obj["aion_orig_matrix"] = [float(v) for row in rec.current_matrix for v in row]
        if rec.source_type == SOURCE_BRUSH and brushes_added > 0:
            rec.obj["aion_source_index"] = 0  # no longer negative
        if rec.source_type == SOURCE_OBJECT and objects_added > 0:
            rec.obj["aion_source_index"] = 0

    for rec in npc_records:
        rec.obj["aion_orig_pos"] = [rec.obj.location.x, rec.obj.location.y, rec.obj.location.z]

    msg = (
        f"Level files updated: {brushes_modified} brushes modified, {brushes_added} added, {brushes_deleted} deleted | "
        f"{objects_modified} objects modified, {objects_added} added, {objects_deleted} deleted | "
        f"{npcs_modified} NPCs | {mission_modified} mission entities | "
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
        npcs_modified=npcs_modified,
        brushes_added=brushes_added,
        brushes_deleted=brushes_deleted,
        objects_added=objects_added,
        objects_deleted=objects_deleted,
    )
