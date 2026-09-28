"""
Viewers and viewport environment package for LostAcademy Aion Model Library.
"""

from .viewer_stage import ViewerStage, VIEWER_COLLECTION_NAME
from .viewport_controls import view_preset_axis, toggle_persp_ortho, reset_view
from .display_modes import set_shading_mode, set_bones_display, toggle_wireframe_overlay
from .animation_player import AnimationPlayer
from .stage_layout import (
    apply_lineup_offset,
    calculate_next_model_x_offset,
    get_stage_models,
    get_model_bounds_x,
)

__all__ = [
    "ViewerStage",
    "VIEWER_COLLECTION_NAME",
    "view_preset_axis",
    "toggle_persp_ortho",
    "reset_view",
    "set_shading_mode",
    "set_bones_display",
    "toggle_wireframe_overlay",
    "AnimationPlayer",
    "apply_lineup_offset",
    "calculate_next_model_x_offset",
    "get_stage_models",
    "get_model_bounds_x",
]
