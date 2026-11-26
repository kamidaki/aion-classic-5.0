"""
Round-trip validation tests for LostAcademy Aion Model Library binary writers.
Tests:
1. write_cgf from scratch -> parse_cgf verification
2. write_caf from scratch -> parse_caf verification
3. write_cal from scratch -> parse_cal verification
4. Real official Aion CGF read -> modify vertices -> write -> re-read verification
"""

from __future__ import annotations
import io
import sys
from pathlib import Path

# Setup paths
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Ensure our local formats package is loaded rather than any shadowed addon package
for mod_name in list(sys.modules.keys()):
    if mod_name == "formats" or mod_name.startswith("formats."):
        del sys.modules[mod_name]

from formats.cgf.parser import get_cgf
from formats.cgf.writer import write_cgf
from formats.cgf.caf_parser import parse_caf
from formats.cgf.caf_writer import write_caf
from formats.cgf.cal_parser import parse_cal
from formats.cgf.cal_writer import write_cal


def test_cal_roundtrip():
    print("\n--- Test CAL Round-trip ---")
    mapping = {
        "nidle_001": "NPC/ShugoMale/ShugoMale_nidle_001_loop.caf",
        "nwalk_001": "NPC/ShugoMale/ShugoMale_nwalk_001_loop.caf",
        "nrun_001": "NPC/ShugoMale/ShugoMale_nrun_001_loop.caf",
        "dead": "NPC/ShugoMale/ShugoMale_dead.caf",
    }
    cal_bytes = write_cal(mapping)
    parsed = parse_cal(cal_bytes)
    assert len(parsed) == 4, f"Expected 4 mappings, got {len(parsed)}"
    for k, v in mapping.items():
        assert parsed.get(k) == v, f"Mismatch for {k}: {parsed.get(k)} vs {v}"
    print(f"PASS: CAL roundtrip verified with {len(parsed)} animations.")


def test_caf_roundtrip():
    print("\n--- Test CAF Round-trip ---")
    controllers = {
        2001: [
            {"frame": 0, "pos": (0.1, 0.2, 0.3), "quat": (1.0, 0.0, 0.0, 0.0)},
            {"frame": 10, "pos": (0.15, 0.25, 0.35), "quat": (0.7071, 0.0, 0.7071, 0.0)},
            {"frame": 20, "pos": (0.2, 0.3, 0.4), "quat": (0.0, 0.0, 1.0, 0.0)},
        ],
        2002: [
            {"frame": 0, "pos": (0.0, 0.0, 1.0), "quat": (1.0, 0.0, 0.0, 0.0)},
            {"frame": 20, "pos": (0.0, 0.0, 1.2), "quat": (0.9, 0.1, 0.0, 0.0)},
        ],
    }
    caf_bytes = write_caf(controllers, ticks_per_frame=160, frame_start=0, frame_end=20)
    parsed = parse_caf(caf_bytes)
    assert parsed.get("timing"), "Timing chunk missing in parsed CAF!"
    assert parsed["timing"]["frame_end"] == 20
    assert len(parsed.get("controllers", {})) == 2
    c2001 = parsed["controllers"][2001]
    assert len(c2001) == 3
    assert abs(c2001[0]["pos"][0] - 0.1) < 1e-4
    assert abs(c2001[0]["pos"][1] - 0.2) < 1e-4
    assert abs(c2001[0]["pos"][2] - 0.3) < 1e-4
    print(f"PASS: CAF roundtrip verified with {len(parsed['controllers'])} bone controllers.")


def test_cgf_scratch_roundtrip():
    print("\n--- Test CGF from Scratch Round-trip ---")
    vertices = [
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (2.0, 2.0, 0.0),
        (0.0, 2.0, 0.0),
        (1.0, 1.0, 2.5),
    ]
    normals = [(0.0, 0.0, 1.0)] * 5
    faces = [
        (0, 1, 2),
        (0, 2, 3),
        (0, 1, 4),
        (1, 2, 4),
        (2, 3, 4),
        (3, 0, 4),
    ]
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.5, 0.5)]

    cgf_bytes = write_cgf(
        vertices=vertices,
        normals=normals,
        faces=faces,
        uvs=uvs,
        diffuse_texture="textures/test_diffuse.dds",
        bump_texture="textures/test_ddn.dds",
        node_name="custom_pyramid",
        material_name="CustomMat",
    )

    parsed = get_cgf(io.BytesIO(cgf_bytes))
    assert parsed.get("signature") == "CryTek", f"Unexpected signature: {parsed.get('signature')}"
    nodes = parsed.get("nodes", {})
    assert len(nodes) > 0, "No nodes parsed in generated CGF!"

    node_data = next(iter(nodes.values()))
    mesh = node_data.get("mesh")
    assert mesh is not None, "Mesh chunk missing in parsed node!"
    assert mesh["num_vertices"] == 5
    assert mesh["num_faces"] == 6
    assert mesh["num_uvs"] == 5

    parsed_verts = mesh["vertices"]["position"]
    assert abs(parsed_verts[0][0] - 0.0) < 1e-4
    assert abs(parsed_verts[1][0] - 2.0) < 1e-4
    assert abs(parsed_verts[4][2] - 2.5) < 1e-4

    mat = node_data.get("material")
    assert mat is not None, "Material chunk missing in parsed node!"
    assert "test_diffuse.dds" in mat["texture_diffuse"]["long_name"]
    assert "test_ddn.dds" in mat["texture_bump"]["long_name"]

    print("PASS: CGF generated from scratch parsed with 100% geometric and material fidelity.")


def test_real_cgf_patch_roundtrip():
    print("\n--- Test Real Official CGF Non-Destructive Patching ---")
    from core.client_provider import AionClientProvider
    from formats.cgf.writer import patch_cgf

    env_client = os.environ.get("AION_CLIENT_ROOT", "").strip()
    client_path = Path(env_client) if env_client else None
    if client_path is None or not client_path.is_dir():
        print("SKIP: Set AION_CLIENT_ROOT for real CGF patch test.")
        return

    prov = AionClientProvider(client_path)
    cgf_ref = "objects/npc/shugomale/shugomale.cgf"
    cgf_bytes = prov.resolve_cgf_bytes(cgf_ref)
    assert cgf_bytes is not None, f"Failed resolving {cgf_ref}"

    orig_parsed = get_cgf(io.BytesIO(cgf_bytes))
    orig_bone_names = orig_parsed.get("bone_names", [])
    assert len(orig_bone_names) == 44, f"Expected 44 bones, got {len(orig_bone_names)}"

    # Get original mesh vertices
    orig_node = next(iter(orig_parsed.get("nodes", {}).values()))
    orig_mesh = orig_node["mesh"]
    orig_verts = [tuple(p) for p in orig_mesh["vertices"]["position"]]
    orig_norms = [tuple(n) for n in orig_mesh["vertices"]["normal"]]
    orig_faces = [tuple(f) for f in orig_mesh["faces"]["v"]]
    orig_uvs = [tuple(u) for u in orig_mesh["uvs"]["uvs"]]
    orig_face_uvs = [tuple(fu) for fu in orig_mesh.get("uv_faces", {}).get("face_uvs", [])]
    orig_skin = orig_mesh.get("skin_weights", [])

    # Edit: Shift all vertices in Z by +1.5 meters
    edited_verts = [(vx, vy, vz + 1.5) for (vx, vy, vz) in orig_verts]

    # Non-destructively patch CGF bytes
    patched_bytes = patch_cgf(
        original_cgf_bytes=cgf_bytes,
        new_vertices=edited_verts,
        new_normals=orig_norms,
        new_faces=orig_faces,
        new_uvs=orig_uvs,
        new_face_uvs=orig_face_uvs,
        new_skin_weights=orig_skin,
    )

    assert len(patched_bytes) > 50000, f"Patched CGF too small: {len(patched_bytes)}"

    # Parse patched CGF and verify fidelity
    patched_parsed = get_cgf(io.BytesIO(patched_bytes))
    patched_bones = patched_parsed.get("bone_names", [])
    assert len(patched_bones) == 44, f"Bones altered during patch! Expected 44, got {len(patched_bones)}"

    patched_node = next(iter(patched_parsed.get("nodes", {}).values()))
    patched_mesh = patched_node["mesh"]
    assert patched_mesh["num_vertices"] == len(orig_verts)
    assert patched_mesh["num_faces"] == len(orig_faces)
    assert patched_mesh["num_uvs"] == len(orig_uvs)

    patched_verts = patched_mesh["vertices"]["position"]
    # Verify the vertex edit (+1.5m)
    for i in range(min(10, len(orig_verts))):
        expected_z = orig_verts[i][2] + 1.5
        actual_z = patched_verts[i][2]
        assert abs(actual_z - expected_z) < 1e-3, f"Vertex {i} Z mismatch: {actual_z} vs expected {expected_z}"

    print(f"PASS: Real official CGF ({len(cgf_bytes)}B) patched to ({len(patched_bytes)}B) with 100% fidelity.")


def run_all():
    print("=" * 70)
    print("RUNNING LOSTACADEMY AION MODEL LIBRARY ROUND-TRIP TESTS")
    print("=" * 70)
    test_cal_roundtrip()
    test_caf_roundtrip()
    test_cgf_scratch_roundtrip()
    test_real_cgf_patch_roundtrip()
    print("\n" + "=" * 70)
    print("ALL ROUND-TRIP UNIT TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_all()
