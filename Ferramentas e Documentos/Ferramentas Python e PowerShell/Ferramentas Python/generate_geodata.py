import os
import sys
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(TOOLS_DIR)))
#!/usr/bin/env python3
"""
Aion Client 4.5 Geodata Compiler
Extracts terrain heightmaps (land_map.h32), level metadata (leveldata.xml),
brush placements (brush.lst), and 3D collision meshes (.cgf) from Client 4.5 levels.
Compiles them into optimized binary server geodata files (*.geo) under data/server/data/geodata/.
"""

import os
import sys
import struct
import math
import glob
import xml.etree.ElementTree as ET
from collections import defaultdict

# Binary Magic for Client 4.5 Server Geodata
MAGIC = b"AIONGEO45"
VERSION = 1

def parse_cgf_mesh(cgf_path):
    """
    Parses a CryEngine/NCAion CGF file to extract collision vertices and triangle indices.
    Returns: list of (vertices, indices, bbox_min, bbox_max)
    """
    if not os.path.exists(cgf_path):
        return None

    try:
        with open(cgf_path, "rb") as f:
            data = f.read()
    except Exception:
        return None

    if len(data) < 32:
        return None

    # Verify signature
    sig = data[:7]
    if sig != b"NCAion\x00" and sig != b"CryTek\x00":
        return None

    # Chunk table offset at byte 16
    chunk_table_offset = struct.unpack_from("<I", data, 16)[0]
    if chunk_table_offset + 4 > len(data):
        return None

    num_chunks = struct.unpack_from("<I", data, chunk_table_offset)[0]
    chunks = []
    for i in range(num_chunks):
        entry_off = chunk_table_offset + 4 + i * 16
        if entry_off + 16 > len(data):
            break
        ctype, cver, coff, cid = struct.unpack_from("<IIII", data, entry_off)
        chunks.append((ctype, cver, coff, cid))

    # Find Mesh chunk (0xCCCC0000)
    mesh_results = []
    for ctype, cver, coff, cid in chunks:
        if ctype == 0xCCCC0000: # ChunkType_Mesh
            if coff + 32 > len(data):
                continue
            # Header: flags1(4), flags2(4), nVerts(4), nTVerts(4), nFaces(4)
            # In 0x744 desc:
            hdr = struct.unpack_from("<8i", data, coff)
            # Find nVerts and nFaces in header
            n_verts = hdr[5]
            n_faces = hdr[6]
            if n_verts <= 0 or n_verts > 65535 or n_faces <= 0 or n_faces > 65535:
                # Try alternate offsets in chunk desc
                n_verts = hdr[3]
                n_faces = hdr[4]
            if n_verts <= 0 or n_verts > 65535 or n_faces <= 0 or n_faces > 65535:
                continue

            # In CryEngine 1 mesh chunk, vertices start after header
            # Vertices are 3 x float (12 bytes)
            # Faces are 3 x ushort or 3 x uint + material/flags
            vert_offset = coff + 64 # approximate header size
            if vert_offset + n_verts * 12 > len(data):
                vert_offset = coff + 32

            verts = []
            min_x, min_y, min_z = 1e9, 1e9, 1e9
            max_x, max_y, max_z = -1e9, -1e9, -1e9

            for v in range(n_verts):
                v_off = vert_offset + v * 12
                if v_off + 12 > len(data):
                    break
                vx, vy, vz = struct.unpack_from("<3f", data, v_off)
                verts.append((vx, vy, vz))
                min_x = min(min_x, vx)
                min_y = min(min_y, vy)
                min_z = min(min_z, vz)
                max_x = max(max_x, vx)
                max_y = max(max_y, vy)
                max_z = max(max_z, vz)

            # Faces offset
            faces_offset = vert_offset + n_verts * 12
            faces = []
            for f in range(n_faces):
                f_off = faces_offset + f * 12 # 3 ints or 3 shorts + flags
                if f_off + 6 > len(data):
                    break
                # Try ushort indices
                i0, i1, i2 = struct.unpack_from("<3H", data, f_off)
                if i0 < n_verts and i1 < n_verts and i2 < n_verts:
                    faces.append((i0, i1, i2))

            if verts and faces:
                mesh_results.append((verts, faces, (min_x, min_y, min_z), (max_x, max_y, max_z)))

    return mesh_results if mesh_results else None

def parse_brush_lst(brush_path, base_dir):
    """
    Parses brush.lst to extract all placed static meshes with their 3x4 world transform matrix.
    Returns: list of (cgf_path, matrix_3x4, bbox_min, bbox_max)
    """
    if not os.path.exists(brush_path):
        return []

    try:
        with open(brush_path, "rb") as f:
            data = f.read()
    except Exception:
        return []

    if len(data) < 24:
        return []

    # Read CGF string table count
    model_count = struct.unpack_from("<I", data, 16)[0]
    str_len = struct.unpack_from("<I", data, 20)[0]
    if str_len == 0 or str_len > 512:
        str_len = 160 # default 160 bytes per model path

    cgf_models = []
    offset = 24
    for i in range(model_count):
        if offset + str_len > len(data):
            break
        raw_name = data[offset : offset + str_len]
        name = raw_name.split(b"\x00")[0].decode("latin1", errors="ignore").strip()
        cgf_models.append(name)
        offset += str_len

    # Instance table
    # Align to instance count offset
    if offset + 4 > len(data):
        return []

    inst_count = struct.unpack_from("<I", data, offset)[0]
    if inst_count == 0 or inst_count > 1000000:
        # Check adjacent offset (e.g. 71699)
        for cand in [offset - 4, offset, offset + 4]:
            if 0 <= cand + 4 <= len(data):
                c = struct.unpack_from("<I", data, cand)[0]
                if 1 <= c <= 100000 and (len(data) - cand - 4) % c == 0:
                    offset = cand
                    inst_count = c
                    break

    offset += 4
    inst_size = 108 # 108 bytes per brush instance
    instances = []

    for i in range(inst_count):
        inst_off = offset + i * inst_size
        if inst_off + inst_size > len(data):
            break
        # Model index at inst_off + 8 (int32)
        model_idx = struct.unpack_from("<i", data, inst_off + 8)[0]
        if 0 <= model_idx < len(cgf_models):
            cgf_name = cgf_models[model_idx]
            # 3x4 Matrix starts at inst_off + 24 (12 floats)
            try:
                m_floats = struct.unpack_from("<12f", data, inst_off + 24)
                # m00, m01, m02, Tx, m10, m11, m12, Ty, m20, m21, m22, Tz
                mat3x4 = [
                    (m_floats[0], m_floats[1], m_floats[2], m_floats[3]),
                    (m_floats[4], m_floats[5], m_floats[6], m_floats[7]),
                    (m_floats[8], m_floats[9], m_floats[10], m_floats[11]),
                ]
                instances.append((cgf_name, mat3x4))
            except Exception:
                continue

    return instances

def build_geodata_for_map(map_id, level_name, levels_dir, output_geo_path, zonemap_info):
    """
    Compiles a single Client 4.5 map into an optimized server geodata binary file.
    """
    level_path = os.path.join(levels_dir, level_name.lower())
    if not os.path.exists(level_path):
        return False

    # 1. Heightmap
    h32_path = os.path.join(level_path, "terrain", "land_map.h32")
    h32_data = b""
    if os.path.exists(h32_path):
        with open(h32_path, "rb") as f:
            h32_data = f.read()

    # 2. Level info / XML
    leveldata_path = os.path.join(level_path, "leveldata.xml")
    unit_size = 2.0
    grid_w = 0
    grid_h = 0
    water_level = 0.0

    if os.path.exists(leveldata_path):
        try:
            tree = ET.parse(leveldata_path)
            linfo = tree.getroot().find(".//LevelInfo")
            if linfo is not None:
                unit_size = float(linfo.get("HeightmapUnitSize", "2"))
                grid_w = int(linfo.get("HeightmapXSize", "0"))
                grid_h = int(linfo.get("HeightmapYSize", "0"))
                water_level = float(linfo.get("WaterLevel", "0"))
        except Exception:
            pass

    if grid_w == 0 or grid_h == 0:
        if len(h32_data) > 0:
            sample_count = len(h32_data) // 3
            side = int(round(math.sqrt(sample_count)))
            grid_w = side
            grid_h = side
        else:
            grid_w = zonemap_info.get("width", 3072) // 2
            grid_h = zonemap_info.get("height", 3072) // 2

    world_size_x = zonemap_info.get("width", int(grid_w * unit_size))
    world_size_y = zonemap_info.get("height", int(grid_h * unit_size))
    if world_size_x == 0:
        world_size_x = int(grid_w * unit_size)
    if world_size_y == 0:
        world_size_y = int(grid_h * unit_size)

    # Convert 3-byte samples to 16-bit height samples
    num_samples = grid_w * grid_h
    height_u16_array = []
    if len(h32_data) >= num_samples * 3:
        for i in range(num_samples):
            idx = i * 3
            b0 = h32_data[idx]
            b1 = h32_data[idx + 1]
            val = b0 | (b1 << 8)
            height_u16_array.append(val)
    elif len(h32_data) > 0:
        actual_samples = len(h32_data) // 3
        for i in range(actual_samples):
            idx = i * 3
            val = h32_data[idx] | (h32_data[idx + 1] << 8)
            height_u16_array.append(val)
        # pad remaining
        while len(height_u16_array) < num_samples:
            height_u16_array.append(0)
    else:
        height_u16_array = [0] * num_samples

    # 3. Brush / 3D Collision Geometry
    brush_path = os.path.join(level_path, "brush.lst")
    instances = parse_brush_lst(brush_path, levels_dir)

    # Cache parsed CGFs to avoid redundant disk reads
    cgf_cache = {}
    collision_meshes = []

    for cgf_rel_path, mat3x4 in instances:
        # Check if it's a collision obstacle or key structure
        is_collision = ("collision_wall" in cgf_rel_path.lower() or
                        "obstacle" in cgf_rel_path.lower() or
                        "structures" in cgf_rel_path.lower() or
                        "building" in cgf_rel_path.lower() or
                        "bridge" in cgf_rel_path.lower() or
                        "castle" in cgf_rel_path.lower() or
                        "tower" in cgf_rel_path.lower() or
                        "door" in cgf_rel_path.lower())

        # Resolve full CGF path
        full_cgf_path = os.path.join(os.path.dirname(levels_dir), cgf_rel_path)
        if not os.path.exists(full_cgf_path):
            full_cgf_path = os.path.join(levels_dir, cgf_rel_path)

        if full_cgf_path not in cgf_cache:
            cgf_cache[full_cgf_path] = parse_cgf_mesh(full_cgf_path)

        mesh_data = cgf_cache[full_cgf_path]
        if not mesh_data:
            # If CGF not parsed directly, create bounding box hull from transform
            tx = mat3x4[0][3]
            ty = mat3x4[1][3]
            tz = mat3x4[2][3]
            # Use small bounding box hull
            size = 8.0
            if "16m" in cgf_rel_path: size = 16.0
            elif "32m" in cgf_rel_path: size = 32.0
            elif "64m" in cgf_rel_path: size = 64.0
            elif "100m" in cgf_rel_path: size = 100.0

            half = size / 2.0
            bmin = (tx - half, ty - half, tz)
            bmax = (tx + half, ty + half, tz + size)
            flags = 1 # Physical obstacle
            if "walk_" in cgf_rel_path.lower():
                flags = 2 # Walkable surface / platform
            elif "door" in cgf_rel_path.lower():
                flags = 4 # Door

            # Create simple box geometry (8 vertices, 12 triangles)
            box_verts = [
                (bmin[0], bmin[1], bmin[2]), (bmax[0], bmin[1], bmin[2]),
                (bmax[0], bmax[1], bmin[2]), (bmin[0], bmax[1], bmin[2]),
                (bmin[0], bmin[1], bmax[2]), (bmax[0], bmin[1], bmax[2]),
                (bmax[0], bmax[1], bmax[2]), (bmin[0], bmax[1], bmax[2]),
            ]
            box_indices = [
                0,1,2, 0,2,3, # bottom
                4,6,5, 4,7,6, # top
                0,4,5, 0,5,1, # front
                2,6,7, 2,7,3, # back
                0,3,7, 0,7,4, # left
                1,5,6, 1,6,2, # right
            ]
            collision_meshes.append({
                "name": os.path.basename(cgf_rel_path),
                "flags": flags,
                "bmin": bmin,
                "bmax": bmax,
                "verts": box_verts,
                "indices": box_indices
            })
            continue

        # Transform CGF vertices to world space using 3x4 matrix
        for verts, faces, l_bmin, l_bmax in mesh_data:
            w_verts = []
            w_bmin = [1e9, 1e9, 1e9]
            w_bmax = [-1e9, -1e9, -1e9]
            for lx, ly, lz in verts:
                wx = mat3x4[0][0] * lx + mat3x4[0][1] * ly + mat3x4[0][2] * lz + mat3x4[0][3]
                wy = mat3x4[1][0] * lx + mat3x4[1][1] * ly + mat3x4[1][2] * lz + mat3x4[1][3]
                wz = mat3x4[2][0] * lx + mat3x4[2][1] * ly + mat3x4[2][2] * lz + mat3x4[2][3]
                w_verts.append((wx, wy, wz))
                w_bmin[0] = min(w_bmin[0], wx)
                w_bmin[1] = min(w_bmin[1], wy)
                w_bmin[2] = min(w_bmin[2], wz)
                w_bmax[0] = max(w_bmax[0], wx)
                w_bmax[1] = max(w_bmax[1], wy)
                w_bmax[2] = max(w_bmax[2], wz)

            flat_indices = []
            for i0, i1, i2 in faces:
                flat_indices.extend([i0, i1, i2])

            flags = 1
            if "walk_" in cgf_rel_path.lower():
                flags = 2
            elif "door" in cgf_rel_path.lower():
                flags = 4

            collision_meshes.append({
                "name": os.path.basename(cgf_rel_path),
                "flags": flags,
                "bmin": tuple(w_bmin),
                "bmax": tuple(w_bmax),
                "verts": w_verts,
                "indices": flat_indices
            })

    # 4. Build Spatial Grid (32x32 cells over world size)
    grid_cells_x = 32
    grid_cells_y = 32
    cell_w = max(1.0, float(world_size_x) / grid_cells_x)
    cell_h = max(1.0, float(world_size_y) / grid_cells_y)

    spatial_grid = defaultdict(list)
    for m_idx, m in enumerate(collision_meshes):
        min_gx = max(0, min(grid_cells_x - 1, int(m["bmin"][0] / cell_w)))
        max_gx = max(0, min(grid_cells_x - 1, int(m["bmax"][0] / cell_w)))
        min_gy = max(0, min(grid_cells_y - 1, int(m["bmin"][1] / cell_h)))
        max_gy = max(0, min(grid_cells_y - 1, int(m["bmax"][1] / cell_h)))

        for gy in range(min_gy, max_gy + 1):
            for gx in range(min_gx, max_gx + 1):
                spatial_grid[(gx, gy)].append(m_idx)

    # 5. Serialize into Binary Server Geodata
    os.makedirs(os.path.dirname(output_geo_path), exist_ok=True)
    with open(output_geo_path, "wb") as out:
        # Header (64 bytes)
        out.write(MAGIC)                          # 9 bytes
        out.write(struct.pack("<B", 0))          # 1 byte padding (10 bytes)
        out.write(struct.pack("<H", VERSION))    # 2 bytes (12 bytes)
        out.write(struct.pack("<I", int(map_id)))# 4 bytes (16 bytes)
        out.write(struct.pack("<II", world_size_x, world_size_y)) # 8 bytes (24 bytes)
        out.write(struct.pack("<II", grid_w, grid_h))             # 8 bytes (32 bytes)
        out.write(struct.pack("<ff", unit_size, water_level))     # 8 bytes (40 bytes)
        out.write(struct.pack("<II", grid_cells_x, grid_cells_y)) # 8 bytes (48 bytes)
        out.write(struct.pack("<I", len(height_u16_array)))       # 4 bytes (52 bytes)
        out.write(struct.pack("<I", len(collision_meshes)))       # 4 bytes (56 bytes)
        out.write(b"\x00" * 8)                                    # 8 bytes reserved (64 bytes total)

        # Heightmap Array (packed uint16)
        h_bytes = struct.pack(f"<{len(height_u16_array)}H", *height_u16_array)
        out.write(h_bytes)

        # Meshes Array
        for m in collision_meshes:
            name_bytes = m["name"].encode("utf-8")
            out.write(struct.pack("<H", len(name_bytes)))
            out.write(name_bytes)
            out.write(struct.pack("<I", m["flags"]))
            out.write(struct.pack("<6f", m["bmin"][0], m["bmin"][1], m["bmin"][2],
                                         m["bmax"][0], m["bmax"][1], m["bmax"][2]))
            
            # Vertices
            out.write(struct.pack("<I", len(m["verts"])))
            for vx, vy, vz in m["verts"]:
                out.write(struct.pack("<3f", vx, vy, vz))

            # Triangle Indices
            out.write(struct.pack("<I", len(m["indices"])))
            if m["indices"]:
                out.write(struct.pack(f"<{len(m['indices'])}H", *m["indices"]))

        # Spatial Grid Index
        for gy in range(grid_cells_y):
            for gx in range(grid_cells_x):
                mesh_ids = spatial_grid.get((gx, gy), [])
                out.write(struct.pack("<H", len(mesh_ids)))
                if mesh_ids:
                    out.write(struct.pack(f"<{len(mesh_ids)}H", *mesh_ids))

    return True

def main():
    print("=" * 70)
    print("Aion Client 4.5 Server Geodata Generation Pipeline")
    print("=" * 70)

    base_dir = PROJECT_ROOT
    client_levels = os.path.join(base_dir, "Produto Final", "data", "client", "levels")
    zonemap_xml = os.path.join(base_dir, "Produto Final", "data", "client", "data", "world", "zonemap.xml")
    output_geodata_dir = os.path.join(base_dir, "Produto Final", "data", "server", "data", "geodata")

    if not os.path.exists(client_levels):
        print(f"ERROR: Levels directory not found at {client_levels}")
        sys.exit(1)

    # Parse zonemap.xml
    zonemaps = {}
    if os.path.exists(zonemap_xml):
        tree = ET.parse(zonemap_xml)
        for zm in tree.getroot().findall(".//zonemap"):
            zid = zm.find("id").text.strip()
            zname = zm.find("name").text.strip() if zm.find("name") is not None else ""
            w = int(zm.find("world_width").text.strip()) if zm.find("world_width") is not None else 3072
            h = int(zm.find("world_height").text.strip()) if zm.find("world_height") is not None else 3072
            zonemaps[zid] = {"name": zname, "width": w, "height": h}

    print(f"Loaded {len(zonemaps)} zonemap definitions.")
    os.makedirs(output_geodata_dir, exist_ok=True)

    success_count = 0
    total_maps = len(zonemaps)

    for zid, zinfo in zonemaps.items():
        lvl_name = zinfo["name"]
        if not lvl_name:
            continue
        out_file = os.path.join(output_geodata_dir, f"{zid}.geo")
        print(f"[*] Compiling Map {zid} ({lvl_name})...", end="", flush=True)
        if build_geodata_for_map(zid, lvl_name, client_levels, out_file, zinfo):
            file_size_kb = os.path.getsize(out_file) / 1024.0
            print(f" [OK] -> {file_size_kb:.1f} KB")
            success_count += 1
        else:
            print(" [SKIPPED - No Client Data]")

    print("=" * 70)
    print(f"[COMPLETE] Compiled {success_count}/{total_maps} maps into {output_geodata_dir}")
    print("=" * 70)

if __name__ == "__main__":
    main()
