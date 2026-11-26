"""
Environment Animation Master Controller for Aion Blender Toolkit.
Manages wind, water, UV scroll, and timeline playback.
"""

from __future__ import annotations

import bpy

from .wind_system import apply_vegetation_wind_sway
from .water_animation import apply_water_wave_animation
from .uv_scroll import animate_mapping_location
from .cga_animator import apply_cga_controller_animation


def play_timeline() -> None:
    """Starts viewport animation playback."""
    try:
        bpy.ops.screen.animation_play()
    except Exception:
        pass


def stop_timeline() -> None:
    """Stops viewport animation playback."""
    try:
        bpy.ops.screen.animation_cancel()
    except Exception:
        pass


def toggle_timeline() -> None:
    """Toggles viewport animation playback."""
    try:
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel()
        else:
            bpy.ops.screen.animation_play()
    except Exception:
        pass
