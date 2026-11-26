"""
Topbar and File menu integration for LostAcademy Aion Model Library.
"""

from __future__ import annotations
import bpy


def menu_func_import(self: bpy.types.Menu, context: bpy.types.Context) -> None:
    self.layout.operator(
        "aion_model.load_asset",
        text="Lost Academy - Importador de Modelos 3D (.cgf)",
        icon="MESH_DATA",
    )


def menu_func_export(self: bpy.types.Menu, context: bpy.types.Context) -> None:
    self.layout.operator(
        "aion_model.export_loose",
        text="Lost Academy - Importador de Modelos 3D (.cgf)",
        icon="EXPORT",
    )


def register() -> None:
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister() -> None:
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
