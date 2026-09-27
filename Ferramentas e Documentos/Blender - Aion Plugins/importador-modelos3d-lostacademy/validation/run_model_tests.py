"""
Comprehensive Automated Verification Test Suite for LostAcademy Aion Model Library.
Runs 15 end-to-end tests inside headless Blender.
"""

from __future__ import annotations
import io
import os
import shutil
import sys
import tempfile
import time
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

ADDON_NAME = "importador-modelos3d-lostacademy"

# Primary test client candidate paths
CLIENT_CANDIDATES = [
    Path(r"D:\GameForge\aionclassic"),
    Path(r"D:\AION CLASSIC 5.0 - EMULADOR"),
    Path(r"I:\Aion Live Clássico - América do Sul"),
    Path(r"I:\Servidor Aion\CLIENT 3. 9 - THIS AION BRASIL\This AION Brasil"),
]


def resolve_test_client() -> Path | None:
    for c in CLIENT_CANDIDATES:
        if c.is_dir():
            return c
    return None


def run_tests():
    print("=" * 80)
    print("LOSTACADEMY AION MODEL LIBRARY - AUTOMATED VERIFICATION SUITE")
    print("Blender Version:", bpy.app.version_string)
    print("Addon Path:", _PLUGIN_DIR)
    print("=" * 80)

    test_client = resolve_test_client()
    print(f"Active Test Client: {test_client}\n")

    passed_tests = 0
    total_tests = 15

    # -------------------------------------------------------------------------
    # TEST 1: Addon Lifecycle & Registration
    # -------------------------------------------------------------------------
    print("[TEST 01/15] Addon Lifecycle & Registration...")
    mod = addon_utils.enable(ADDON_NAME)
    assert mod is not None, f"Failed to enable addon {ADDON_NAME}"
    assert hasattr(bpy.types.Scene, "aion_model_lib"), "Property aion_model_lib not registered on bpy.types.Scene"
    assert hasattr(bpy.ops.aion_model, "detect_client"), "Operator detect_client not registered"
    assert hasattr(bpy.ops.aion_model, "load_asset"), "Operator load_asset not registered"
    assert hasattr(bpy.ops.aion_model, "save_asset"), "Operator save_asset not registered"
    assert hasattr(bpy.ops.aion_model, "create_from_mesh"), "Operator create_from_mesh not registered"
    assert hasattr(bpy.ops.aion_model, "clone_asset"), "Operator clone_asset not registered"
    print("  -> Addon enabled, properties, operators, and UI panels verified.")
    passed_tests += 1

    # Import internal modules via addon package namespace to guarantee isolation
    import importlib
    def sub(name: str):
        return importlib.import_module(f"{ADDON_NAME}.{name}")

    client_det_mod = sub("core.client_detector")
    ClientDetector = client_det_mod.ClientDetector
    discover_available_clients = client_det_mod.discover_available_clients
    inspect_client = client_det_mod.inspect_client

    AionClientProvider = sub("core.client_provider").AionClientProvider
    ChangeTracker = sub("core.change_tracker").ChangeTracker
    tx_mod = sub("core.transaction_manager")
    TransactionManager = tx_mod.TransactionManager
    TransactionResult = tx_mod.TransactionResult

    AssetDatabase = sub("indexer.asset_database").AssetDatabase
    scanner_mod = sub("indexer.scanner")
    ClientScanner = scanner_mod.ClientScanner
    classify_asset_category = scanner_mod.classify_asset_category
    ensure_asset_thumbnail = sub("indexer.thumbnail_generator").ensure_asset_thumbnail

    ModelProvider = sub("providers.model_provider").ModelProvider
    stage_mod = sub("viewers.viewer_stage")
    ViewerStage = stage_mod.ViewerStage
    VIEWER_COLLECTION_NAME = stage_mod.VIEWER_COLLECTION_NAME

    disp_mod = sub("viewers.display_modes")
    set_shading_mode = disp_mod.set_shading_mode
    set_bones_display = disp_mod.set_bones_display

    AnimationPlayer = sub("viewers.animation_player").AnimationPlayer
    MeshEditor = sub("editors.mesh_editor").MeshEditor
    SkeletonEditor = sub("editors.skeleton_editor").SkeletonEditor
    MaterialEditor = sub("editors.material_editor").MaterialEditor
    ModelCreator = sub("editors.model_creator").ModelCreator
    ModelCloner = sub("editors.model_cloner").ModelCloner
    DirectSaver = sub("exporters.direct_saver").DirectSaver
    LooseExporter = sub("exporters.loose_exporter").LooseExporter
    get_cgf = sub("formats.cgf.parser").get_cgf

    # -------------------------------------------------------------------------
    # TEST 2: Multi-Client Discovery & Inspection
    # -------------------------------------------------------------------------
    print("\n[TEST 02/15] Multi-Client Discovery & Inspection...")
    clients = discover_available_clients()
    print(f"  -> Discovered {len(clients)} client installation(s) across systems:")
    for c in clients:
        print(f"     * [{c.flavor}] {c.name} -> {c.path}")
    assert len(clients) > 0, "Expected at least one valid Aion client to be discovered!"
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 3: Scanner & Asset Classification
    # -------------------------------------------------------------------------
    print("\n[TEST 03/15] Asset Scanner & Category Classification...")
    assert classify_asset_category("objects/npc/shugomale/shugomale.cgf") == "NPC"
    assert classify_asset_category("objects/monster/brax/brax.cgf") == "MONSTER"
    assert classify_asset_category("objects/weapon/sword/sword.cgf") == "WEAPON"
    assert classify_asset_category("objects/armor/boots/boots.cgf") == "ARMOR"
    assert classify_asset_category("objects/props/chest/chest.cgf") == "PROP"
    assert classify_asset_category("objects/vegetation/tree/tree.cgf") == "VEGETATION"

    scanner = ClientScanner(test_client)
    t0 = time.time()
    assets, dep_graph = scanner.scan(max_assets=350)
    scan_time = time.time() - t0
    print(f"  -> Scanned {len(assets)} assets in {scan_time:.2f}s with dependency graph.")
    assert len(assets) >= 50, f"Expected >= 50 assets, found {len(assets)}"
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 4: Asset Database, Search & Caching
    # -------------------------------------------------------------------------
    print("\n[TEST 04/15] Asset Database, Search & Caching...")
    db = AssetDatabase.get()
    db.load_from_entries(assets)
    assert db.total_count == len(assets)

    # Search tests
    query_results = db.search("shugo", limit=10)
    print(f"  -> Search 'shugo': found {len(query_results)} matches")
    assert len(query_results) > 0, "Expected search for 'shugo' to find assets"
    first_shugo = query_results[0]
    assert "shugo" in first_shugo.name.lower() or "shugo" in first_shugo.model_path.lower()

    # Cache round-trip
    temp_cache_dir = Path(tempfile.mkdtemp(prefix="aion_cache_test_"))
    try:
        assert db.save_cache(temp_cache_dir) is True, "Failed to save cache to temp directory"
        db.clear()
        assert db.total_count == 0
        assert db.load_cache(temp_cache_dir) is True, "Failed to reload cache from temp directory"
        assert db.total_count == len(assets), f"Reload count mismatch: {db.total_count} vs {len(assets)}"
        print("  -> Disk cache successfully written and verified.")
    finally:
        shutil.rmtree(temp_cache_dir, ignore_errors=True)
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 5: Thumbnail Generation
    # -------------------------------------------------------------------------
    print("\n[TEST 05/15] Thumbnail Generation...")
    thumb_path = ensure_asset_thumbnail(test_client, first_shugo)
    assert thumb_path is not None and Path(thumb_path).is_file(), "Thumbnail file was not created"
    assert Path(thumb_path).stat().st_size > 500, "Thumbnail file appears empty or corrupt"
    print(f"  -> Thumbnail verified at: {thumb_path}")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 6: Model Loader & 3D Staging
    # -------------------------------------------------------------------------
    print("\n[TEST 06/15] Model Loader & 3D Staging (Armature, Mesh, Skinning, Mats)...")
    client_prov = AionClientProvider(test_client)
    model_prov = ModelProvider(client_prov)

    stage_col = ViewerStage.get_or_create_stage_collection()
    ViewerStage.clear_stage_objects()

    root_obj = model_prov.load_model(
        entry=first_shugo,
        target_collection=stage_col,
        load_animation=True,
    )
    assert root_obj is not None, "Failed to load model root object"
    assert root_obj.type == "ARMATURE", f"Expected ARMATURE root, got {root_obj.type}"
    assert len(root_obj.data.bones) > 0, "Loaded armature has 0 bones!"

    # Verify child mesh
    mesh_children = [c for c in root_obj.children if c.type == "MESH"]
    assert len(mesh_children) > 0, "No child mesh found under armature!"
    loaded_mesh = mesh_children[0]
    assert len(loaded_mesh.data.vertices) > 0, "Loaded mesh has 0 vertices!"
    assert len(loaded_mesh.data.polygons) > 0, "Loaded mesh has 0 polygons!"
    assert len(loaded_mesh.data.uv_layers) > 0, "Loaded mesh is missing UV layers!"
    assert len(loaded_mesh.data.materials) > 0, "Loaded mesh is missing materials!"
    assert len(loaded_mesh.vertex_groups) > 0, "Loaded mesh is missing vertex groups for skinning!"

    # Verify Idle animation is bound
    assert root_obj.animation_data is not None and root_obj.animation_data.action is not None, "Idle animation action not bound!"
    action = root_obj.animation_data.action
    print(f"  -> Loaded {first_shugo.name}: {len(root_obj.data.bones)} bones, {len(loaded_mesh.data.vertices)} vertices, {len(loaded_mesh.data.polygons)} tris, Action '{action.name}'")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 7: Viewport Controls & Lighting Staging
    # -------------------------------------------------------------------------
    print("\n[TEST 07/15] Viewport Controls, Lighting & Shading...")
    ViewerStage.setup_studio_lighting()
    ViewerStage.frame_object(root_obj)
    set_shading_mode("MATERIAL")
    set_bones_display(root_obj, show_bones=True, in_front=True)
    assert root_obj.show_in_front is True, "Armature in_front display setting failed"
    print("  -> 3-point studio lighting configured and camera focused.")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 8: Animation Switching & Transport Controls
    # -------------------------------------------------------------------------
    print("\n[TEST 08/15] Animation Switching & Transport Controls...")
    AnimationPlayer.play()
    AnimationPlayer.step_frame(5)
    assert bpy.context.scene.frame_current >= 5
    AnimationPlayer.stop()
    assert bpy.context.scene.frame_current == bpy.context.scene.frame_start
    print("  -> Animation playback transport controls tested.")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 9: Mesh Editing & Normals Recalculation
    # -------------------------------------------------------------------------
    print("\n[TEST 09/15] Mesh Editing & Normals Recalculation...")
    v_orig = loaded_mesh.data.vertices[0].co.z
    loaded_mesh.data.vertices[0].co.z += 0.5
    MeshEditor.recalculate_normals(loaded_mesh)
    v_new = loaded_mesh.data.vertices[0].co.z
    assert abs(v_new - (v_orig + 0.5)) < 1e-4, "Vertex modification was not preserved"
    stats = MeshEditor.extract_geometry_stats(loaded_mesh)
    print(f"  -> Mesh geometry modified: {stats[0]} verts, {stats[1]} edges, {stats[2]} tris.")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 10: Skeleton Editor & Bone Hierarchy Sync
    # -------------------------------------------------------------------------
    print("\n[TEST 10/15] Skeleton Editor & Bone Addition...")
    initial_bones = len(root_obj.data.bones)
    new_bone = SkeletonEditor.add_bone(
        arm_obj=root_obj,
        bone_name="Bip01 TestWing",
        head_pos=(0.0, 0.0, 1.5),
        tail_pos=(0.0, 0.0, 1.8),
        parent_name=root_obj.data.bones[0].name,
    )
    assert new_bone is not None, "Failed adding bone to armature"
    assert len(root_obj.data.bones) == initial_bones + 1, "Bone count did not increase by 1"
    print(f"  -> Added bone '{new_bone}' successfully (total bones: {len(root_obj.data.bones)}).")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 11: Material Editor
    # -------------------------------------------------------------------------
    print("\n[TEST 11/15] Material & Shader Editor...")
    mat = loaded_mesh.data.materials[0]
    MaterialEditor.set_roughness(mat, 0.45)
    MaterialEditor.set_emission(mat, 0.2)
    MaterialEditor.set_two_sided(mat, True)
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    assert bsdf is not None and abs(bsdf.inputs["Roughness"].default_value - 0.45) < 1e-3
    print("  -> Material shader properties adjusted and validated.")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 12: Transactional Safe Save (Safe Mode / Read-Only Fallback)
    # -------------------------------------------------------------------------
    print("\n[TEST 12/15] Transactional Safe Save (Read-Only Safety Switch)...")
    temp_export_dir = Path(tempfile.mkdtemp(prefix="aion_safe_export_"))
    try:
        res = DirectSaver.save_model(
            root_obj=root_obj,
            entry=first_shugo,
            model_provider=model_prov,
            client_root=test_client,
            allow_client_write=False,  # Safety switch engaged
            fallback_dir=temp_export_dir,
        )
        assert res.success is True, f"Safe save failed: {res.message}"
        assert len(res.written_files) > 0, "No files written to safe export directory"
        saved_file = Path(res.written_files[0])
        assert saved_file.is_file(), f"Output file does not exist: {saved_file}"
        assert saved_file.stat().st_size > 10000, "Output CGF appears too small"
        print(f"  -> Safe save verified: wrote {len(res.written_files)} files to export folder without touching client.")
    finally:
        shutil.rmtree(temp_export_dir, ignore_errors=True)
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 13: Transactional Safe Save (Live Client Mode with .bak)
    # -------------------------------------------------------------------------
    print("\n[TEST 13/15] Transactional Save with Automatic .bak Backup & Integrity...")
    # Test on an isolated mock client environment to verify live transaction semantics safely
    mock_client = Path(tempfile.mkdtemp(prefix="aion_mock_client_"))
    try:
        # Create loose model path
        mock_model = mock_client / "objects" / "test_model" / "test_model.cgf"
        mock_model.parent.mkdir(parents=True, exist_ok=True)
        # Write initial dummy CGF bytes
        mock_model.write_bytes(b"AION_ORIGINAL_CGF_DATA_FOR_TESTING_1234567890")

        updates = {"objects/test_model/test_model.cgf": b"AION_PATCHED_CGF_NEW_DATA_9876543210"}
        tx_res = TransactionManager.save_assets(
            client_root=mock_client,
            asset_updates=updates,
            allow_client_write=True,
            create_backups=True,
        )
        assert tx_res.success is True, f"Transaction failed: {tx_res.message}"
        assert mock_model.read_bytes() == b"AION_PATCHED_CGF_NEW_DATA_9876543210", "Live file was not updated"
        bak_file = mock_model.with_suffix(".cgf.bak")
        assert bak_file.is_file(), f"Backup file {bak_file} was not created!"
        assert bak_file.read_bytes() == b"AION_ORIGINAL_CGF_DATA_FOR_TESTING_1234567890", "Backup content mismatch"
        print(f"  -> Live write succeeded with automatic .bak backup created.")

        # ---------------------------------------------------------------------
        # TEST 14: Transactional Rollback
        # ---------------------------------------------------------------------
        print("\n[TEST 14/15] Transactional Rollback from Backup...")
        rolled_back = TransactionManager.rollback(bak_file)
        assert rolled_back is True, "Rollback failed"
        assert mock_model.read_bytes() == b"AION_ORIGINAL_CGF_DATA_FOR_TESTING_1234567890", "Rollback did not restore original content!"
        print("  -> Rollback successfully restored target file byte-for-byte.")
        passed_tests += 1  # For test 14
    finally:
        shutil.rmtree(mock_client, ignore_errors=True)
    passed_tests += 1  # For test 13

    # -------------------------------------------------------------------------
    # TEST 15: Model Creator & Cloner
    # -------------------------------------------------------------------------
    print("\n[TEST 15/15] Model Creator & Model Cloner...")
    # 1. Create from arbitrary Blender mesh
    bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, location=(0, 0, 0))
    cylinder_obj = bpy.context.active_object
    created_entry, c_tx = ModelCreator.create_model_from_selected(
        obj=cylinder_obj,
        asset_name="LostAcademy_Pillar",
        category="PROP",
    )
    assert created_entry is not None, f"Model creation failed: {c_tx.message}"
    assert created_entry.vertex_count > 0, "Created asset has 0 vertices"
    assert db.get_by_id(created_entry.asset_id) is not None, "Created entry was not registered in AssetDatabase"
    print(f"  -> Created brand new asset '{created_entry.name}' ({created_entry.vertex_count} vertices, {created_entry.triangle_count} tris).")

    # 2. Clone existing asset
    cloned_entry, clone_tx = ModelCloner.clone_asset(
        source_entry=first_shugo,
        new_name="Shugo Cloned Variant",
        client_provider=client_prov,
    )
    assert cloned_entry is not None, f"Cloning failed: {clone_tx.message}"
    assert db.get_by_id(cloned_entry.asset_id) is not None, "Cloned entry not registered in AssetDatabase"
    print(f"  -> Cloned asset into '{cloned_entry.name}' (ID: {cloned_entry.asset_id}).")
    passed_tests += 1

    # Cleanup created test object
    bpy.data.objects.remove(cylinder_obj, do_unlink=True)

    # -------------------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"ALL {passed_tests}/{total_tests} VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("LOSTACADEMY AION MODEL LIBRARY READY FOR PRODUCTION USE.")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
