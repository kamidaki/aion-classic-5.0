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
    # Check signature
    sig = ""
    while True:
        b = stream.read(1)
        if not b or b == b"\x00":
            break
        sig += b.decode("ascii", errors="replace")

    # Read signature terminator
    stream.read(1)

    type_of_file = struct.unpack("<I", stream.read(4))[0]
    if type_of_file != 0xFFFF0001:
        return {}  # Not an animation chunk file

    version = struct.unpack("<I", stream.read(4))[0]
    table_offset = struct.unpack("<I", stream.read(4))[0]

    stream.seek(table_offset)
    num_chunks = struct.unpack("<I", stream.read(4))[0]

    controllers: Dict[int, List[Dict[str, Any]]] = {}
    timing: Dict[str, Any] = {
        "ticks_per_frame": 160,
        "frame_start": 0,
        "frame_end": 0,
        "frame_count": 0,
    }

    chunks_list: List[Tuple[int, int, int, int]] = []
    for _ in range(num_chunks):
        raw_type = struct.unpack("<I", stream.read(4))[0]
        ver = struct.unpack("<I", stream.read(4))[0]
        off = struct.unpack("<I", stream.read(4))[0]
        cid = struct.unpack("<I", stream.read(4))[0]
        chunks_list.append((raw_type, ver, off, cid))

    # Pass 1: Parse Timing chunk first
    for raw_type, ver, off, cid in chunks_list:
        if raw_type == CHUNK_TIMING:
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
            break

    tpf = timing["ticks_per_frame"] if timing["ticks_per_frame"] > 0 else 160

    # Pass 2: Parse Controller chunks using accurate tick / tpf frame timestamps
    for raw_type, ver, off, cid in chunks_list:
        if raw_type == CHUNK_CONTROLLER:
            stream.seek(off)
            kcount, ctrl_id = struct.unpack("<II", stream.read(8))
            keys: List[Dict[str, Any]] = []
            for frame_idx in range(kcount):
                tick = struct.unpack("<i", stream.read(4))[0]
                px, py, pz = struct.unpack("<3f", stream.read(12))
                qx, qy, qz, qw = struct.unpack("<4f", stream.read(16))
                # Layout: [tick, px, py, pz, qx, qy, qz, qw]
                # CryEngine units: cm -> meters (/ 100)
                # Blender quaternion: (w, x, y, z)
                frame_time = tick / float(tpf)
                keys.append({
                    "tick": tick,
                    "frame": frame_time,
                    "pos": (px / 100.0, py / 100.0, pz / 100.0),
                    "quat": (qw, qx, qy, qz),
                })
            controllers[ctrl_id] = keys

    return {
        "timing": timing,
        "controllers": controllers,
    }
