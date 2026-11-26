import os
import sys
import tempfile
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
model_prov = mod.providers.model_provider.ModelProvider(prov)

candidates = [
    ("sprigg", "objects/monster/sprigg/sprigg.cgf"),
    ("brax", "objects/monster/brax/brax.cgf"),
    ("shugo", "objects/npc/shugo/shugo.cgf"),
]

out_dir = Path(tempfile.gettempdir()) / "aion_model_validation"
out_dir.mkdir(parents=True, exist_ok=True)

for tag, path in candidates:
    cgf_bytes = prov.resolve_cgf_bytes(path)
    cal_map, caf_bytes = prov.resolve_animation_asset(path)
    if not cgf_bytes or not caf_bytes:
        print(f"Skipping {tag}: cgf or caf not found")
        continue

    parsed_cgf = mod.formats.cgf.parser.get_cgf(io.BytesIO(cgf_bytes))
    parsed_caf = mod.formats.cgf.caf_parser.parse_caf(caf_bytes)

    bone_names = parsed_cgf.get("bone_names", [])
    bone_anim = parsed_cgf.get("bone_anim", [])
    bone_initial_pos = parsed_cgf.get("bone_initial_pos", [])

    if not bone_names or not bone_initial_pos:
        print(f"Skipping {tag}: no skeleton")
        continue

    # Column-major bind matrices
    bind_matrices = []
    for m in bone_initial_pos:
        rot = Matrix(((m[0], m[3], m[6]), (m[1], m[4], m[7]), (m[2], m[5], m[8])))
        pos = Vector((m[9]/100, m[10]/100, m[11]/100))
        bind_matrices.append(Matrix.Translation(pos) @ rot.to_4x4())

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

    # Clean scene
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    col = bpy.data.collections.new("Col")
    bpy.context.scene.collection.children.link(col)

    entry = mod.indexer.asset_entry.AssetEntry(tag, tag.upper(), "MONSTER", path)
    rig_obj = model_prov.load_model(entry, col, load_animation=False)

    # Rebuild edit bones with column-major matrices
    bpy.context.view_layer.objects.active = rig_obj
    bpy.ops.object.mode_set(mode="EDIT")
    for i, bn in enumerate(bone_names):
        if bn in rig_obj.data.edit_bones:
            eb = rig_obj.data.edit_bones[bn]
            mat = bind_matrices[i]
            eb.head = mat.translation
            bone_dir = mat.to_3x3().col[1].normalized()
            if bone_dir.length < 0.001: bone_dir = Vector((0, 1, 0))
            eb.tail = eb.head + bone_dir * 0.05
            eb.matrix = mat
    bpy.ops.object.mode_set(mode="POSE")

    action = bpy.data.actions.new(f"{tag}_Action")
    rig_obj.animation_data_create()
    rig_obj.animation_data.action = action

    sample_controller = mod.providers.animation_provider.sample_controller
    timing = parsed_caf.get("timing", {})
    f_start = int(timing.get("frame_start", 0))
    f_end = int(timing.get("frame_end", 60))

    for f in range(f_start, f_end + 1):
        for b_idx in range(len(bone_names)):
            b_name = bone_names[b_idx]
            if b_name not in rig_obj.pose.bones:
                continue
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

            basis_m = rest_local.inverted() @ local_m

            pbone = rig_obj.pose.bones[b_name]
            pbone.location = basis_m.translation
            pbone.rotation_quaternion = basis_m.to_quaternion()
            pbone.scale = basis_m.to_scale()

            pbone.keyframe_insert("location", frame=f)
            pbone.keyframe_insert("rotation_quaternion", frame=f)
            pbone.keyframe_insert("scale", frame=f)

    bpy.ops.object.mode_set(mode="OBJECT")

    # Render frame 15
    scene = bpy.context.scene
    scene.frame_start = f_start
    scene.frame_end = f_end
    scene.frame_set(15)

    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = (0.0, -3.5, 1.2)
    cam.rotation_euler = (math.radians(80), 0, 0)
    col.objects.link(cam)
    scene.camera = cam

    light_data = bpy.data.lights.new("Sun", type="SUN")
    light = bpy.data.objects.new("Sun", light_data)
    light.location = (2.0, -2.0, 5.0)
    col.objects.link(light)

    scene.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.types, "RenderEngineEEVEE_NEXT") else "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 700

    out_p = out_dir / f"test_cand_{tag}.png"
    scene.render.filepath = str(out_p)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {tag} to {out_p}")
