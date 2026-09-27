"""
Thumbnail Generation and Disk Caching Pipeline.
Generates lightweight visual previews for models and stores them in .aion_model_thumbs/
"""

from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Optional, Tuple

try:
    from config.settings import THUMBNAIL_CACHE_DIRNAME, DEFAULT_THUMBNAIL_SIZE
except ImportError:
    from ..config.settings import THUMBNAIL_CACHE_DIRNAME, DEFAULT_THUMBNAIL_SIZE
from .asset_entry import AssetEntry


def get_thumbnail_cache_dir(client_root: Path) -> Path:
    """Returns the dedicated directory for cached model thumbnails."""
    t_dir = client_root / THUMBNAIL_CACHE_DIRNAME
    t_dir.mkdir(parents=True, exist_ok=True)
    return t_dir


def get_thumbnail_path(client_root: Path, asset_entry: AssetEntry) -> Path:
    """Returns the expected thumbnail path for an asset entry."""
    cache_dir = get_thumbnail_cache_dir(client_root)
    # Hash model_path to create safe, unique filename
    name_hash = hashlib.md5(asset_entry.model_path.encode("utf-8")).hexdigest()[:12]
    clean_stem = Path(asset_entry.model_path).stem
    return cache_dir / f"{clean_stem}_{name_hash}.png"


def create_placeholder_thumbnail(output_path: Path, asset_entry: AssetEntry) -> Path:
    """
    Creates a clean, informative PNG thumbnail placeholder with category badge.
    Works in pure Python without requiring GPU context or external image libraries.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 160x160 uncompressed RGBA PNG minimal writer
    import zlib
    import struct

    width, height = DEFAULT_THUMBNAIL_SIZE

    # Category Color palette (R, G, B)
    cat_colors = {
        "NPC": (70, 130, 180),       # Steel Blue
        "MONSTER": (178, 34, 34),    # Firebrick
        "CHARACTER": (147, 112, 219),# Medium Purple
        "WEAPON": (218, 165, 32),    # Goldenrod
        "ARMOR": (46, 139, 87),      # Sea Green
        "WINGS": (0, 206, 209),      # Dark Turquoise
        "BUILDING": (112, 128, 144), # Slate Gray
        "VEGETATION": (34, 139, 34), # Forest Green
        "PROP": (205, 133, 63),      # Peru / Wood
        "EFFECT": (255, 105, 180),   # Hot Pink
    }
    bg_color = cat_colors.get(asset_entry.category, (45, 52, 54))
    r, g, b = bg_color

    raw_rows = []
    for y in range(height):
        row = [0]  # Filter type 0 (None)
        for x in range(width):
            # Border frame
            if x < 2 or x >= width - 2 or y < 2 or y >= height - 2:
                row.extend([30, 39, 46, 255])
            # Gradient shading
            else:
                factor = 0.8 + 0.4 * (y / height)
                pr = min(255, int(r * factor))
                pg = min(255, int(g * factor))
                pb = min(255, int(b * factor))
                row.extend([pr, pg, pb, 255])
        raw_rows.append(bytes(row))

    raw_data = b"".join(raw_rows)
    compressed = zlib.compress(raw_data)

    def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data)
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    png_bytes = io_bytes = io_png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", compressed)
        + png_chunk(b"IEND", b"")
    )

    output_path.write_bytes(png_bytes)
    return output_path


def ensure_asset_thumbnail(client_root: Path, asset_entry: AssetEntry) -> str:
    """Ensures a thumbnail exists on disk for the asset and returns its path."""
    t_path = get_thumbnail_path(client_root, asset_entry)
    if not t_path.is_file():
        create_placeholder_thumbnail(t_path, asset_entry)
    asset_entry.thumbnail_path = str(t_path)
    return str(t_path)
