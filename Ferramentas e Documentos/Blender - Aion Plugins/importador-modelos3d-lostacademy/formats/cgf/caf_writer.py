"""
CryEngine 1 / Aion CAF (ChunkFile_Anim) Binary Serializer.
Encodes bone keyframe controllers, timing metadata, and chunk headers into official Aion .caf files.
"""

from __future__ import annotations
import io
import struct
from typing import Any, Dict, List, Optional, Tuple

CHUNK_CONTROLLER = 0xCCCC000D
CHUNK_TIMING = 0xCCCC000E
SIG_CAF = b"NCAion\x00\x00"


def write_caf(
    controllers: Dict[int, List[Dict[str, Any]]],
    ticks_per_frame: int = 160,
    frame_start: int = 0,
    frame_end: int = 60,
    secs_per_tick: float = 0.00020833333,
    range_name: str = "default",
    version: int = 0x750,
) -> bytes:
    """
    Serializes animation controller keyframes and timing into binary CryEngine CAF format.
    
    controllers: Dict[ctrl_id, List[Dict]]
      Each keyframe dict has:
        - 'frame': int (or time float)
        - 'pos': Tuple[float, float, float] in meters (converted to cm * 100)
        - 'quat': Tuple[float, float, float, float] (w, x, y, z) -> saved as [time, x, y, z, w]
    """
    stream = io.BytesIO()

    # 1. Signature & File Header (20 bytes total for NCAion\x00\x00 + 3 uint32)
    stream.write(SIG_CAF)
    type_of_file = 0xFFFF0001
    table_offset_pos = stream.tell() + 8  # Where table_offset uint32 will be located

    stream.write(struct.pack("<III", type_of_file, version, 0))  # Placeholder table_offset

    chunk_headers: List[Tuple[int, int, int, int]] = []
    chunk_id = 0

    # 2. Write Controller Chunks
    for ctrl_id, keys in sorted(controllers.items()):
        chunk_offset = stream.tell()
        kcount = len(keys)
        # Controller chunk body: kcount (uint32), ctrl_id (uint32)
        stream.write(struct.pack("<II", kcount, ctrl_id))

        # Each keyframe: 8 floats: [time, px, py, pz, qx, qy, qz, qw]
        for idx, k in enumerate(keys):
            frame_time = float(k.get("frame", idx))
            pos = k.get("pos", (0.0, 0.0, 0.0))
            quat = k.get("quat", (1.0, 0.0, 0.0, 0.0))  # (w, x, y, z)

            # Units: meters -> cm (* 100)
            px = float(pos[0]) * 100.0
            py = float(pos[1]) * 100.0
            pz = float(pos[2]) * 100.0

            # Quaternion layout in Aion CAF: [qx, qy, qz, qw]
            qw = float(quat[0])
            qx = float(quat[1])
            qy = float(quat[2])
            qz = float(quat[3])

            stream.write(struct.pack("<8f", frame_time, px, py, pz, qx, qy, qz, qw))

        # Controller chunk header version typically 0x829
        chunk_headers.append((CHUNK_CONTROLLER, 0x829, chunk_offset, chunk_id))
        chunk_id += 1

    # 3. Write Timing Chunk (0xCCCC000E)
    timing_offset = stream.tell()
    # 16-byte chunk header
    stream.write(struct.pack("<IIII", CHUNK_TIMING, 0x918, timing_offset, chunk_id))
    stream.write(struct.pack("<f", float(secs_per_tick)))
    stream.write(struct.pack("<I", int(ticks_per_frame)))

    name_bytes = range_name.encode("latin-1")[:31].ljust(32, b"\x00")
    stream.write(name_bytes)
    stream.write(struct.pack("<III", int(frame_start), int(frame_end), 0))

    chunk_headers.append((CHUNK_TIMING, 0x918, timing_offset, chunk_id))
    chunk_id += 1

    # 4. Write Chunk Table
    table_offset = stream.tell()
    stream.write(struct.pack("<I", len(chunk_headers)))
    for raw_type, ver, off, cid in chunk_headers:
        stream.write(struct.pack("<IIII", raw_type, ver, off, cid))

    # 5. Patch table_offset in header
    stream.seek(table_offset_pos)
    stream.write(struct.pack("<I", table_offset))

    return stream.getvalue()
