"""
Aion Map Editing and Round-Trip Synchronization Package.
"""

from .roundtrip_tracker import (
    SOURCE_BRUSH,
    SOURCE_OBJECT,
    SOURCE_MISSION,
    ObjectChangeRecord,
    tag_object_instance,
    get_object_metadata,
    collect_scene_changes,
)
from .terrain_editor import (
    find_terrain_object,
    sync_sculpted_terrain_to_land_map,
)
from .object_editor import (
    snap_objects_to_terrain,
    randomize_object_transforms,
)
from .level_serializer import (
    LevelSerializationReport,
    serialize_scene_to_level_files,
)

__all__ = [
    "SOURCE_BRUSH",
    "SOURCE_OBJECT",
    "SOURCE_MISSION",
    "ObjectChangeRecord",
    "tag_object_instance",
    "get_object_metadata",
    "collect_scene_changes",
    "find_terrain_object",
    "sync_sculpted_terrain_to_land_map",
    "snap_objects_to_terrain",
    "randomize_object_transforms",
    "LevelSerializationReport",
    "serialize_scene_to_level_files",
]
