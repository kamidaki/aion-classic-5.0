"""
Save, Export, and Transactional Rollback Operators for LostAcademy Aion Model Library.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

import bpy
from bpy.props import StringProperty, BoolProperty

from ..core.transaction_manager import TransactionManager, TransactionResult
from ..editors.mesh_editor import MeshEditor
from ..exporters.direct_saver import DirectSaver
from ..exporters.loose_exporter import LooseExporter
from ..indexer.asset_database import AssetDatabase
from ..viewers.viewer_stage import ViewerStage
from .library_ops import get_client_provider, get_model_provider

logger = logging.getLogger(__name__)


def find_active_or_stage_root(context: bpy.types.Context) -> bpy.types.Object | None:
    """Locates the root model object (Armature if rigged, otherwise Mesh)."""
    obj = context.active_object
    if obj:
        if obj.type == "ARMATURE":
            return obj
        if obj.type == "MESH":
            if obj.parent and obj.parent.type == "ARMATURE":
                return obj.parent
            return obj

    # Fallback to stage objects
    stage_col = ViewerStage.get_or_create_stage_collection()
    for o in stage_col.objects:
        if o.type == "ARMATURE":
            return o
    for o in stage_col.objects:
        if o.type == "MESH":
            return o
    return None


class AION_OT_save_asset(bpy.types.Operator):
    """Saves the modified model, armature, animations, and materials directly to client files or safe export folder."""
    bl_idname = "aion_model.save_asset"
    bl_label = "Save to Client / Export"
    bl_description = "Commit modifications back to client files or safe export folder"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        asset_id = settings.active_asset_id
        if not asset_id:
            self.report({"WARNING"}, "No active Aion asset selected to save.")
            return {"CANCELLED"}

        db = AssetDatabase.get()
        entry = db.get_by_id(asset_id)
        if not entry:
            self.report({"ERROR"}, f"Asset '{asset_id}' not found in database.")
            return {"CANCELLED"}

        client_dir = settings.client_path
        if not client_dir or not Path(client_dir).is_dir():
            self.report({"ERROR"}, "Valid client folder not configured.")
            return {"CANCELLED"}

        model_prov = get_model_provider(client_dir)
        if not model_prov:
            self.report({"ERROR"}, "Failed to initialize model provider.")
            return {"CANCELLED"}

        root_obj = find_active_or_stage_root(context)
        if not root_obj:
            self.report({"ERROR"}, "No active 3D model found to save.")
            return {"CANCELLED"}

        # Ensure object mode before serialization
        MeshEditor.return_to_object_mode()

        fallback_dir = Path(settings.export_fallback_dir) if settings.export_fallback_dir else None

        result: TransactionResult = DirectSaver.save_model(
            root_obj=root_obj,
            entry=entry,
            model_provider=model_prov,
            client_root=Path(client_dir),
            allow_client_write=settings.allow_client_write,
            fallback_dir=fallback_dir,
        )

        if result.success:
            settings.active_is_modified = False
            entry.is_modified = False
            # Update item in UI collection
            for item in settings.asset_items:
                if item.asset_id == asset_id:
                    item.is_modified = False
                    break

            self.report({"INFO"}, result.message)
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, f"Save Failed: {result.message}")
            return {"CANCELLED"}


class AION_OT_export_loose(bpy.types.Operator):
    """Exports model geometry, armature, and animations to a loose folder on disk."""
    bl_idname = "aion_model.export_loose"
    bl_label = "Export Loose Files"
    bl_description = "Export asset to an arbitrary folder without modifying game files"
    bl_options = {"REGISTER"}

    directory: StringProperty(
        name="Target Folder",
        description="Directory to export loose files into",
        subtype='DIR_PATH',
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.directory:
            self.report({"WARNING"}, "No export folder chosen.")
            return {"CANCELLED"}

        settings = context.scene.aion_model_lib
        db = AssetDatabase.get()
        entry = db.get_by_id(settings.active_asset_id)
        if not entry:
            self.report({"ERROR"}, "No active asset to export.")
            return {"CANCELLED"}

        model_prov = get_model_provider(settings.client_path)
        if not model_prov:
            self.report({"ERROR"}, "Model provider not available.")
            return {"CANCELLED"}

        root_obj = find_active_or_stage_root(context)
        if not root_obj:
            self.report({"ERROR"}, "No active model found in stage.")
            return {"CANCELLED"}

        MeshEditor.return_to_object_mode()

        res = LooseExporter.export_asset(
            root_obj=root_obj,
            entry=entry,
            model_provider=model_prov,
            target_dir=Path(self.directory),
        )

        if res.get("success"):
            files_count = len(res.get("written_files", []))
            self.report({"INFO"}, f"Exported {files_count} file(s) to {self.directory}")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, f"Export Failed: {res.get('error')}")
            return {"CANCELLED"}


class AION_OT_rollback_asset(bpy.types.Operator):
    """Restores the previous version of the active asset from its backup (.bak / .pak.bak)."""
    bl_idname = "aion_model.rollback_asset"
    bl_label = "Rollback Asset"
    bl_description = "Restore original asset from backup file"
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(
        name="Backup File",
        description="Path to .bak or .pak.bak file",
        subtype='FILE_PATH',
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.filepath:
            self.report({"WARNING"}, "No backup file selected.")
            return {"CANCELLED"}

        bak_path = Path(self.filepath)
        if not bak_path.is_file():
            self.report({"ERROR"}, "Backup file not found.")
            return {"CANCELLED"}

        success = TransactionManager.rollback(bak_path)
        if success:
            self.report({"INFO"}, f"Successfully restored {bak_path.name}")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, f"Failed to restore {bak_path.name}")
            return {"CANCELLED"}


CLASSES = (
    AION_OT_save_asset,
    AION_OT_export_loose,
    AION_OT_rollback_asset,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
