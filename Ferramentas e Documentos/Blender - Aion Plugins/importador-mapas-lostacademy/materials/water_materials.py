"""
Water, Ocean, Lava, and Liquid Surface Material Generator for Blender.
Supports animated flow drivers, dynamic procedural 4D ripples, and realistic transparency.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import bpy

from formats.level import (
    LIQUID_KIND_LAVA,
    LIQUID_PRESET_LAVA_EMISSIVE,
    LIQUID_PRESET_NORMAL,
    LIQUID_PRESET_TRANSPARENT,
    LiquidSurfaceRecipe,
)


def create_liquid_material(
    recipe: LiquidSurfaceRecipe,
    *,
    alpha: float = 0.45,
    tile_scale: float = 32.0,
    animate_flow: bool = True,
    flow_speed: float = 0.012,
) -> tuple[bpy.types.Material, dict[str, int]]:
    """Creates a high quality water, lava, or liquid surface material with live animated wave ripples."""
    mat_name = f"AION_Liquid_{recipe.selected_kind.lower()}_{recipe.selected_preset.lower()}"
    material = bpy.data.materials.new(mat_name)
    material.use_nodes = True

    try:
        material.blend_method = "BLEND"
    except (AttributeError, TypeError):
        pass
    try:
        material.surface_render_method = "BLENDED"
    except (AttributeError, TypeError):
        pass
    try:
        material.show_transparent_back = True
    except (AttributeError, TypeError):
        pass

    tree = material.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-600, 0)
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)
    mapping.inputs["Scale"].default_value = (float(tile_scale), float(tile_scale), 1.0)
    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

    # Continuous flow driver
    if animate_flow:
        try:
            drv_x = mapping.inputs["Location"].driver_add("default_value", 0)
            drv_x.driver.expression = f"frame * {flow_speed}"
            drv_y = mapping.inputs["Location"].driver_add("default_value", 1)
            drv_y.driver.expression = f"frame * {flow_speed * 0.6}"
        except Exception:
            pass

    loaded = _load_candidates(recipe.candidates)
    used = []

    if recipe.selected_kind == LIQUID_KIND_LAVA or recipe.selected_preset == LIQUID_PRESET_LAVA_EMISSIVE:
        used.extend(_wire_lava(nodes, links, mapping, output, loaded, recipe.selected_preset))
    else:
        used.extend(_wire_water(nodes, links, mapping, output, loaded, recipe.selected_preset, alpha, tile_scale))

    return material, {
        "textures_loaded": len(loaded),
        "textures_used": len({item["candidate"].texture for item in used}),
    }


def _load_candidates(candidates):
    loaded = []
    for candidate in candidates:
        if not candidate.exists:
            continue
        try:
            image = bpy.data.images.load(candidate.resolved_path, check_existing=True)
            loaded.append({"candidate": candidate, "image": image})
        except Exception:
            continue
    return loaded


def _wire_water(nodes, links, mapping, output, loaded, preset, alpha, tile_scale=32.0):
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    bsdf.inputs["Alpha"].default_value = max(0.0, min(1.0, float(alpha)))
    bsdf.inputs["Base Color"].default_value = (0.05, 0.32, 0.46, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.05
    try:
        bsdf.inputs["IOR"].default_value = 1.333
    except Exception:
        pass
    try:
        bsdf.inputs["Transmission Weight"].default_value = 0.65
    except Exception:
        pass

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    used = []
    texture = _first_loaded(
        loaded,
        roles=("diffuse_base", "caustics", "reflection"),
        kinds=("WATER", "SWAMP", "MAGIC", "UNKNOWN"),
    )
    norm_from_tex = None
    if texture:
        tex = nodes.new("ShaderNodeTexImage")
        tex.location = (-200, 200)
        tex.image = texture["image"]
        links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        tex_name = str(texture["candidate"].texture).lower()
        if any(x in tex_name for x in ("swamp", "norm", "ddn", "bump", "flow", "vector")):
            norm_from_tex = nodes.new("ShaderNodeNormalMap")
            norm_from_tex.location = (-20, 200)
            links.new(tex.outputs["Color"], norm_from_tex.inputs["Color"])
        else:
            links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        used.append(texture)

    # Multi-layer animated flowing ripples (flowing caustics + wave bump)
    try:
        tex_coord = next((n for n in nodes if n.type == "TEX_COORD"), None)
        if tex_coord is None:
            tex_coord = nodes.new("ShaderNodeTexCoord")
            tex_coord.location = (-950, -250)

        # Layer 1 (Primary flow direction)
        map1 = nodes.new("ShaderNodeMapping")
        map1.location = (-650, -150)
        map1.inputs["Scale"].default_value = (float(tile_scale) * 1.5, float(tile_scale) * 1.5, 1.0)
        links.new(tex_coord.outputs["UV"], map1.inputs["Vector"])
        drv1_x = map1.inputs["Location"].driver_add("default_value", 0)
        drv1_x.driver.expression = "frame * 0.02"
        drv1_y = map1.inputs["Location"].driver_add("default_value", 1)
        drv1_y.driver.expression = "frame * 0.012"

        noise1 = nodes.new("ShaderNodeTexNoise")
        noise1.location = (-400, -150)
        noise1.noise_dimensions = "3D"
        noise1.inputs["Scale"].default_value = 4.0
        noise1.inputs["Detail"].default_value = 4.0
        noise1.inputs["Roughness"].default_value = 0.5
        links.new(map1.outputs["Vector"], noise1.inputs["Vector"])

        # Layer 2 (Cross ripple flow for organic water interference)
        map2 = nodes.new("ShaderNodeMapping")
        map2.location = (-650, -450)
        map2.inputs["Scale"].default_value = (float(tile_scale) * 2.2, float(tile_scale) * 2.2, 1.0)
        links.new(tex_coord.outputs["UV"], map2.inputs["Vector"])
        drv2_x = map2.inputs["Location"].driver_add("default_value", 0)
        drv2_x.driver.expression = "-frame * 0.016"
        drv2_y = map2.inputs["Location"].driver_add("default_value", 1)
        drv2_y.driver.expression = "frame * 0.022"

        noise2 = nodes.new("ShaderNodeTexNoise")
        noise2.location = (-400, -450)
        noise2.noise_dimensions = "3D"
        noise2.inputs["Scale"].default_value = 6.0
        noise2.inputs["Detail"].default_value = 4.0
        noise2.inputs["Roughness"].default_value = 0.6
        links.new(map2.outputs["Vector"], noise2.inputs["Vector"])

        mix_waves = nodes.new("ShaderNodeMix")
        mix_waves.data_type = "FLOAT"
        mix_waves.location = (-150, -300)
        mix_waves.inputs[0].default_value = 0.5
        links.new(noise1.outputs["Fac"], mix_waves.inputs[2])
        links.new(noise2.outputs["Fac"], mix_waves.inputs[3])

        bump = nodes.new("ShaderNodeBump")
        bump.location = (50, -300)
        bump.inputs["Strength"].default_value = 0.35
        bump.inputs["Distance"].default_value = 0.15
        links.new(mix_waves.outputs[0], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    except Exception:
        pass

    return used


def _wire_lava(nodes, links, mapping, output, loaded, preset):
    texture = _first_loaded(
        loaded,
        roles=("emission_glow", "diffuse_base", "caustics"),
        kinds=("LAVA", "UNKNOWN"),
    )
    emission = nodes.new("ShaderNodeEmission")
    emission.location = (200, 0)
    emission.inputs["Color"].default_value = (1.0, 0.25, 0.03, 1.0)
    emission.inputs["Strength"].default_value = 4.0 if preset == LIQUID_PRESET_LAVA_EMISSIVE else 2.5
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    if not texture:
        return []

    tex = nodes.new("ShaderNodeTexImage")
    tex.location = (-200, 0)
    tex.image = texture["image"]
    links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], emission.inputs["Color"])
    return [texture]


def _first_loaded(loaded, *, roles, kinds):
    for kind in kinds:
        for role in roles:
            for item in loaded:
                candidate = item["candidate"]
                if candidate.role == role and candidate.liquid_kind == kind:
                    return item
    for role in roles:
        for item in loaded:
            if item["candidate"].role == role:
                return item
    return None
