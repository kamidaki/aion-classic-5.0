"""
Blender Property Definitions for LostAcademy Aion Model Library.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, List, Optional

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from ..config.settings import (
    DEFAULT_CLIENT_PATHS,
    KNOWN_CATEGORIES,
    SAFETY_ALLOW_CLIENT_WRITE_DEFAULT,
)


class AionAnimItem(bpy.types.PropertyGroup):
    """Represents an animation entry belonging to a model's CAL list."""
    name: StringProperty(name="Anim Name", default="")
    caf_path: StringProperty(name="CAF Path", default="")


class AionAssetItem(bpy.types.PropertyGroup):
    """Represents a single model asset in the UI asset list."""
    asset_id: StringProperty(name="Asset ID", default="")
    name: StringProperty(name="Name", default="")
    category: StringProperty(name="Category", default="OTHER")
    model_path: StringProperty(name="Model Path", default="")
    skeleton_path: StringProperty(name="Skeleton Path", default="")
    cal_path: StringProperty(name="CAL Path", default="")
    poly_count: IntProperty(name="Polygons", default=0)
    vertex_count: IntProperty(name="Vertices", default=0)
    bone_count: IntProperty(name="Bones", default=0)
    anim_count: IntProperty(name="Animations", default=0)
    has_thumbnail: BoolProperty(name="Has Thumbnail", default=False)
    thumbnail_path: StringProperty(name="Thumbnail Path", default="")
    is_modified: BoolProperty(name="Modified", default=False)


def on_filter_updated(self: Any, context: bpy.types.Context) -> None:
    """Invoked when search text or category filter changes."""
    # Triggers operator to refresh filtered collection if database is loaded
    try:
        bpy.ops.aion_model.filter_assets()
    except Exception:
        pass


class AionModelLibrarySettings(bpy.types.PropertyGroup):
    """Main settings and state for the Aion Model Library addon."""

    # Client Selection
    client_path: StringProperty(
        name="Client Directory",
        description="Path to Aion client root folder (contains Data, Objects, etc.)",
        subtype='DIR_PATH',
        default=DEFAULT_CLIENT_PATHS[0] if DEFAULT_CLIENT_PATHS else "",
    )
    client_flavor: StringProperty(
        name="Client Flavor",
        description="Detected client generation/version",
        default="Not Detected",
    )

    # Safety
    allow_client_write: BoolProperty(
        name="Allow Client Write",
        description="CRITICAL SAFETY TOGGLE: Enable writing and patching directly inside official game client files/PAKs. When disabled, changes are saved to the Safe Export Directory.",
        default=SAFETY_ALLOW_CLIENT_WRITE_DEFAULT,
    )
    auto_backup: BoolProperty(
        name="Automatic Backups",
        description="Always create .bak or .pak.bak copies before modifying any client file",
        default=True,
    )
    export_fallback_dir: StringProperty(
        name="Safe Export Directory",
        description="Target directory for modified assets when Allow Client Write is disabled",
        subtype='DIR_PATH',
        default="",
    )

    # Search & Filtering
    search_query: StringProperty(
        name="Search",
        description="Search models by name, ID, or file path",
        default="",
        update=on_filter_updated,
    )
    category_filter: EnumProperty(
        name="Category",
        description="Filter assets by category",
        items=KNOWN_CATEGORIES,
        default="ALL",
        update=on_filter_updated,
    )

    # Scanned asset list
    asset_items: CollectionProperty(type=AionAssetItem)
    active_asset_index: IntProperty(
        name="Active Asset Index",
        default=0,
    )
    scanned_total_count: IntProperty(
        name="Total Scanned Assets",
        default=0,
    )

    # Active loaded asset metadata
    active_asset_id: StringProperty(name="Asset ID", default="")
    active_asset_name: StringProperty(name="Asset Name", default="")
    active_category: StringProperty(name="Category", default="")
    active_model_path: StringProperty(name="Model Path", default="")
    active_skeleton_path: StringProperty(name="Skeleton Path", default="")
    active_cal_path: StringProperty(name="CAL Path", default="")
    active_is_modified: BoolProperty(name="Modified Status", default=False)
    active_poly_count: IntProperty(name="Polygons", default=0)
    active_vertex_count: IntProperty(name="Vertices", default=0)
    active_bone_count: IntProperty(name="Bones", default=0)

    # Animations of active loaded asset
    active_anims: CollectionProperty(type=AionAnimItem)
    active_anim_index: IntProperty(name="Active Anim Index", default=0)

    # Viewport & Display
    studio_lighting: BoolProperty(
        name="Studio Lighting",
        description="Add 3-point studio lighting rig to viewer collection",
        default=True,
    )
    camera_auto_frame: BoolProperty(
        name="Auto Frame Camera",
        description="Automatically frame active camera to loaded model bounding box",
        default=True,
    )
    show_armature: BoolProperty(
        name="Show Bones",
        description="Toggle armature bone visibility in 3D viewport",
        default=True,
    )
    bone_display_type: EnumProperty(
        name="Bone Display",
        items=[
            ('OCTAHEDRAL', 'Octahedral', 'Standard bone display'),
            ('STICK', 'Stick', 'Simple stick display'),
            ('BBONE', 'B-Bone', 'Bendy bone display'),
            ('WIRE', 'Wire', 'Wireframe bone display'),
        ],
        default='OCTAHEDRAL',
    )

    # Creation & Cloning
    new_asset_id: StringProperty(name="New Asset ID", default="custom_mesh_01")
    new_category: EnumProperty(
        name="New Category",
        items=[c for c in KNOWN_CATEGORIES if c[0] != "ALL"],
        default="PROP",
    )
    new_model_path: StringProperty(
        name="New Model Path",
        default="objects/custom/custom_mesh_01.cgf",
    )
    clone_new_id: StringProperty(name="Cloned Asset ID", default="cloned_asset_01")
    clone_new_path: StringProperty(
        name="Cloned Path",
        default="objects/custom/cloned_asset_01.cgf",
    )


CLASSES = (
    AionAnimItem,
    AionAssetItem,
    AionModelLibrarySettings,
)


def register_properties() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.aion_model_lib = PointerProperty(type=AionModelLibrarySettings)


def unregister_properties() -> None:
    if hasattr(bpy.types.Scene, "aion_model_lib"):
        del bpy.types.Scene.aion_model_lib
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
