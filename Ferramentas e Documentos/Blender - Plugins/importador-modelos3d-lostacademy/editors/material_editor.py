"""
Material & Texture Editor for Aion Assets.
Adjusts Principled BSDF shader properties and manages texture slot assignments.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

import bpy


class MaterialEditor:
    """Manages material shader properties and texture assignments."""

    @staticmethod
    def set_diffuse_image(mat: bpy.types.Material, image: bpy.types.Image) -> bool:
        """Assigns an image to the Base Color slot of a Principled BSDF node."""
        if not mat or not mat.use_nodes or not image:
            return False

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not bsdf:
            return False

        # Find or create TexImage node
        tex_node = None
        for link in bsdf.inputs["Base Color"].links:
            if link.from_node.type == "TEX_IMAGE":
                tex_node = link.from_node
                break

        if not tex_node:
            tex_node = nodes.new(type="ShaderNodeTexImage")
            tex_node.location = (-400, 100)
            links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

        tex_node.image = image
        return True

    @staticmethod
    def set_roughness(mat: bpy.types.Material, value: float) -> None:
        """Sets the specular roughness on the Principled BSDF node."""
        if not mat or not mat.use_nodes:
            return
        bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf and "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = max(0.0, min(1.0, value))

    @staticmethod
    def set_emission(mat: bpy.types.Material, strength: float) -> None:
        """Sets emission strength on the Principled BSDF node."""
        if not mat or not mat.use_nodes:
            return
        bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf and "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = max(0.0, strength)

    @staticmethod
    def set_two_sided(mat: bpy.types.Material, enable: bool) -> None:
        """Enables or disables backface culling."""
        if hasattr(mat, "use_backface_culling"):
            mat.use_backface_culling = not enable
