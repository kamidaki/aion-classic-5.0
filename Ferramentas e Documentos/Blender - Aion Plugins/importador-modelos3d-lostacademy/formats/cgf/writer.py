"""
CryEngine 1 / Aion CGF Binary Serializer & Chunk Assembler.
Supports:
- Generating complete .cgf models from scratch (Meshes, Nodes, Materials, Skeletons)
- Non-destructive round-trip patching of existing CGFs preserving unknown chunks and metadata
- Preservation of metric units (Blender meters <-> CryEngine cm)
"""

from __future__ import annotations
import io
import struct
from typing import Any, Dict, List, Optional, Tuple

from .skeleton_writer import (
    serialize_bone_name_list,
    serialize_bone_initial_pos,
    serialize_bone_anim,
    serialize_skin_weights,
)

CHUNK_MESH = 0xCCCC0000
CHUNK_HELPER = 0xCCCC0001
CHUNK_BONE_ANIM = 0xCCCC0003
CHUNK_BONE_NAME_LIST = 0xCCCC0005
CHUNK_MTL_LIST = 0xCCCC0006
CHUNK_NODE = 0xCCCC000B
CHUNK_MTL = 0xCCCC000C
CHUNK_TIMING = 0xCCCC000E
CHUNK_BONE_INITIAL_POS = 0xCCCC0012
CHUNK_SOURCE_INFO = 0xCCCC0013

SIG_CGF = b"CryTek\x00\x00"


def serialize_texture_map(
    path: str = "",
    texture_type: int = 0,
    amount: int = 100,
    u_tile: bool = True,
    v_tile: bool = True,
    u_scl: float = 1.0,
    v_scl: float = 1.0,
) -> bytes:
    """Serializes a 236-byte texture slot block."""
    stream = io.BytesIO()
    # 128 bytes ASCII path
    path_bytes = path.replace("/", "\\").encode("latin-1")[:127]
    stream.write(path_bytes.ljust(128, b"\x00"))
    # 1 byte texture_type, 1 byte no_mip_map, 1 byte amount
    stream.write(struct.pack("<BBB", texture_type, 0, amount))
    # 32 bytes reserved
    stream.write(b"\x00" * 32)
    # u_tile, u_mirror, v_tile, v_mirror
    stream.write(struct.pack("<????", u_tile, False, v_tile, False))
    # reserved_3 (1 byte)
    stream.write(b"\x00")
    # ref_update (4), ref_size (4), ref_blur (float)
    stream.write(struct.pack("<IIf", 0, 0, 0.0))
    # 7 floats: u_off, u_scl, u_rot, v_off, v_scl, v_rot, w_rot
    stream.write(struct.pack("<7f", 0.0, u_scl, 0.0, 0.0, v_scl, 0.0, 0.0))
    # 7 uint32 controllers
    stream.write(struct.pack("<7I", 0, 0, 0, 0, 0, 0, 0))
    return stream.getvalue()


def serialize_mtl_chunk(
    name: str = "Material_01 (Aion_BG_Base)",
    diffuse_texture: str = "",
    bump_texture: str = "",
    specular_texture: str = "",
    opacity_texture: str = "",
    chunk_id: int = 0,
    version: int = 0x744,
    two_sided: bool = False,
    alpha_test: bool = False,
    emissive: bool = False,
) -> bytes:
    """Serializes a Material chunk (0xCCCC000C)."""
    stream = io.BytesIO()
    # 16-byte chunk header
    stream.write(struct.pack("<IIII", CHUNK_MTL, version, 0, chunk_id))
    # 128 bytes name
    name_bytes = name.encode("latin-1")[:127]
    stream.write(name_bytes.ljust(128, b"\x00"))
    # mtl_type = 1 (Standard)
    stream.write(struct.pack("<I", 1))

    # Diffuse, Specular, Ambient RGB (255, 255, 255)
    stream.write(struct.pack("<3B", 255, 255, 255))
    stream.write(struct.pack("<3B", 255, 255, 255))
    stream.write(struct.pack("<3B", 255, 255, 255))
    # 3 bytes padding
    stream.write(b"\x00\x00\x00")

    # specular_level, specular_shininess, self_illum, opacity
    self_illum = 1.0 if emissive else 0.0
    stream.write(struct.pack("<4f", 0.0, 10.0, self_illum, 1.0))
    # 8 bytes padding
    stream.write(b"\x00" * 8)

    # 10 texture maps:
    # 0: ambient, 1: diffuse, 2: specular, 3: opacity, 4: bump,
    # 5: gloss, 6: filter, 7: reflection, 8: subsurf, 9: detail
    stream.write(serialize_texture_map(""))  # ambient
    stream.write(serialize_texture_map(diffuse_texture))  # diffuse
    stream.write(serialize_texture_map(specular_texture))  # specular
    stream.write(serialize_texture_map(opacity_texture))  # opacity
    stream.write(serialize_texture_map(bump_texture))  # bump / normal
    stream.write(serialize_texture_map(""))  # gloss
    stream.write(serialize_texture_map(""))  # filter
    stream.write(serialize_texture_map(""))  # reflection
    stream.write(serialize_texture_map(""))  # subsurf
    stream.write(serialize_texture_map(""))  # detail

    # mtl_flags: bit 1 (2) = two_sided, etc.
    flags_val = 0
    if two_sided:
        flags_val |= 2
    stream.write(struct.pack("<I", flags_val))
    # mtl_collide, static_friction, sliding_friction
    stream.write(struct.pack("<3f", 0.0, 0.0, 0.0))

    return stream.getvalue()


def serialize_mesh_chunk(
    vertices: List[Tuple[float, float, float]],
    normals: List[Tuple[float, float, float]],
    faces: List[Tuple[int, int, int]],
    uvs: List[Tuple[float, float]],
    face_uvs: Optional[List[Tuple[int, int, int]]] = None,
    face_materials: Optional[List[int]] = None,
    skin_weights: Optional[List[List[Tuple[int, float]]]] = None,
    vertex_colors: Optional[List[Tuple[int, int, int]]] = None,
    chunk_id: int = 1,
    version: int = 0x744,
) -> bytes:
    """
    Serializes a Mesh chunk (0xCCCC0000).
    Vertices in meters are converted to cm (* 100).
    """
    stream = io.BytesIO()
    # 16-byte chunk header
    stream.write(struct.pack("<IIII", CHUNK_MESH, version, 0, chunk_id))

    has_weights = bool(skin_weights and len(skin_weights) == len(vertices))
    has_colors = bool(vertex_colors and len(vertex_colors) == len(vertices))

    num_vertices = len(vertices)
    num_uvs = len(uvs)
    num_faces = len(faces)

    stream.write(struct.pack("<??2s", has_weights, has_colors, b"\x00\x00"))
    stream.write(struct.pack("<4I", num_vertices, num_uvs, num_faces, 0))

    # Vertices (positions in cm + normals)
    for i in range(num_vertices):
        vx, vy, vz = vertices[i]
        nx, ny, nz = normals[i] if i < len(normals) else (0.0, 0.0, 1.0)
        stream.write(struct.pack("<6f", vx * 100.0, vy * 100.0, vz * 100.0, nx, ny, nz))

    # Faces (indices, material slot, smoothing group)
    for i in range(num_faces):
        v0, v1, v2 = faces[i]
        mat_id = face_materials[i] if face_materials and i < len(face_materials) else 0
        stream.write(struct.pack("<5I", v0, v1, v2, mat_id, 1))

    # UVs
    if num_uvs > 0:
        for u, v in uvs:
            stream.write(struct.pack("<2f", float(u), float(v)))
        for i in range(num_faces):
            if face_uvs and i < len(face_uvs):
                uv0, uv1, uv2 = face_uvs[i]
            else:
                uv0, uv1, uv2 = faces[i]
            stream.write(struct.pack("<3I", uv0, uv1, uv2))

    # Vertex Colors
    if has_colors and vertex_colors:
        for r, g, b in vertex_colors:
            stream.write(struct.pack("<3B", int(r), int(g), int(b)))

    # Skin Weights
    if has_weights and skin_weights:
        stream.write(serialize_skin_weights(skin_weights))

    return stream.getvalue()


def serialize_node_chunk(
    name: str = "mesh_node",
    mesh_chunk_id: int = 1,
    material_chunk_id: int = 0,
    chunk_id: int = 2,
    version: int = 0x744,
) -> bytes:
    """Serializes a Node chunk (0xCCCC000B) linking geometry to material."""
    stream = io.BytesIO()
    # 16-byte chunk header
    stream.write(struct.pack("<IIII", CHUNK_NODE, version, 0, chunk_id))

    # 64 bytes ASCII name
    name_bytes = name.encode("latin-1")[:63]
    stream.write(name_bytes.ljust(64, b"\x00"))

    # object_id (mesh_id), parent_id, num_children, material_id, is_group_head, is_group_member, reserved
    stream.write(struct.pack("<4I2B2s", mesh_chunk_id, 0xFFFFFFFF, 0, material_chunk_id, 0, 0, b"\x00\x00"))

    # 16-float transform matrix (Identity row-major)
    identity_16 = [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]
    stream.write(struct.pack("<16f", *identity_16))

    # position (3 floats in cm), rotation (4 floats), scale (3 floats)
    stream.write(struct.pack("<3f", 0.0, 0.0, 0.0))
    stream.write(struct.pack("<4f", 0.0, 0.0, 0.0, 1.0))
    stream.write(struct.pack("<3f", 1.0, 1.0, 1.0))

    # pos_ctrl_id, rot_ctrl_id, scl_ctrl_id, prop_str_len
    stream.write(struct.pack("<4I", 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0))

    return stream.getvalue()


def serialize_source_info_chunk(
    source_file: str = "exported.cgf",
    author: str = "LostAcademy Model Library",
    chunk_id: int = 3,
    version: int = 0x744,
) -> bytes:
    """Serializes a SourceInfo chunk (0xCCCC0013)."""
    stream = io.BytesIO()
    stream.write(source_file.encode("latin-1") + b"\x00")
    stream.write(b"2026-09-27\x00")
    stream.write(author.encode("latin-1") + b"\x00")
    return stream.getvalue()


def write_cgf(
    vertices: List[Tuple[float, float, float]],
    normals: List[Tuple[float, float, float]],
    faces: List[Tuple[int, int, int]],
    uvs: List[Tuple[float, float]],
    face_uvs: Optional[List[Tuple[int, int, int]]] = None,
    face_materials: Optional[List[int]] = None,
    diffuse_texture: str = "",
    bump_texture: str = "",
    specular_texture: str = "",
    node_name: str = "mesh_node",
    material_name: str = "Material_01",
    bone_names: Optional[List[str]] = None,
    bone_initial_pos: Optional[List[Tuple[float, ...]]] = None,
    bone_anim: Optional[List[Dict[str, Any]]] = None,
    skin_weights: Optional[List[List[Tuple[int, float]]]] = None,
) -> bytes:
    """
    Builds a complete, valid CryEngine 1 CGF file from mesh and optional skeleton data.
    """
    stream = io.BytesIO()

    # 1. File Header (20 bytes)
    stream.write(SIG_CGF)
    type_of_file = 0xFFFF0000
    cgf_version = 0x744
    table_offset_pos = stream.tell() + 8
    stream.write(struct.pack("<III", type_of_file, cgf_version, 0))  # Placeholder table_offset

    chunks_data: List[Tuple[int, int, int, bytes]] = []  # (raw_type, version, chunk_id, payload)
    current_chunk_id = 0

    # 0: Material Chunk
    mtl_bytes = serialize_mtl_chunk(
        name=f"{material_name} (Aion_BG_Base)",
        diffuse_texture=diffuse_texture,
        bump_texture=bump_texture,
        specular_texture=specular_texture,
        chunk_id=current_chunk_id,
    )
    chunks_data.append((CHUNK_MTL, 0x744, current_chunk_id, mtl_bytes))
    mtl_chunk_id = current_chunk_id
    current_chunk_id += 1

    # 1: Mesh Chunk
    mesh_chunk_id = current_chunk_id
    current_chunk_id += 1

    # 2: Node Chunk
    node_bytes = serialize_node_chunk(
        name=node_name,
        mesh_chunk_id=mesh_chunk_id,
        material_chunk_id=mtl_chunk_id,
        chunk_id=current_chunk_id,
    )
    chunks_data.append((CHUNK_NODE, 0x744, current_chunk_id, node_bytes))
    current_chunk_id += 1

    # Optional Skeletons
    if bone_names and bone_initial_pos and bone_anim:
        # BoneNameList
        bn_bytes = serialize_bone_name_list(bone_names, current_chunk_id)
        chunks_data.append((CHUNK_BONE_NAME_LIST, 0x744, current_chunk_id, bn_bytes))
        current_chunk_id += 1

        # BoneInitialPos
        bip_bytes = serialize_bone_initial_pos(bone_initial_pos, mesh_chunk_id, current_chunk_id)
        chunks_data.append((CHUNK_BONE_INITIAL_POS, 0x744, current_chunk_id, bip_bytes))
        current_chunk_id += 1

        # BoneAnim
        ba_bytes = serialize_bone_anim(bone_anim, current_chunk_id)
        chunks_data.append((CHUNK_BONE_ANIM, 0x290, current_chunk_id, ba_bytes))
        current_chunk_id += 1

    # Mesh Chunk serialization (after skinning ids are known)
    mesh_bytes = serialize_mesh_chunk(
        vertices=vertices,
        normals=normals,
        faces=faces,
        uvs=uvs,
        face_uvs=face_uvs,
        face_materials=face_materials,
        skin_weights=skin_weights,
        chunk_id=mesh_chunk_id,
    )
    # Insert mesh chunk at its designated slot
    chunks_data.insert(1, (CHUNK_MESH, 0x744, mesh_chunk_id, mesh_bytes))

    # SourceInfo Chunk
    src_bytes = serialize_source_info_chunk(f"{node_name}.cgf", chunk_id=current_chunk_id)
    chunks_data.append((CHUNK_SOURCE_INFO, 0x744, current_chunk_id, src_bytes))
    current_chunk_id += 1

    # 2. Write Chunk Payloads
    chunk_table_records: List[Tuple[int, int, int, int]] = []
    chunks_with_internal_header = {CHUNK_MESH, CHUNK_NODE, CHUNK_MTL, CHUNK_BONE_ANIM}
    for raw_type, ver, cid, payload in chunks_data:
        offset = stream.tell()
        patched_payload = bytearray(payload)
        if raw_type in chunks_with_internal_header and len(patched_payload) >= 16:
            struct.pack_into("<I", patched_payload, 8, offset)
        stream.write(patched_payload)
        chunk_table_records.append((raw_type, ver, offset, cid))

    # 3. Write Chunk Headers Table
    table_offset = stream.tell()
    stream.write(struct.pack("<I", len(chunk_table_records)))
    for raw_type, ver, off, cid in chunk_table_records:
        stream.write(struct.pack("<IIII", raw_type, ver, off, cid))

    # 4. Patch table_offset in File Header
    stream.seek(table_offset_pos)
    stream.write(struct.pack("<I", table_offset))

    return stream.getvalue()


def patch_cgf(
    original_cgf_bytes: bytes,
    new_vertices: Optional[List[Tuple[float, float, float]]] = None,
    new_normals: Optional[List[Tuple[float, float, float]]] = None,
    new_faces: Optional[List[Tuple[int, int, int]]] = None,
    new_uvs: Optional[List[Tuple[float, float]]] = None,
    new_face_uvs: Optional[List[Tuple[int, int, int]]] = None,
    new_face_materials: Optional[List[int]] = None,
    new_skin_weights: Optional[List[List[Tuple[int, float]]]] = None,
    new_diffuse_texture: Optional[str] = None,
    new_bump_texture: Optional[str] = None,
    new_specular_texture: Optional[str] = None,
    new_bone_names: Optional[List[str]] = None,
    new_bone_initial_pos: Optional[List[Tuple[float, ...]]] = None,
    new_bone_anim: Optional[List[Dict[str, Any]]] = None,
) -> bytes:
    """
    Non-destructively patches an existing CGF file.
    Re-encodes only modified chunks while preserving all unknown or unedited chunks byte-for-byte.
    """
    if len(original_cgf_bytes) < 32:
        raise ValueError("Invalid CGF file data: too small")

    stream = io.BytesIO(original_cgf_bytes)

    # 1. Parse header
    sig = ""
    while True:
        b = stream.read(1)
        if not b or b == b"\x00":
            break
        sig += b.decode("ascii", errors="replace")
    stream.read(1)  # terminator

    type_of_file = struct.unpack("<I", stream.read(4))[0]
    cgf_version = struct.unpack("<I", stream.read(4))[0]
    orig_table_offset = struct.unpack("<I", stream.read(4))[0]

    # 2. Read existing chunk table
    stream.seek(orig_table_offset)
    num_chunks = struct.unpack("<I", stream.read(4))[0]
    chunk_headers = []
    for i in range(num_chunks):
        raw_type, ver, off, cid = struct.unpack("<IIII", stream.read(16))
        chunk_headers.append({
            "type": raw_type,
            "version": ver,
            "offset": off,
            "id": cid,
        })

    # Sort chunks by offset to compute sizes
    sorted_chunks = sorted(chunk_headers, key=lambda c: c["offset"])
    chunk_sizes: Dict[int, int] = {}
    for idx, c in enumerate(sorted_chunks):
        c_off = c["offset"]
        if idx + 1 < len(sorted_chunks):
            next_off = sorted_chunks[idx + 1]["offset"]
        else:
            next_off = orig_table_offset
        chunk_sizes[c["id"]] = max(0, next_off - c_off)

    # 3. Build new chunks list
    out_chunks: List[Tuple[int, int, int, bytes]] = []

    for c in chunk_headers:
        cid = c["id"]
        ctype = c["type"]
        cver = c["version"]
        coff = c["offset"]
        csize = chunk_sizes.get(cid, 0)

        # Read original payload
        stream.seek(coff)
        orig_payload = stream.read(csize)

        payload_to_write = orig_payload

        # Case 1: Mesh chunk update
        if ctype == CHUNK_MESH and new_vertices is not None:
            # Reconstruct mesh chunk
            normals_use = new_normals if new_normals is not None else [(0.0, 0.0, 1.0)] * len(new_vertices)
            faces_use = new_faces if new_faces is not None else []
            uvs_use = new_uvs if new_uvs is not None else []
            payload_to_write = serialize_mesh_chunk(
                vertices=new_vertices,
                normals=normals_use,
                faces=faces_use,
                uvs=uvs_use,
                face_uvs=new_face_uvs,
                face_materials=new_face_materials,
                skin_weights=new_skin_weights,
                chunk_id=cid,
                version=cver,
            )

        # Case 2: Material chunk update (e.g. textures)
        elif ctype == CHUNK_MTL and (new_diffuse_texture is not None or new_bump_texture is not None or new_specular_texture is not None):
            # Patch texture slots directly in existing material payload
            # Diffuse is slot 1 (offset 16 + 128 + 4 + 3*3 + 3 + 4*4 + 8 + 236*1)
            # Or if payload is standard size, modify in-place
            patched_mtl = bytearray(orig_payload)
            # Texture block start = 16 (hdr) + 128 (name) + 4 (type) + 9 (colors) + 3 (pad) + 16 (floats) + 8 (pad) = 184
            if len(patched_mtl) >= 184 + 236 * 5:
                tex_block_start = 184
                if new_diffuse_texture is not None:
                    # Slot 1: Diffuse
                    d_off = tex_block_start + 236 * 1
                    diff_bytes = new_diffuse_texture.replace("/", "\\").encode("latin-1")[:127].ljust(128, b"\x00")
                    patched_mtl[d_off : d_off + 128] = diff_bytes
                if new_specular_texture is not None:
                    # Slot 2: Specular
                    s_off = tex_block_start + 236 * 2
                    spec_bytes = new_specular_texture.replace("/", "\\").encode("latin-1")[:127].ljust(128, b"\x00")
                    patched_mtl[s_off : s_off + 128] = spec_bytes
                if new_bump_texture is not None:
                    # Slot 4: Bump / Normal
                    b_off = tex_block_start + 236 * 4
                    bump_bytes = new_bump_texture.replace("/", "\\").encode("latin-1")[:127].ljust(128, b"\x00")
                    patched_mtl[b_off : b_off + 128] = bump_bytes
            payload_to_write = bytes(patched_mtl)

        # Case 3: BoneNameList update
        elif ctype == CHUNK_BONE_NAME_LIST and new_bone_names is not None:
            payload_to_write = serialize_bone_name_list(new_bone_names, chunk_id=cid, version=cver)

        # Case 4: BoneInitialPos update
        elif ctype == CHUNK_BONE_INITIAL_POS and new_bone_initial_pos is not None:
            # Keep original mesh_id
            orig_mesh_id = struct.unpack_from("<I", orig_payload, 0)[0] if len(orig_payload) >= 4 else 0
            payload_to_write = serialize_bone_initial_pos(new_bone_initial_pos, orig_mesh_id, chunk_id=cid, version=cver)

        # Case 5: BoneAnim update
        elif ctype == CHUNK_BONE_ANIM and new_bone_anim is not None:
            payload_to_write = serialize_bone_anim(new_bone_anim, chunk_id=cid, version=cver)

        out_chunks.append((ctype, cver, cid, payload_to_write))

    # 4. Assemble new file
    out_stream = io.BytesIO()
    out_stream.write(sig.encode("ascii") + b"\x00\x00")
    tbl_pos = out_stream.tell() + 8
    out_stream.write(struct.pack("<III", type_of_file, cgf_version, 0))

    new_table_records: List[Tuple[int, int, int, int]] = []
    chunks_with_internal_header = {CHUNK_MESH, CHUNK_NODE, CHUNK_MTL, CHUNK_BONE_ANIM}

    for ctype, cver, cid, payload in out_chunks:
        offset = out_stream.tell()
        patched_payload = bytearray(payload)
        if ctype in chunks_with_internal_header and len(patched_payload) >= 16:
            struct.pack_into("<I", patched_payload, 8, offset)
        out_stream.write(patched_payload)
        new_table_records.append((ctype, cver, offset, cid))

    # Write Table
    new_table_offset = out_stream.tell()
    out_stream.write(struct.pack("<I", len(new_table_records)))
    for ctype, cver, off, cid in new_table_records:
        out_stream.write(struct.pack("<IIII", ctype, cver, off, cid))

    # Patch table offset in header
    out_stream.seek(tbl_pos)
    out_stream.write(struct.pack("<I", new_table_offset))

    return out_stream.getvalue()

