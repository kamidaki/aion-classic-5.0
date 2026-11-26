"""
LostAcademy Aion Model Library - Blender Addon.
A production-quality visual asset library, model viewer, animation player,
and full-featured CryEngine CGF / CAL / CAF model editor directly inside Blender.
Supports: CLIENT -> INDEX -> VIEW -> EDIT -> SAVE -> CLIENT
"""

from __future__ import annotations

bl_info = {
    "name": "Lost Academy - Importador de Modelos 3D (Aion Model Library)",
    "author": "LostAcademy Team",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Barra Lateral (N) > Modelos Aion",
    "description": "Biblioteca visual de modelos 3D do Aion, visualizador de assets, animações e editor completo de CGF/CAL/CAF diretamente no Blender.",
    "warning": "",
    "doc_url": "https://github.com/kamidaki/aion-classic-5.0",
    "category": "Import-Export",
}

import bpy

from .properties import register_properties, unregister_properties
from . import operators
from . import ui


def register() -> None:
    """Registers all addon components."""
    register_properties()
    operators.register()
    ui.register()


def unregister() -> None:
    """Unregisters all addon components."""
    ui.unregister()
    operators.unregister()
    unregister_properties()


if __name__ == "__main__":
    register()
