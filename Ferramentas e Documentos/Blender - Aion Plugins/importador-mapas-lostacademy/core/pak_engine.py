"""
Aion PAK Engine and High-Performance Resource Resolver for Blender Aion Toolkit.

Supports:
- Zero-dependency binary parsing of CryEngine / Aion .pak archives.
- Aion XOR 32-byte stream deobfuscation.
- Method 0 (Stored) and Method 8 (Deflate via zlib).
- Transparent on-demand extraction of level files (terrain, XMLs, LSTs) to a local cache.
- Fast O(1) global catalog indexing for CGF models, CGA entities, DDS textures, and Shaders.
- Byte-for-byte compatible packing into official CryEngine Level.pak archives with .pak.bak backups.
"""

from __future__ import annotations

import gzip
import io
import json
import os
import shutil
import struct
import tempfile
import time
import zlib
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

# 1056-byte XOR table used by Aion Classic CryEngine pak archives
AION_XOR_TABLE = bytes([
    0x86, 0xfa, 0x1a, 0x1c, 0x07, 0xbd, 0xd8, 0x64, 0xce, 0xee, 0x59, 0x88, 0xcd, 0xa9, 0x1d, 0x06,
    0xf7, 0x3d, 0x31, 0x58, 0x83, 0xa1, 0x5c, 0x7e, 0xdf, 0xa6, 0x50, 0x9e, 0x89, 0xa8, 0x12, 0xd2,
    0x25, 0x49, 0x75, 0xe2, 0x07, 0x0f, 0xeb, 0x01, 0x97, 0x4a, 0x66, 0x35, 0xab, 0x32, 0x9d, 0xa7,
    0x4e, 0xa2, 0x89, 0x62, 0x0f, 0x55, 0x41, 0xc5, 0x52, 0x10, 0x1f, 0x47, 0xb0, 0xa0, 0x63, 0xa6,
    0xf0, 0x1c, 0x1c, 0x4c, 0x9b, 0x3c, 0xac, 0xe2, 0xb3, 0x4e, 0x9f, 0xf1, 0xa4, 0x91, 0x29, 0x82,
    0xe4, 0x76, 0x0d, 0x8d, 0x4f, 0xa3, 0x34, 0x4a, 0xcc, 0x1c, 0xc7, 0x18, 0x48, 0x8e, 0xfe, 0x18,
    0x79, 0x08, 0x87, 0x28, 0x8e, 0x24, 0xb7, 0x6b, 0x38, 0xf2, 0x58, 0x01, 0x2d, 0xa8, 0x58, 0x0e,
    0x9c, 0x54, 0x29, 0xcf, 0xa1, 0xae, 0x0a, 0xd2, 0x3b, 0x4a, 0x10, 0xf8, 0xd8, 0x19, 0x31, 0x7d,
    0xf3, 0xae, 0x1b, 0x90, 0xd2, 0x2f, 0x16, 0xc7, 0xe5, 0x3b, 0xcc, 0xef, 0xe1, 0xe1, 0x2c, 0x86,
    0x00, 0xdd, 0x35, 0x67, 0x8d, 0x25, 0xfc, 0xed, 0x32, 0x1f, 0xa9, 0x1a, 0x12, 0x6d, 0xb0, 0xf7,
    0x3d, 0xb6, 0x1f, 0xe8, 0x81, 0x4d, 0x36, 0xe7, 0x25, 0x30, 0x21, 0x90, 0x86, 0x30, 0x0e, 0xee,
    0x40, 0xbe, 0x6e, 0xda, 0xc1, 0x3a, 0xaf, 0xf2, 0xec, 0x28, 0x2c, 0xf1, 0xcd, 0x44, 0x98, 0x72,
    0xda, 0xcd, 0xc6, 0xd9, 0xdf, 0xf7, 0xee, 0x88, 0x04, 0xe1, 0x62, 0x00, 0x08, 0x0e, 0xcd, 0x16,
    0x37, 0xab, 0xf9, 0xf5, 0x14, 0xaa, 0x2e, 0x00, 0x4e, 0xf8, 0x18, 0x41, 0x0b, 0xd9, 0x6f, 0x9b,
    0xfa, 0xad, 0x2b, 0x54, 0x56, 0x2e, 0x7f, 0x2c, 0x3b, 0x6a, 0x82, 0xa1, 0x7c, 0x7c, 0xa6, 0x8f,
    0x66, 0x5e, 0xe7, 0xcf, 0x83, 0xb9, 0xea, 0xfc, 0xe2, 0x31, 0xd4, 0x10, 0xf3, 0xf4, 0x22, 0xec,
    0x73, 0x14, 0x4f, 0x94, 0x78, 0x79, 0x8f, 0x1e, 0x29, 0xea, 0x5f, 0x21, 0x1e, 0x08, 0x37, 0xb8,
    0xf6, 0x9a, 0x2d, 0xc5, 0x36, 0x34, 0xc1, 0x97, 0xdc, 0x75, 0xb2, 0xad, 0xd7, 0xe3, 0x04, 0xa7,
    0xc0, 0xc9, 0x1c, 0x1a, 0x00, 0xe9, 0x2d, 0x6f, 0xd6, 0x8d, 0xbc, 0x73, 0x52, 0xc0, 0x8a, 0xb6,
    0xba, 0x2c, 0xa6, 0x7d, 0x7b, 0x6f, 0xf4, 0x47, 0x1a, 0x72, 0xe9, 0xb2, 0x30, 0x7d, 0xd4, 0xd3,
    0x09, 0x9c, 0x65, 0xb0, 0xd0, 0x17, 0xcf, 0xfc, 0xf2, 0xff, 0x46, 0xd2, 0xa6, 0x43, 0x11, 0x76,
    0x2b, 0xe5, 0x1d, 0xe5, 0xc9, 0x47, 0x2f, 0x4b, 0x1b, 0xdd, 0x9a, 0xfd, 0x9d, 0x20, 0xb6, 0x43,
    0x1a, 0x64, 0xe3, 0x68, 0xf3, 0x21, 0x57, 0x68, 0xd4, 0x04, 0x8f, 0xc3, 0xce, 0xaf, 0xa3, 0xab,
    0x69, 0xa3, 0x3c, 0x34, 0xbe, 0x1f, 0x84, 0xa8, 0x0e, 0x74, 0xcb, 0xb7, 0xe6, 0xb1, 0x39, 0x8d,
    0x68, 0x00, 0x3a, 0x9b, 0x9c, 0xb1, 0x09, 0x1c, 0x7d, 0x52, 0x15, 0x12, 0xa6, 0xb0, 0x83, 0xd3,
    0x40, 0x47, 0x9b, 0xe4, 0x22, 0xe3, 0x6e, 0x30, 0xc4, 0xfc, 0x6f, 0x4f, 0xfe, 0x9f, 0x51, 0x14,
    0x13, 0x57, 0xf1, 0xeb, 0x25, 0xf7, 0x95, 0x4c, 0x92, 0xb6, 0x3c, 0xd0, 0x34, 0x79, 0x59, 0x33,
    0x20, 0xbe, 0xb8, 0xbf, 0xe0, 0x0a, 0xd2, 0x77, 0xbc, 0x43, 0x5c, 0x7d, 0xfc, 0xe1, 0x59, 0x00,
    0xde, 0x5a, 0x7d, 0x44, 0x11, 0xac, 0x13, 0xf2, 0x64, 0x84, 0x4f, 0x5d, 0xa2, 0xc4, 0x36, 0xd7,
    0x23, 0xfa, 0xf8, 0xd1, 0x14, 0x8d, 0xf9, 0xdd, 0x17, 0x1d, 0x52, 0x41, 0x22, 0xf5, 0x1a, 0x42,
    0x39, 0xfe, 0x36, 0xd5, 0x0a, 0x10, 0x01, 0xd2, 0xea, 0x12, 0x82, 0x5a, 0x48, 0xd2, 0x94, 0x95,
    0x0a, 0xf7, 0xab, 0x70, 0xf7, 0xf2, 0x98, 0x89, 0xa1, 0x68, 0xf9, 0xe1, 0xd6, 0xe1, 0xbd, 0x92,
    0x38, 0x45, 0x5f, 0x19, 0xe2, 0xea, 0x46, 0x76, 0xc5, 0xc3, 0xf2, 0xb4, 0x9f, 0x70, 0x53, 0x09,
    0x3f, 0xb8, 0x06, 0x3a, 0xf3, 0x46, 0xc8, 0x6a, 0xcd, 0x0a, 0xe3, 0xf0, 0xaa, 0x34, 0xd9, 0x72,
    0x98, 0x34, 0x23, 0xd1, 0x96, 0x8c, 0x32, 0x32, 0x3b, 0x00, 0xa3, 0x9e, 0x4f, 0xed, 0xbc, 0x97,
    0xd4, 0x4a, 0x26, 0x15, 0x96, 0x1d, 0x0e, 0x36, 0xb8, 0xee, 0x86, 0x45, 0x57, 0x04, 0x6d, 0x2b,
    0xc0, 0xdb, 0x91, 0x0a, 0x46, 0xce, 0x7c, 0x1f, 0x3c, 0x3a, 0x81, 0x94, 0x22, 0x26, 0x82, 0x6d,
    0x83, 0xbd, 0x13, 0x2d, 0x96, 0x91, 0x53, 0x6c, 0x26, 0x0c, 0x44, 0xfe, 0xbd, 0xee, 0xda, 0xcc,
    0xbd, 0x52, 0xa6, 0x11, 0x3e, 0x10, 0x42, 0x20, 0x60, 0xeb, 0x5f, 0x5b, 0x0d, 0x7c, 0xbb, 0x80,
    0xac, 0x2f, 0xb9, 0xf9, 0xd2, 0x4a, 0xeb, 0x54, 0x80, 0x60, 0x62, 0x85, 0xe5, 0x1a, 0xf0, 0x30,
    0x45, 0xb7, 0x44, 0x82, 0xef, 0x3a, 0x0c, 0xe0, 0xe5, 0x94, 0xfa, 0xfd, 0x2e, 0xd9, 0xeb, 0x8d,
    0x5a, 0xc2, 0xef, 0x39, 0x51, 0x71, 0x92, 0xfa, 0xdb, 0xef, 0x14, 0x88, 0x00, 0xff, 0xe3, 0xf6,
    0xb5, 0x34, 0x34, 0x40, 0xf5, 0xbb, 0xc8, 0xd3, 0xb5, 0xbd, 0xf6, 0xcf, 0xc7, 0xb1, 0xf9, 0x18,
    0x3d, 0xa2, 0x74, 0xef, 0x40, 0xbc, 0x6b, 0x39, 0xf2, 0xc8, 0x6e, 0x00, 0x64, 0x78, 0x52, 0x88,
    0x13, 0xf4, 0x27, 0x74, 0x14, 0x8f, 0xce, 0x34, 0x5e, 0xf9, 0xe0, 0x6d, 0x47, 0xfc, 0x38, 0x6d,
    0xb0, 0x03, 0xed, 0x6c, 0xf6, 0x68, 0x00, 0xac, 0x2b, 0xfe, 0x73, 0x2c, 0x94, 0x9e, 0x3f, 0x17,
    0x0c, 0x33, 0xb9, 0x8f, 0x33, 0x34, 0xde, 0x05, 0x18, 0xe1, 0x2b, 0xb9, 0x42, 0x3f, 0x5f, 0xa2,
    0xb4, 0x1e, 0xe9, 0x45, 0xf3, 0x38, 0x43, 0xbb, 0x8e, 0xb0, 0x0a, 0x94, 0x39, 0xee, 0xff, 0x9a,
    0xf4, 0x2d, 0x6c, 0x4b, 0x66, 0xb1, 0x1e, 0x0f, 0xc2, 0x18, 0x32, 0xe1, 0x74, 0xff, 0x90, 0x94,
    0xf2, 0x38, 0xdd, 0x56, 0xdc, 0x78, 0x91, 0x96, 0xd1, 0x04, 0x03, 0x09, 0x21, 0x39, 0xb2, 0xd4,
    0xcc, 0x2a, 0xa8, 0xab, 0xe8, 0x99, 0x1c, 0xe7, 0xe4, 0x43, 0x3b, 0x58, 0xc1, 0x59, 0x54, 0xe8,
    0xbd, 0x9c, 0x28, 0xc6, 0x81, 0xfc, 0xad, 0x33, 0x4f, 0x24, 0x16, 0xa0, 0x47, 0xd1, 0x4c, 0x4d,
    0x39, 0x7a, 0xc1, 0xf7, 0x1d, 0x04, 0xcf, 0xe7, 0xae, 0x17, 0x71, 0xd9, 0x37, 0xdc, 0x9c, 0x0a,
    0x0e, 0x9d, 0x0e, 0x04, 0xd7, 0x24, 0xc1, 0x50, 0x0c, 0x49, 0xe3, 0xbc, 0xca, 0x98, 0x89, 0x55,
    0x86, 0x73, 0xf1, 0xc3, 0x8d, 0x8f, 0x99, 0x34, 0xf7, 0x4b, 0xe7, 0x69, 0x0a, 0xb0, 0xc1, 0x2f,
    0x85, 0x97, 0xbf, 0xc3, 0xfd, 0xd0, 0x62, 0x75, 0xb1, 0xad, 0xf3, 0x04, 0xf3, 0xf3, 0x77, 0x06,
    0xaa, 0x77, 0x5a, 0xe7, 0xeb, 0x67, 0x3f, 0xb5, 0x40, 0xa1, 0x9c, 0x53, 0x96, 0xfd, 0x85, 0x53,
    0x6e, 0xed, 0x52, 0x05, 0x3b, 0x6e, 0x89, 0xef, 0x95, 0x98, 0xb6, 0x66, 0x34, 0xd0, 0x8a, 0x3f,
    0x44, 0xea, 0x06, 0x86, 0x13, 0x39, 0xef, 0x20, 0xad, 0xe4, 0x73, 0x2c, 0x61, 0x77, 0x10, 0x3d,
    0xb9, 0x0b, 0xc2, 0x0c, 0xfd, 0xf2, 0x99, 0xd8, 0xb1, 0x57, 0x83, 0x1b, 0x24, 0xa6, 0xa0, 0xab,
    0x97, 0x3e, 0xe5, 0x09, 0x07, 0x3f, 0x43, 0xed, 0x12, 0xe3, 0x36, 0xce, 0x16, 0x58, 0xf2, 0x78,
    0x00, 0x63, 0xf7, 0x67, 0xdc, 0xd9, 0x5f, 0x0d, 0xaa, 0x3e, 0x9a, 0xa3, 0x83, 0x72, 0xfe, 0xba,
    0x92, 0xe9, 0xd4, 0x22, 0xf0, 0x38, 0x38, 0x61, 0xe2, 0x79, 0x9b, 0x5e, 0x8a, 0x62, 0x27, 0x59,
    0x84, 0x71, 0xc0, 0xeb, 0x95, 0x28, 0x0d, 0x34, 0xcb, 0xab, 0x25, 0xc6, 0x3b, 0xbc, 0x52, 0xa5,
    0xca, 0x6b, 0x93, 0xca, 0x23, 0x6d, 0x35, 0x87, 0x41, 0x87, 0x3e, 0x48, 0xb9, 0xdf, 0x0e, 0xfd,
    0x30, 0xb8, 0xd1, 0xb8, 0x10, 0x68, 0x3d, 0xbc, 0x09, 0x04, 0x31, 0x94, 0x5c, 0x91, 0xaf, 0x6c,
])

SIG_EOCD = b"\xaf\xb4\xfa\xf9"
SIG_CENTRAL = b"\xaf\xb4\xfe\xfd"
SIG_LOCAL = b"\xaf\xb4\xfc\xfb"


def deobfuscate_stream(data: bytes | bytearray) -> bytes:
    """XOR-decrypt the first min(32, len) bytes of an Aion compressed/stored stream."""
    if not data:
        return b""
    arr = bytearray(data)
    count = min(32, len(arr))
    off = len(arr) & 0x3FF
    for i in range(count):
        arr[i] ^= AION_XOR_TABLE[off + i]
    return bytes(arr)


class AionPakEntry:
    __slots__ = ("name", "method", "csize", "usize", "crc", "local_offset", "pak_path")

    def __init__(
        self,
        name: str,
        method: int,
        csize: int,
        usize: int,
        crc: int,
        local_offset: int,
        pak_path: str,
    ):
        self.name = name.replace("\\", "/").strip().lstrip("/")
        self.method = method
        self.csize = csize
        self.usize = usize
        self.crc = crc
        self.local_offset = local_offset
        self.pak_path = pak_path

    @property
    def lower_name(self) -> str:
        return self.name.lower()


class AionPakArchive:
    """Represents an open Aion PAK file with fast random access."""

    def __init__(self, filepath: str | Path):
        self.filepath = str(filepath)
        self.entries: Dict[str, AionPakEntry] = {}
        self._zip: Optional[zipfile.ZipFile] = None
        self._file_handle: Optional[io.BufferedReader] = None
        self._load_central_directory()

    def __enter__(self) -> "AionPakArchive":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        if self._file_handle is not None:
            try:
                self._file_handle.close()
            except Exception:
                pass
            self._file_handle = None
        if self._zip is not None:
            try:
                self._zip.close()
            except Exception:
                pass
            self._zip = None

    def namelist(self) -> List[str]:
        return [entry.name for entry in self.entries.values()]

    def _load_central_directory(self) -> None:
        if not os.path.isfile(self.filepath):
            return

        if zipfile.is_zipfile(self.filepath):
            try:
                self._zip = zipfile.ZipFile(self.filepath, "r")
                for info in self._zip.infolist():
                    entry = AionPakEntry(
                        name=info.filename,
                        method=info.compress_type,
                        csize=info.compress_size,
                        usize=info.file_size,
                        crc=info.CRC,
                        local_offset=getattr(info, "header_offset", 0),
                        pak_path=self.filepath,
                    )
                    self.entries[entry.lower_name] = entry
                return
            except Exception:
                self._zip = None

        with open(self.filepath, "rb") as f:
            f.seek(0, os.SEEK_END)
            file_len = f.tell()
            if file_len < 22:
                return

            # Scan last 64KB for End of Central Directory signature
            scan_len = min(65536, file_len)
            f.seek(file_len - scan_len, os.SEEK_SET)
            tail = f.read(scan_len)

            eocd_idx = tail.rfind(SIG_EOCD)
            if eocd_idx == -1:
                return

            eocd_pos = (file_len - scan_len) + eocd_idx
            f.seek(eocd_pos + 4, os.SEEK_SET)
            eocd_data = f.read(18)
            if len(eocd_data) < 16:
                return

            # EOCD: disk_num(2), cd_disk(2), disk_entries(2), total_entries(2), cd_size(4), cd_offset(4)
            _, _, _, total_entries, cd_size, cd_offset = struct.unpack("<HHHHII", eocd_data[:16])

            f.seek(cd_offset, os.SEEK_SET)
            cd_bytes = f.read(cd_size)
            stream = io.BytesIO(cd_bytes)

            while True:
                sig = stream.read(4)
                if len(sig) < 4 or sig != SIG_CENTRAL:
                    break

                header = stream.read(42)
                if len(header) < 42:
                    break

                (
                    v_made,
                    v_need,
                    flags,
                    method,
                    mtime,
                    mdate,
                    crc,
                    csize,
                    usize,
                    fn_len,
                    extra_len,
                    comm_len,
                    d_start,
                    i_attr,
                    e_attr,
                    loc_offset,
                ) = struct.unpack("<HHHHHHIIIHHHHHII", header)

                raw_fn = stream.read(fn_len)
                if extra_len:
                    stream.seek(extra_len, os.SEEK_CUR)
                if comm_len:
                    stream.seek(comm_len, os.SEEK_CUR)

                fn = raw_fn.decode("latin1", errors="replace")
                entry = AionPakEntry(
                    name=fn,
                    method=method,
                    csize=csize,
                    usize=usize,
                    crc=crc,
                    local_offset=loc_offset,
                    pak_path=self.filepath,
                )
                self.entries[entry.lower_name] = entry

    def read_file(self, filename: str) -> Optional[bytes]:
        """Convenience method to read and decompress a file by relative path."""
        clean = filename.replace("\\", "/").strip().lstrip("/").lower()
        entry = self.entries.get(clean)
        if not entry:
            return None
        return self.read_entry(entry)

    def read_entry(self, entry: AionPakEntry) -> Optional[bytes]:
        """Reads and decompresses an entry from this PAK file."""
        if self._zip is not None:
            try:
                return self._zip.read(entry.name)
            except Exception:
                return None

        if not os.path.isfile(self.filepath):
            return None

        with open(self.filepath, "rb") as f:
            f.seek(entry.local_offset, os.SEEK_SET)
            sig = f.read(4)
            if sig != SIG_LOCAL:
                return None

            header = f.read(26)
            if len(header) < 26:
                return None

            _, _, method, _, _, _, csize, usize, fn_len, extra_len = struct.unpack(
                "<HHHHHIIIHH", header
            )
            f.seek(fn_len + extra_len, os.SEEK_CUR)

            raw_stream = f.read(csize)
            if len(raw_stream) != csize:
                return None

            deobf = deobfuscate_stream(raw_stream)

            if method == 0:
                return deobf
            elif method == 8:
                try:
                    return zlib.decompress(deobf, -15)
                except Exception:
                    try:
                        return zlib.decompress(deobf)
                    except Exception:
                        return None
            else:
                return None


class AionLevelUnpacker:
    """Prepares level files (.h32, .xml, .lst) into a cache directory transparently."""

    LEVEL_CRITICAL_FILES = [
        "brush.lst",
        "leveldata.xml",
        "mission_mission0.xml",
        "objects.lst",
        "terrain/land_map.h32",
        "staticdeferredlights.lst",
    ]

    @classmethod
    def prepare_level_directory(cls, level_dir: str | Path) -> Path:
        level_path = Path(level_dir).resolve()
        if level_path.is_file():
            level_path = level_path.parent

        pak_path = level_path / "Level.pak"
        if not pak_path.is_file():
            return level_path

        cache_dir = level_path / ".aion_cache"
        marker_file = cache_dir / ".level_pak_mtime"
        level_pak_mtime = pak_path.stat().st_mtime

        if marker_file.is_file():
            try:
                cached_mtime = float(marker_file.read_text(encoding="utf-8").strip())
                if cached_mtime == level_pak_mtime:
                    return cache_dir
            except Exception:
                pass

        cache_dir.mkdir(parents=True, exist_ok=True)
        archive = AionPakArchive(pak_path)
        try:
            for rel_file in cls.LEVEL_CRITICAL_FILES:
                entry = archive.entries.get(rel_file.lower())
                if entry:
                    dest = cache_dir / rel_file
                    data = archive.read_entry(entry)
                    if data is not None:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(data)
        finally:
            archive.close()

        # Unpack all level-specific PAKs (e.g. lf1.pak, leveletc.pak, terrainlm.pak, levellm.pak)
        for extra_pak in level_path.glob("*.pak"):
            if extra_pak.name.lower() == "level.pak":
                continue
            try:
                extra_archive = AionPakArchive(extra_pak)
                try:
                    for entry in extra_archive.entries.values():
                        dest = cache_dir / entry.name
                        if not dest.exists():
                            data = extra_archive.read_entry(entry)
                            if data is not None:
                                dest.parent.mkdir(parents=True, exist_ok=True)
                                dest.write_bytes(data)
                                if dest.name.lower() == "cover_low_shadow.dds":
                                    shadow_alt = cache_dir / "terrain" / "cover_low_shadow.dds"
                                    if not shadow_alt.exists():
                                        shadow_alt.parent.mkdir(parents=True, exist_ok=True)
                                        shadow_alt.write_bytes(data)
                finally:
                    extra_archive.close()
            except Exception:
                pass

        try:
            marker_file.write_text(str(level_pak_mtime), encoding="utf-8")
        except Exception:
            pass

        return cache_dir

    unpack_level = prepare_level_directory



def cryengine_pak_sort_key(pak_path: Path | str) -> Tuple[int, str]:
    """
    Official CryEngine PAK loading precedence:
    1. Base PAKs are loaded in alphabetical order (priority 0).
    2. Files starting with 'z_' or 'Z_', or containing 'patch' or 'override'
       are patch/override PAKs loaded later (priority 1), overriding base assets.
    """
    p = Path(pak_path)
    name = p.name.lower()
    is_patch = (
        name.startswith("z_")
        or name.startswith("z")
        or "patch" in name
        or "override" in name
    )
    return (1 if is_patch else 0, name)

class AionCatalogIndex:
    """
    In-memory fast inverted index across client PAK files.
    Allows sub-millisecond O(1) lookups for textures, meshes, and shaders.
    """

    def __init__(self, client_root: Path):
        self.client_root = client_root
        self._path_to_pak_entry: Dict[str, Tuple[Path, AionPakEntry]] = {}
        self._basename_to_pak_entry: Dict[str, Tuple[Path, AionPakEntry]] = {}
        self._indexed_paks: Set[str] = set()
        self._archives: Dict[str, AionPakArchive] = {}
        self._file_cache: Dict[str, bytes] = {}

    def get_archive(self, pak_path: Path | str) -> AionPakArchive:
        key = str(pak_path).lower()
        if key not in self._archives:
            self._archives[key] = AionPakArchive(pak_path)
        return self._archives[key]

    def index_pak(self, pak_path: Path) -> None:
        key = str(pak_path).lower()
        if key in self._indexed_paks or not pak_path.is_file():
            return
        self._indexed_paks.add(key)
        arc = self.get_archive(pak_path)
        for lower_name, entry in arc.entries.items():
            self._path_to_pak_entry[lower_name] = (pak_path, entry)
            base = lower_name.split("/")[-1]
            # CryEngine: Later patch PAKs (z_*) override earlier base assets
            self._basename_to_pak_entry[base] = (pak_path, entry)

    def index_directory_paks(self, dir_path: Path, pattern: str = "*.pak") -> None:
        if not dir_path.is_dir():
            return
        # Official CryEngine order: sort base files first, patch files (z_*) last
        paks = sorted(dir_path.glob(pattern), key=cryengine_pak_sort_key)
        for pak_file in paks:
            self.index_pak(pak_file)

    def find_entry(self, clean_path: str) -> Optional[Tuple[Path, AionPakEntry]]:
        clean_lower = clean_path.replace("\\", "/").strip().lstrip("/").lower()
        if not clean_lower:
            return None

        # 1. Exact relative path match
        match = self._path_to_pak_entry.get(clean_lower)
        if match:
            return match

        # 2. Stripped prefix matches (e.g. levels/common/, textures/, objects/)
        for prefix in ("levels/common/", "textures/", "objects/", "shaders/"):
            if clean_lower.startswith(prefix):
                sub = clean_lower[len(prefix):]
                match = self._path_to_pak_entry.get(sub)
                if match:
                    return match

        # 3. Basename match
        base = clean_lower.split("/")[-1]
        return self._basename_to_pak_entry.get(base)

    find_file = find_entry

    @property
    def indexed_paks_count(self) -> int:
        return len(self._indexed_paks)

    def extract_file(self, rel_path: str) -> Optional[bytes]:
        """Extracts and decompresses a file directly from indexed PAKs with LRU caching for small files."""
        clean_key = rel_path.replace("\\", "/").strip().lstrip("/").lower()
        if clean_key in self._file_cache:
            return self._file_cache[clean_key]

        entry_info = self.find_entry(rel_path)
        if not entry_info:
            return None
        pak_path, entry = entry_info
        archive = self.get_archive(pak_path)
        data = archive.read_entry(entry)

        if data is not None and len(data) <= 524288:  # Cache files <= 512KB
            if len(self._file_cache) >= 256:
                first_key = next(iter(self._file_cache))
                del self._file_cache[first_key]
            self._file_cache[clean_key] = data

        return data

    def save_cache(self, cache_file: Path | str) -> bool:
        """Serializes current catalog index to disk cache using compact JSON and transparent gzip."""
        try:
            cache_path = Path(cache_file)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            entries_list = []
            for lower_name, (pak_path, entry) in self._path_to_pak_entry.items():
                try:
                    rel_pak = os.path.relpath(pak_path, self.client_root).replace("\\", "/")
                except Exception:
                    rel_pak = str(pak_path).replace("\\", "/")
                entries_list.append([
                    lower_name,
                    entry.name,
                    entry.method,
                    entry.csize,
                    entry.usize,
                    entry.crc,
                    entry.local_offset,
                    rel_pak,
                ])

            indexed_paks_list = []
            for p in self._indexed_paks:
                try:
                    rel_p = os.path.relpath(p, self.client_root).replace("\\", "/")
                except Exception:
                    rel_p = str(p).replace("\\", "/")
                indexed_paks_list.append(rel_p)

            payload = {
                "version": 1,
                "timestamp": time.time(),
                "client_root": str(self.client_root),
                "indexed_paks": indexed_paks_list,
                "entries": entries_list,
            }
            raw_json = json.dumps(payload, separators=(",", ":"))
            raw_bytes = raw_json.encode("utf-8")

            _1MB = 1024 * 1024
            gz_path = cache_path.with_name(cache_path.name + ".gz") if not cache_path.name.endswith(".gz") else cache_path

            if len(raw_bytes) > _1MB or cache_path.name.endswith(".gz"):
                with gzip.open(gz_path, "wb") as f_gz:
                    f_gz.write(raw_bytes)
                if not cache_path.name.endswith(".gz") and cache_path.is_file():
                    cache_path.unlink(missing_ok=True)
            else:
                cache_path.write_bytes(raw_bytes)
                if gz_path != cache_path and gz_path.is_file():
                    gz_path.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def load_cache(self, cache_file: Path | str) -> bool:
        """Loads catalog index from disk cache (supporting both .json and .json.gz)."""
        try:
            cache_path = Path(cache_file)
            gz_path = cache_path.with_name(cache_path.name + ".gz") if not cache_path.name.endswith(".gz") else cache_path

            raw_bytes: Optional[bytes] = None
            if gz_path.is_file():
                try:
                    with gzip.open(gz_path, "rb") as f_gz:
                        raw_bytes = f_gz.read()
                except Exception:
                    raw_bytes = None

            if raw_bytes is None and cache_path.is_file():
                raw_bytes = cache_path.read_bytes()

            if raw_bytes is None:
                return False

            data = json.loads(raw_bytes.decode("utf-8"))
            if not isinstance(data, dict) or data.get("version") != 1:
                return False

            entries_list = data.get("entries", [])
            indexed_paks_list = data.get("indexed_paks", [])

            pak_path_cache: Dict[str, Tuple[Path, str]] = {}
            for rel_p in indexed_paks_list:
                fp = self.client_root / rel_p if not os.path.isabs(rel_p) else Path(rel_p)
                pair = (fp, str(fp))
                pak_path_cache[rel_p] = pair
                self._indexed_paks.add(pair[1].lower())

            path_to_pak = self._path_to_pak_entry
            base_to_pak = self._basename_to_pak_entry
            client_root = self.client_root

            for item in entries_list:
                # [lower_name, name, method, csize, usize, crc, local_offset, rel_pak]
                lower_name, name, method, csize, usize, crc, loc_offset, rel_pak = item
                pair = pak_path_cache.get(rel_pak)
                if pair is None:
                    fp = client_root / rel_pak if not os.path.isabs(rel_pak) else Path(rel_pak)
                    pair = (fp, str(fp))
                    pak_path_cache[rel_pak] = pair
                    self._indexed_paks.add(pair[1].lower())

                full_pak, pak_str = pair
                entry = AionPakEntry(
                    name=name,
                    method=method,
                    csize=csize,
                    usize=usize,
                    crc=crc,
                    local_offset=loc_offset,
                    pak_path=pak_str,
                )
                val = (full_pak, entry)
                path_to_pak[lower_name] = val
                idx = lower_name.rfind("/")
                base = lower_name[idx + 1 :] if idx != -1 else lower_name
                if base not in base_to_pak:
                    base_to_pak[base] = val

            return len(self._path_to_pak_entry) > 0
        except Exception:
            return False

    def close(self) -> None:
        """Closes all open pak archive handles in catalog."""
        for arc in self._archives.values():
            arc.close()
        self._archives.clear()
        self._file_cache.clear()


class AionClientPakResolver:
    """
    High-performance on-demand resource resolver for CGF models, CGA entities, DDS textures, and Shaders.
    Extracts requested resources into a local cache on first use.
    """

    def __init__(self, client_root: str | Path):
        self.client_root = Path(client_root)
        self.cache_dir = self._init_cache_dir()
        self.catalog = AionCatalogIndex(self.client_root)
        self._resolved_cache: Dict[str, Optional[Path]] = {}
        self._directory_children_cache: Dict[Path, Dict[str, Path]] = {}
        self._catalog_initialized = False

    def _init_cache_dir(self) -> Path:
        candidate = self.client_root / ".aion_cache"
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            test_file = candidate / ".perm_check"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
            return candidate
        except Exception:
            temp_cache = Path(tempfile.gettempdir()) / "aion_blender_cache" / "global"
            temp_cache.mkdir(parents=True, exist_ok=True)
            return temp_cache

    def ensure_catalog(self) -> None:
        if self._catalog_initialized:
            return

        cache_file = self.cache_dir / "catalog_index.json"
        if self.catalog.load_cache(cache_file):
            self._catalog_initialized = True
            return

        # Index common texture & mesh PAKs
        common_dir = self.client_root / "levels" / "common"
        if common_dir.is_dir():
            self.catalog.index_directory_paks(common_dir, "*.pak")

        # Index client Textures PAKs (recursively)
        tex_dir = self.client_root / "Textures"
        if tex_dir.is_dir():
            for pak_file in tex_dir.rglob("*.pak"):
                self.catalog.index_pak(pak_file)

        # Index client Objects PAKs (recursively for all subdirectories like npc/level_object, etc.)
        obj_dir = self.client_root / "objects"
        if obj_dir.is_dir():
            for pak_file in obj_dir.rglob("*.pak"):
                self.catalog.index_pak(pak_file)

        # Index Data/npcs PAK
        npc_pak = self.client_root / "Data" / "npcs" / "npcs.pak"
        if npc_pak.is_file():
            self.catalog.index_pak(npc_pak)

        # Index Data/world PAK
        world_pak = self.client_root / "Data" / "world" / "world.pak"
        if world_pak.is_file():
            self.catalog.index_pak(world_pak)

        # Index Shaders (recursively)
        shaders_dir = self.client_root / "Shaders"
        if shaders_dir.is_dir():
            for pak_file in shaders_dir.rglob("*.pak"):
                self.catalog.index_pak(pak_file)

        self._catalog_initialized = True

        try:
            self.catalog.save_cache(cache_file)
        except Exception:
            pass

    def _index_candidates_for_ref(self, clean: str) -> None:
        """On-demand indexing of candidate PAK directories for resources not yet in catalog."""
        clean_norm = clean.replace("\\", "/").strip().lstrip("/").lower()
        parts = clean_norm.split("/")
        if not parts:
            return

        if len(parts) > 1:
            cand_dir = self.client_root / Path(*parts[:-1])
            if cand_dir.is_dir():
                self.catalog.index_directory_paks(cand_dir, "*.pak")
            if len(parts) > 2:
                cand_parent = self.client_root / Path(*parts[:-2])
                if cand_parent.is_dir():
                    self.catalog.index_directory_paks(cand_parent, "*.pak")

        if clean_norm.startswith("objects/"):
            obj_dir = self.client_root / "objects"
            if len(parts) >= 2:
                sub_dir = obj_dir / parts[1]
                if sub_dir.is_dir():
                    self.catalog.index_directory_paks(sub_dir, "*.pak")

    def close(self) -> None:
        """Closes catalog archives and releases all file locks."""
        if self.catalog:
            self.catalog.close()

    def resolve_resource(self, reference: str, target_lod: int = 0) -> Optional[Path]:
        """
        Resolves a resource reference (CGF, DDS, CSL, XML) to an absolute Path on disk.
        If packed in a .pak, extracts it into the cache directory on demand.
        Supports LOD companion files (<stem>_lod<N>.cgf) when target_lod > 0.
        """
        clean = reference.replace("\\", "/").strip().lstrip("/").lower()
        if not clean:
            return None

        # LOD Resolution: if target_lod > 0 and reference is a .cgf
        if target_lod > 0 and clean.endswith(".cgf"):
            stem = clean[:-4]
            # Try from target_lod down to 1
            for lvl in range(target_lod, 0, -1):
                lod_ref = f"{stem}_lod{lvl}.cgf"
                res = self._resolve_single_resource(lod_ref)
                if res and res.is_file():
                    return res

        return self._resolve_single_resource(clean)

    def _resolve_single_resource(self, clean: str) -> Optional[Path]:
        if clean in self._resolved_cache:
            return self._resolved_cache[clean]

        # 1. Check if already extracted in cache
        cached_path = self.cache_dir / clean
        if cached_path.is_file():
            self._resolved_cache[clean] = cached_path
            return cached_path

        # Also check with basename in cache
        base_name = clean.split("/")[-1]
        base_cached = self.cache_dir / base_name
        if base_cached.is_file():
            self._resolved_cache[clean] = base_cached
            return base_cached

        # 2. Check if exists loose in client root
        loose = self._resolve_loose(clean)
        if loose is not None:
            self._resolved_cache[clean] = loose
            return loose

        # Also check without levels/common/ prefix if loose
        if clean.startswith("levels/common/"):
            short_clean = clean[len("levels/common/"):]
            loose_short = self._resolve_loose(short_clean)
            if loose_short is not None:
                self._resolved_cache[clean] = loose_short
                return loose_short

        # 3. Ensure catalog index is loaded and query it
        self.ensure_catalog()
        match = self.catalog.find_entry(clean)
        if not match and clean.startswith("levels/common/"):
            match = self.catalog.find_entry(clean[len("levels/common/"):])
        if not match:
            self._index_candidates_for_ref(clean)
            match = self.catalog.find_entry(clean)
        if not match and clean.startswith("levels/common/"):
            match = self.catalog.find_entry(clean[len("levels/common/"):])

        if match:
            pak_path, entry = match
            arc = self.catalog.get_archive(pak_path)
            data = arc.read_entry(entry)
            if data is not None:
                dest_path = self.cache_dir / clean
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_bytes(data)
                self._resolved_cache[clean] = dest_path
                return dest_path

        self._resolved_cache[clean] = None
        return None

    def resolve_resources_batch(
        self,
        references: Iterable[str],
        max_workers: int = 8,
        target_lod: int = 0,
    ) -> Dict[str, Optional[Path]]:
        """
        Extracts and resolves multiple resources concurrently across worker threads.
        Bypasses main thread disk/decompression bottlenecks.
        Supports target_lod (0..3) for automatic companion LOD mesh resolution.
        """
        import concurrent.futures

        refs = list(references)
        results: Dict[str, Optional[Path]] = {}
        pending = []

        for ref in refs:
            clean = ref.replace("\\", "/").strip().lstrip("/").lower()
            if target_lod == 0 and clean in self._resolved_cache:
                results[ref] = self._resolved_cache[clean]
            else:
                pending.append(ref)

        if not pending:
            return results

        self.ensure_catalog()

        def _worker(r: str) -> Tuple[str, Optional[Path]]:
            return r, self.resolve_resource(r, target_lod=target_lod)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_worker, r) for r in pending]
            for future in concurrent.futures.as_completed(futures):
                try:
                    orig_ref, res_path = future.result()
                    results[orig_ref] = res_path
                except Exception:
                    pass

        return results

    resolve_file = resolve_resource

    def _resolve_loose(self, normalized_relative: str) -> Optional[Path]:
        current = self.client_root
        parts = normalized_relative.split("/")
        for part in parts:
            if not part:
                continue
            cand = current / part
            if cand.exists():
                current = cand
                continue
            if not current.is_dir():
                return None
            if current not in self._directory_children_cache:
                self._directory_children_cache[current] = {
                    child.name.lower(): child for child in current.iterdir()
                }
            match = self._directory_children_cache[current].get(part.lower())
            if match is None:
                return None
            current = match
        return current if current.is_file() else None


def pack_level_directory(source_dir: str | Path, output_pak: str | Path, create_backup: bool = True) -> tuple[int, int]:
    """
    Packs a directory of level files (e.g. .aion_cache or edited level folder) into an official Aion Level.pak.
    Applies raw Deflate compression and Aion 32-byte XOR stream encryption.
    Optionally backs up the existing Level.pak as Level.pak.bak.
    Returns (files_packed_count, total_bytes_written).
    """
    source_path = Path(source_dir)
    target_pak = Path(output_pak)

    if create_backup and target_pak.is_file():
        backup_path = target_pak.with_suffix(".pak.bak")
        if not backup_path.exists():
            shutil.copy2(target_pak, backup_path)

    tmp_out = target_pak.with_suffix(".tmp_pak")
    file_records = []

    with open(tmp_out, "wb") as f:
        for root, dirs, files in os.walk(source_path):
            for file in sorted(files):
                if file.startswith("."):
                    continue
                full_path = os.path.join(root, file)
                rel_name = os.path.relpath(full_path, source_path).replace("\\", "/")
                raw_bytes = Path(full_path).read_bytes()
                crc = zlib.crc32(raw_bytes)
                usize = len(raw_bytes)

                comp_obj = zlib.compressobj(6, zlib.DEFLATED, -15)
                comp_bytes = comp_obj.compress(raw_bytes) + comp_obj.flush()
                method = 8
                if len(comp_bytes) >= usize:
                    method = 0
                    comp_bytes = raw_bytes

                csize = len(comp_bytes)
                obf_bytes = deobfuscate_stream(comp_bytes)

                loc_offset = f.tell()
                name_bytes = rel_name.encode("latin1")
                loc_header = bytearray(SIG_LOCAL)
                loc_header += struct.pack("<HHHHHIIIHH", 20, 0, method, 0, 0, crc, csize, usize, len(name_bytes), 0)
                loc_header += name_bytes
                f.write(loc_header)
                f.write(obf_bytes)

                file_records.append({
                    "name_bytes": name_bytes,
                    "method": method,
                    "crc": crc,
                    "csize": csize,
                    "usize": usize,
                    "loc_offset": loc_offset,
                })

        cd_offset = f.tell()
        for r in file_records:
            cd_entry = bytearray(SIG_CENTRAL)
            cd_entry += struct.pack("<HHHHHHIIIHHHHHII", 20, 20, 0, r["method"], 0, 0, r["crc"], r["csize"], r["usize"], len(r["name_bytes"]), 0, 0, 0, 0, 0, r["loc_offset"])
            cd_entry += r["name_bytes"]
            f.write(cd_entry)

        cd_size = f.tell() - cd_offset
        eocd = bytearray(SIG_EOCD)
        eocd += struct.pack("<HHHHIIH", 0, 0, len(file_records), len(file_records), cd_size, cd_offset, 0)
        f.write(eocd)

    total_bytes = tmp_out.stat().st_size
    os.replace(str(tmp_out), str(target_pak))
    return len(file_records), total_bytes


# Module-level singleton resolver
_GLOBAL_RESOLVER: Optional[AionClientPakResolver] = None


def get_pak_resolver(client_root: str | Path | None) -> Optional[AionClientPakResolver]:
    """Returns or creates the singleton AionClientPakResolver for the given client root."""
    global _GLOBAL_RESOLVER
    if not client_root:
        return None
    root_path = Path(client_root)
    if _GLOBAL_RESOLVER is None or _GLOBAL_RESOLVER.client_root != root_path:
        _GLOBAL_RESOLVER = AionClientPakResolver(root_path)
    return _GLOBAL_RESOLVER
