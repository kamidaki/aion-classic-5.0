"""
Direct Level Exporter for Aion Blender Toolkit.
Implements the Direct Save workflow:
Blender Edits -> Update Level Files -> Repack Level.pak -> Ready for Game Client.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import bpy

from core.pak_engine import pack_level_directory
from editing.level_serializer import serialize_scene_to_level_files


@dataclass(frozen=True)
class LevelExportResult:
    success: bool
    message: str
    target_pak: Path
    backup_created: bool
    files_packed_count: int
    total_bytes: int


def export_and_save_level(
    scene: bpy.types.Scene,
    level_dir: str | Path,
    *,
    create_backup: bool = True,
    repack_pak: bool = True,
) -> LevelExportResult:
    """
    Direct Save Workflow:
    1. Scans Blender scene for modified brushes, vegetation, placeables, terrain.
    2. Writes changes into client-ready Aion format files (brush.lst, objects.lst, land_map.h32, etc.).
    3. Automatically repacks the directory into Level.pak with automatic Level.pak.bak backup.
    4. Client is immediately ready to load the map with zero manual steps!
    """
    level_path = Path(level_dir).resolve()
    if level_path.is_file():
        level_path = level_path.parent

    # Step 1 & 2: Serialize scene edits into level files
    report = serialize_scene_to_level_files(scene, level_path)
    if not report.success:
        return LevelExportResult(
            success=False,
            message=f"Serialization failed: {report.message}",
            target_pak=level_path / "Level.pak",
            backup_created=False,
            files_packed_count=0,
            total_bytes=0,
        )

    target_pak = level_path / "Level.pak"
    files_packed = 0
    total_bytes = 0

    # Step 3: Repack into official Level.pak
    if repack_pak:
        try:
            files_packed, total_bytes = pack_level_directory(
                source_dir=report.target_dir,
                output_pak=target_pak,
                create_backup=create_backup,
            )
        except Exception as exc:
            return LevelExportResult(
                success=False,
                message=f"Error repacking Level.pak: {exc}",
                target_pak=target_pak,
                backup_created=False,
                files_packed_count=0,
                total_bytes=0,
            )

    backup_path = target_pak.with_suffix(".pak.bak")
    backup_exists = backup_path.is_file()
    size_mb = total_bytes / (1024 * 1024)

    msg = (
        f"Map saved successfully! {report.message}. "
        f"Repacked {files_packed} files into {target_pak.name} ({size_mb:.2f} MB)."
    )
    if create_backup and backup_exists:
        msg += " Backup saved: Level.pak.bak."

    return LevelExportResult(
        success=True,
        message=msg,
        target_pak=target_pak,
        backup_created=create_backup and backup_exists,
        files_packed_count=files_packed,
        total_bytes=total_bytes,
    )
