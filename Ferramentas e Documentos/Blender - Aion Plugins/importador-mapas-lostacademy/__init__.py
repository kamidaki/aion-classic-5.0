bl_info = {
    "name": "Aion Map Toolkit - Editor & Importer",
    "author": "Aion Classic & Retail Tools",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "3D Viewport > Sidebar > Aion Map, File > Import/Export",
    "description": "Importador, Editor e Visualizador de Mapas do Aion (Classic/3.9/Live) com Esqueletos, Animações Idle e Salvamento Direto",
    "category": "Import-Export",
}

__version__ = ".".join(str(part) for part in bl_info["version"])

import sys
from pathlib import Path

# Ensure plugin directory and vendor directory are in sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_VENDOR_DIR = _PLUGIN_DIR / "_vendor"

if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

if _VENDOR_DIR.is_dir() and str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import bpy

from .properties import register as register_properties, unregister as unregister_properties
from .operators import register as register_operators, unregister as unregister_operators
from .ui import register as register_ui, unregister as unregister_ui

from .operators.import_cgf import AION_OT_import_cgf
from .operators.import_level import AION_OT_import_level_folder
from .operators.export_level import AION_OT_direct_save, AION_OT_export_level, AION_OT_repack_level


def menu_func_import(self, context):
    self.layout.operator(AION_OT_import_cgf.bl_idname, text="Aion CGF / CGA (.cgf)")
    self.layout.operator(AION_OT_import_level_folder.bl_idname, text="Aion Level (Folder or Level.pak)")


def menu_func_export(self, context):
    self.layout.operator(AION_OT_direct_save.bl_idname, text="Aion Direct Save Map")
    self.layout.operator(AION_OT_export_level.bl_idname, text="Aion Level (.pak)")


def register():
    register_properties()
    register_operators()
    register_ui()

    try:
        bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    except Exception:
        pass
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    try:
        bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    except Exception:
        pass
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    try:
        bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    except Exception:
        pass

    try:
        bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    except Exception:
        pass

    unregister_ui()
    unregister_operators()
    unregister_properties()


if __name__ == "__main__":
    register()
