"""
Creation & Cloning Operators for LostAcademy Aion Model Library.
Supports creating new Aion CGF assets from arbitrary Blender meshes and cloning existing assets.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

import bpy
from bpy.props import StringProperty, EnumProperty

from ..config.settings import KNOWN_CATEGORIES
from ..editors.model_creator import ModelCreator
from ..editors.model_cloner import ModelCloner
from ..indexer.asset_database import AssetDatabase
from .library_ops import get_client_provider

logger = logging.getLogger(__name__)


class AION_OT_create_from_mesh(bpy.types.Operator):
    """Creates a new Aion CGF asset from the selected Blender mesh."""
    bl_idname = "aion_model.create_from_mesh"
    bl_label = "Create Aion Model"
    bl_description = "Export selected mesh into a new Aion CGF asset and register in the library"
    bl_options = {"REGISTER", "UNDO"}

    asset_name: StringProperty(name="Asset Name", default="New_Custom_Model")
    category: EnumProperty(
        name="Category",
        items=[c for c in KNOWN_CATEGORIES if c[0] != "ALL"],
        default="OBJECT",
    )
    target_path: StringProperty(name="Relative Path", default="")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Please select a Mesh object to convert.")
            return {"CANCELLED"}

        client_root = Path(settings.client_path) if settings.client_path else None

        entry, tx_res = ModelCreator.create_model_from_selected(
            obj=obj,
            asset_name=self.asset_name,
            category=self.category,
            target_relative_path=self.target_path.strip(),
            client_root=client_root,
            allow_client_write=settings.allow_client_write,
        )

        if entry:
            # Refresh UI list
            bpy.ops.aion_model.filter_assets()
            settings.active_asset_id = entry.asset_id
            settings.active_asset_name = entry.name
            settings.active_category = entry.category
            settings.active_model_path = entry.model_path
            self.report({"INFO"}, f"Successfully created asset '{entry.name}' ({tx_res.message})")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, f"Creation failed: {tx_res.message}")
            return {"CANCELLED"}


class AION_OT_clone_asset(bpy.types.Operator):
    """Duplicates the currently selected asset into a new editable Aion asset."""
    bl_idname = "aion_model.clone_asset"
    bl_label = "Clone Asset"
    bl_description = "Duplicate selected model and create a new independent asset"
    bl_options = {"REGISTER", "UNDO"}

    new_name: StringProperty(name="New Asset Name", default="Cloned_Asset")
    new_path: StringProperty(name="New Model Path", default="")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        if not settings.active_asset_id:
            self.report({"WARNING"}, "No asset selected to clone.")
            return {"CANCELLED"}

        db = AssetDatabase.get()
        source_entry = db.get_by_id(settings.active_asset_id)
        if not source_entry:
            self.report({"ERROR"}, "Source asset not found in database.")
            return {"CANCELLED"}

        client_prov = get_client_provider(settings.client_path)
        if not client_prov:
            self.report({"ERROR"}, "Valid client folder not configured.")
            return {"CANCELLED"}

        cloned_entry, tx_res = ModelCloner.clone_asset(
            source_entry=source_entry,
            new_name=self.new_name,
            client_provider=client_prov,
            target_relative_path=self.new_path.strip() if self.new_path else None,
            allow_client_write=settings.allow_client_write,
        )

        if cloned_entry:
            bpy.ops.aion_model.filter_assets()
            settings.active_asset_id = cloned_entry.asset_id
            settings.active_asset_name = cloned_entry.name
            settings.active_category = cloned_entry.category
            settings.active_model_path = cloned_entry.model_path
            self.report({"INFO"}, f"Successfully cloned into '{cloned_entry.name}'")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, f"Cloning failed: {tx_res.message}")
            return {"CANCELLED"}


CLASSES = (
    AION_OT_create_from_mesh,
    AION_OT_clone_asset,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
