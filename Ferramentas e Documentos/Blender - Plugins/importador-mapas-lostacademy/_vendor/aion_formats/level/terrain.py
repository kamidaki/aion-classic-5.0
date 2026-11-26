import math
from dataclasses import dataclass
from pathlib import Path


LAND_MAP_BYTES_PER_SAMPLE = 3
LAND_MAP_HEIGHT_SCALE = 32


class LandMapSample:
    __slots__ = ("height_raw", "height", "color")

    def __init__(self, height_raw: int, height: float, color: int):
        self.height_raw = height_raw
        self.height = height
        self.color = color

    def __repr__(self) -> str:
        return f"LandMapSample(height_raw={self.height_raw}, height={self.height}, color={self.color})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, LandMapSample):
            return False
        return (
            self.height_raw == other.height_raw
            and math.isclose(self.height, other.height, rel_tol=1e-7, abs_tol=1e-7)
            and self.color == other.color
        )


@dataclass(frozen=True)
class LandMap:
    width: int
    height: int
    sample_count: int
    bytes_per_sample: int
    height_scale: int
    samples: tuple[LandMapSample, ...]
    min_height: float
    max_height: float
    trailing_bytes: bytes


def parse_land_map_h32(path: str | Path) -> LandMap:
    data = Path(path).read_bytes()
    sample_count, remainder = divmod(len(data), LAND_MAP_BYTES_PER_SAMPLE)
    if remainder:
        raise ValueError("land_map.h32 size is not divisible by 3 bytes per sample")

    width = int(math.isqrt(sample_count))
    if width * width != sample_count:
        raise ValueError(f"land_map.h32 sample count {sample_count} is not a square grid")

    inv_scale = 1.0 / LAND_MAP_HEIGHT_SCALE
    samples = []
    min_h = float("inf")
    max_h = float("-inf")

    # Fast bitwise unpack directly from bytes (avoids 1,000,000 slice allocations and int.from_bytes calls)
    for offset in range(0, sample_count * LAND_MAP_BYTES_PER_SAMPLE, LAND_MAP_BYTES_PER_SAMPLE):
        h_raw = data[offset] | (data[offset + 1] << 8)
        c = data[offset + 2]
        h = h_raw * inv_scale
        if h < min_h:
            min_h = h
        if h > max_h:
            max_h = h
        samples.append(LandMapSample(h_raw, h, c))

    if min_h == float("inf"):
        min_h = 0.0
        max_h = 0.0

    return LandMap(
        width=width,
        height=width,
        sample_count=sample_count,
        bytes_per_sample=LAND_MAP_BYTES_PER_SAMPLE,
        height_scale=LAND_MAP_HEIGHT_SCALE,
        samples=tuple(samples),
        min_height=min_h,
        max_height=max_h,
        trailing_bytes=data[sample_count * LAND_MAP_BYTES_PER_SAMPLE :],
    )


def write_land_map_h32(path: str | Path, land_map: LandMap) -> int:
    """
    Serializes a LandMap heightfield structure back to binary land_map.h32 format.
    Returns total bytes written.
    """
    out = bytearray(len(land_map.samples) * LAND_MAP_BYTES_PER_SAMPLE)
    idx = 0
    scale = land_map.height_scale or LAND_MAP_HEIGHT_SCALE

    for s in land_map.samples:
        if getattr(s, "height_raw", None) is not None:
            h_raw = s.height_raw
        else:
            h_raw = max(0, min(65535, int(round(float(s.height) * scale))))
        out[idx] = h_raw & 0xFF
        out[idx + 1] = (h_raw >> 8) & 0xFF
        out[idx + 2] = s.color & 0xFF
        idx += 3

    if land_map.trailing_bytes:
        out.extend(land_map.trailing_bytes)

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(bytes(out))
    return len(out)
