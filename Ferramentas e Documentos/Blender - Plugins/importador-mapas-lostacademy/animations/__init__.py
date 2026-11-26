"""
Aion Animation Package.
Includes wind sway, water waves, UV scrolling, CGA controllers, and environment playback.
"""

from .wind_system import apply_vegetation_wind_sway, is_vegetation_reference
from .water_animation import apply_water_wave_animation
from .uv_scroll import animate_mapping_location
from .cga_animator import apply_cga_controller_animation
from .environment_animation import play_timeline, stop_timeline, toggle_timeline

__all__ = [
    "apply_vegetation_wind_sway",
    "is_vegetation_reference",
    "apply_water_wave_animation",
    "animate_mapping_location",
    "apply_cga_controller_animation",
    "play_timeline",
    "stop_timeline",
    "toggle_timeline",
]
