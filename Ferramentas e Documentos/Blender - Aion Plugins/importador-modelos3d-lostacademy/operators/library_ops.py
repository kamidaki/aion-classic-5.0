"""
Library Operators for LostAcademy Aion Model Library.
Handles client detection, asset scanning, search/filtering, asset loading into 3D stage, and clearing.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

import bpy

from ..config.settings import DEFAULT_CLIENT_PATHS
from ..core.client_detector import ClientDetector
from ..core.client_provider import AionClientProvider
from ..indexer.asset_database import AssetDatabase
from ..indexer.scanner import Scanner
from ..providers.model_provider import ModelProvider
from ..viewers.display_modes import set_shading_mode
from ..viewers.viewer_stage import ViewerStage

logger = logging.getLogger(__name__)

# Cached provider instances
_CLIENT_PROVIDER: Optional[AionClientProvider] = None
_MODEL_PROVIDER: Optional[ModelProvider] = None


def get_client_provider(client_path: str) -> Optional[AionClientProvider]:
    """Returns or creates a cached AionClientProvider for client_path."""
    global _CLIENT_PROVIDER, _MODEL_PROVIDER
    if not client_path:
        return None
    p = Path(client_path).resolve()
    if not p.is_dir():
        return None
    if _CLIENT_PROVIDER is None or _CLIENT_PROVIDER.root != p:
        _CLIENT_PROVIDER = AionClientProvider(p)
        _MODEL_PROVIDER = ModelProvider(_CLIENT_PROVIDER)
    return _CLIENT_PROVIDER


def get_model_provider(client_path: str) -> Optional[ModelProvider]:
    """Returns or creates a cached ModelProvider for client_path."""
    global _CLIENT_PROVIDER, _MODEL_PROVIDER
    cp = get_client_provider(client_path)
    if not cp:
        return None
    if _MODEL_PROVIDER is None:
        _MODEL_PROVIDER = ModelProvider(cp)
    return _MODEL_PROVIDER


class AION_OT_detect_client(bpy.types.Operator):
    """Detects Aion client installation and determines flavor/generation."""
    bl_idname = "aion_model.detect_client"
    bl_label = "Detect Client"
    bl_description = "Auto-detect Aion client folder and configuration"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        search_dirs = [settings.client_path] if settings.client_path else []
        search_dirs.extend(DEFAULT_CLIENT_PATHS)

        detected = None
        for d in search_dirs:
            if d and Path(d).is_dir():
                detected = ClientDetector.detect_client(Path(d))
                if detected:
                    break

        if detected:
            settings.client_path = str(detected.root_path)
            settings.client_flavor = detected.flavor
            self.report(
                {"INFO"},
                f"Detected {detected.flavor} at {detected.root_path}",
            )
            return {"FINISHED"}
        else:
            self.report({"WARNING"}, "No valid Aion client found. Please specify folder manually.")
            return {"CANCELLED"}


class AION_OT_scan_assets(bpy.types.Operator):
    """Scans the client directory to discover 3D models, armatures, animations, and archetypes."""
    bl_idname = "aion_model.scan_assets"
    bl_label = "Scan Client Assets"
    bl_description = "Scan client folder and PAKs to index all 3D models"
    bl_options = {"REGISTER"}

    force_rescan: bpy.props.BoolProperty(name="Force Full Rescan", default=False)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        client_dir = settings.client_path
        if not client_dir or not Path(client_dir).is_dir():
            self.report({"ERROR"}, "Please select a valid Aion client folder first.")
            return {"CANCELLED"}

        client_path = Path(client_dir)
        db = AssetDatabase.get()

        # Check if cache exists on disk for instant loading (0.1s instead of 3 minutes)
        if not self.force_rescan and db.load_cache(client_path):
            settings.scanned_total_count = db.total_count
            bpy.ops.aion_model.filter_assets()
            self.report(
                {"INFO"},
                f"Loaded {db.total_count} assets instantly from index cache! (Click Rescan to rebuild)",
            )
            return {"FINISHED"}

        # Perform fast scan
        scanner = Scanner(client_root=client_path)
        scanned_assets = scanner.scan_all()
        db.load_from_entries(scanned_assets)

        # Persist index cache to disk
        db.save_cache(client_path)

        settings.scanned_total_count = len(scanned_assets)

        # Trigger filter to populate UI list
        bpy.ops.aion_model.filter_assets()

        self.report(
            {"INFO"},
            f"Successfully scanned {len(scanned_assets)} assets across {len(db.get_categories())} categories (cached to disk).",
        )
        return {"FINISHED"}


class AION_OT_filter_assets(bpy.types.Operator):
    """Filters displayed asset list by search keyword and category."""
    bl_idname = "aion_model.filter_assets"
    bl_label = "Filter Assets"
    bl_description = "Apply search keyword and category filter to asset list"
    bl_options = {"INTERNAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        db = AssetDatabase.get()

        # Auto-load cache if database in memory is empty but client has saved cache
        if db.total_count == 0 and settings.client_path:
            p = Path(settings.client_path)
            if p.is_dir() and db.load_cache(p):
                settings.scanned_total_count = db.total_count

        if not db.all_assets:
            settings.asset_items.clear()
            return {"FINISHED"}

        cat = None if settings.category_filter == "ALL" else settings.category_filter
        q = (settings.search_query or "").strip()

        filtered = db.search(query=q, category=cat, limit=500)

        # Populate asset_items
        settings.asset_items.clear()
        for entry in filtered:
            item = settings.asset_items.add()
            item.asset_id = entry.asset_id
            item.name = entry.name
            item.category = entry.category
            item.model_path = entry.model_path
            item.skeleton_path = entry.skeleton_path or ""
            item.cal_path = entry.cal_path or ""
            item.poly_count = getattr(entry, "triangle_count", getattr(entry, "poly_count", 0))
            item.vertex_count = getattr(entry, "vertex_count", 0)
            item.bone_count = getattr(entry, "bone_count", 0)
            item.anim_count = len(entry.animations) if getattr(entry, "animations", None) else getattr(entry, "animation_count", 0)
            item.is_modified = bool(getattr(entry, "is_modified", False))

        if settings.active_asset_index >= len(settings.asset_items):
            settings.active_asset_index = max(0, len(settings.asset_items) - 1)

        return {"FINISHED"}


class AION_OT_load_asset(bpy.types.Operator):
    """Loads the selected Aion model into the dedicated 3D viewer stage."""
    bl_idname = "aion_model.load_asset"
    bl_label = "View Model"
    bl_description = "Load selected model, skeleton, materials, and idle animation into the 3D viewer"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        if not settings.asset_items or settings.active_asset_index < 0:
            self.report({"WARNING"}, "No asset selected.")
            return {"CANCELLED"}

        if settings.active_asset_index >= len(settings.asset_items):
            settings.active_asset_index = 0

        selected_item = settings.asset_items[settings.active_asset_index]
        db = AssetDatabase.get()
        entry = db.get_by_id(selected_item.asset_id)
        if not entry:
            self.report({"ERROR"}, f"Asset '{selected_item.asset_id}' not found in database.")
            return {"CANCELLED"}

        client_prov = get_client_provider(settings.client_path)
        model_prov = get_model_provider(settings.client_path)
        if not client_prov or not model_prov:
            self.report({"ERROR"}, "Failed to initialize client provider. Check client directory.")
            return {"CANCELLED"}

        # 1. Setup viewer collection & lighting
        stage_col = ViewerStage.get_or_create_stage_collection()
        ViewerStage.clear_stage_objects()

        if settings.studio_lighting:
            ViewerStage.setup_studio_lighting()

        # 2. Load model into stage
        try:
            root_obj = model_prov.load_model(
                entry=entry,
                target_collection=stage_col,
                load_animation=True,
            )
        except Exception as e:
            logger.error("Failed to load model %s: %s", entry.name, e, exc_info=True)
            self.report({"ERROR"}, f"Failed to load model {entry.name}: {e}")
            return {"CANCELLED"}

        if not root_obj:
            self.report({"ERROR"}, f"Could not load geometry for {entry.name}.")
            return {"CANCELLED"}

        # 3. Update active settings metadata
        settings.active_asset_id = entry.asset_id
        settings.active_asset_name = entry.name
        settings.active_category = entry.category
        settings.active_model_path = entry.model_path
        settings.active_skeleton_path = entry.skeleton_path or ""
        settings.active_cal_path = entry.cal_path or ""
        settings.active_is_modified = entry.is_modified

        # Geometry counts
        if root_obj.type == "ARMATURE":
            settings.active_bone_count = len(root_obj.data.bones)
            mesh_children = [c for c in root_obj.children if c.type == "MESH"]
            if mesh_children:
                m = mesh_children[0].data
                settings.active_vertex_count = len(m.vertices)
                settings.active_poly_count = len(m.polygons)
        elif root_obj.type == "MESH":
            settings.active_bone_count = 0
            settings.active_vertex_count = len(root_obj.data.vertices)
            settings.active_poly_count = len(root_obj.data.polygons)

        # 4. Populate active animation list
        settings.active_anims.clear()
        if entry.cal_path:
            try:
                try:
                    from formats.cgf.cal_parser import parse_cal
                except ImportError:
                    from ..formats.cgf.cal_parser import parse_cal
                cal_bytes = client_prov.catalog.extract_file(entry.cal_path)
                if not cal_bytes and (Path(settings.client_path) / entry.cal_path).is_file():
                    cal_bytes = (Path(settings.client_path) / entry.cal_path).read_bytes()
                if cal_bytes:
                    cal_map = parse_cal(cal_bytes)
                    for state_name, caf_rel in cal_map.items():
                        anim_item = settings.active_anims.add()
                        anim_item.name = state_name
                        anim_item.caf_path = caf_rel
            except Exception:
                pass

        if not settings.active_anims and entry.animations:
            if isinstance(entry.animations, dict):
                for anim_name, caf_path in entry.animations.items():
                    anim_item = settings.active_anims.add()
                    anim_item.name = anim_name
                    anim_item.caf_path = str(caf_path)
            elif isinstance(entry.animations, list):
                for item in entry.animations:
                    anim_item = settings.active_anims.add()
                    if isinstance(item, (list, tuple)) and len(item) == 2:
                        anim_item.name = str(item[0])
                        anim_item.caf_path = str(item[1])
                    else:
                        anim_item.name = str(item)
                        anim_item.caf_path = str(item)

        # 5. Frame camera & set shading
        if settings.camera_auto_frame:
            ViewerStage.frame_object(root_obj)

        set_shading_mode("MATERIAL")

        self.report({"INFO"}, f"Loaded {entry.name} ({entry.category})")
        return {"FINISHED"}


class AION_OT_clear_stage(bpy.types.Operator):
    """Clears all objects from the viewer stage."""
    bl_idname = "aion_model.clear_stage"
    bl_label = "Clear Stage"
    bl_description = "Remove all models from the viewer stage"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        ViewerStage.clear_stage_objects()
        settings = context.scene.aion_model_lib
        settings.active_asset_id = ""
        settings.active_asset_name = ""
        settings.active_anims.clear()
        self.report({"INFO"}, "Viewer stage cleared.")
        return {"FINISHED"}


CLASSES = (
    AION_OT_detect_client,
    AION_OT_scan_assets,
    AION_OT_filter_assets,
    AION_OT_load_asset,
    AION_OT_clear_stage,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
