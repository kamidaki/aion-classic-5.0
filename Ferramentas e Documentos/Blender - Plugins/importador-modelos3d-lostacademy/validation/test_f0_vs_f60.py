import os
import sys
from pathlib import Path
import io
import math
import binascii
import bpy
from mathutils import Matrix, Vector, Quaternion

plugin_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(plugin_dir.parent))
sys.path.insert(0, str(plugin_dir))

_env_client = os.environ.get("AION_CLIENT_ROOT", "").strip()
if not _env_client or not Path(_env_client).is_dir():
    raise SystemExit("Defina AION_CLIENT_ROOT apontando para o cliente Aion.")

mod = __import__("importador-modelos3d-lostacademy")
prov = mod.core.client_provider.AionClientProvider(_env_client)
cal_map, caf_bytes = prov.resolve_animation_asset("objects/monster/dragonfly/dragonfly.cgf")
parsed_caf = mod.formats.cgf.caf_parser.parse_caf(caf_bytes)
cgf_bytes = prov.resolve_cgf_bytes("objects/monster/dragonfly/dragonfly.cgf")
parsed_cgf = mod.formats.cgf.parser.get_cgf(io.BytesIO(cgf_bytes))

model_prov = mod.providers.model_provider.ModelProvider(prov)

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
col = bpy.data.collections.new("Col")
bpy.context.scene.collection.children.link(col)

entry = mod.indexer.asset_entry.AssetEntry("dragonfly", "DF", "MONSTER", "objects/monster/dragonfly/dragonfly.cgf")
rig_obj = model_prov.load_model(entry, col, load_animation=False)

bone_names = parsed_cgf["bone_names"]
bone_anim = parsed_cgf["bone_anim"]
bone_initial_pos = parsed_cgf["bone_initial_pos"]

bind_matrices = []
for m in bone_initial_pos:
    rot = Matrix(((m[0], m[3], m[6]), (m[1], m[4], m[7]), (m[2], m[5], m[8])))
    pos = Vector((m[9]/100, m[10]/100, m[11]/100))
    bind_matrices.append(Matrix.Translation(pos) @ rot.to_4x4())

# Set edit bones
bpy.context.view_layer.objects.active = rig_obj
bpy.ops.object.mode_set(mode="EDIT")
for i, bn in enumerate(bone_names):
    eb = rig_obj.data.edit_bones[bn]
    mat = bind_matrices[i]
    eb.head = mat.translation
    bone_dir = mat.to_3x3().col[1].normalized()
    if bone_dir.length < 0.001: bone_dir = Vector((0, 1, 0))
    eb.tail = eb.head + bone_dir * 0.05
    eb.matrix = mat
bpy.ops.object.mode_set(mode="POSE")

ctrls = parsed_caf["controllers"]
ctrl_to_bone = {}
for i, b_info in enumerate(bone_anim):
    cid = b_info.get("ctrl_id")
    if cid is not None and i < len(bone_names):
        ctrl_to_bone[cid] = bone_names[i]
for b_name in bone_names:
    ctrl_to_bone[binascii.crc32(b_name.encode("latin-1"))] = b_name
    ctrl_to_bone[binascii.crc32(b_name.lower().encode("latin-1"))] = b_name

bone_tracks = {}
for cid, keys in ctrls.items():
    b_name = ctrl_to_bone.get(cid)
    if b_name: bone_tracks[b_name] = keys

eval_order = []
visited = set()
def visit(b_idx):
    pid = bone_anim[b_idx].get("parent_id", -1)
    if pid >= 0 and pid not in visited: visit(pid)
    if b_idx not in visited:
        visited.add(b_idx)
        eval_order.append(b_idx)
for i in range(len(bone_names)): visit(i)

action = bpy.data.actions.new("Test")
rig_obj.animation_data_create()
rig_obj.animation_data.action = action

sample_controller = mod.providers.animation_provider.sample_controller

for f in range(61):
    bpy.context.scene.frame_set(f)
    world_matrices = {}
    for b_idx in eval_order:
        b_name = bone_names[b_idx]
        pid = bone_anim[b_idx].get("parent_id", -1)
        bind_m = bind_matrices[b_idx]
        if pid >= 0:
            rest_local = bind_matrices[pid].inverted() @ bind_m
        else:
            rest_local = bind_m

        if b_name in bone_tracks:
            pos_v, quat_v = sample_controller(bone_tracks[b_name], float(f))
            quat_v = quat_v.conjugated()
            local_m = Matrix.Translation(pos_v) @ quat_v.to_matrix().to_4x4()
        else:
            local_m = rest_local

        if pid >= 0 and pid in world_matrices:
            world_m = world_matrices[pid] @ local_m
        else:
            world_m = local_m
        world_matrices[b_idx] = world_m

        pbone = rig_obj.pose.bones[b_name]
        pbone.matrix = world_m
        pbone.keyframe_insert("location", frame=f)
        pbone.keyframe_insert("rotation_quaternion", frame=f)

bpy.ops.object.mode_set(mode="OBJECT")

# Now evaluate frame 0 vs frame 60
bpy.context.scene.frame_set(0)
f0_matrices = {b: rig_obj.pose.bones[b].matrix.copy() for b in bone_names}

bpy.context.scene.frame_set(60)
f60_matrices = {b: rig_obj.pose.bones[b].matrix.copy() for b in bone_names}

max_diff = 0.0
for b in bone_names:
    diff = (f0_matrices[b].translation - f60_matrices[b].translation).length
    if diff > max_diff:
        max_diff = diff
    if diff > 0.001:
        print(f"Bone {b} diff between frame 0 and 60: {diff:.4f}m")

print(f"Max difference between frame 0 and 60 across all bones: {max_diff:.6f}m")
