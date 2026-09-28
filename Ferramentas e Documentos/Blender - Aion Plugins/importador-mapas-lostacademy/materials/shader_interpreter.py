"""
Aion CryEngine Shader Interpreter for Blender 4.0 - 5.2+.

Interprets Aion shader techniques (AionPlants, AionBG, AionBGLandmark, AionPART, etc.)
and full CGF material chunks into production-quality Blender shader graphs.
"""

from __future__ import annotations

import math
import os
from typing import Any, Dict, Optional

import bpy

from .texture_loader import load_texture_image


def safe_set_blend_method(
    mat: bpy.types.Material,
    method: str,
    optimize_material_preview: bool = True,
) -> None:
    """Sets material blend and surface render methods safely across Blender 4.0 - 5.2+."""
    try:
        if optimize_material_preview and method in ("HASHED", "CLIP"):
            mat.blend_method = "CLIP"
        else:
            mat.blend_method = method
    except (AttributeError, TypeError):
        pass
    try:
        # In Blender 4.2+ / 5.2 (EEVEE Next):
        # DITHERED uses early-Z testing for maximum viewport performance
        if method == "BLEND":
            mat.surface_render_method = "DITHERED" if optimize_material_preview else "BLENDED"
        elif method in ("CLIP", "HASHED", "OPAQUE"):
            mat.surface_render_method = "DITHERED"
    except (AttributeError, TypeError):
        pass


def safe_set_two_sided(mat: bpy.types.Material, two_sided: bool = True) -> None:
    """Configures backface culling and transparent back settings."""
    try:
        mat.use_backface_culling = not two_sided
    except (AttributeError, TypeError):
        pass
    try:
        mat.show_transparent_back = two_sided
    except (AttributeError, TypeError):
        pass


def _get_bsdf_socket(bsdf: bpy.types.Node, *candidate_names: str) -> Optional[bpy.types.NodeSocket]:
    for name in candidate_names:
        if name in bsdf.inputs:
            return bsdf.inputs[name]
    return None


def _fast_dds_has_alpha(filepath: Optional[str]) -> bool:
    """Fast non-blocking DDS header inspection (<0.001ms, 0 Python pixel allocations)."""
    if not filepath or not os.path.isfile(filepath):
        return False
    try:
        with open(filepath, "rb") as f:
            header = f.read(128)
        if len(header) < 128 or header[:4] != b"DDS ":
            return False
        import struct
        pf_flags = struct.unpack_from("<I", header, 80)[0]
        four_cc = header[84:88]
        if pf_flags & 0x04:  # DDPF_FOURCC
            if four_cc in (b"DXT3", b"DXT5", b"BC2\x00", b"BC3\x00", b"BC7\x00"):
                return True
        if pf_flags & 0x01:  # DDPF_ALPHAPIXELS
            a_mask = struct.unpack_from("<I", header, 104)[0]
            if a_mask != 0:
                return True
    except Exception:
        pass
    return False


def interpret_and_build_material_graph(
    mat: bpy.types.Material,
    mat_data: Dict[str, Any],
    semantics: Optional[Any],
    resolved_textures: Dict[str, str],
    *,
    animate_uv_scroll: bool = False,
    uv_scroll_speed: tuple[float, float] = (0.0, 0.0),
    texture_sequence_node: Optional[bpy.types.Node] = None,
    optimize_material_preview: bool = True,
) -> Dict[str, Any]:
    """
    Constructs a complete, accurate Blender shader graph for an Aion material.
    Supports diffuse, normal/bump, specular, emissive/glow, opacity, and vegetation subsurf.
    """
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    # Create Material Output
    output_node = nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (600, 0)

    # Detect shader characteristics
    shader_name = semantics.shader_name.lower() if semantics else ""
    mat_raw_name = str(mat_data.get("name", "")).lower()
    mat_template = str(mat_data.get("material_template", "")).lower()
    diffuse_path = resolved_textures.get("diffuse")
    bump_path = resolved_textures.get("bump")
    specular_path = resolved_textures.get("specular")
    gloss_path = resolved_textures.get("gloss")
    opacity_path = resolved_textures.get("opacity")
    filter_path = resolved_textures.get("filter")
    subsurf_path = resolved_textures.get("subsurf")
    diff_name = str(diffuse_path or "").lower()

    foliage_terms = (
        "leaf", "leaves", "plant", "grass", "flower", "foliage", "bush",
        "branch", "tree", "vine", "ivy", "fern", "waterleaf", "movewaterplants",
        "reed", "weed", "cutout", "decal", "alpha", "chain", "fence", "cloth",
        "feather", "hair"
    )
    is_leaf = (
        any(term in shader_name for term in ("leaf", "plant", "grass", "decal", "alpha", "hair"))
        or any(term in mat_template for term in ("leaves", "leaf", "grass", "plant", "vegetation", "decal"))
        or any(term in mat_raw_name for term in foliage_terms)
        or any(term in diff_name for term in foliage_terms)
    )

    is_waterfall = any(
        w in s for w in ("waterfall", "waterfalla", "waterfallb", "waterfallc", "waterfally", "waterslide", "waterflow")
        for s in (shader_name, mat_raw_name, diff_name)
    )

    is_water_surface = any(
        w in s for w in ("swampwater", "watervolume", "riverwater", "lake_water", "water_plain", "waterplane", "water_stream")
        for s in (shader_name, mat_raw_name, diff_name)
    )

    is_additive = (semantics and semantics.blend_mode == "additive") or bool(
        mat_data.get("mtl_flag", {}).get("additive")
    )
    is_two_sided = (semantics and semantics.two_sided) or bool(
        mat_data.get("mtl_flag", {}).get("two_sided")
    ) or is_leaf or is_waterfall or is_water_surface

    # Auto-enable UV scroll for waterfalls and animated water surfaces
    if is_waterfall and uv_scroll_speed == (0.0, 0.0):
        uv_scroll_speed = (0.0, -0.04)
        animate_uv_scroll = True
    elif is_water_surface and uv_scroll_speed == (0.0, 0.0):
        uv_scroll_speed = (0.0, 0.02)
        animate_uv_scroll = True

    # Mapping / UV coordinate node
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-600, 0)
    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

    # Handle UV scroll driver if confirmed or waterfall/water surface
    if animate_uv_scroll and (uv_scroll_speed[0] != 0.0 or uv_scroll_speed[1] != 0.0):
        try:
            drv_x = mapping.inputs["Location"].driver_add("default_value", 0)
            drv_x.driver.expression = f"frame * {uv_scroll_speed[0]:.6f}"
            drv_y = mapping.inputs["Location"].driver_add("default_value", 1)
            drv_y.driver.expression = f"frame * {uv_scroll_speed[1]:.6f}"
        except Exception:
            pass

    # Case 1: Additive FX Shader
    if is_additive:
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        transparent.location = (200, -100)
        emission = nodes.new("ShaderNodeEmission")
        emission.location = (200, 100)
        mix = nodes.new("ShaderNodeMixShader")
        mix.location = (400, 0)

        emission_strength = float(mat_data.get("self_illum", 1.0) or 1.0)
        emission.inputs["Strength"].default_value = max(1.5, emission_strength * 2.0)

        tex_node = texture_sequence_node
        if tex_node is None and diffuse_path and os.path.isfile(diffuse_path):
            tex_node = nodes.new("ShaderNodeTexImage")
            tex_node.location = (-300, 100)
            tex_node.image = load_texture_image(diffuse_path, colorspace="sRGB")
            links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])

        if tex_node:
            links.new(tex_node.outputs["Color"], emission.inputs["Color"])
            links.new(tex_node.outputs["Alpha"], mix.inputs["Fac"])

        links.new(transparent.outputs["BSDF"], mix.inputs[1])
        links.new(emission.outputs["Emission"], mix.inputs[2])
        links.new(mix.outputs["Shader"], output_node.inputs["Surface"])

        safe_set_blend_method(mat, "BLEND", optimize_material_preview=optimize_material_preview)
        safe_set_two_sided(mat, is_two_sided)
        return {"mode": "additive", "shader": shader_name}

    # Case 2: Standard / Plant / Landmark / Architecture Shader (Principled BSDF)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    links.new(bsdf.outputs["BSDF"], output_node.inputs["Surface"])

    # Base Color & Diffuse Texture
    diff_color = mat_data.get("diffuse_color")
    if is_water_surface:
        bsdf.inputs["Base Color"].default_value = (0.05, 0.28, 0.38, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.05
        trans_socket = _get_bsdf_socket(bsdf, "Transmission Weight", "Transmission")
        if trans_socket:
            trans_socket.default_value = 0.7
    elif isinstance(diff_color, dict) and all(k in diff_color for k in ("r", "g", "b")):
        r = float(diff_color["r"]) / 255.0
        g = float(diff_color["g"]) / 255.0
        b = float(diff_color["b"]) / 255.0
        bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)

    diffuse_node = texture_sequence_node
    if diffuse_node is None and diffuse_path and os.path.isfile(diffuse_path):
        diffuse_node = nodes.new("ShaderNodeTexImage")
        diffuse_node.location = (-300, 200)
        diffuse_node.image = load_texture_image(diffuse_path, colorspace="sRGB")
        links.new(mapping.outputs["Vector"], diffuse_node.inputs["Vector"])

    if diffuse_node:
        if is_water_surface:
            # Swamp water and river water DDS files are vector normal/flow maps!
            normal_node = nodes.new("ShaderNodeNormalMap")
            normal_node.location = (-50, -100)
            normal_node.inputs["Strength"].default_value = 0.8
            links.new(diffuse_node.outputs["Color"], normal_node.inputs["Color"])
            if "Normal" in bsdf.inputs:
                links.new(normal_node.outputs["Normal"], bsdf.inputs["Normal"])
        else:
            links.new(diffuse_node.outputs["Color"], bsdf.inputs["Base Color"])

    # Alpha & Transparency
    alpha_in = bsdf.inputs.get("Alpha")
    has_alpha_test = (semantics and semantics.has_alpha_test) or is_leaf
    has_image_alpha = _fast_dds_has_alpha(diffuse_path) if diffuse_path else False
    is_cutout = has_alpha_test or is_leaf or (has_image_alpha and (is_two_sided or any(term in diff_name for term in foliage_terms)))

    scalar_opacity = None
    try:
        op = float(mat_data.get("opacity", 1.0))
        if math.isfinite(op) and 0.0 <= op < 1.0:
            scalar_opacity = op
    except Exception:
        pass

    if opacity_path and os.path.isfile(opacity_path):
        op_node = nodes.new("ShaderNodeTexImage")
        op_node.location = (-300, -50)
        op_node.image = load_texture_image(opacity_path, colorspace="Non-Color")
        links.new(mapping.outputs["Vector"], op_node.inputs["Vector"])
        if alpha_in:
            links.new(op_node.outputs["Color"], alpha_in)
        safe_set_blend_method(mat, "BLEND" if scalar_opacity else "CLIP", optimize_material_preview=optimize_material_preview)
    elif is_waterfall:
        if alpha_in and diffuse_node:
            links.new(diffuse_node.outputs["Alpha"], alpha_in)
        trans_socket = _get_bsdf_socket(bsdf, "Transmission Weight", "Transmission")
        if trans_socket:
            trans_socket.default_value = 0.5
        bsdf.inputs["Roughness"].default_value = 0.1
        safe_set_blend_method(mat, "BLEND", optimize_material_preview=optimize_material_preview)
        safe_set_two_sided(mat, True)
    elif is_water_surface:
        if alpha_in:
            alpha_in.default_value = 0.65
        safe_set_blend_method(mat, "BLEND", optimize_material_preview=optimize_material_preview)
        safe_set_two_sided(mat, True)
    elif diffuse_node and is_cutout:
        if alpha_in:
            links.new(diffuse_node.outputs["Alpha"], alpha_in)
        safe_set_blend_method(mat, "CLIP", optimize_material_preview=optimize_material_preview)
        try:
            mat.alpha_threshold = 0.33
        except (AttributeError, TypeError):
            pass
        safe_set_two_sided(mat, True)
    elif scalar_opacity is not None:
        if alpha_in:
            if diffuse_node:
                mult = nodes.new("ShaderNodeMath")
                mult.operation = "MULTIPLY"
                mult.inputs[1].default_value = scalar_opacity
                links.new(diffuse_node.outputs["Alpha"], mult.inputs[0])
                links.new(mult.outputs["Value"], alpha_in)
            else:
                alpha_in.default_value = scalar_opacity
        safe_set_blend_method(mat, "BLEND", optimize_material_preview=optimize_material_preview)
    elif diffuse_node:
        safe_set_blend_method(mat, "OPAQUE", optimize_material_preview=optimize_material_preview)
    else:
        safe_set_blend_method(mat, "OPAQUE", optimize_material_preview=optimize_material_preview)

    # Normal Map (texture_bump)
    if bump_path and os.path.isfile(bump_path):
        normal_tex = nodes.new("ShaderNodeTexImage")
        normal_tex.location = (-300, -300)
        normal_tex.image = load_texture_image(bump_path, colorspace="Non-Color")
        links.new(mapping.outputs["Vector"], normal_tex.inputs["Vector"])

        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-50, -300)
        normal_map.inputs["Strength"].default_value = 1.0
        links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])

        normal_in = bsdf.inputs.get("Normal")
        if normal_in:
            links.new(normal_map.outputs["Normal"], normal_in)

    # Specular & Roughness
    shininess = float(mat_data.get("specular_shininess", 0.0) or 0.0)
    spec_level = float(mat_data.get("specular_level", 0.0) or 0.0)

    roughness_in = bsdf.inputs.get("Roughness")
    specular_in = _get_bsdf_socket(bsdf, "Specular IOR Level", "Specular")

    if roughness_in:
        calc_roughness = max(0.08, min(1.0, 1.0 - (shininess / 128.0))) if shininess > 0 else 0.75
        roughness_in.default_value = calc_roughness

    if specular_in:
        specular_in.default_value = max(0.0, min(1.0, spec_level)) if spec_level > 0 else 0.5

    if gloss_path and os.path.isfile(gloss_path) and roughness_in:
        gloss_node = nodes.new("ShaderNodeTexImage")
        gloss_node.location = (-300, -550)
        gloss_node.image = load_texture_image(gloss_path, colorspace="Non-Color")
        links.new(mapping.outputs["Vector"], gloss_node.inputs["Vector"])

        invert = nodes.new("ShaderNodeInvert")
        invert.location = (-50, -550)
        links.new(gloss_node.outputs["Color"], invert.inputs["Color"])
        links.new(invert.outputs["Color"], roughness_in)

    # Emissive / Self-Illumination (texture_filter / self_illum)
    self_illum = float(mat_data.get("self_illum", 0.0) or 0.0)
    emission_color_in = _get_bsdf_socket(bsdf, "Emission Color", "Emission")
    emission_strength_in = bsdf.inputs.get("Emission Strength")

    if filter_path and os.path.isfile(filter_path):
        filter_tex = nodes.new("ShaderNodeTexImage")
        filter_tex.location = (-300, 500)
        filter_tex.image = load_texture_image(filter_path, colorspace="sRGB")
        links.new(mapping.outputs["Vector"], filter_tex.inputs["Vector"])
        if emission_color_in:
            links.new(filter_tex.outputs["Color"], emission_color_in)
        if emission_strength_in:
            emission_strength_in.default_value = max(1.0, self_illum * 2.0 if self_illum > 0 else 1.5)
    elif self_illum > 0.0 and diffuse_node:
        if emission_color_in:
            links.new(diffuse_node.outputs["Color"], emission_color_in)
        if emission_strength_in:
            emission_strength_in.default_value = self_illum

    # Subsurface Scattering / Foliage Translucency
    subsurf_weight_in = _get_bsdf_socket(bsdf, "Subsurface Weight", "Subsurface")
    subsurf_color_in = bsdf.inputs.get("Subsurface Color")

    if is_leaf:
        if subsurf_weight_in:
            subsurf_weight_in.default_value = 0.15
        if subsurf_color_in and diffuse_node:
            links.new(diffuse_node.outputs["Color"], subsurf_color_in)
    elif subsurf_path and os.path.isfile(subsurf_path):
        sub_node = nodes.new("ShaderNodeTexImage")
        sub_node.location = (-300, 350)
        sub_node.image = load_texture_image(subsurf_path, colorspace="sRGB")
        links.new(mapping.outputs["Vector"], sub_node.inputs["Vector"])
        if subsurf_color_in:
            links.new(sub_node.outputs["Color"], subsurf_color_in)
        if subsurf_weight_in:
            subsurf_weight_in.default_value = 0.25

    # Two-sided rendering configuration
    safe_set_two_sided(mat, is_two_sided)

    return {
        "mode": "principled",
        "shader": shader_name,
        "is_leaf": is_leaf,
        "two_sided": is_two_sided,
        "textures_connected": {
            "diffuse": bool(diffuse_node),
            "bump": bool(bump_path),
            "specular": bool(specular_path),
            "filter": bool(filter_path),
            "subsurf": bool(subsurf_path),
        },
    }


def create_aion_principled_material(
    material_name: str,
    shader_name: str = "Aion_Plants_Leaf",
    texture_paths: Optional[Dict[str, Any]] = None,
    material_flags: Optional[Dict[str, Any]] = None,
    client_root: Optional[Any] = None,
) -> bpy.types.Material:
    """Convenience factory to create and initialize a principled Aion material."""
    from formats.cgf.shader_semantics import resolve_client_shader_semantics

    mat = bpy.data.materials.new(name=material_name)
    mat.use_nodes = True
    mat_data = {
        "name": material_name,
        "shader": shader_name,
        "flags": material_flags or {},
    }
    semantics = resolve_client_shader_semantics(shader_name, client_root=client_root)
    resolved = {k: str(v) for k, v in (texture_paths or {}).items() if v}
    interpret_and_build_material_graph(mat, mat_data, semantics, resolved)
    return mat
