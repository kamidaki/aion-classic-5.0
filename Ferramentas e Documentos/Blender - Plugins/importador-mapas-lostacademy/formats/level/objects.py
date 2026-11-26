import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .leveldata import LevelData


OBJECTS_LST_HEADER = 0x10
OBJECTS_LST_RECORD_SIZE = 16


@dataclass(frozen=True)
class ObjectPlacement:
    vegetation_index: int
    vegetation_file: str | None
    raw_position: tuple[int, int, int]
    position: tuple[float, float, float]
    scale: float
    heading_raw: int
    heading_degrees: float
    unknown_byte: int


@dataclass(frozen=True)
class ObjectsList:
    header: int
    placements: tuple[ObjectPlacement, ...]
    trailing_bytes: bytes


def _position_scale(level_data: Optional[LevelData]) -> float:
    if level_data and level_data.level_info and level_data.level_info.heightmap_x_size:
        return 32768 / level_data.level_info.heightmap_x_size
    return 32.0


def parse_objects_lst(path: str | Path | bytes | bytearray, level_data: Optional[LevelData] = None) -> ObjectsList:
    data = bytes(path) if isinstance(path, (bytes, bytearray)) else Path(path).read_bytes()
    if len(data) < 4:
        raise ValueError("objects.lst is too short to contain a header")

    header = int.from_bytes(data[:4], byteorder="little")
    if header != OBJECTS_LST_HEADER:
        raise ValueError(f"objects.lst header 0x{header:x} does not match 0x{OBJECTS_LST_HEADER:x}")

    magic = _position_scale(level_data)
    inv_magic = 1.0 / magic
    deg_scale = 360.0 / 255.0
    placements = []

    veg_files = level_data.vegetation_files if level_data else None
    veg_len = len(veg_files) if veg_files else 0

    record_count = (len(data) - 4) // OBJECTS_LST_RECORD_SIZE
    records_end = 4 + record_count * OBJECTS_LST_RECORD_SIZE

    # High-speed vectorized C unpack: 3 uint16, 2 uint8, 1 float, 1 uint32 (16 bytes)
    unpacker = struct.iter_unpack("<3HBBfI", data[4:records_end])
    for x_pos, y_pos, z_pos, veg_idx, unk_b, scale, heading_raw in unpacker:
        v_file = veg_files[veg_idx] if veg_idx < veg_len else None
        placements.append(
            ObjectPlacement(
                vegetation_index=veg_idx,
                vegetation_file=v_file,
                raw_position=(x_pos, y_pos, z_pos),
                position=(x_pos * inv_magic, y_pos * inv_magic, z_pos * inv_magic),
                scale=scale,
                heading_raw=heading_raw,
                heading_degrees=heading_raw * deg_scale,
                unknown_byte=unk_b,
            )
        )

    return ObjectsList(
        header=header,
        placements=tuple(placements),
        trailing_bytes=data[records_end:],
    )


def write_objects_lst(path: str | Path, objects_list: ObjectsList, level_data: Optional[LevelData] = None) -> int:
    """
    Serializes an ObjectsList structure back to binary objects.lst format.
    Returns total bytes written.
    """
    magic = _position_scale(level_data)
    out = bytearray()
    out.extend(objects_list.header.to_bytes(4, byteorder="little"))

    for p in objects_list.placements:
        if p.raw_position is not None:
            x_raw, y_raw, z_raw = p.raw_position
        else:
            x_raw = max(0, min(65535, int(round(p.position[0] * magic))))
            y_raw = max(0, min(65535, int(round(p.position[1] * magic))))
            z_raw = max(0, min(65535, int(round(p.position[2] * magic))))

        out.extend(x_raw.to_bytes(2, byteorder="little"))
        out.extend(y_raw.to_bytes(2, byteorder="little"))
        out.extend(z_raw.to_bytes(2, byteorder="little"))
        out.append(p.vegetation_index & 0xFF)
        out.append(p.unknown_byte & 0xFF)
        out.extend(struct.pack("<f", float(p.scale)))

        if getattr(p, "heading_raw", None) is not None:
            h_raw = p.heading_raw
        else:
            h_raw = int(round(float(p.heading_degrees or 0.0) * 255.0 / 360.0)) & 0xFFFFFFFF
        out.extend(h_raw.to_bytes(4, byteorder="little"))

    out.extend(objects_list.trailing_bytes)

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(bytes(out))
    return len(out)
