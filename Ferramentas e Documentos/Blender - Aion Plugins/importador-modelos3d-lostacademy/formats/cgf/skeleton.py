"""
CryEngine 1 Skeleton & Skinning Chunks Parser.
Handles:
- BoneNameList (0xCCCC0005): Null-terminated ASCII bone names
- BoneInitialPos (0xCCCC0012): 4x3 rest/bind matrices per bone (metric cm)
- BoneAnim (0xCCCC0003): Parent-child hierarchy, controller IDs
- Mesh Skin Weights: CryBoneVertex links (bone_id, weight) per vertex
"""

from __future__ import annotations

import io
import struct
from typing import Any, Dict, List, Optional, Tuple


CHUNK_BONE_NAME_LIST = 0xCCCC0005
CHUNK_BONE_INITIAL_POS = 0xCCCC0012
CHUNK_BONE_ANIM = 0xCCCC0003


def parse_bone_name_list(stream: io.BytesIO, offset: int) -> List[str]:
    """Parses BoneNameList chunk into a list of bone name strings."""
    stream.seek(offset)
    count = struct.unpack("<I", stream.read(4))[0]
    raw = stream.read(4096)
    parts = raw.split(b"\x00")[:count]
    return [p.decode("latin-1", errors="replace") for p in parts if p]


def parse_bone_initial_pos(stream: io.BytesIO, offset: int) -> List[Tuple[float, ...]]:
    """
    Parses BoneInitialPos chunk.
    Returns a list of 12-float tuples (4x3 row-major transformation matrix per bone).
    Floats 9, 10, 11 represent the bone origin position (in cm).
    """
    stream.seek(offset)
    mesh_id = struct.unpack("<I", stream.read(4))[0]
    count = struct.unpack("<I", stream.read(4))[0]
    if count <= 0:
        return []
    raw = stream.read(count * 48)
    return list(struct.iter_unpack("<12f", raw))


def parse_bone_anim(stream: io.BytesIO, offset: int) -> List[Dict[str, Any]]:
    """
    Parses BoneAnim chunk (version 0x290).
    Returns list of dicts with bone_id, parent_id, num_children, ctrl_id.
    """
    stream.seek(offset + 16)  # skip 16 bytes chunk header
    count = struct.unpack("<I", stream.read(4))[0]
    stride = 152
    bones: List[Dict[str, Any]] = []
    for i in range(count):
        b_off = offset + 20 + i * stride
        stream.seek(b_off)
        bid, pid, nch, ctrl = struct.unpack("<4i", stream.read(16))
        bones.append({
            "bone_id": bid,
            "parent_id": pid,
            "num_children": nch,
            "ctrl_id": ctrl & 0xFFFFFFFF,
        })
    return bones


def parse_mesh_skin_weights(
    stream: io.BytesIO,
    skin_offset: int,
    num_vertices: int,
) -> List[List[Tuple[int, float]]]:
    """
    Parses CryBoneVertex skinning links from the mesh chunk.
    Returns list of list of (bone_id, weight) tuples for each vertex.
    """
    stream.seek(skin_offset)
    vertex_weights: List[List[Tuple[int, float]]] = []
    for _ in range(num_vertices):
        num_links = struct.unpack("<I", stream.read(4))[0]
        if num_links == 0:
            vertex_weights.append([])
            continue
        raw_links = stream.read(num_links * 20)
        links = [(b_id, w) for b_id, w in struct.iter_unpack("<I12xf", raw_links)]
        vertex_weights.append(links)
    return vertex_weights
