"""
CryEngine 1 Skeleton & Skinning Chunks Binary Serializer.
Encodes:
- BoneNameList (0xCCCC0005)
- BoneInitialPos (0xCCCC0012)
- BoneAnim (0xCCCC0003, version 0x290)
- CryBoneVertex Skin Weights
"""

from __future__ import annotations
import io
import struct
from typing import Any, Dict, List, Tuple

CHUNK_BONE_NAME_LIST = 0xCCCC0005
CHUNK_BONE_INITIAL_POS = 0xCCCC0012
CHUNK_BONE_ANIM = 0xCCCC0003


def serialize_bone_name_list(bone_names: List[str], chunk_id: int, version: int = 0x744) -> bytes:
    """Serializes bone names into a BoneNameList chunk payload."""
    stream = io.BytesIO()
    # Count of bones
    stream.write(struct.pack("<I", len(bone_names)))
    # Null-terminated ASCII names
    for name in bone_names:
        stream.write(name.encode("latin-1") + b"\x00")
    return stream.getvalue()


def serialize_bone_initial_pos(
    matrices: List[Tuple[float, ...]],
    mesh_id: int,
    chunk_id: int,
    version: int = 0x744,
) -> bytes:
    """Serializes 4x3 row-major bind matrices into a BoneInitialPos chunk payload."""
    stream = io.BytesIO()
    stream.write(struct.pack("<II", mesh_id, len(matrices)))
    for m in matrices:
        if len(m) < 12:
            m = list(m) + [0.0] * (12 - len(m))
        stream.write(struct.pack("<12f", *m[:12]))
    return stream.getvalue()


def serialize_bone_anim(
    bones: List[Dict[str, Any]],
    chunk_id: int,
    version: int = 0x290,
) -> bytes:
    """Serializes parent-child bone relationships and controller IDs into a BoneAnim chunk payload."""
    stream = io.BytesIO()
    # 16-byte chunk header
    stream.write(struct.pack("<IIII", CHUNK_BONE_ANIM, version, 0, chunk_id))
    # Count of bones
    stream.write(struct.pack("<I", len(bones)))
    # 152 bytes per bone record
    for b in bones:
        bid = int(b.get("bone_id", 0))
        pid = int(b.get("parent_id", -1))
        nch = int(b.get("num_children", 0))
        ctrl = int(b.get("ctrl_id", 0)) & 0xFFFFFFFF
        stream.write(struct.pack("<3iI", bid, pid, nch, ctrl))
        # 136 bytes reserved / transform padding
        raw_padding = b.get("raw_padding")
        if isinstance(raw_padding, bytes) and len(raw_padding) == 136:
            stream.write(raw_padding)
        else:
            stream.write(b"\x00" * 136)
    return stream.getvalue()


def serialize_skin_weights(skin_weights: List[List[Tuple[int, float]]]) -> bytes:
    """Serializes CryBoneVertex skinning links for the mesh chunk payload."""
    stream = io.BytesIO()
    for links in skin_weights:
        stream.write(struct.pack("<I", len(links)))
        for bone_id, weight in links:
            stream.write(struct.pack("<I", int(bone_id)))
            stream.write(struct.pack("<3f", 0.0, 0.0, 0.0))  # 12 bytes offset
            stream.write(struct.pack("<f", float(weight)))
    return stream.getvalue()
