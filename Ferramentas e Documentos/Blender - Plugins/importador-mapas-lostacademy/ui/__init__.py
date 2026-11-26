"""
UI Package for Aion Blender Toolkit.
"""

from __future__ import annotations

from .panels import register as register_panels
from .panels import unregister as unregister_panels


def register():
    register_panels()


def unregister():
    unregister_panels()
