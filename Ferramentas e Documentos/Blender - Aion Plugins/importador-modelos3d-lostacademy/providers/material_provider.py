"""
Bidirectional Material Provider for Aion Assets.
Translates CryEngine Mtl chunks to Blender 4.0 - 5.2 Principled BSDF shader trees
and extracts modified shader parameters back to Aion Mtl binary structures.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional

import bpy
from .base_provider import IMaterialProvider
from .texture_provider import TextureProvider


class MaterialProvider(IMaterialProvider):
    """Manages Principled BSDF node tree construction and extraction."""

    def __init__(self, texture_provider: TextureProvider):
        self.tex_provider = texture_provider
        self._material_cache: Dict[str, bpy.types.Material] = {}

    def create_material(
        self,
        material_name: str,
        mtl_chunk: Dict[str, Any],
        resolved_textures: Optional[Dict[str, Optional[Path]]] = None,
    ) -> bpy.types.Material:
        """Constructs a Principled BSDF material tree matching Aion shader properties."""
        clean_name = material_name.split("(")[0].strip() or "Aion_Material"
        cached = self._material_cache.get(clean_name)
        if cached and cached.name in bpy.data.materials:
            return cached

        mat = bpy.data.materials.new(name=clean_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Output node
        out_node = nodes.new(type="ShaderNodeOutputMaterial")
        out_node.location = (400, 0)

        # Principled BSDF node
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

        # Extract texture names from Mtl chunk
        diff_info = mtl_chunk.get("texture_diffuse") or {}
        bump_info = mtl_chunk.get("texture_bump") or {}
        spec_info = mtl_chunk.get("texture_specular") or {}
        opac_info = mtl_chunk.get("texture_opacity") or {}

        diff_path = diff_info.get("long_name") or diff_info.get("name") or ""
        bump_path = bump_info.get("long_name") or bump_info.get("name") or ""
        spec_path = spec_info.get("long_name") or spec_info.get("name") or ""
        opac_path = opac_info.get("long_name") or opac_info.get("name") or ""

        # 1. Diffuse / Base Color
        if diff_path:
            diff_img = self.tex_provider.get_texture_image(diff_path)
            if diff_img:
                tex_node = nodes.new(type="ShaderNodeTexImage")
                tex_node.location = (-400, 100)
                tex_node.image = diff_img
                links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

                # Connect alpha if present
                if opac_path or diff_img.channels == 4:
                    links.new(tex_node.outputs["Alpha"], bsdf.inputs["Alpha"])
                    # Alpha blend / clip mode in Eevee / Cycles
                    if hasattr(mat, "blend_method"):
                        mat.blend_method = "CLIP"
                    if hasattr(mat, "shadow_method"):
                        mat.shadow_method = "CLIP"

        # 2. Normal / Bump Map
        if bump_path:
            bump_img = self.tex_provider.get_texture_image(bump_path)
            if bump_img:
                bump_img.colorspace_settings.name = "Non-Color"
                bump_tex_node = nodes.new(type="ShaderNodeTexImage")
                bump_tex_node.location = (-700, -200)
                bump_tex_node.image = bump_img

                norm_node = nodes.new(type="ShaderNodeNormalMap")
                norm_node.location = (-300, -200)
                links.new(bump_tex_node.outputs["Color"], norm_node.inputs["Color"])
                links.new(norm_node.outputs["Normal"], bsdf.inputs["Normal"])

        # 3. Specular / Shininess
        shininess = float(mtl_chunk.get("specular_shininess", 10.0) or 10.0)
        # Convert CryEngine shininess (0..100) to Blender roughness (1..0)
        roughness = max(0.05, min(1.0, 1.0 - (shininess / 100.0)))
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness

        # 4. Self-Illumination / Emission
        self_illum = float(mtl_chunk.get("self_illum", 0.0) or 0.0)
        if self_illum > 0.0 and "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = self_illum
            if "Emission Color" in bsdf.inputs and diff_path:
                # Link diffuse to emission
                pass

        # 5. Two-sided flag
        flags = mtl_chunk.get("mtl_flag", {})
        if isinstance(flags, dict) and flags.get("two_sided"):
            if hasattr(mat, "use_backface_culling"):
                mat.use_backface_culling = False

        self._material_cache[clean_name] = mat
        return mat

    def extract_material_params(self, mat: bpy.types.Material) -> Dict[str, Any]:
        """Reads modified shader node values back into an Aion Mtl dictionary."""
        params: Dict[str, Any] = {
            "name": mat.name,
            "diffuse_texture": "",
            "bump_texture": "",
            "specular_texture": "",
            "opacity_texture": "",
            "roughness": 0.5,
            "self_illum": 0.0,
            "two_sided": False,
        }

        if not mat.use_nodes or not mat.node_tree:
            return params

        nodes = mat.node_tree.nodes
        bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            # Check Base Color link
            base_color_link = bsdf.inputs["Base Color"].links
            if base_color_link and base_color_link[0].from_node.type == "TEX_IMAGE":
                img = base_color_link[0].from_node.image
                if img:
                    params["diffuse_texture"] = img.filepath or img.name

            # Check Normal Map link
            normal_link = bsdf.inputs["Normal"].links
            if normal_link and normal_link[0].from_node.type == "NORMAL_MAP":
                nmap_node = normal_link[0].from_node
                color_link = nmap_node.inputs["Color"].links
                if color_link and color_link[0].from_node.type == "TEX_IMAGE":
                    img = color_link[0].from_node.image
                    if img:
                        params["bump_texture"] = img.filepath or img.name

            # Roughness
            if "Roughness" in bsdf.inputs:
                params["roughness"] = float(bsdf.inputs["Roughness"].default_value)

            # Emission
            if "Emission Strength" in bsdf.inputs:
                params["self_illum"] = float(bsdf.inputs["Emission Strength"].default_value)

        if hasattr(mat, "use_backface_culling"):
            params["two_sided"] = not mat.use_backface_culling

        return params
