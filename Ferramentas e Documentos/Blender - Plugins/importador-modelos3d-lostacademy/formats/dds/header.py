"""
DirectDraw Surface (DDS) binary header inspector.
Reads the first 128 bytes of any DDS file to determine dimensions, pixel format, and mipmap count without loading raw pixel buffers.
"""

from __future__ import annotations
import struct
from typing import Dict, Any, Optional

DDS_MAGIC = b"DDS "


def parse_dds_header(header_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    Parses a 128-byte DDS header.
    Returns metadata dict: width, height, mipmap_count, fourcc, has_alpha, pitch_or_linear_size.
    """
    if len(header_bytes) < 128:
        return None
    if header_bytes[:4] != DDS_MAGIC:
        return None

    # DDS_HEADER layout:
    # dwSize (4), dwFlags (4), dwHeight (4), dwWidth (4), dwPitchOrLinearSize (4), dwDepth (4), dwMipMapCount (4)
    size, flags, height, width, pitch, depth, mipmaps = struct.unpack_from("<7I", header_bytes, 4)

    # PixelFormat: offset 76 (32 bytes)
    # pf_size (4), pf_flags (4), pf_fourcc (4), pf_rgb_bit_count (4), pf_r_bit_mask (4), pf_g_bit_mask (4), pf_b_bit_mask (4), pf_a_bit_mask (4)
    pf_size, pf_flags, pf_fourcc, pf_bit_count, r_mask, g_mask, b_mask, a_mask = struct.unpack_from(
        "<8I", header_bytes, 76
    )

    fourcc_str = header_bytes[84:88].decode("ascii", errors="replace").strip("\x00")

    return {
        "width": width,
        "height": height,
        "mipmap_count": max(1, mipmaps),
        "fourcc": fourcc_str if fourcc_str else "RGBA",
        "bit_count": pf_bit_count,
        "has_alpha": bool(pf_flags & 0x1 or a_mask != 0 or fourcc_str in ("DXT3", "DXT5")),
        "linear_size": pitch,
    }
