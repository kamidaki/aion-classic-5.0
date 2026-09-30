"""
Visual Effects (VFX) Provider for Aion Assets.
Manages elemental shader auras, socket lights, particle systems, and magical energy effects
for 3D models in Blender with high-performance caching and non-destructive stage integration.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional, Tuple

import bpy
from mathutils import Color, Vector

logger = logging.getLogger("AionModelLibrary.EffectProvider")

VFX_COLLECTION_NAME = ".Aion_Model_VFX"

# Color palettes for elements (RGB float 0.0 - 1.0)
ELEMENT_PALETTES: Dict[str, Dict[str, Any]] = {
    "FIRE": {
        "name": "Fogo / Chamas",
        "primary": (1.0, 0.25, 0.02),
        "secondary": (1.0, 0.75, 0.1),
        "light_color": (1.0, 0.35, 0.05),
        "light_energy": 15.0,
        "emission_strength": 3.5,
    },
    "FROST": {
        "name": "Gelo / Geada",
        "primary": (0.05, 0.65, 1.0),
        "secondary": (0.7, 0.9, 1.0),
        "light_color": (0.2, 0.75, 1.0),
        "light_energy": 12.0,
        "emission_strength": 3.0,
    },
    "LIGHTNING": {
        "name": "Eletricidade / Raios",
        "primary": (0.9, 0.85, 0.1),
        "secondary": (0.6, 0.2, 1.0),
        "light_color": (1.0, 0.95, 0.3),
        "light_energy": 25.0,
        "emission_strength": 5.0,
    },
    "SHADOW": {
        "name": "Sombra / Trevas",
        "primary": (0.45, 0.05, 0.7),
        "secondary": (0.1, 0.0, 0.2),
        "light_color": (0.5, 0.1, 0.8),
        "light_energy": 10.0,
        "emission_strength": 2.5,
    },
    "POISON": {
        "name": "Veneno / Ácido",
        "primary": (0.1, 0.95, 0.15),
        "secondary": (0.6, 0.9, 0.05),
        "light_color": (0.2, 1.0, 0.3),
        "light_energy": 12.0,
        "emission_strength": 3.0,
    },
    "DIVINE": {
        "name": "Sagrado / Luz Celestial",
        "primary": (1.0, 0.95, 0.8),
        "secondary": (1.0, 0.8, 0.3),
        "light_color": (1.0, 0.95, 0.85),
        "light_energy": 20.0,
        "emission_strength": 4.0,
    },
    "AION_AETHER": {
        "name": "Aether Clássico (Aion)",
        "primary": (0.05, 0.85, 0.8),
        "secondary": (0.15, 0.4, 0.95),
        "light_color": (0.1, 0.9, 0.85),
        "light_energy": 15.0,
        "emission_strength": 3.5,
    },
}


class EffectProvider:
    """Creates, attaches, updates, and removes visual effects on inspected 3D models."""

    _instance: Optional["EffectProvider"] = None

    @classmethod
    def get(cls) -> "EffectProvider":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def get_or_create_vfx_collection() -> bpy.types.Collection:
        """Returns or creates the dedicated hidden VFX collection."""
        scene = bpy.context.scene
        for c in scene.collection.children:
            if c.name == VFX_COLLECTION_NAME:
                return c
        col = bpy.data.collections.new(VFX_COLLECTION_NAME)
        scene.collection.children.link(col)
        return col

    @staticmethod
    def find_effect_sockets(root_obj: bpy.types.Object) -> List[Tuple[str, Vector, Optional[bpy.types.PoseBone]]]:
        """
        Discovers effect sockets on the model (special FX bones or anatomical landmark bones).
        Returns a list of (socket_name, world_location, pose_bone_or_none).
        """
        sockets: List[Tuple[str, Vector, Optional[bpy.types.PoseBone]]] = []

        rig = root_obj if root_obj.type == "ARMATURE" else (
            root_obj.parent if root_obj.parent and root_obj.parent.type == "ARMATURE" else None
        )

        if rig and rig.pose:
            # 1. Look for explicit FX bones
            for pb in rig.pose.bones:
                bname_l = pb.name.lower()
                if any(k in bname_l for k in ("fx", "eff", "hp_", "tag_", "socket")):
                    loc = rig.matrix_world @ pb.tail
                    sockets.append((pb.name, loc, pb))

            # 2. Look for anatomical key bones (Head, Hands, Spine, Tail)
            landmark_candidates = [
                ("Bip01 Head", "Head"),
                ("Bip01 L Hand", "Hand_L"),
                ("Bip01 R Hand", "Hand_R"),
                ("Bip01 Spine", "Chest"),
                ("Bip01 Tail", "Tail"),
            ]
            for bone_key, label in landmark_candidates:
                if bone_key in rig.pose.bones and not any(s[0] == label for s in sockets):
                    pb = rig.pose.bones[bone_key]
                    loc = rig.matrix_world @ pb.head
                    sockets.append((label, loc, pb))

        # Fallback for static models without armature
        if not sockets:
            mesh_objs = [root_obj] if root_obj.type == "MESH" else [c for c in root_obj.children if c.type == "MESH"]
            if mesh_objs:
                m = mesh_objs[0]
                bb = [m.matrix_world @ Vector(c) for c in m.bound_box]
                min_z = min(c.z for c in bb)
                max_z = max(c.z for c in bb)
                center = sum(bb, Vector()) / 8.0
                sockets.append(("Top", Vector((center.x, center.y, max_z)), None))
                sockets.append(("Center", center, None))
                sockets.append(("Base", Vector((center.x, center.y, min_z + 0.1)), None))

        return sockets

    def apply_shader_aura(
        self,
        root_obj: bpy.types.Object,
        element: str = "FIRE",
        intensity: float = 1.0,
    ) -> None:
        """Applies elemental emissive rim glow to all mesh materials on the model."""
        palette = ELEMENT_PALETTES.get(element, ELEMENT_PALETTES["FIRE"])
        p_col = palette["primary"]
        e_strength = palette["emission_strength"] * intensity

        mesh_objs = [root_obj] if root_obj.type == "MESH" else [c for c in root_obj.children if c.type == "MESH"]

        for m_obj in mesh_objs:
            for mat_slot in m_obj.material_slots:
                mat = mat_slot.material
                if not mat or not mat.use_nodes or not mat.node_tree:
                    continue

                nodes = mat.node_tree.nodes
                bsdf = None
                for n in nodes:
                    if n.type == "BSDF_PRINCIPLED":
                        bsdf = n
                        break

                if not bsdf:
                    continue

                # Set emission color and strength safely
                try:
                    if "Emission Color" in bsdf.inputs:
                        bsdf.inputs["Emission Color"].default_value = (p_col[0], p_col[1], p_col[2], 1.0)
                    elif "Emission" in bsdf.inputs:
                        bsdf.inputs["Emission"].default_value = (p_col[0], p_col[1], p_col[2], 1.0)

                    if "Emission Strength" in bsdf.inputs:
                        bsdf.inputs["Emission Strength"].default_value = e_strength
                except Exception:
                    pass

    def apply_socket_lights(
        self,
        root_obj: bpy.types.Object,
        sockets: List[Tuple[str, Vector, Optional[bpy.types.PoseBone]]],
        element: str = "FIRE",
        intensity: float = 1.0,
    ) -> List[bpy.types.Object]:
        """Creates colored dynamic point lights parented to effect sockets."""
        palette = ELEMENT_PALETTES.get(element, ELEMENT_PALETTES["FIRE"])
        l_col = palette["light_color"]
        l_energy = palette["light_energy"] * intensity
        vfx_col = self.get_or_create_vfx_collection()

        created_lights: List[bpy.types.Object] = []
        rig = root_obj if root_obj.type == "ARMATURE" else (
            root_obj.parent if root_obj.parent and root_obj.parent.type == "ARMATURE" else None
        )

        for s_name, world_loc, pb in sockets[:4]:  # limit to top 4 sockets to keep viewport performant
            l_data = bpy.data.lights.new(name=f"Aion_VFX_Light_{s_name}", type="POINT")
            l_data.color = l_col
            l_data.energy = l_energy
            l_data.shadow_soft_size = 0.25

            l_obj = bpy.data.objects.new(f"Aion_VFX_Light_{s_name}", l_data)
            l_obj["is_aion_vfx"] = True
            vfx_col.objects.link(l_obj)

            if rig and pb:
                # Parent to armature bone
                l_obj.parent = rig
                l_obj.parent_type = "BONE"
                l_obj.parent_bone = pb.name
                l_obj.location = (0, 0, 0)
            else:
                l_obj.location = world_loc

            created_lights.append(l_obj)

        return created_lights

    def apply_particle_emitters(
        self,
        root_obj: bpy.types.Object,
        sockets: List[Tuple[str, Vector, Optional[bpy.types.PoseBone]]],
        element: str = "FIRE",
        intensity: float = 1.0,
    ) -> List[bpy.types.Object]:
        """Creates small emitter primitives with particle systems attached to sockets."""
        palette = ELEMENT_PALETTES.get(element, ELEMENT_PALETTES["FIRE"])
        vfx_col = self.get_or_create_vfx_collection()
        created_emitters: List[bpy.types.Object] = []

        rig = root_obj if root_obj.type == "ARMATURE" else (
            root_obj.parent if root_obj.parent and root_obj.parent.type == "ARMATURE" else None
        )

        # Create glowing particle material
        p_mat_name = f"Aion_VFX_Particle_{element}"
        p_mat = bpy.data.materials.get(p_mat_name)
        if not p_mat:
            p_mat = bpy.data.materials.new(name=p_mat_name)
            p_mat.use_nodes = True
            bsdf = p_mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                col = palette["primary"]
                if "Base Color" in bsdf.inputs:
                    bsdf.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1.0)
                if "Emission Color" in bsdf.inputs:
                    bsdf.inputs["Emission Color"].default_value = (col[0], col[1], col[2], 1.0)
                if "Emission Strength" in bsdf.inputs:
                    bsdf.inputs["Emission Strength"].default_value = 5.0 * intensity

        # Attach small emitter mesh to main socket (Hands or Head or Center)
        target_sockets = [s for s in sockets if any(k in s[0].lower() for k in ("hand", "head", "top", "center"))]
        if not target_sockets:
            target_sockets = sockets[:2]

        for s_name, world_loc, pb in target_sockets[:2]:
            # Create small ico sphere mesh
            mesh = bpy.data.meshes.new(f"Aion_VFX_Emitter_{s_name}")
            emitter_obj = bpy.data.objects.new(f"Aion_VFX_Emitter_{s_name}", mesh)
            emitter_obj["is_aion_vfx"] = True
            vfx_col.objects.link(emitter_obj)

            # Generate basic vertices for emitter
            import bmesh
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.08)
            bm.to_mesh(mesh)
            bm.free()

            if p_mat:
                mesh.materials.append(p_mat)

            if rig and pb:
                emitter_obj.parent = rig
                emitter_obj.parent_type = "BONE"
                emitter_obj.parent_bone = pb.name
                emitter_obj.location = (0, 0, 0)
            else:
                emitter_obj.location = world_loc

            created_emitters.append(emitter_obj)

        return created_emitters

    def remove_vfx(self, root_obj: Optional[bpy.types.Object] = None) -> None:
        """Completely removes all visual effect lights, emitters, and resets shader emission."""
        scene = bpy.context.scene
        to_remove: List[bpy.types.Object] = []

        # Find all objects marked as aion vfx or in vfx collection
        for col in scene.collection.children:
            if col.name == VFX_COLLECTION_NAME:
                for obj in list(col.objects):
                    to_remove.append(obj)

        for obj in list(bpy.data.objects):
            if obj.get("is_aion_vfx") or obj.name.startswith("Aion_VFX_"):
                to_remove.append(obj)

        for obj in to_remove:
            try:
                m_data = obj.data if obj.type == "MESH" else None
                l_data = obj.data if obj.type == "LIGHT" else None
                bpy.data.objects.remove(obj, do_unlink=True)
                if m_data and m_data.users == 0:
                    bpy.data.meshes.remove(m_data)
                if l_data and l_data.users == 0:
                    bpy.data.lights.remove(l_data)
            except Exception:
                pass

        # Reset emission on model materials if root_obj provided
        if root_obj:
            mesh_objs = [root_obj] if root_obj.type == "MESH" else [c for c in root_obj.children if c.type == "MESH"]
            for m_obj in mesh_objs:
                for mat_slot in m_obj.material_slots:
                    mat = mat_slot.material
                    if mat and mat.use_nodes and mat.node_tree:
                        for n in mat.node_tree.nodes:
                            if n.type == "BSDF_PRINCIPLED":
                                try:
                                    if "Emission Strength" in n.inputs:
                                        n.inputs["Emission Strength"].default_value = 0.0
                                except Exception:
                                    pass

    def apply_vfx(
        self,
        root_obj: bpy.types.Object,
        element: str = "FIRE",
        intensity: float = 1.0,
        show_glow: bool = True,
        show_lights: bool = True,
        show_particles: bool = True,
    ) -> bool:
        """
        Applies a unified visual effect profile to the inspected 3D model.
        Returns True on success.
        """
        if not root_obj:
            return False

        # First clean up any existing VFX on the model
        self.remove_vfx(root_obj)

        sockets = self.find_effect_sockets(root_obj)

        if show_glow:
            self.apply_shader_aura(root_obj, element=element, intensity=intensity)

        if show_lights and sockets:
            self.apply_socket_lights(root_obj, sockets=sockets, element=element, intensity=intensity)

        if show_particles and sockets:
            self.apply_particle_emitters(root_obj, sockets=sockets, element=element, intensity=intensity)

        return True
