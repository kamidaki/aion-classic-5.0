"""
Terrain Material and Blend Shader Generator for Blender.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import bpy

from core.pak_engine import get_pak_resolver
from formats.level import SurfaceType, TerrainMaterialInventory


@dataclass(frozen=True)
class TerrainDetailTextureReference:
    raw_path: str
    normalized_relative_path: str
    resolved_path: str | None
    exists: bool


@dataclass(frozen=True)
class TerrainTextureNodeResult:
    texture_load_requested: bool
    texture_images_loaded: int
    texture_images_failed: int
    texture_nodes_created: int


@dataclass(frozen=True)
class TerrainMaterialSlot:
    terrain_material_index: int
    slot_index: int
    name: str
    surface_type: Optional[SurfaceType]
    material: Optional[bpy.types.Material] = None


def resolve_terrain_detail_texture(
    client_root: str | Path | None,
    detail_texture: str | None,
) -> TerrainDetailTextureReference:
    raw_path = detail_texture or ""
    normalized_relative_path = raw_path.replace("\\", "/").lstrip("/")

    if not client_root or not normalized_relative_path:
        return TerrainDetailTextureReference(
            raw_path=raw_path,
            normalized_relative_path=normalized_relative_path,
            resolved_path=None,
            exists=False,
        )

    root_path = Path(client_root)
    resolved_path = root_path / Path(*normalized_relative_path.split("/"))

    if not resolved_path.is_file():
        parts = normalized_relative_path.split("/")
        if len(parts) >= 2 and parts[0].lower() == "levels":
            level_name = parts[1]
            sub_path = Path(*parts[2:])
            cand_cache = root_path / "levels" / level_name / ".aion_cache" / sub_path
            if cand_cache.is_file():
                resolved_path = cand_cache
            else:
                file_name = parts[-1]
                cand_detail = root_path / "levels" / level_name / ".aion_cache" / "detail" / file_name
                if cand_detail.is_file():
                    resolved_path = cand_detail

    if not resolved_path.is_file():
        resolver = get_pak_resolver(root_path)
        if resolver is not None:
            pak_res = resolver.resolve_resource(normalized_relative_path)
            if pak_res and pak_res.is_file():
                resolved_path = pak_res

    exists = resolved_path.is_file()
    return TerrainDetailTextureReference(
        raw_path=raw_path,
        normalized_relative_path=normalized_relative_path,
        resolved_path=str(resolved_path) if exists else str(resolved_path),
        exists=exists,
    )


def create_terrain_materials(
    mesh: bpy.types.Mesh,
    inventory: TerrainMaterialInventory,
    client_root: str | Path | None,
) -> tuple[TerrainMaterialSlot, ...]:
    slots = []
    for usage in inventory.used_material_indices:
        st = usage.surface_type
        tex_ref = resolve_terrain_detail_texture(client_root, st.detail_texture if st else None)
        slot_name = f"AION_Terrain_{usage.terrain_material_index:02d}_{st.name if st and st.name else 'Material'}"

        mat = bpy.data.materials.new(slot_name)
        mat.use_nodes = True
        mat["aion_terrain_material_index"] = usage.terrain_material_index
        mat["aion_detail_texture"] = tex_ref.normalized_relative_path
        mat["aion_detail_texture_resolved"] = tex_ref.resolved_path or ""
        mat["aion_detail_texture_exists"] = tex_ref.exists

        # Procedural distinct tint for viewport
        hue = (float(usage.terrain_material_index) * 0.618033988749895) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 0.5, 0.8)
        mat.diffuse_color = (r, g, b, 1.0)

        # Build basic Principled BSDF
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (100, 0)
        bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.85
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        if tex_ref.exists and tex_ref.resolved_path:
            try:
                img = bpy.data.images.load(tex_ref.resolved_path, check_existing=True)
                tex_node = nodes.new("ShaderNodeTexImage")
                tex_node.location = (-250, 0)
                tex_node.image = img
                links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
            except Exception:
                pass

        mesh.materials.append(mat)
        slots.append(
            TerrainMaterialSlot(
                terrain_material_index=usage.terrain_material_index,
                slot_index=len(slots),
                name=slot_name,
                surface_type=st,
                material=mat,
            )
        )

    return tuple(slots)
