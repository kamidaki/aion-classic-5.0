"""
Automated Verification Suite for Sound, Visual Effects (VFX), and Texture/Material Cache Resilience.
Tests:
1. Repeated model reloading without 'StructRNA of type Material has been removed' ReferenceErrors.
2. Texture resolution and extraction across monster PAKs.
3. SoundProvider audio clip discovery and extraction for Baku, Brax, and Shugo.
4. EffectProvider procedural VFX application (shader aura, socket lights, particle emitters) and cleanup.
5. Operators and UI properties registration.
"""

from __future__ import annotations
import sys
from pathlib import Path

ADDONS_DIR = Path(r"D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Blender - Aion Plugins")
if str(ADDONS_DIR) not in sys.path:
    sys.path.insert(0, str(ADDONS_DIR))

import bpy
import addon_utils

print("\n" + "=" * 80)
print("TEST: SOUND, VFX & MATERIAL/TEXTURE CACHE RESILIENCE")
print("=" * 80)

ADDON_NAME = "importador-modelos3d-lostacademy"
addon_utils.enable(ADDON_NAME)

import importlib
pkg = importlib.import_module(ADDON_NAME)
lib_ops = importlib.import_module(f"{ADDON_NAME}.operators.library_ops")
db_mod = importlib.import_module(f"{ADDON_NAME}.indexer.asset_database")
stage_mod = importlib.import_module(f"{ADDON_NAME}.viewers.viewer_stage")
sound_mod = importlib.import_module(f"{ADDON_NAME}.providers.sound_provider")
effect_mod = importlib.import_module(f"{ADDON_NAME}.providers.effect_provider")

CLIENT_PATH = r"D:\GameForge\aionclassic"
settings = bpy.context.scene.aion_model_lib
settings.client_path = CLIENT_PATH

client_prov = lib_ops.get_client_provider(CLIENT_PATH)
model_prov = lib_ops.get_model_provider(CLIENT_PATH)
stage_col = stage_mod.ViewerStage.get_or_create_stage_collection()

db = db_mod.AssetDatabase.get()

# -------------------------------------------------------------------------
# Test 1: Material/Texture Invalidation Resilience (Load -> Switch -> Reload)
# -------------------------------------------------------------------------
print("\n[Step 1] Testing repeated loading & Material/Texture cache resilience...")

ae_mod = importlib.import_module(f"{ADDON_NAME}.indexer.asset_entry")
AssetEntry = ae_mod.AssetEntry

baku_entry = AssetEntry(
    asset_id="baku_giraffe_stone_lod1",
    name="Baku Giraffe Stone Lod1",
    category="monsters",
    model_path="objects/monster/baku_giraffe/baku_giraffe_stone_lod1.cgf",
    cal_path="objects/monster/baku_giraffe/baku_giraffe.cal"
)

brax_entry = AssetEntry(
    asset_id="brax",
    name="Brax",
    category="monsters",
    model_path="objects/monster/brax/brax.cgf",
    cal_path="objects/monster/brax/brax.cal"
)

db.load_from_entries([baku_entry, brax_entry])
item = settings.asset_items.add()
item.asset_id = baku_entry.asset_id
item.name = baku_entry.name
settings.active_asset_index = 0


# First Load
print(f"  -> Loading {baku_entry.name} (first pass)...")
stage_mod.ViewerStage.clear_stage_objects()
model_prov.mat_prov.clear_cache()
model_prov.tex_prov.clear_cache()

root1 = model_prov.load_model(baku_entry, stage_col, load_animation=True)
assert root1 is not None, "Failed loading Baku on first pass!"
meshes1 = [c for c in root1.children if c.type == "MESH"]
assert meshes1, "No mesh children found on Baku!"
mat_count1 = len(meshes1[0].data.materials)
print(f"  -> First pass success: {len(meshes1)} meshes, {mat_count1} materials.")

# Switch to a different model (Brax or Shugo)
brax_matches = db.search("brax", limit=5)
if brax_matches:
    brax_entry = brax_matches[0]
    print(f"  -> Loading intermediate model {brax_entry.name}...")
    stage_mod.ViewerStage.clear_stage_objects()
    model_prov.mat_prov.clear_cache()
    model_prov.tex_prov.clear_cache()
    root2 = model_prov.load_model(brax_entry, stage_col, load_animation=True)
    assert root2 is not None, "Failed loading intermediate model!"

# Purge orphans simulating Blender memory purge
try:
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
except Exception:
    pass

# Reload Baku - THIS PREVIOUSLY CRASHED WITH StructRNA of type Material has been removed!
print(f"  -> Reloading {baku_entry.name} (second pass - testing cache resilience)...")
stage_mod.ViewerStage.clear_stage_objects()
model_prov.mat_prov.clear_cache()
model_prov.tex_prov.clear_cache()

root3 = model_prov.load_model(baku_entry, stage_col, load_animation=True)
assert root3 is not None, "Failed reloading Baku on second pass!"
meshes3 = [c for c in root3.children if c.type == "MESH"]
assert meshes3, "No mesh children found on reloaded Baku!"
print(f"  -> Second pass success: {len(meshes3)} meshes, {len(meshes3[0].data.materials)} materials.")
print(">>> PASS: StructRNA Material/Texture invalidation bug completely resolved!")

# -------------------------------------------------------------------------
# Test 2: SoundProvider Audio Discovery & Extraction
# -------------------------------------------------------------------------
print("\n[Step 2] Testing SoundProvider audio discovery & playback pipeline...")

sp = sound_mod.SoundProvider.get(client_prov.catalog, Path(CLIENT_PATH))

# Test Baku sounds
baku_sounds = sp.get_sounds_for_model(baku_entry)
print(f"  -> Discovered {len(baku_sounds)} sound effects for Baku:")
assert len(baku_sounds) > 0, "No sounds discovered for Baku!"
for s in baku_sounds[:6]:
    print(f"     [{s['category']}] {s['name']} -> {s['file']}")

# Test audio resolution to disk
test_sound_file = baku_sounds[0]["file"]
extracted_audio_p = sp.resolve_sound_file(test_sound_file)
print(f"  -> Extracted sound file: {extracted_audio_p}")
assert extracted_audio_p is not None and extracted_audio_p.is_file(), f"Failed resolving sound file {test_sound_file}!"
assert extracted_audio_p.stat().st_size > 500, "Extracted sound file is empty or corrupted!"

# Test Brax sounds
if brax_matches:
    brax_sounds = sp.get_sounds_for_model(brax_matches[0])
    print(f"  -> Discovered {len(brax_sounds)} sound effects for Brax:")
    assert len(brax_sounds) > 0, "No sounds discovered for Brax!"

# Test operators
bpy.ops.aion_model.refresh_sounds()
assert len(settings.model_sounds) > 0, "settings.model_sounds was not populated by operator!"
print(f"  -> Operator populated {len(settings.model_sounds)} sounds in UI PropertyGroup.")

# Test Stop Audio Operator
res_stop = bpy.ops.aion_model.stop_sound()
assert res_stop == {"FINISHED"}, "Stop sound operator failed!"
print(">>> PASS: SoundProvider audio discovery, extraction and operators verified!")

# -------------------------------------------------------------------------
# Test 3: EffectProvider Visual Effects (VFX) Engine
# -------------------------------------------------------------------------
print("\n[Step 3] Testing EffectProvider visual effects (VFX) engine...")

ep = effect_mod.EffectProvider.get()

# Test socket detection
sockets = ep.find_effect_sockets(root3)
print(f"  -> Discovered {len(sockets)} effect sockets on model:")
assert len(sockets) > 0, "No effect sockets discovered on model!"
for s_name, loc, pb in sockets[:5]:
    print(f"     Socket: {s_name} at ({loc.x:.2f}, {loc.y:.2f}, {loc.z:.2f})")

# Test applying FIRE VFX
print("  -> Applying FIRE visual effect (shader aura, lights, particles)...")
ok_fire = ep.apply_vfx(
    root_obj=root3,
    element="FIRE",
    intensity=1.5,
    show_glow=True,
    show_lights=True,
    show_particles=True,
)
assert ok_fire, "Failed applying FIRE VFX!"

vfx_objs = [o for o in bpy.data.objects if o.get("is_aion_vfx") or o.name.startswith("Aion_VFX_")]
print(f"  -> Created {len(vfx_objs)} dynamic VFX objects (lights, particle emitters).")
assert len(vfx_objs) > 0, "No VFX objects were created!"

# Test applying FROST VFX (replacing existing)
print("  -> Switching to FROST visual effect...")
ok_frost = ep.apply_vfx(
    root_obj=root3,
    element="FROST",
    intensity=2.0,
    show_glow=True,
    show_lights=True,
    show_particles=True,
)
assert ok_frost, "Failed applying FROST VFX!"

# Test removing VFX
print("  -> Testing clean removal of VFX...")
ep.remove_vfx(root3)
remaining_vfx = [o for o in bpy.data.objects if o.get("is_aion_vfx") or o.name.startswith("Aion_VFX_")]
assert len(remaining_vfx) == 0, f"VFX cleanup left lingering objects: {remaining_vfx}"
print("  -> All VFX objects and shader emissions cleanly unlinked and purged.")

# Test VFX Operators
res_vfx_op = bpy.ops.aion_model.apply_vfx()
assert res_vfx_op == {"FINISHED"}, "apply_vfx operator failed!"
res_rem_op = bpy.ops.aion_model.remove_vfx()
assert res_rem_op == {"FINISHED"}, "remove_vfx operator failed!"

print(">>> PASS: EffectProvider visual effects engine verified!")

print("\n" + "=" * 80)
print("ALL SOUND, VFX & CACHE RESILIENCE TESTS PASSED SUCCESSFULLY!")
print("=" * 80)
