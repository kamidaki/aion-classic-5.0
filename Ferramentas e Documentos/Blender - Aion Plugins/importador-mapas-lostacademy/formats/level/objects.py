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
    placements = []
    offset = 4

    while offset + OBJECTS_LST_RECORD_SIZE <= len(data):
        record = data[offset : offset + OBJECTS_LST_RECORD_SIZE]
        x_pos = int.from_bytes(record[0:2], "little")
        y_pos = int.from_bytes(record[2:4], "little")
        z_pos = int.from_bytes(record[4:6], "little")
        vegetation_index = int.from_bytes(record[6:7], "little")
        unknown_byte = int.from_bytes(record[7:8], "little")
        scale = struct.unpack("<f", record[8:12])[0]
        heading_raw = int.from_bytes(record[12:16], "little")
        heading_degrees = heading_raw * 360 / 255
        vegetation_file = (
            level_data.vegetation_files[vegetation_index]
            if level_data and vegetation_index < len(level_data.vegetation_files)
            else None
        )

        placements.append(
            ObjectPlacement(
                vegetation_index=vegetation_index,
                vegetation_file=vegetation_file,
                raw_position=(x_pos, y_pos, z_pos),
                position=(x_pos / magic, y_pos / magic, z_pos / magic),
                scale=scale,
                heading_raw=heading_raw,
                heading_degrees=heading_degrees,
                unknown_byte=unknown_byte,
            )
        )
        offset += OBJECTS_LST_RECORD_SIZE

    return ObjectsList(
        header=header,
        placements=tuple(placements),
        trailing_bytes=data[offset:],
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

