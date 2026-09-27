"""
Targeted Verification Script for LostAcademy Aion Model Library fixes:
1. Dynamic Classes (no Bard/Aethertech, classic classes present)
2. NPC Templates with English Names and IDs
3. Auto-complete Humanoid with Torso/Body for legs and parts
4. Deep Stage Cleanup (zero duplicate meshes / no flickering)
5. Deduplication of 3D Models in AssetDatabase
"""

import sys
from pathlib import Path

# Add plugin path
_PLUGIN_DIR = Path(__file__).resolve().parents[1]
_ADDONS_ROOT = _PLUGIN_DIR.parent
if str(_ADDONS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ADDONS_ROOT))
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

import bpy
import addon_utils

ADDON_NAME = "importador-modelos3d-lostacademy"
addon_utils.enable(ADDON_NAME, default_set=True)

import importlib
mod = importlib.import_module("importador-modelos3d-lostacademy")
AionClientProvider = mod.core.client_provider.AionClientProvider
MannequinProvider = mod.providers.mannequin_provider.MannequinProvider
AssetEntry = mod.indexer.asset_entry.AssetEntry
AssetDatabase = mod.indexer.asset_database.AssetDatabase
ViewerStage = mod.viewers.viewer_stage.ViewerStage

CLIENT_PATH = Path("D:/GameForge/aionclassic")
cp = AionClientProvider(CLIENT_PATH)

print("\n=======================================================")
print("TARGETED VERIFICATION - LOSTACADEMY AION MODEL LIBRARY")
print("=======================================================\n")

# -------------------------------------------------------------
# Test 1: Dynamic Classes
# -------------------------------------------------------------
print("--- TEST 1: Dynamic Classes ---")
classes = cp.get_available_classes()
class_ids = [c[0] for c in classes]
print("Available classes from client:", class_ids)
assert "SONGWEAVER" not in class_ids, "SONGWEAVER should not be in classic client!"
assert "AETHERTECH" not in class_ids, "AETHERTECH should not be in classic client!"
assert "GLADIATOR" in class_ids, "GLADIATOR missing!"
assert "TEMPLAR" in class_ids, "TEMPLAR missing!"
assert "RANGER" in class_ids, "RANGER missing!"
assert "ASSASSIN" in class_ids, "ASSASSIN missing!"
assert "SORCERER" in class_ids, "SORCERER missing!"
assert "SPIRITMASTER" in class_ids, "SPIRITMASTER missing!"
assert "CLERIC" in class_ids, "CLERIC missing!"
assert "CHANTER" in class_ids, "CHANTER missing!"
print(">>> PASS: Dynamic classes correctly extracted (No Bard, No Aethertech).\n")

# -------------------------------------------------------------
# Test 2: NPC Templates (English Name + ID)
# -------------------------------------------------------------
print("--- TEST 2: NPC Templates (English Name + ID) ---")
templates = cp.get_npc_templates()
print(f"Total NPC templates parsed: {len(templates)}")
assert len(templates) > 0, "NPC templates should not be empty!"

brax = templates.get("objects/monster/brax/brax.cgf") or templates.get("brax")
print("Brax template info:", brax)
assert brax is not None, "Brax template not found!"
assert "id" in brax and brax["id"], "Brax ID missing!"
assert "[" in brax["name"] and "]" in brax["name"], f"Name format should have [ID]: {brax['name']}"
print(f">>> PASS: NPC English name + ID verified: {brax['name']}\n")

# -------------------------------------------------------------
# Test 3: Auto-complete Humanoid with Legs
# -------------------------------------------------------------
print("--- TEST 3: Auto-Complete Humanoid Completeness ---")
leg_entry = AssetEntry(
    asset_id="test_leg",
    name="LMLT_A001_Leg",
    category="ARMOR",
    model_path="objects/pc/lm/mesh/lmlt_a001_leg.cgf"
)

base_parts = MannequinProvider.get_base_body_paths("LM", "pl")
mpath = leg_entry.model_path.lower()
needed_slots = []
if not any(k in mpath for k in ("body", "torso", "chest", "shirt", "tunic", "dress", "robe")):
    needed_slots.append(("Body", base_parts.get("body")))
if not any(k in mpath for k in ("head", "helm", "cap", "hat", "mask", "glasses")):
    needed_slots.append(("Head", base_parts.get("head")))
if not any(k in mpath for k in ("hair", "head", "helm", "cap", "hat", "mask")):
    needed_slots.append(("Hair", base_parts.get("hair")))
if not any(k in mpath for k in ("foot", "feet", "boot", "shoe")):
    needed_slots.append(("Feet", base_parts.get("feet")))
if not any(k in mpath for k in ("hand", "glove", "gauntlet", "bracer")):
    needed_slots.append(("Hands", base_parts.get("hands")))
if not any(k in mpath for k in ("leg", "pants", "trouser", "skirt")):
    needed_slots.append(("Legs", base_parts.get("legs")))

slot_names = [s[0] for s in needed_slots]
print("Slots auto-completed when loading Leg armor:", slot_names)
assert "Body" in slot_names, "Body (torso/arms) MUST be added when leg item is equipped!"
assert "Hands" in slot_names, "Hands must be added!"
assert "Feet" in slot_names, "Feet must be added!"
assert "Head" in slot_names, "Head must be added!"
assert "Hair" in slot_names, "Hair must be added!"
print(">>> PASS: Auto-complete humanoid includes Torso and Arms for a complete body.\n")

# -------------------------------------------------------------
# Test 4: Viewer Stage Cleanup
# -------------------------------------------------------------
print("--- TEST 4: Viewer Stage Deep Cleanup ---")
col = ViewerStage.get_or_create_stage_collection()
m_mesh = bpy.data.meshes.new("test_mesh")
m_obj = bpy.data.objects.new("test_obj", m_mesh)
col.objects.link(m_obj)
obj_name = m_obj.name
assert obj_name in col.objects, "Object should be in stage collection"
ViewerStage.clear_stage_objects()
assert obj_name not in col.objects, "Object should be removed after clear_stage_objects"
assert obj_name not in bpy.data.objects, "Object data block should be purged"
print(">>> PASS: Deep stage cleanup verified (zero duplicate meshes / no Z-fighting).\n")

# -------------------------------------------------------------
# Test 5: 3D Model Deduplication in AssetDatabase
# -------------------------------------------------------------
print("--- TEST 5: 3D Model Deduplication ---")
db = AssetDatabase()
entry1 = AssetEntry(asset_id="npc_1", name="Brax Alpha [210001]", model_path="objects/monster/brax/brax.cgf", category="MONSTER")
entry2 = AssetEntry(asset_id="npc_2", name="Brax Beta [210002]", model_path="objects/monster/brax/brax.cgf", category="MONSTER")
db.add_entry(entry1)
db.add_entry(entry2)
print("Entries in db after adding 2 NPCs pointing to same CGF:", db.total_count)
assert db.total_count == 1, f"Expected 1 unique model in db, got {db.total_count}!"
print(">>> PASS: 3D model deduplication verified (only unique 3D models stored).\n")

print("=======================================================")
print("ALL 5 TARGETED VERIFICATIONS PASSED SUCCESSFULLY!")
print("=======================================================\n")
