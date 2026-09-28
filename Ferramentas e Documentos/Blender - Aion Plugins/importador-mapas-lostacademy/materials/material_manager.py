"""
Material Manager for Aion Blender Toolkit.
Handles material caching, slot allocation, texture path resolution, and metadata attachment.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import bpy

from core.pak_engine import get_pak_resolver
from formats.cgf.shader_semantics import resolve_client_shader_semantics
from formats.cgf.texture_sequences import resolve_texture_sequence
from .shader_interpreter import interpret_and_build_material_graph


_MATERIAL_CACHE: Dict[str, str] = {}


def clean_material_cache() -> None:
    _MATERIAL_CACHE.clear()


def _clean_texture_path(value: Any) -> str:
    if not value:
        return ""
    return str(value).strip().strip("\x00").replace("/", os.sep).replace("\\", os.sep)


def _client_root_from_path(path_str: str) -> Optional[str]:
    path = os.path.abspath(path_str)
    if ".aion_cache" in path.lower():
        idx = path.lower().find(".aion_cache")
        root = path[:idx].rstrip("\\/")
        if root:
            return root
    parts = path.split(os.sep)
    for idx, part in enumerate(parts):
        if part.lower() in ("levels", "objects", "textures", "shaders", "effects"):
            if idx > 0:
                return os.sep.join(parts[:idx])
    return None


def resolve_texture_slot(
    texture_dict: Optional[Dict[str, Any]],
    model_path: str,
    client_root: Optional[str],
) -> str:
    """Resolves an Aion texture slot dictionary to an absolute file path."""
    if not isinstance(texture_dict, dict):
        return ""

    tex_name = _clean_texture_path(texture_dict.get("name"))
    tex_long = _clean_texture_path(texture_dict.get("long_name"))
    model_dir = os.path.dirname(model_path) if os.path.isfile(model_path) else model_path

    # Check direct disk paths first
    if tex_long and client_root:
        disk_path = os.path.normcase(os.path.abspath(os.path.join(client_root, tex_long)))
        if os.path.isfile(disk_path):
            return disk_path

    if tex_name and model_dir:
        disk_path = os.path.normcase(os.path.abspath(os.path.join(model_dir, tex_name)))
        if os.path.isfile(disk_path):
            return disk_path

    # Use PAK resolver
    if client_root:
        resolver = get_pak_resolver(client_root)
        if resolver:
            if tex_long:
                resolved = resolver.resolve_resource(tex_long)
                if resolved and os.path.isfile(str(resolved)):
                    return os.path.normcase(os.path.abspath(str(resolved)))
            if tex_name:
                resolved = resolver.resolve_resource(tex_name)
                if resolved and os.path.isfile(str(resolved)):
                    return os.path.normcase(os.path.abspath(str(resolved)))

    if tex_long and client_root:
        return os.path.normcase(os.path.abspath(os.path.join(client_root, tex_long)))
    if tex_name and model_dir:
        return os.path.normcase(os.path.abspath(os.path.join(model_dir, tex_name)))
    return ""


def get_or_create_aion_material(
    mat_data: Dict[str, Any],
    model_path: str,
    *,
    client_root: Optional[str] = None,
    animate_texture_sequences: bool = True,
    texture_animation_fps: int = 10,
    animate_shader_uv_scroll: bool = True,
) -> bpy.types.Material:
    """
    Retrieves or creates a Blender material for an Aion CGF material chunk.
    """
    if client_root is None:
        client_root = _client_root_from_path(model_path)

    raw_name = mat_data.get("name", "AION_MAT")
    shader_hint = ""
    # Extract shader name from parentheses e.g. "Material #5(Aion_BG_Base)/mat_stone"
    if "(" in raw_name and ")" in raw_name:
        shader_hint = raw_name[raw_name.find("(") + 1 : raw_name.find(")")].strip()

    # Resolve all texture slots
    resolved_textures: Dict[str, str] = {
        "diffuse": resolve_texture_slot(mat_data.get("texture_diffuse"), model_path, client_root),
        "bump": resolve_texture_slot(mat_data.get("texture_bump"), model_path, client_root),
        "specular": resolve_texture_slot(mat_data.get("texture_specular"), model_path, client_root),
        "gloss": resolve_texture_slot(mat_data.get("texture_gloss"), model_path, client_root),
        "opacity": resolve_texture_slot(mat_data.get("texture_opacity"), model_path, client_root),
        "filter": resolve_texture_slot(mat_data.get("texture_filter"), model_path, client_root),
        "subsurf": resolve_texture_slot(mat_data.get("texture_subsurf"), model_path, client_root),
        "detail": resolve_texture_slot(mat_data.get("texture_detail"), model_path, client_root),
    }

    # Resolve shader semantics
    semantics = None
    if client_root and shader_hint:
        semantics = resolve_client_shader_semantics(client_root, shader_hint)

    # Build unique visual fingerprint cache key (independent of model_path for massive deduplication)
    diffuse_tex = resolved_textures.get("diffuse") or ""
    bump_tex = resolved_textures.get("bump") or ""
    specular_tex = resolved_textures.get("specular") or ""
    gloss_tex = resolved_textures.get("gloss") or ""
    opacity_tex = resolved_textures.get("opacity") or ""
    filter_tex = resolved_textures.get("filter") or ""
    shader_name = semantics.shader_name if semantics else shader_hint

    cache_key = "|".join([
        shader_name.lower(),
        diffuse_tex.lower(),
        bump_tex.lower(),
        specular_tex.lower(),
        gloss_tex.lower(),
        opacity_tex.lower(),
        filter_tex.lower(),
        repr(mat_data.get("opacity")),
        repr(mat_data.get("diffuse_color")),
        repr(mat_data.get("specular_shininess")),
        repr(mat_data.get("specular_level")),
        repr(mat_data.get("self_illum")),
        repr(mat_data.get("mtl_flag", {}).get("two_sided")),
        repr(mat_data.get("mtl_flag", {}).get("additive")),
    ])

    if cache_key in _MATERIAL_CACHE:
        mat_name = _MATERIAL_CACHE[cache_key]
        try:
            mat = bpy.data.materials.get(mat_name)
            if mat is not None:
                _ = mat.name
                return mat
        except (ReferenceError, Exception):
            _MATERIAL_CACHE.pop(cache_key, None)

    # Generate clean, informative datablock name
    short_hash = hashlib.md5(cache_key.encode("utf-8")).hexdigest()[:6]
    if diffuse_tex:
        base_tex_name = Path(diffuse_tex).stem
    else:
        base_tex_name = raw_name.split("(")[0].strip() or "AionMat"
    material_name = f"Aion_{base_tex_name}_{short_hash}"

    mat = bpy.data.materials.new(material_name)
    _MATERIAL_CACHE[cache_key] = mat.name

    # Check for animated texture sequence
    diffuse_info = mat_data.get("texture_diffuse") or {}
    sequence = (
        resolve_texture_sequence(
            diffuse_info,
            cgf_path=model_path,
            client_root=client_root,
            fps=texture_animation_fps,
        )
        if animate_texture_sequences and diffuse_info
        else None
    )

    uv_scroll_speed = (0.0, 0.0)
    if animate_shader_uv_scroll and semantics and semantics.uv_scroll_confirmed:
        uv_scroll_speed = (
            float(semantics.uv_scroll_speed_x or 0.0),
            float(semantics.uv_scroll_speed_y or 0.0),
        )

    # Build the shader graph
    result = interpret_and_build_material_graph(
        mat,
        mat_data,
        semantics,
        resolved_textures,
        animate_uv_scroll=animate_shader_uv_scroll,
        uv_scroll_speed=uv_scroll_speed,
    )

    # Attach Aion metadata to the material datablock
    mat["aion_material_name"] = raw_name
    mat["aion_shader_name"] = shader_hint
    mat["aion_diffuse_texture"] = resolved_textures.get("diffuse", "")
    mat["aion_bump_texture"] = resolved_textures.get("bump", "")
    mat["aion_filter_texture"] = resolved_textures.get("filter", "")
    mat["aion_is_two_sided"] = result.get("two_sided", False)
    mat["aion_is_leaf"] = result.get("is_leaf", False)

    return mat
