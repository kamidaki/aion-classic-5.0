"""
Base interfaces for LostAcademy Aion Model Library Provider Architecture.
Isolates client-specific binary format details behind clean, common representations.
"""

from __future__ import annotations
import abc
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bpy
from ..indexer.asset_entry import AssetEntry


class IModelProvider(abc.ABC):
    """Interface for loading, instantiating, and serializing 3D models."""

    @abc.abstractmethod
    def load_model(self, entry: AssetEntry, target_collection: bpy.types.Collection) -> Optional[bpy.types.Object]:
        pass

    @abc.abstractmethod
    def serialize_model(self, root_obj: bpy.types.Object, entry: AssetEntry) -> bytes:
        pass


class ISkeletonProvider(abc.ABC):
    """Interface for building and extracting skeletal armatures."""

    @abc.abstractmethod
    def build_armature(
        self,
        name: str,
        bone_names: List[str],
        bone_initial_pos: List[Tuple[float, ...]],
        bone_anim: List[Dict[str, Any]],
        collection: bpy.types.Collection,
    ) -> Optional[bpy.types.Object]:
        pass

    @abc.abstractmethod
    def extract_armature(
        self, arm_obj: bpy.types.Object
    ) -> Tuple[List[str], List[Tuple[float, ...]], List[Dict[str, Any]]]:
        pass


class IAnimationProvider(abc.ABC):
    """Interface for parsing, keyframing, and serializing animations."""

    @abc.abstractmethod
    def load_animation(
        self,
        rig_obj: bpy.types.Object,
        caf_bytes: bytes,
        action_name: str,
        bone_names: Optional[List[str]] = None,
        bone_anim: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[bpy.types.Action]:
        pass

    @abc.abstractmethod
    def serialize_action(
        self,
        rig_obj: bpy.types.Object,
        action: bpy.types.Action,
        bone_names: List[str],
        bone_anim: List[Dict[str, Any]],
    ) -> bytes:
        pass


class IMaterialProvider(abc.ABC):
    """Interface for bidirectional CryEngine Mtl <-> Principled BSDF node trees."""

    @abc.abstractmethod
    def create_material(
        self,
        material_name: str,
        mtl_chunk: Dict[str, Any],
        resolved_textures: Dict[str, Optional[Path]],
    ) -> bpy.types.Material:
        pass

    @abc.abstractmethod
    def extract_material_params(self, mat: bpy.types.Material) -> Dict[str, Any]:
        pass


class ITextureProvider(abc.ABC):
    """Interface for resolving, loading, and replacing textures."""

    @abc.abstractmethod
    def get_texture_image(self, rel_path: str) -> Optional[bpy.types.Image]:
        pass


class ISoundProvider(abc.ABC):
    """Interface for resolving, extracting, and playing model sounds."""

    @abc.abstractmethod
    def get_sounds_for_model(self, entry: AssetEntry) -> List[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def play_sound(self, sound_rel_or_file: str, volume: float = 1.0, pitch: float = 1.0) -> bool:
        pass

    @abc.abstractmethod
    def stop_all_sounds(self) -> None:
        pass


class IEffectProvider(abc.ABC):
    """Interface for managing visual effects on inspected 3D models."""

    @abc.abstractmethod
    def apply_vfx(
        self,
        root_obj: bpy.types.Object,
        element: str = "FIRE",
        intensity: float = 1.0,
        show_glow: bool = True,
        show_lights: bool = True,
        show_particles: bool = True,
    ) -> bool:
        pass

    @abc.abstractmethod
    def remove_vfx(self, root_obj: Optional[bpy.types.Object] = None) -> None:
        pass

