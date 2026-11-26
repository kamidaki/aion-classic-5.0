"""
Properties package for Aion Blender Toolkit.
"""

from __future__ import annotations

from .scene_properties import (
    AionSceneSettings,
    register as register_properties,
    unregister as unregister_properties,
)


def register():
    register_properties()


def unregister():
    unregister_properties()


__all__ = [
    "AionSceneSettings",
    "register",
    "unregister",
]
