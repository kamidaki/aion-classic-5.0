"""
Validation script for Shugo walk animation and multi-animation switching.
Verifies:
- Switching between Idle, Walk, Run, Attack animations on Shugo and Brax
- Measuring vertex displacement and mesh deformation to ensure no explosive stretching (> 0.25m per joint / no 1.5m-3m stretching)
"""

from __future__ import annotations
import math
import os
import sys
from pathlib import Path

# Setup module path
_PLUGIN_DIR = Path(__file__).resolve().parents[1]
_ADDONS_ROOT = _PLUGIN_DIR.parent
if str(_ADDONS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ADDONS_ROOT))
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

import bpy
import addon_utils
from mathutils import Vector

ADDON_NAME = "importador-modelos3d-lostacademy"
addon_utils.enable(ADDON_NAME, default_set=True)

import importlib
mod = importlib.import_module(ADDON_NAME)
AionClientProvider = mod.core.client_provider.AionClientProvider
ModelProvider = mod.providers.model_provider.ModelProvider
AssetEntry = mod.indexer.asset_entry.AssetEntry
ViewerStage = mod.viewers.viewer_stage.ViewerStage


def test_shugo_walk_and_animations():
    print("=" * 80)
    print("TEST: SHUGO WALK DISPLACEMENT & MULTI-ANIMATION VERIFICATION")
    print("=" * 80)

    env_client = os.environ.get("AION_CLIENT_ROOT", "").strip()
    if not env_client or not Path(env_client).is_dir():
        print("SKIP: Set AION_CLIENT_ROOT to run Shugo walk test.")
        return
    client_path = Path(env_client)
    cp = AionClientProvider(client_path)
    mp = ModelProvider(cp)

    stage_col = ViewerStage.get_or_create_stage_collection()
    ViewerStage.clear_stage_objects()

    shugo_entry = AssetEntry(
        asset_id="shugomale",
        name="Shugo Male",
        category="NPC",
        model_path="objects/npc/shugomale/shugomale.cgf",
    )

    print("\n[Step 1] Loading Shugo Model...")
    rig_obj = mp.load_model(shugo_entry, target_collection=stage_col, load_animation=False)
    assert rig_obj is not None, "Failed to load Shugo model"
    assert rig_obj.type == "ARMATURE", f"Expected ARMATURE, got {rig_obj.type}"

    mesh_children = [c for c in rig_obj.children if c.type == "MESH"]
    assert len(mesh_children) > 0, "No mesh children found on Shugo rig"
    mesh_obj = mesh_children[0]
    num_verts = len(mesh_obj.data.vertices)
    print(f"  -> Rig loaded: {len(rig_obj.data.bones)} bones, Mesh '{mesh_obj.name}' with {num_verts} vertices")

    # Record rest pose vertex positions in world space
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_mesh_rest = mesh_obj.evaluated_get(depsgraph).to_mesh()
    rest_positions = [Vector(v.co) for v in eval_mesh_rest.vertices]
    mesh_obj.to_mesh_clear()

    # Calculate rest bounding box dimensions
    rest_xs = [p.x for p in rest_positions]
    rest_ys = [p.y for p in rest_positions]
    rest_zs = [p.z for p in rest_positions]
    rest_width = max(rest_xs) - min(rest_xs)
    rest_depth = max(rest_ys) - min(rest_ys)
    rest_height = max(rest_zs) - min(rest_zs)
    print(f"  -> Rest bounding box: Width={rest_width:.3f}m, Depth={rest_depth:.3f}m, Height={rest_height:.3f}m")

    # Resolve CAL mapping
    cal_map, _ = cp.resolve_animation_asset(shugo_entry.model_path)
    assert cal_map is not None, "Failed to parse CAL mapping for Shugo"
    print(f"  -> Shugo CAL has {len(cal_map)} animation sequences")

    # Check for Walk, Run, Idle, Attack
    walk_key = next((k for k in ("nwalk_001", "cwalk_noweapon_001") if k in cal_map), None)
    run_key = next((k for k in ("nrun_001", "crun_noweapon_001") if k in cal_map), None)
    idle_key = next((k for k in ("nidle_001", "cidle_noweapon_001") if k in cal_map), None)
    attack_key = next((k for k in ("cattack_noweapon_001", "cattack_1hand_001") if k in cal_map), None)

    print(f"  -> Selected sequences: Idle='{idle_key}', Walk='{walk_key}', Run='{run_key}', Attack='{attack_key}'")
    assert walk_key is not None, "No walk animation found in CAL!"

    b_names, b_pos, b_anim = mp.skel_prov.extract_armature(rig_obj)

    # Test loading and switching each animation
    tested_anims = [k for k in (idle_key, walk_key, run_key, attack_key) if k]
    for anim_name in tested_anims:
        caf_rel = cal_map[anim_name]
        caf_bytes = cp.find_caf_bytes(caf_rel, source_model_path=shugo_entry.model_path)
        assert caf_bytes is not None, f"Failed finding CAF bytes for {anim_name} ({caf_rel})"
        action = mp.anim_prov.load_animation(
            rig_obj=rig_obj,
            caf_bytes=caf_bytes,
            action_name=f"Shugo_{anim_name}",
            bone_names=b_names,
            bone_anim=b_anim,
        )
        assert action is not None, f"Failed loading action for {anim_name}"
        f_start = int(action.frame_range[0])
        f_end = int(action.frame_range[1])
        print(f"  -> Successfully loaded '{anim_name}': {f_end - f_start + 1} frames [{f_start}..{f_end}]")

    # Now deeply analyze Walk animation displacement
    print("\n[Step 2] Measuring Shugo Walk Deformation & Displacement...")
    walk_caf_rel = cal_map[walk_key]
    walk_caf_bytes = cp.find_caf_bytes(walk_caf_rel, source_model_path=shugo_entry.model_path)
    walk_action = mp.anim_prov.load_animation(
        rig_obj=rig_obj,
        caf_bytes=walk_caf_bytes,
        action_name=f"Shugo_{walk_key}",
        bone_names=b_names,
        bone_anim=b_anim,
    )
    assert walk_action is not None, "Failed to load walk action"

    f_start = int(walk_action.frame_range[0])
    f_end = int(walk_action.frame_range[1])

    max_displacement_from_rest = 0.0
    max_interframe_displacement = 0.0
    max_height_stretched = 0.0
    prev_positions = None

    # Track root bone motion to account for root translation vs relative mesh deformation
    root_bone_name = rig_obj.data.bones[0].name
    pbone_root = rig_obj.pose.bones[root_bone_name]
    rest_root_loc = rig_obj.data.bones[root_bone_name].matrix_local.translation.copy()

    max_torso_displacement = 0.0
    torso_bones = {"Bip01 Pelvis", "Bip01 Spine", "Bip01 Spine1", "Bip01 Neck", "Bip01 Head"}

    frame_stats = []

    for f in range(f_start, f_end + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        eval_m = mesh_obj.evaluated_get(dg).to_mesh()
        cur_positions = [Vector(v.co) for v in eval_m.vertices]
        mesh_obj.to_mesh_clear()

        # Root motion offset on this frame relative to rest root
        root_motion = pbone_root.matrix.translation - rest_root_loc

        # Calculate bounding box on this frame
        cur_zs = [p.z for p in cur_positions]
        cur_height = max(cur_zs) - min(cur_zs)
        max_height_stretched = max(max_height_stretched, cur_height)

        # Displacement relative to root motion (anatomical local deformation)
        frame_max_disp = 0.0
        for i in range(num_verts):
            disp = (cur_positions[i] - root_motion - rest_positions[i]).length
            if disp > frame_max_disp:
                frame_max_disp = disp
            v_groups = {mesh_obj.vertex_groups[g.group].name for g in mesh_obj.data.vertices[i].groups}
            if v_groups.intersection(torso_bones):
                max_torso_displacement = max(max_torso_displacement, disp)

        max_displacement_from_rest = max(max_displacement_from_rest, frame_max_disp)

        # Inter-frame velocity/displacement (sanity check against explosive pops)
        if prev_positions is not None:
            frame_inter_max = max((cur_positions[i] - prev_positions[i]).length for i in range(num_verts))
            max_interframe_displacement = max(max_interframe_displacement, frame_inter_max)

        prev_positions = cur_positions
        frame_stats.append((f, frame_max_disp, cur_height))

    print(f"\n  Walk Cycle Metrics ({f_end - f_start + 1} frames):")
    print(f"  * Rest Height: {rest_height:.3f}m | Max Animated Height: {max_height_stretched:.3f}m (Stretch: {max_height_stretched - rest_height:+.3f}m)")
    print(f"  * Max Inter-frame Vertex Shift: {max_interframe_displacement:.4f}m (Smooth motion, no popping)")
    print(f"  * Max Anatomical Torso/Spine Displacement: {max_torso_displacement:.4f}m")
    print(f"  * Max Mesh Vertex Displacement (Tail Tip): {max_displacement_from_rest:.4f}m")

    # Sanity checks:
    # 1. Height must not blow up: Shugo rest height is ~1.56m. Under previous bug it blew up to 4.06m (+2.5m stretch).
    assert max_height_stretched < rest_height * 1.5, f"Mesh stretched abnormally! Rest height {rest_height:.2f}m, anim height {max_height_stretched:.2f}m"

    # 2. Maximum relative joint/vertex displacement in normal body joints (torso/spine/head) must be anatomically consistent (<= 0.25m)
    assert max_torso_displacement <= 0.25, f"Torso vertex displacement too high: {max_torso_displacement:.4f}m > 0.25m!"

    # 3. Inter-frame displacement must be smooth (< 0.25m) with no explosive pops
    assert max_interframe_displacement < 0.25, f"Inter-frame shift too high (popping): {max_interframe_displacement:.4f}m > 0.25m!"

    print("\n>>> PASS: Shugo walk animation displacement is anatomically consistent (<= 0.25m) with ZERO explosive stretching!\n")


def test_brax_animations():
    print("=" * 80)
    print("TEST: MONSTER BRAX MULTI-ANIMATION SWITCHING (IDLE, WALK, RUN, ATTACK)")
    print("=" * 80)

    env_client = os.environ.get("AION_CLIENT_ROOT", "").strip()
    if not env_client or not Path(env_client).is_dir():
        print("SKIP: Set AION_CLIENT_ROOT to run Shugo walk test.")
        return
    client_path = Path(env_client)
    cp = AionClientProvider(client_path)
    mp = ModelProvider(cp)

    stage_col = ViewerStage.get_or_create_stage_collection()
    ViewerStage.clear_stage_objects()

    brax_entry = AssetEntry(
        asset_id="brax",
        name="Brax",
        category="MONSTER",
        model_path="objects/monster/brax/brax.cgf",
    )

    print("\n[Step 1] Loading Brax Model...")
    rig_obj = mp.load_model(brax_entry, target_collection=stage_col, load_animation=False)
    assert rig_obj is not None, "Failed to load Brax model"
    mesh_children = [c for c in rig_obj.children if c.type == "MESH"]
    assert len(mesh_children) > 0, "No mesh children on Brax rig"
    mesh_obj = mesh_children[0]

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_m = mesh_obj.evaluated_get(dg).to_mesh()
    rest_zs = [v.co.z for v in eval_m.vertices]
    rest_height = max(rest_zs) - min(rest_zs)
    mesh_obj.to_mesh_clear()
    print(f"  -> Brax Rest Height: {rest_height:.3f}m, Bones: {len(rig_obj.data.bones)}, Verts: {len(mesh_obj.data.vertices)}")

    cal_map, _ = cp.resolve_animation_asset(brax_entry.model_path)
    assert cal_map is not None, "Failed to parse CAL mapping for Brax"

    b_names, b_pos, b_anim = mp.skel_prov.extract_armature(rig_obj)
    anims_to_test = ["nidle_001", "nwalk_001", "nrun_001", "cattack_noweapon_001"]

    for anim_name in anims_to_test:
        assert anim_name in cal_map, f"Animation {anim_name} not found in Brax CAL"
        caf_bytes = cp.find_caf_bytes(cal_map[anim_name], source_model_path=brax_entry.model_path)
        assert caf_bytes is not None, f"Failed finding CAF bytes for Brax {anim_name}"
        action = mp.anim_prov.load_animation(
            rig_obj=rig_obj,
            caf_bytes=caf_bytes,
            action_name=f"Brax_{anim_name}",
            bone_names=b_names,
            bone_anim=b_anim,
        )
        assert action is not None, f"Failed loading Brax action {anim_name}"

        max_h = 0.0
        for f in range(int(action.frame_range[0]), int(action.frame_range[1]) + 1):
            bpy.context.scene.frame_set(f)
            bpy.context.view_layer.update()
            dg_eval = bpy.context.evaluated_depsgraph_get()
            eval_mesh = mesh_obj.evaluated_get(dg_eval).to_mesh()
            cur_zs = [v.co.z for v in eval_mesh.vertices]
            h = max(cur_zs) - min(cur_zs)
            max_h = max(max_h, h)
            mesh_obj.to_mesh_clear()

        stretch = max_h - rest_height
        print(f"  -> Tested '{anim_name}': max_height={max_h:.3f}m (Stretch: {stretch:+.3f}m)")
        assert max_h < rest_height * 1.3, f"Brax mesh stretched abnormally under {anim_name}: {max_h:.2f}m > {rest_height * 1.3:.2f}m"

    print("\n>>> PASS: Brax monster animation switching verified with ZERO abnormal deformation!\n")


if __name__ == "__main__":
    test_shugo_walk_and_animations()
    test_brax_animations()

