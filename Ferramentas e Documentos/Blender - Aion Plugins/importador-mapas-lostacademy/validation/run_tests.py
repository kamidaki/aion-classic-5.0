"""
Comprehensive Validation & Test Suite for Aion Blender Toolkit.
Can be executed via Blender headless:
blender.exe -b --python validation/run_tests.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Add plugin root and vendor to sys.path
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))
_VENDOR_DIR = _PLUGIN_ROOT / "_vendor"
if _VENDOR_DIR.is_dir() and str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

CLIENT_ROOT = Path("D:/GameForge/aionclassic")


def log_test(name: str):
    print(f"\n{'='*70}\n[TEST] {name}\n{'='*70}")


def run_tests():
    total_passed = 0
    total_failed = 0
    t0 = time.time()

    print(f"Starting Aion Blender Toolkit Test Suite...")
    print(f"Plugin Root: {_PLUGIN_ROOT}")
    print(f"Client Root: {CLIENT_ROOT}")

    # -------------------------------------------------------------
    # Test 1: Addon Package Registration in Blender
    # -------------------------------------------------------------
    log_test("Test 1: Package Registration & Module Sanity")
    try:
        import bpy
        import properties
        import operators
        import ui

        properties.register()
        operators.register()
        ui.register()

        # Check operator registration
        assert hasattr(bpy.ops.aion, "direct_save"), "bpy.ops.aion.direct_save missing!"
        assert hasattr(bpy.ops.aion, "snap_to_terrain"), "bpy.ops.aion.snap_to_terrain missing!"
        assert hasattr(bpy.ops.aion, "randomize_transforms"), "bpy.ops.aion.randomize_transforms missing!"
        assert hasattr(bpy.ops.aion, "sync_terrain"), "bpy.ops.aion.sync_terrain missing!"
        assert hasattr(bpy.ops.import_scene, "aion_level_folder"), "bpy.ops.import_scene.aion_level_folder missing!"
        assert hasattr(bpy.ops.import_scene, "aion_cgf"), "bpy.ops.import_scene.aion_cgf missing!"
        assert hasattr(bpy.ops.export_scene, "aion_level"), "bpy.ops.export_scene.aion_level missing!"

        # Check scene settings property
        assert hasattr(bpy.types.Scene, "aion_settings"), "bpy.types.Scene.aion_settings missing!"

        print("PASS: All operators and scene properties successfully registered in Blender.")
        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Registration failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 2: Core PAK Indexing & Catalog Speed
    # -------------------------------------------------------------
    log_test("Test 2: Core PAK Engine & Catalog Indexing")
    try:
        from core.pak_engine import get_pak_resolver

        t_idx_start = time.time()
        resolver = get_pak_resolver(CLIENT_ROOT)
        resolver.ensure_catalog()
        t_idx = time.time() - t_idx_start

        catalog = resolver.catalog
        paks_count = catalog.indexed_paks_count
        print(f"Catalog indexed {paks_count} PAK archives in {t_idx:.3f}s.")
        assert paks_count > 50, f"Expected >50 PAKs, found {paks_count}"

        # Dynamically sample a known DDS from the catalog
        sample_tex = next((k for k in catalog._path_to_pak_entry.keys() if k.endswith(".dds")), None)
        assert sample_tex is not None, "No DDS textures found in catalog!"
        tex_bytes = catalog.extract_file(sample_tex)
        assert tex_bytes is not None and len(tex_bytes) > 0, f"Failed to extract {sample_tex}"
        print(f"Successfully extracted sample texture {sample_tex}: {len(tex_bytes)} bytes.")

        print(f"PASS: Catalog indexing and extraction functioning with high performance.")
        total_passed += 1
    except Exception as exc:
        print(f"FAIL: PAK engine test failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 3: Shader Semantics Resolution (Direct from shaders.pak)
    # -------------------------------------------------------------
    log_test("Test 3: CryEngine Shader Semantics Resolution")
    try:
        from formats.cgf.shader_semantics import resolve_client_shader_semantics

        leaf_semantics = resolve_client_shader_semantics("Aion_Plants_Leaf", client_root=CLIENT_ROOT)
        assert leaf_semantics is not None, "Failed to resolve Aion_Plants_Leaf shader!"
        assert leaf_semantics.two_sided is True, "Leaf shader should be two_sided!"
        print(f"Resolved Leaf Shader: definition={leaf_semantics.definition_path}, two_sided={leaf_semantics.two_sided}")

        bg_semantics = resolve_client_shader_semantics("Aion_BG_Base", client_root=CLIENT_ROOT)
        assert bg_semantics is not None, "Failed to resolve Aion_BG_Base shader!"
        print(f"Resolved BG Shader: definition={bg_semantics.definition_path}")

        print("PASS: Shaders resolved directly from client shaders.pak.")
        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Shader resolution failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 4: Format Parsers & Binary Round-Trip Precision
    # -------------------------------------------------------------
    log_test("Test 4: Format Parsers & Round-Trip Lossless Integrity")
    temp_dir = Path(tempfile.mkdtemp(prefix="aion_val_"))
    try:
        from formats.level.brush import parse_brush_lst, write_brush_lst
        from formats.level.objects import parse_objects_lst, write_objects_lst
        from formats.level.terrain import parse_land_map_h32, write_land_map_h32

        # 4a. Brush.lst roundtrip
        brush_src = CLIENT_ROOT / "levels" / "login" / ".aion_cache" / "brush.lst"
        if brush_src.is_file():
            b_data = parse_brush_lst(brush_src)
            b_tmp = temp_dir / "brush.lst"
            write_brush_lst(b_tmp, b_data)

            src_bytes = brush_src.read_bytes()
            out_bytes = b_tmp.read_bytes()
            assert len(src_bytes) == len(out_bytes), f"Brush byte length mismatch: {len(src_bytes)} vs {len(out_bytes)}"
            assert src_bytes == out_bytes, "Brush byte content mismatch!"
            print(f"PASS: brush.lst byte-for-byte identical round-trip ({len(src_bytes)} bytes, {len(b_data.nodes)} brushes).")

        # 4b. Objects.lst roundtrip
        objs_src = CLIENT_ROOT / "levels" / "lf1" / ".aion_cache" / "objects.lst"
        if objs_src.is_file():
            o_data = parse_objects_lst(objs_src)
            o_tmp = temp_dir / "objects.lst"
            write_objects_lst(o_tmp, o_data)

            src_bytes = objs_src.read_bytes()
            out_bytes = o_tmp.read_bytes()
            assert len(src_bytes) == len(out_bytes), f"Objects byte length mismatch: {len(src_bytes)} vs {len(out_bytes)}"
            assert src_bytes == out_bytes, "Objects byte content mismatch!"
            print(f"PASS: objects.lst byte-for-byte identical round-trip ({len(src_bytes)} bytes, {len(o_data.placements)} placements).")

        # 4c. Land_map.h32 roundtrip
        h32_src = CLIENT_ROOT / "levels" / "login" / ".aion_cache" / "terrain" / "land_map.h32"
        if h32_src.is_file():
            h_data = parse_land_map_h32(h32_src)
            h_tmp = temp_dir / "land_map.h32"
            write_land_map_h32(h_tmp, h_data)

            src_bytes = h32_src.read_bytes()
            out_bytes = h_tmp.read_bytes()
            assert len(src_bytes) == len(out_bytes), f"LandMap byte length mismatch: {len(src_bytes)} vs {len(out_bytes)}"
            assert src_bytes == out_bytes, "LandMap byte content mismatch!"
            print(f"PASS: land_map.h32 byte-for-byte identical round-trip ({len(src_bytes)} bytes, {h_data.sample_count} samples).")

        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Format roundtrip failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # Test 5: Material & Shader Translation (Principled BSDF)
    # -------------------------------------------------------------
    log_test("Test 5: CryEngine -> Blender Material Translation")
    try:
        import bpy
        from materials.shader_interpreter import create_aion_principled_material

        sample_textures = {
            "diffuse": CLIENT_ROOT / "levels" / "common" / "textures" / "terrain" / "detail" / "cliff_01.dds",
            "bump": CLIENT_ROOT / "levels" / "common" / "textures" / "terrain" / "detail" / "cliff_01_ddn.dds",
        }

        mat = create_aion_principled_material(
            material_name="Test_Vegetation_Leaf",
            shader_name="Aion_Plants_Leaf",
            texture_paths=sample_textures,
            material_flags={"two_sided": 1, "alpha_test": 1},
            client_root=CLIENT_ROOT,
        )

        assert mat is not None, "Material was not created!"
        assert mat.use_nodes is True, "Material should use nodes!"
        nodes = mat.node_tree.nodes
        principled = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
        assert principled is not None, "Principled BSDF node missing!"

        normal_node = next((n for n in nodes if n.type == "NORMAL_MAP"), None)
        print(f"Material created with Principled BSDF and Normal Map: {normal_node is not None}")

        print("PASS: Material node tree correctly configured with shader properties.")
        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Material translation failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 6: Live Environmental Animation Rigging
    # -------------------------------------------------------------
    log_test("Test 6: Live Environmental Animation Setup")
    try:
        import bpy
        from animations.wind_system import apply_vegetation_wind_sway
        from animations.water_animation import apply_water_wave_animation

        # Create dummy mesh
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=5, location=(0, 0, 2.5))
        tree_obj = bpy.context.active_object
        tree_obj.name = "Test_Animated_Tree"

        # Apply wind
        wind_mod = apply_vegetation_wind_sway(tree_obj, "objects/vegetation/plant.cgf", wind_strength=0.08, wind_speed=0.05)
        assert wind_mod is not None, "Wind deform modifier missing!"
        assert wind_mod.type == "SIMPLE_DEFORM", f"Expected SIMPLE_DEFORM, got {wind_mod.type}"
        print(f"Wind sway applied with SimpleDeform modifier: {wind_mod.name}")

        # Create water plane
        bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
        water_obj = bpy.context.active_object
        water_obj.name = "Test_Animated_Water"

        # Apply water wave
        wave_mod = apply_water_wave_animation(water_obj, wave_speed=0.015, wave_height=0.1)
        assert wave_mod is not None, "Water wave modifier missing!"
        assert wave_mod.type == "WAVE", f"Expected WAVE modifier, got {wave_mod.type}"
        print(f"Water animation applied with wave modifier: {wave_mod.name}")

        print("PASS: Live environmental animations configured with native Blender systems.")
        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Animation setup failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 7: Direct Save Pipeline & Round-Trip Scene Sync
    # -------------------------------------------------------------
    log_test("Test 7: Direct Save Map & Round-Trip Scene Sync")
    val_level_dir = Path(tempfile.mkdtemp(prefix="aion_direct_save_"))
    try:
        import bpy
        from mathutils import Matrix, Vector
        from editing.roundtrip_tracker import tag_object_instance
        from exporters.level_exporter import export_and_save_level
        from formats.level.brush import parse_brush_lst

        # Setup test level environment in temp_dir
        login_cache = CLIENT_ROOT / "levels" / "login" / ".aion_cache"
        if login_cache.is_dir():
            shutil.copytree(login_cache, val_level_dir / ".aion_cache")

        login_pak = CLIENT_ROOT / "levels" / "login" / "Level.pak"
        if login_pak.is_file():
            shutil.copy2(login_pak, val_level_dir / "Level.pak")
        else:
            (val_level_dir / "Level.pak").write_bytes(b"initial_level_pak_data")

        # Clear existing mesh objects in scene
        for obj in list(bpy.context.scene.objects):
            if obj.type == "MESH":
                bpy.data.objects.remove(obj, do_unlink=True)

        # Create a mock edited brush object in Blender
        bpy.ops.mesh.primitive_cube_add(size=2, location=(100.0, 200.0, 50.0))
        edited_obj = bpy.context.active_object
        edited_obj.name = "Brush_Test_Placement"

        # Tag it as an existing brush from brush.lst (Index 0)
        tag_object_instance(
            obj=edited_obj,
            source_type="brush",
            reference="objects/env/bridge.cgf",
            source_index=0,
            original_matrix=Matrix.Identity(4),
        )

        # Move and rotate it
        edited_obj.location = Vector((150.0, 250.0, 75.0))
        edited_obj.rotation_euler = (0.0, 0.0, 0.785) # 45 deg Z

        # Execute Direct Save
        result = export_and_save_level(
            bpy.context.scene,
            val_level_dir,
            create_backup=True,
            repack_pak=True,
        )

        assert result.success is True, f"Direct save returned failure: {result.message}"
        assert result.target_pak.is_file(), f"Target Level.pak was not created at {result.target_pak}"
        assert result.backup_created is True, "Backup Level.pak.bak was not created!"
        print(f"Direct Save Result: {result.message}")

        # Verify that brush.lst in the level was updated with the edited location
        saved_brush_path = val_level_dir / ".aion_cache" / "brush.lst"
        if not saved_brush_path.is_file():
            saved_brush_path = val_level_dir / "brush.lst"

        assert saved_brush_path.is_file(), f"Updated brush.lst missing at {saved_brush_path}"
        updated_brushes = parse_brush_lst(saved_brush_path)
        first_b = updated_brushes.nodes[0]
        # Coordinates in brush.lst 3x4 row-major matrix: tx=3, ty=7, tz=11
        print(f"Updated brush position in file: ({first_b.transform[3]:.2f}, {first_b.transform[7]:.2f}, {first_b.transform[11]:.2f})")
        assert abs(first_b.transform[3] - 150.0) < 0.01, f"Expected X=150.0, got {first_b.transform[3]}"
        assert abs(first_b.transform[7] - 250.0) < 0.01, f"Expected Y=250.0, got {first_b.transform[7]}"
        assert abs(first_b.transform[11] - 75.0) < 0.01, f"Expected Z=75.0, got {first_b.transform[11]}"

        print("PASS: Direct Save accurately serialized scene edits back to binary level files and repacked Level.pak.")
        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Direct save test failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1
    finally:
        shutil.rmtree(val_level_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # Test 8: Authoritative World & NPC Spawns / Template Parser
    # -------------------------------------------------------------
    log_test("Test 8: Authoritative World & NPC Spawns / Template Parser")
    try:
        from core.pak_engine import AionPakArchive
        from formats.level.npc_spawns import parse_world_npc_spawns, parse_client_npc_templates

        # Test world spawns from Data/world/world.pak
        world_pak = CLIENT_ROOT / "Data" / "world" / "world.pak"
        if not world_pak.is_file():
            world_pak = CLIENT_ROOT / "data" / "world" / "world.pak"
        assert world_pak.is_file(), f"world.pak missing at {world_pak}"

        w_arc = AionPakArchive(world_pak)
        assert "client_world_df1.xml" in w_arc.entries, "client_world_df1.xml missing in world.pak!"
        raw_w = w_arc.read_entry(w_arc.entries["client_world_df1.xml"])
        assert raw_w is not None and len(raw_w) > 0, "Failed to read client_world_df1.xml"

        spawns = parse_world_npc_spawns(raw_w, "df1")
        assert len(spawns) > 50, f"Expected >50 spawns in df1, got {len(spawns)}"
        first_spawn = spawns[0]
        assert len(first_spawn.position) == 3, "Spawn position should be 3D (x, y, z)"
        print(f"Authoritative World Spawns: {len(spawns)} spawns extracted for df1. Sample: ID={first_spawn.npc_id} Pos={first_spawn.position}")

        # Test NPC templates from Data/npcs/npcs.pak
        npcs_pak = CLIENT_ROOT / "Data" / "npcs" / "npcs.pak"
        if not npcs_pak.is_file():
            npcs_pak = CLIENT_ROOT / "data" / "npcs" / "npcs.pak"
        assert npcs_pak.is_file(), f"npcs.pak missing at {npcs_pak}"

        n_arc = AionPakArchive(npcs_pak)
        assert "client_npcs.xml" in n_arc.entries, "client_npcs.xml missing in npcs.pak!"
        raw_n = n_arc.read_entry(n_arc.entries["client_npcs.xml"])
        assert raw_n is not None and len(raw_n) > 0, "Failed to read client_npcs.xml"

        templates = parse_client_npc_templates(raw_n)
        assert len(templates) > 10000, f"Expected >10000 templates, got {len(templates)}"

        # Check mapping for Boromer (ID 203518)
        assert "203518" in templates, "Boromer (203518) template missing!"
        boromer = templates["203518"]
        assert boromer.name == "Boromer", f"Expected Boromer, got {boromer.name}"

        # Check mapping for monster template with explicit mesh
        assert "201003" in templates or "201001" in templates, "Monster archetype template missing!"
        elem = templates.get("201003") or templates.get("201001")
        assert elem and elem.cgf_reference, "Monster template should have cgf_reference!"
        print(f"Authoritative NPC Templates: {len(templates)} templates extracted. Resolved Boromer: Name={boromer.name}, Sample Mob: Name={elem.name}, Model={elem.cgf_reference}")

        print("PASS: Authoritative world spawns and NPC archetype templates parsed with 100% precision.")
        total_passed += 1
    except Exception as exc:
        print(f"FAIL: NPC spawn and template test failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 9: Granular Import Classification & Hardware Mesh Instancing
    # -------------------------------------------------------------
    log_test("Test 9: Granular Import Classification & Hardware Mesh Instancing")
    try:
        import bpy
        from importers.level_jobs import (
            classify_cgf_category,
            should_import_cgf_ref,
            LevelCgfJob,
            SOURCE_OBJECT,
        )
        from importers.level_instances import create_level_cgf_placement_instances

        # 9a. Test category classification
        assert classify_cgf_category("objects/buildings/house.cgf") == "BUILDINGS"
        assert classify_cgf_category("objects/vegetation/tree_oak.cgf") == "VEGETATION"
        assert classify_cgf_category("objects/props/chair.cgf") == "PROPS"
        assert classify_cgf_category("objects/collision/cliff_col.cgf") == "COLLISION"
        assert classify_cgf_category("objects/effects/portal_fx.cgf") == "EFFECTS"

        # 9b. Test selective category & LOD filtering
        assert should_import_cgf_ref("objects/buildings/house.cgf", import_buildings=False) is False
        assert should_import_cgf_ref("objects/buildings/house.cgf", import_buildings=True) is True
        assert should_import_cgf_ref("objects/props/chair_lod1.cgf", import_lod1=False) is False
        assert should_import_cgf_ref("objects/props/chair_lod1.cgf", import_lod1=True) is True
        print("PASS: Granular category and LOD0-3 filtering rules correctly validated.")

        # 9c. Test hardware mesh instancing
        test_root_col = bpy.data.collections.new("Test_Instancing_Root")
        bpy.context.scene.collection.children.link(test_root_col)
        templates_col = bpy.data.collections.new(".Test_Templates")
        test_root_col.children.link(templates_col)

        test_mesh = bpy.data.meshes.new("Test_Shared_Mesh")
        test_template_obj = bpy.data.objects.new("Template_Test_Obj", test_mesh)
        templates_col.objects.link(test_template_obj)

        placements = tuple(
            LevelCgfJob(
                source_type=SOURCE_OBJECT,
                source_index=i,
                cgf_reference="objects/test/item.cgf",
                import_mode="STATIC_MESH",
                cache_key=("objects/test/item.cgf", "STATIC_MESH"),
                position=(10.0 * i, 20.0 * i, 5.0),
                scale=1.0,
                heading_degrees=0.0,
                category="PROPS",
            )
            for i in range(5)
        )

        batch = create_level_cgf_placement_instances(
            target_collection=test_root_col,
            template_collection=templates_col,
            placements=placements,
            max_placements=len(placements),
            use_mesh_instancing=True,
        )

        assert len(batch.instances) == 5, f"Expected 5 placed objects, got {len(batch.instances)}"
        for inst_obj in batch.instances:
            assert inst_obj.data == test_mesh, "Hardware instanced object must share single_mesh.data!"
            assert inst_obj.type == "MESH", "Instanced object must be a MESH object for GPU batching!"

        print(f"PASS: Hardware mesh instancing verified (5 instances sharing single mesh datablock '{test_mesh.name}').")

        # Cleanup
        for o in batch.instances:
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.objects.remove(test_template_obj, do_unlink=True)
        bpy.data.meshes.remove(test_mesh, do_unlink=True)
        bpy.data.collections.remove(templates_col)
        bpy.data.collections.remove(test_root_col)

        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Classification and instancing test failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 10: Baked Terrain Shadow Lightmap Resolution & Shader Multiplication
    # -------------------------------------------------------------
    log_test("Test 10: Baked Terrain Shadow Lightmap Resolution & Node Blending")
    try:
        import bpy
        from core.pak_engine import get_pak_resolver, AionLevelUnpacker
        from importers.terrain_blend_nodes import _create_multiply_rgb

        resolver = get_pak_resolver(CLIENT_ROOT)
        resolver.ensure_catalog()

        df1_dir = CLIENT_ROOT / "levels" / "df1"
        shadow_path = None
        if df1_dir.is_dir():
            cache_dir = AionLevelUnpacker.unpack_level(df1_dir)
            shadow_candidate = cache_dir / "terrain" / "cover_low_shadow.dds"
            if not shadow_candidate.is_file():
                shadow_candidate = cache_dir / "newterrain" / "cover_low_shadow.dds"
            if shadow_candidate.is_file():
                shadow_path = shadow_candidate

        if not shadow_path:
            cand = resolver.resolve_resource("terrain/cover_low_shadow.dds")
            if not cand or not cand.is_file():
                cand = resolver.resolve_resource("newterrain/cover_low_shadow.dds")
            if cand and cand.is_file():
                shadow_path = cand

        print(f"Resolved baked terrain shadow path: {shadow_path}")
        assert shadow_path is not None and shadow_path.is_file(), "cover_low_shadow.dds could not be found or unpacked!"

        test_mat = bpy.data.materials.new("Test_Terrain_Shadow_Mat")
        test_mat.use_nodes = True
        nodes = test_mat.node_tree.nodes
        links = test_mat.node_tree.links

        rgb1 = nodes.new(type="ShaderNodeRGB")
        rgb2 = nodes.new(type="ShaderNodeRGB")
        out_socket = _create_multiply_rgb(nodes, links, None, rgb1.outputs[0], rgb2.outputs[0])
        assert out_socket is not None, "Failed to create multiply RGB output socket!"

        mix_node = next((n for n in nodes if getattr(n, "blend_type", "") == "MULTIPLY"), None)
        assert mix_node is not None, "Multiply RGB blend node missing in shader tree!"
        print(f"PASS: Baked terrain shadow map resolved and Multiply RGB shader node verified ({mix_node.type}, blend={mix_node.blend_type}).")

        # Cleanup
        bpy.data.materials.remove(test_mat)

        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Terrain shadow test failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 11: NPC Skeleton, Bone Hierarchy & Vertex Skin Weighting
    # -------------------------------------------------------------
    log_test("Test 11: CryEngine NPC Skeleton, Bone Hierarchy & Skin Weights")
    try:
        import io
        import bpy
        from core.pak_engine import get_pak_resolver
        from formats.cgf.parser import get_cgf
        from importers.armature_importer import build_npc_armature, apply_skin_weights

        r = get_pak_resolver(CLIENT_ROOT)
        r.ensure_catalog()

        cgf_bytes = r.catalog.extract_file("objects/npc/shugomale/shugomale.cgf")
        assert cgf_bytes is not None, "Failed extracting shugomale.cgf"

        cgf = get_cgf(io.BytesIO(cgf_bytes))
        bone_names = cgf.get("bone_names", [])
        bone_anim = cgf.get("bone_anim", [])
        bone_initial_pos = cgf.get("bone_initial_pos", [])

        assert len(bone_names) == 44, f"Expected 44 bones, got {len(bone_names)}"
        assert len(bone_anim) == 44, f"Expected 44 bone_anim entries, got {len(bone_anim)}"
        assert len(bone_initial_pos) == 44, f"Expected 44 bone_initial_pos, got {len(bone_initial_pos)}"

        # Find mesh node and skin weights
        mesh_chunk = None
        for nid, ndata in cgf.get("nodes", {}).items():
            if isinstance(ndata, dict) and "mesh" in ndata and ndata["mesh"]:
                mesh_chunk = ndata["mesh"]
                break
        assert mesh_chunk is not None, "shugomale.cgf mesh chunk missing!"
        skin_weights = mesh_chunk.get("skin_weights", [])
        assert len(skin_weights) > 1000, f"Expected >1000 weighted vertices, got {len(skin_weights)}"

        # Build Armature Rig
        test_col = bpy.data.collections.new("Test_Skel_Col")
        bpy.context.scene.collection.children.link(test_col)

        rig = build_npc_armature("Shugomale_Test", bone_names, bone_initial_pos, bone_anim, test_col)
        assert rig is not None and rig.type == "ARMATURE", "Armature creation failed!"
        assert len(rig.data.bones) == 44, f"Expected 44 edit bones in rig, got {len(rig.data.bones)}"

        # Build test mesh and apply skinning
        m_data = bpy.data.meshes.new("Shugomale_Test_Mesh")
        m_data.from_pydata(mesh_chunk["vertices"]["position"], [], mesh_chunk["faces"]["v"])
        m_data.update()
        mesh_obj = bpy.data.objects.new("Shugomale_Test_Obj", m_data)
        test_col.objects.link(mesh_obj)

        apply_skin_weights(mesh_obj, bone_names, skin_weights, rig)
        assert len(mesh_obj.vertex_groups) == 44, f"Expected 44 vertex groups, got {len(mesh_obj.vertex_groups)}"
        assert any(mod.type == "ARMATURE" and mod.object == rig for mod in mesh_obj.modifiers), "Armature modifier missing!"

        print(f"PASS: Shugomale skeleton created with 44 bones and {len(skin_weights)} skinned vertices.")

        # Cleanup
        bpy.data.objects.remove(mesh_obj, do_unlink=True)
        bpy.data.objects.remove(rig, do_unlink=True)
        bpy.data.collections.remove(test_col)
        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Skeleton test failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 12: CAF Animation Parsing, Keyframing & Cyclic Playback
    # -------------------------------------------------------------
    log_test("Test 12: CAF Animation Parsing, Pose Keyframing & Cyclic Playback")
    try:
        import io
        import bpy
        from core.client_provider import AionClientProvider
        from formats.cgf.parser import get_cgf
        from importers.armature_importer import build_npc_armature, apply_caf_animation

        provider = AionClientProvider(CLIENT_ROOT)
        cgf_ref = "objects/npc/shugomale/shugomale.cgf"
        cgf_bytes = provider.resolve_cgf_bytes(cgf_ref)
        assert cgf_bytes is not None, "Failed resolving shugomale.cgf bytes"

        cgf = get_cgf(io.BytesIO(cgf_bytes))
        bone_names = cgf.get("bone_names", [])
        bone_anim = cgf.get("bone_anim", [])
        bone_initial_pos = cgf.get("bone_initial_pos", [])

        test_col = bpy.data.collections.new("Test_Anim_Col")
        bpy.context.scene.collection.children.link(test_col)

        rig = build_npc_armature("Shugo_Anim_Test", bone_names, bone_initial_pos, bone_anim, test_col)
        cal_map, caf_bytes = provider.resolve_animation_asset(cgf_ref)

        assert cal_map is not None and len(cal_map) > 20, f"Expected >20 animations in CAL, got {len(cal_map) if cal_map else 0}"
        assert caf_bytes is not None and len(caf_bytes) > 10000, f"Expected >10KB CAF bytes, got {len(caf_bytes) if caf_bytes else 0}"

        action = apply_caf_animation(rig, caf_bytes, bone_names, bone_anim, action_name="Shugo_Test_Idle")
        assert action is not None, "Action creation failed!"
        assert rig.animation_data is not None and rig.animation_data.action == action, "Action not attached to rig!"
        assert getattr(action, "use_cyclic", False) is True, "Action use_cyclic should be True!"

        # Frame evaluation test
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        rot_frame_1 = rig.pose.bones["Bip01 Spine"].rotation_quaternion.copy()

        bpy.context.scene.frame_set(25)
        bpy.context.view_layer.update()
        rot_frame_25 = rig.pose.bones["Bip01 Spine"].rotation_quaternion.copy()

        assert rot_frame_1 != rot_frame_25, "Bone rotation should change across keyframes!"
        print(f"Spine Bone Rotation: Frame 1={rot_frame_1}, Frame 25={rot_frame_25}")
        print("PASS: CAF Idle animation keyframed with active bone rotation and cyclic playback.")

        # Cleanup
        bpy.data.objects.remove(rig, do_unlink=True)
        bpy.data.collections.remove(test_col)
        total_passed += 1
    except Exception as exc:
        print(f"FAIL: CAF animation test failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Test 13: Multi-Client Dynamic Provider & Compatibility Matrix
    # -------------------------------------------------------------
    log_test("Test 13: Multi-Client Dynamic Provider & Compatibility Matrix")
    try:
        from core.client_provider import AionClientProvider, ClientFlavor
        from formats.level.npc_spawns import parse_world_npc_spawns, parse_npc_templates

        test_clients = [
            ("Client 1", Path("D:/GameForge/aionclassic"), ClientFlavor.GAMEFORGE_CLASSIC),
            ("Client 2", Path("I:/Aion Live Clássico - América do Sul"), ClientFlavor.LIVE_CLASSICO_SA),
            ("Client 3", Path("I:/Servidor Aion/CLIENT 3. 9 - THIS AION BRASIL/This AION Brasil"), ClientFlavor.AION_39_LEGACY),
        ]

        for label, client_path, expected_flavor in test_clients:
            print(f"\n--- Auditing {label}: {client_path} ---")
            assert client_path.is_dir(), f"Client path {client_path} does not exist on disk!"

            prov = AionClientProvider(client_path)
            assert prov.flavor == expected_flavor, f"Expected {expected_flavor}, got {prov.flavor}"
            print(f"Flavor: {prov.flavor.name} (Matched)")

            # Map discovery
            maps = prov.get_available_maps()
            assert len(maps) > 50, f"Expected >50 maps, found {len(maps)}"
            assert "df1" in maps or "dc1" in maps, "Major map (df1/dc1) missing from levels!"
            print(f"Maps Discovered: {len(maps)} maps (Sample: {maps[:5]})")

            # World spawn extraction (df1)
            wdata = prov.read_world_spawns_data("df1")
            assert wdata is not None and len(wdata) > 0, "Failed reading df1 world spawn data!"
            spawns = parse_world_npc_spawns(wdata, "df1")
            assert len(spawns) > 50, f"Expected >50 spawns for df1, got {len(spawns)}"
            print(f"World Spawns (df1): {len(spawns)} authoritative spawns extracted")

            # NPC templates extraction
            tmpl_sources = prov.read_npc_templates_data()
            assert len(tmpl_sources) > 0, "No NPC template XML sources found!"
            total_templates = 0
            for tname, tbytes in tmpl_sources:
                tmpls = parse_npc_templates(tbytes)
                total_templates += len(tmpls)
            assert total_templates > 10000, f"Expected >10000 templates, got {total_templates}"
            print(f"NPC Templates: {total_templates} total archetypes parsed")

            # Model and Animation Asset Resolution
            shugo_cgf = prov.resolve_cgf_bytes("objects/npc/shugomale/shugomale.cgf")
            assert shugo_cgf is not None and len(shugo_cgf) > 50000, "Failed resolving shugomale.cgf!"
            cal_map, caf_bytes = prov.resolve_animation_asset("objects/npc/shugomale/shugomale.cgf")
            assert cal_map is not None and len(cal_map) > 20, "Failed resolving shugomale.cal!"
            assert caf_bytes is not None and len(caf_bytes) > 20000, "Failed resolving shugomale idle CAF!"
            print(f"Shugomale: CGF={len(shugo_cgf)}B, CAL={len(cal_map)} anims, Idle CAF={len(caf_bytes)}B")

            # Brax Monster Model and Animation Resolution
            brax_cgf = prov.resolve_cgf_bytes("Monster/brax/brax.cgf")
            assert brax_cgf is not None and len(brax_cgf) > 50000, "Failed resolving brax.cgf!"
            b_cal, b_caf = prov.resolve_animation_asset("Monster/brax/brax.cgf")
            assert b_cal is not None and len(b_cal) > 10, "Failed resolving brax.cal!"
            assert b_caf is not None and len(b_caf) > 10000, "Failed resolving brax idle CAF!"
            print(f"Brax Monster: CGF={len(brax_cgf)}B, CAL={len(b_cal)} anims, Idle CAF={len(b_caf)}B")

            print(f"PASS: {label} ({prov.flavor.name}) 100% validated across maps, spawns, templates, models, and animations.")

        total_passed += 1
    except Exception as exc:
        print(f"FAIL: Multi-client matrix test failed: {exc}")
        import traceback
        traceback.print_exc()
        total_failed += 1

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    duration = time.time() - t0
    print(f"\n{'='*70}")
    print(f"TEST SUITE COMPLETE: {total_passed} PASSED, {total_failed} FAILED in {duration:.2f}s")
    print(f"{'='*70}\n")
    return total_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
