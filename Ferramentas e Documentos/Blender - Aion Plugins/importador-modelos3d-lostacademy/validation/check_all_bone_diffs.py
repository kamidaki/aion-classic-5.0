import sys
import math
from pathlib import Path
import importlib
import io
import binascii
from mathutils import Matrix, Vector, Quaternion

plugin_dir = Path(r"D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Blender - Aion Plugins\importador-modelos3d-lostacademy")
sys.path.insert(0, str(plugin_dir.parent))
sys.path.insert(0, str(plugin_dir))

mod = importlib.import_module("importador-modelos3d-lostacademy")
prov = mod.core.client_provider.AionClientProvider(r"D:\GameForge\aionclassic")
cgf_bytes = prov.resolve_cgf_bytes("objects/monster/dragonfly/dragonfly.cgf")
cal_map, caf_bytes = prov.resolve_animation_asset("objects/monster/dragonfly/dragonfly.cgf")
parsed_cgf = mod.formats.cgf.parser.get_cgf(io.BytesIO(cgf_bytes))
parsed_caf = mod.formats.cgf.caf_parser.parse_caf(caf_bytes)

bone_names = parsed_cgf.get("bone_names", [])
bone_initial_pos = parsed_cgf.get("bone_initial_pos", [])
bone_anim = parsed_cgf.get("bone_anim", [])

bind_matrices = []
for i, m in enumerate(bone_initial_pos):
    rot_3x3 = Matrix((
        (m[0], m[1], m[2]),
        (m[3], m[4], m[5]),
        (m[6], m[7], m[8]),
    ))
    pos = Vector((m[9] / 100.0, m[10] / 100.0, m[11] / 100.0))
    bind_mat = Matrix.Translation(pos) @ rot_3x3.to_4x4()
    bind_matrices.append(bind_mat)

ctrls = parsed_caf["controllers"]

large_diffs = []
small_diffs = []

for b_idx in range(len(bone_names)):
    bname = bone_names[b_idx]
    pid = bone_anim[b_idx]["parent_id"]
    bind_m = bind_matrices[b_idx]
    if pid >= 0:
        p_bind_m = bind_matrices[pid]
        rest_local_m = p_bind_m.inverted() @ bind_m
    else:
        rest_local_m = bind_m

    rest_loc = rest_local_m.translation
    rest_rot = rest_local_m.to_quaternion()

    cid = bone_anim[b_idx]["ctrl_id"]
    keys = ctrls.get(cid)
    if not keys:
        keys = ctrls.get(binascii.crc32(bname.encode("latin-1")))
        if not keys:
            keys = ctrls.get(binascii.crc32(bname.lower().encode("latin-1")))

    if keys:
        caf_pos = Vector(keys[0]["pos"])
        caf_quat = Quaternion(keys[0]["quat"])
        diff_quat = rest_rot.rotation_difference(caf_quat)
        deg = math.degrees(diff_quat.angle)
        pos_diff = (rest_loc - caf_pos).length
        if deg > 30.0 or pos_diff > 0.1:
            large_diffs.append((b_idx, bname, deg, pos_diff, rest_loc, caf_pos, rest_rot, caf_quat))
        else:
            small_diffs.append((b_idx, bname, deg, pos_diff))

print(f"Total bones checked: {len(bone_names)}")
print(f"Bones with SMALL diff (<= 30 deg, <= 10cm): {len(small_diffs)}")
print(f"Bones with LARGE diff (> 30 deg or > 10cm): {len(large_diffs)}")

print("\n--- LARGE DIFFERENCE BONES ---")
for b in large_diffs:
    print(f"Bone {b[0]} '{b[1]}': rot_diff={b[2]:.1f} deg, pos_diff={b[3]:.3f}m")
    print(f"    rest_loc={b[4]}, caf_pos={b[5]}")
    print(f"    rest_rot={b[6]}, caf_quat={b[7]}")
