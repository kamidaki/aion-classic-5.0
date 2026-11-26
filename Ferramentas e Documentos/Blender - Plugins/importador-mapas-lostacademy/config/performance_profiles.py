"""
Performance Profiles & 60+ FPS Viewport Tuning for Aion Blender Toolkit.
Designed specifically for weak CPUs and weak / integrated GPUs so maps load
linearly without UI freezes and navigate at 60+ FPS in Blender 4.0 - 5.2+.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

import bpy


DEFAULT_PERFORMANCE_PROFILE = "LOW"

PERFORMANCE_PROFILES: Dict[str, Dict[str, Any]] = {
    "LOW": {
        "label": "PC Fraco / 60+ FPS (Recomendado)",
        "terrain_lod": 4,
        "target_model_lod": 2,
        "max_terrain_blend_layers": 10,
        "simple_shaders": True,
        "disable_dynamic_shadows": True,
        "merge_template_submeshes": True,
        "animate_water_shader": False,
        "animate_skydome": False,
        "lightweight_water": True,
        "import_npc_rigs": False,
        "tick_budget_ms": 6.0,
        "shadow_resolution_scale": 0.25,
        "taa_samples": 1,
        "simplify_subdivision": 0,
    },
    "BALANCED": {
        "label": "Equilibrado",
        "terrain_lod": 2,
        "target_model_lod": 1,
        "max_terrain_blend_layers": 8,
        "simple_shaders": False,
        "disable_dynamic_shadows": False,
        "merge_template_submeshes": True,
        "animate_water_shader": False,
        "animate_skydome": False,
        "lightweight_water": True,
        "import_npc_rigs": False,
        "tick_budget_ms": 7.0,
        "shadow_resolution_scale": 0.25,
        "taa_samples": 4,
        "simplify_subdivision": 0,
    },
    "HIGH": {
        "label": "Alta Qualidade (GPU Dedicada)",
        "terrain_lod": 2,
        "target_model_lod": 0,
        "max_terrain_blend_layers": 12,
        "simple_shaders": False,
        "disable_dynamic_shadows": False,
        "merge_template_submeshes": True,
        "animate_water_shader": False,
        "animate_skydome": False,
        "lightweight_water": False,
        "import_npc_rigs": True,
        "tick_budget_ms": 8.0,
        "shadow_resolution_scale": 0.5,
        "taa_samples": 8,
        "simplify_subdivision": 1,
    },
}


def normalize_performance_profile(profile: str | None) -> str:
    """Normalizes a profile key to LOW, BALANCED, or HIGH."""
    if not profile:
        return DEFAULT_PERFORMANCE_PROFILE
    key = str(profile).strip().upper()
    if key in PERFORMANCE_PROFILES:
        return key
    return DEFAULT_PERFORMANCE_PROFILE


def resolve_profile_settings(profile: str | None = None) -> Dict[str, Any]:
    """Returns a copy of the resolved settings dictionary for the selected profile."""
    key = normalize_performance_profile(profile)
    cfg = deepcopy(PERFORMANCE_PROFILES[key])
    cfg["profile"] = key
    return cfg


def _safe_setattr(obj: Any, attr: str, value: Any) -> bool:
    if obj is None or not hasattr(obj, attr):
        return False
    try:
        setattr(obj, attr, value)
        return True
    except (AttributeError, TypeError, ValueError):
        return False


def frame_viewport_on_map(
    center_xyz: tuple[float, float, float],
    distance: float = 1200.0,
) -> int:
    """
    Centers all open 3D Viewports on the map center with clip_end=50000m using pure data API
    (no bpy.ops required; safe inside bpy.app.timers and background mode).
    """
    import math
    from mathutils import Euler, Vector

    updated = 0
    target = Vector((float(center_xyz[0]), float(center_xyz[1]), float(center_xyz[2])))
    rot_q = Euler((math.radians(55.0), 0.0, math.radians(-35.0)), "XYZ").to_quaternion()
    dist_val = max(50.0, float(distance))

    for wm in getattr(bpy.data, "window_managers", ()):
        for win in getattr(wm, "windows", ()):
            screen = getattr(win, "screen", None)
            if screen is None:
                continue
            for area in getattr(screen, "areas", ()):
                if getattr(area, "type", "") != "VIEW_3D":
                    continue
                for space in getattr(area, "spaces", ()):
                    if getattr(space, "type", "") != "VIEW_3D":
                        continue
                    _safe_setattr(space, "clip_start", 1.0)
                    _safe_setattr(space, "clip_end", 50000.0)
                    r3d = getattr(space, "region_3d", None)
                    if r3d is not None:
                        _safe_setattr(r3d, "view_location", target)
                        _safe_setattr(r3d, "view_distance", dist_val)
                        _safe_setattr(r3d, "view_rotation", rot_q)
                    updated += 1
                try:
                    area.tag_redraw()
                except Exception:
                    pass
    return updated


def apply_viewport_60fps_optimization(
    context: bpy.types.Context | None = None,
    profile: str | None = "LOW",
) -> Dict[str, Any]:
    """
    Configures scene Eevee, simplify, and 3D viewport clipping/shading settings
    for smooth 60+ FPS navigation on weak GPUs across all open windows.
    """
    cfg = resolve_profile_settings(profile)
    ctx = context or getattr(bpy, "context", None)
    scene = getattr(ctx, "scene", None) if ctx else None
    applied: Dict[str, Any] = {"profile": cfg["profile"], "viewports_updated": 0}

    if scene is not None:
        render = getattr(scene, "render", None)
        if render is not None:
            _safe_setattr(render, "use_simplify", True)
            _safe_setattr(render, "simplify_subdivision", cfg["simplify_subdivision"])
            _safe_setattr(render, "simplify_volumes", 0)
            applied["simplify"] = True

        eevee = getattr(scene, "eevee", None)
        if eevee is not None:
            is_low = cfg["profile"] == "LOW"
            _safe_setattr(eevee, "use_raytracing", False)
            _safe_setattr(eevee, "use_fast_gi", False)
            _safe_setattr(eevee, "use_volumetric_shadows", False)
            _safe_setattr(eevee, "use_shadow_jitter_viewport", False)
            _safe_setattr(eevee, "taa_samples", cfg["taa_samples"])
            _safe_setattr(eevee, "taa_render_samples", max(1, min(16, cfg["taa_samples"] * 2)))
            _safe_setattr(eevee, "use_taa_reprojection", not is_low)
            _safe_setattr(eevee, "use_shadows", not cfg["disable_dynamic_shadows"])
            _safe_setattr(eevee, "shadow_resolution_scale", cfg["shadow_resolution_scale"])
            _safe_setattr(eevee, "volumetric_samples", 8 if is_low else 16)
            applied["eevee_shadows"] = not cfg["disable_dynamic_shadows"]
            applied["taa_samples"] = cfg["taa_samples"]

    is_low = cfg["profile"] == "LOW"
    screens = []
    for wm in getattr(bpy.data, "window_managers", ()):
        for win in getattr(wm, "windows", ()):
            sc = getattr(win, "screen", None)
            if sc is not None and sc not in screens:
                screens.append(sc)
    ctx_screen = getattr(ctx, "screen", None) if ctx else None
    if ctx_screen is not None and ctx_screen not in screens:
        screens.append(ctx_screen)

    for screen in screens:
        for area in getattr(screen, "areas", ()):
            if getattr(area, "type", "") != "VIEW_3D":
                continue
            for space in getattr(area, "spaces", ()):
                if getattr(space, "type", "") != "VIEW_3D":
                    continue
                _safe_setattr(space, "clip_start", 1.0)
                _safe_setattr(space, "clip_end", 50000.0)
                shading = getattr(space, "shading", None)
                if shading is not None and is_low:
                    shading_type = getattr(shading, "type", "")
                    if shading_type == "MATERIAL":
                        _safe_setattr(shading, "use_scene_lights", False)
                applied["viewports_updated"] += 1
            try:
                area.tag_redraw()
            except Exception:
                pass

    return applied
