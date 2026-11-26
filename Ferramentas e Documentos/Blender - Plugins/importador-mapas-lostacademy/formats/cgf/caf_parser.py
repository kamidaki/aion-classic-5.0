"""
CryEngine 1 Animation File (.caf) Parser.
Reads ChunkFile_Anim (0xffff0001) structures containing:
- Timing chunk (0xCCCC000E): ticks_per_frame, global_range start/end
- Controller chunks (0xCCCC000D): bone keyframes (translation, quaternion rotation)
"""

from __future__ import annotations

import io
import struct
from typing import Any, Dict, List, Optional


CHUNK_CONTROLLER = 0xCCCC000D
CHUNK_TIMING = 0xCCCC000E


def parse_caf(data: bytes) -> Dict[str, Any]:
    """
    Parses a CryEngine CAF animation file.
    Returns a dict containing:
    - 'ticks_per_frame': int (typically 160)
    - 'frame_start': int
    - 'frame_end': int
    - 'frame_count': int
    - 'controllers': Dict[ctrl_id, List[Dict[str, Any]]] where each keyframe has:
        - 'frame': int
        - 'pos': Tuple[float, float, float] (meters)
        - 'quat': Tuple[float, float, float, float] (w, x, y, z for Blender)
    """
    if len(data) < 32:
        return {}

    stream = io.BytesIO(data)
    # Check signature safely (max 64 bytes)
    sig = ""
    while len(sig) < 64:
        b = stream.read(1)
        if not b or b == b"\x00":
            break
        sig += b.decode("ascii", errors="replace")

    # Read signature terminator
    stream.read(1)

    if stream.tell() + 12 > len(data):
        return {}

    type_of_file = struct.unpack("<I", stream.read(4))[0]
    if type_of_file != 0xFFFF0001:
        return {}  # Not an animation chunk file

    version = struct.unpack("<I", stream.read(4))[0]
    table_offset = struct.unpack("<I", stream.read(4))[0]

    if table_offset + 4 > len(data):
        return {}

    stream.seek(table_offset)
    num_chunks = struct.unpack("<I", stream.read(4))[0]
    if num_chunks > 10000:
        return {}

    controllers: Dict[int, List[Dict[str, Any]]] = {}
    timing: Dict[str, Any] = {
        "ticks_per_frame": 160,
        "frame_start": 0,
        "frame_end": 0,
        "frame_count": 0,
    }

    for _ in range(num_chunks):
        if stream.tell() + 16 > len(data):
            break
        raw_type = struct.unpack("<I", stream.read(4))[0]
        ver = struct.unpack("<I", stream.read(4))[0]
        off = struct.unpack("<I", stream.read(4))[0]
        cid = struct.unpack("<I", stream.read(4))[0]

        curr = stream.tell()
        if raw_type == CHUNK_TIMING and off + 48 <= len(data):
            stream.seek(off + 16)
            s_tick = struct.unpack("<f", stream.read(4))[0]
            tpf = struct.unpack("<I", stream.read(4))[0]
            name_bytes = stream.read(32).split(b"\x00")[0]
            start_frame = struct.unpack("<I", stream.read(4))[0]
            end_frame = struct.unpack("<I", stream.read(4))[0]
            timing["ticks_per_frame"] = tpf if tpf > 0 else 160
            timing["frame_start"] = start_frame
            timing["frame_end"] = end_frame
            timing["frame_count"] = max(1, end_frame - start_frame + 1)
        elif raw_type == CHUNK_CONTROLLER and off + 8 <= len(data):
            stream.seek(off)
            kcount, ctrl_id = struct.unpack("<II", stream.read(8))
            keys: List[Dict[str, Any]] = []
            if off + 8 + kcount * 32 <= len(data) and kcount < 100000:
                for frame_idx in range(kcount):
                    floats = struct.unpack("<8f", stream.read(32))
                    keys.append({
                        "frame": frame_idx,
                        "pos": (floats[1] / 100.0, floats[2] / 100.0, floats[3] / 100.0),
                        "quat": (floats[7], floats[4], floats[5], floats[6]),
                    })
                controllers[ctrl_id] = keys

        stream.seek(curr)

    return {
        "timing": timing,
        "controllers": controllers,
    }
