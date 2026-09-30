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
    bl_label = "Criar Modelo Aion"
    bl_description = "Exporta a malha selecionada para um novo modelo CGF do Aion e registra na biblioteca"
    bl_options = {"REGISTER", "UNDO"}

    asset_name: StringProperty(name="Nome do Modelo", default="Novo_Modelo_Custom")
    category: EnumProperty(
        name="Categoria",
        items=[c for c in KNOWN_CATEGORIES if c[0] != "ALL"],
        default="OBJECT",
    )
    target_path: StringProperty(name="Caminho Relativo", default="")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Por favor selecione um objeto de Malha (Mesh) para converter.")
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
            self.report({"INFO"}, f"Modelo '{entry.name}' criado com sucesso! ({tx_res.message})")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, f"Falha na criação: {tx_res.message}")
            return {"CANCELLED"}


class AION_OT_clone_asset(bpy.types.Operator):
    """Duplicates the currently selected asset into a new editable Aion asset."""
    bl_idname = "aion_model.clone_asset"
    bl_label = "Clonar Modelo"
    bl_description = "Duplicar o modelo selecionado e criar um novo modelo independente"
    bl_options = {"REGISTER", "UNDO"}

    new_name: StringProperty(name="Novo Nome do Modelo", default="Modelo_Clonado")
    new_path: StringProperty(name="Novo Caminho do Modelo", default="")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        if not settings.active_asset_id:
            self.report({"WARNING"}, "Nenhum modelo selecionado para clonar.")
            return {"CANCELLED"}

        db = AssetDatabase.get()
        source_entry = db.get_by_id(settings.active_asset_id)
        if not source_entry:
            self.report({"ERROR"}, "Modelo de origem não encontrado no banco de dados.")
            return {"CANCELLED"}

        client_prov = get_client_provider(settings.client_path)
        if not client_prov:
            self.report({"ERROR"}, "Pasta do cliente inválida ou não configurada.")
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
            self.report({"INFO"}, f"Clonado com sucesso para '{cloned_entry.name}'")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, f"Falha na clonagem: {tx_res.message}")
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
