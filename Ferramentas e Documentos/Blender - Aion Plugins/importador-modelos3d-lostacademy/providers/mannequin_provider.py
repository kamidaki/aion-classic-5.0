"""
Mannequin & Dressing Room Provider for LostAcademy Aion Model Library.
Enables assembling, previewing, and equipping full Aion character classes
(all 11 classes across Elyos/Asmodian Male/Female) and auto-completing modular humanoid NPCs.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bpy
from mathutils import Vector

from ..indexer.asset_entry import AssetEntry

logger = logging.getLogger(__name__)

# Canonical Class Loadouts (Armor type + Default Weapon)
CLASS_PRESETS = {
    "GLADIATOR": {
        "armor_type": "pl",
        "weapon_main": "objects/items/ts_idarena01t.cgf",
        "weapon_sub": None,
        "weapon_bone": "Bip01 R Hand",
    },
    "TEMPLAR": {
        "armor_type": "pl",
        "weapon_main": "objects/items/sw_yunnpc01.cgf",
        "weapon_sub": "objects/items/sh_idarenanpc01.cgf",
        "weapon_bone": "Bip01 R Hand",
        "sub_bone": "Bip01 L Hand",
    },
    "RANGER": {
        "armor_type": "lt",
        "weapon_main": "objects/items/bo_cromedenpc.cgf",
        "weapon_sub": None,
        "weapon_bone": "Bip01 L Hand",
    },
    "ASSASSIN": {
        "armor_type": "lt",
        "weapon_main": "objects/items/da_yunnpc01.cgf",
        "weapon_sub": "objects/items/da_a103c.cgf",
        "weapon_bone": "Bip01 R Hand",
        "sub_bone": "Bip01 L Hand",
    },
    "SORCERER": {
        "armor_type": "rb",
        "weapon_main": "objects/items/or_idelemental01ac.cgf",
        "weapon_sub": None,
        "weapon_bone": "Bip01 R Hand",
    },
    "SPIRITMASTER": {
        "armor_type": "rb",
        "weapon_main": "objects/items/or_idelemental01ac.cgf",
        "weapon_sub": None,
        "weapon_bone": "Bip01 R Hand",
    },
    "CLERIC": {
        "armor_type": "ch",
        "weapon_main": "objects/items/ma_yunnpc01.cgf",
        "weapon_sub": "objects/items/sh_idarenanpc01.cgf",
        "weapon_bone": "Bip01 R Hand",
        "sub_bone": "Bip01 L Hand",
    },
    "CHANTER": {
        "armor_type": "ch",
        "weapon_main": "objects/items/st_yunnpc01.cgf",
        "weapon_sub": None,
        "weapon_bone": "Bip01 R Hand",
    },
    "GUNSLINGER": {
        "armor_type": "lt",
        "weapon_main": "objects/items/gu_v002.cgf",
        "weapon_sub": "objects/items/gu_v002.cgf",
        "weapon_bone": "Bip01 R Hand",
        "sub_bone": "Bip01 L Hand",
    },
    "SONGWEAVER": {
        "armor_type": "rb",
        "weapon_main": "objects/npc/event_object/luminarie/harp_2.cgf",
        "weapon_sub": None,
        "weapon_bone": "Bip01 L Hand",
    },
    "AETHERTECH": {
        "armor_type": "ch",
        "weapon_main": "objects/items/cb_housing02a_l.cgf",
        "weapon_sub": None,
        "weapon_bone": "Bip01 R Hand",
    },
}


class MannequinProvider:
    """Manages character dressing room, class presets, and modular humanoid auto-completion."""

    @staticmethod
    def detect_humanoid_prefix(model_path: str) -> Optional[str]:
        """Detects if a model belongs to a modular humanoid race (LF, LM, DF, DM, CLF, CLM, CAF, CAM)."""
        p_lower = model_path.lower().replace("\\", "/")
        fn = p_lower.split("/")[-1]

        for pfx in ("lf", "lm", "df", "dm", "clf", "clm", "caf", "cam"):
            if fn.startswith(f"{pfx}_") or fn.startswith(f"{pfx}pl_") or fn.startswith(f"{pfx}lt_") or \
               fn.startswith(f"{pfx}ch_") or fn.startswith(f"{pfx}rb_") or fn.startswith(f"{pfx}cl_") or \
               fn.startswith(f"{pfx}0"):
                return pfx.upper()
            if f"/{pfx}/" in p_lower:
                return pfx.upper()
        return None

    @staticmethod
    def get_base_body_paths(race_gender: str, armor_type: str = "pl") -> Dict[str, str]:
        """Returns standard paths for head, hair, body, legs, feet, and hands."""
        rg = race_gender.lower()
        at = armor_type.lower()

        # Handle commoner NPC prefixes
        if rg in ("clf", "clm", "caf", "cam"):
            hand_map = {
                "clf": "objects/npc/human/clf/clfch001_hand.cgf",
                "clm": "objects/npc/human/clm/clmch001_hand.cgf",
                "cam": "objects/npc/human/cam/camfp001_hand.cgf",
                "caf": "objects/npc/human/clf/clfch001_hand.cgf",
            }
            return {
                "head": f"objects/npc/human/{rg}/{rg}001_head.cgf",
                "hair": f"objects/npc/human/{rg}/{rg}001_hair.cgf",
                "body": f"objects/npc/human/{rg}/{rg}cl001_body.cgf",
                "legs": "",
                "feet": f"objects/npc/human/{rg}/{rg}cl001_foot.cgf",
                "hands": hand_map.get(rg, f"objects/npc/human/{rg}/{rg}ch001_hand.cgf"),
            }

        # PC races: LF, LM, DF, DM
        return {
            "head": f"objects/pc/{rg}/mesh/{rg}001_head.cgf",
            "hair": f"objects/pc/{rg}/mesh/{rg}001_hair.cgf",
            "body": f"objects/pc/{rg}/mesh/{rg}{at}_a001_body.cgf",
            "legs": f"objects/pc/{rg}/mesh/{rg}{at}_a001_leg.cgf",
            "feet": f"objects/pc/{rg}/mesh/{rg}{at}_a001_foot.cgf",
            "hands": f"objects/pc/{rg}/mesh/{rg}{at}_a001_hand.cgf",
        }

    @staticmethod
    def assemble_class_character(
        client_provider: Any,
        model_provider: Any,
        race_gender: str,
        class_name: str,
        target_collection: bpy.types.Collection,
    ) -> Optional[bpy.types.Object]:
        """Loads and equips an entire class preset with default armor and weapons."""
        preset = CLASS_PRESETS.get(class_name.upper())
        if not preset:
            preset = CLASS_PRESETS["GLADIATOR"]

        rg = race_gender.upper()
        if rg not in ("LF", "LM", "DF", "DM"):
            rg = "LF"

        armor_type = preset["armor_type"]
        parts = MannequinProvider.get_base_body_paths(rg, armor_type)

        # 1. Load Torso / Body to build the master armature rig
        body_path = parts.get("body")
        if not body_path:
            return None

        body_entry = AssetEntry(
            asset_id=f"mannequin_{rg}_{class_name}_body",
            name=f"{rg}_{class_name}_Body",
            category="ARMOR",
            model_path=body_path,
        )
        master_rig = model_provider.load_model(body_entry, target_collection, load_animation=True)
        if not master_rig:
            return None

        if master_rig.type != "ARMATURE" and master_rig.parent and master_rig.parent.type == "ARMATURE":
            master_rig = master_rig.parent

        master_rig.name = f"Aion_{rg}_{class_name}_Rig"

        # 2. Equip other body parts on the same rig
        other_parts = [
            ("Head", parts.get("head")),
            ("Hair", parts.get("hair")),
            ("Legs", parts.get("legs")),
            ("Feet", parts.get("feet")),
            ("Hands", parts.get("hands")),
        ]

        for slot_name, part_path in other_parts:
            if not part_path:
                continue
            entry = AssetEntry(
                asset_id=f"mannequin_{rg}_{slot_name.lower()}",
                name=f"{rg}_{slot_name}",
                category="CHARACTER" if slot_name in ("Head", "Hair") else "ARMOR",
                model_path=part_path,
            )
            model_provider.load_model(
                entry,
                target_collection,
                load_animation=False,
                target_rig=master_rig,
            )

        # 3. Equip Main Weapon
        main_weap = preset.get("weapon_main")
        if main_weap:
            weap_entry = AssetEntry(
                asset_id=f"mannequin_{rg}_mainweap",
                name=f"{class_name}_Weapon",
                category="WEAPON",
                model_path=main_weap,
            )
            model_provider.load_model(
                weap_entry,
                target_collection,
                load_animation=False,
                target_rig=master_rig,
            )

        # 4. Equip Sub Weapon / Shield if available
        sub_weap = preset.get("weapon_sub")
        if sub_weap:
            sub_entry = AssetEntry(
                asset_id=f"mannequin_{rg}_subweap",
                name=f"{class_name}_Offhand",
                category="WEAPON",
                model_path=sub_weap,
            )
            model_provider.load_model(
                sub_entry,
                target_collection,
                load_animation=False,
                target_rig=master_rig,
            )

        return master_rig

    @staticmethod
    def auto_complete_humanoid(
        client_provider: Any,
        model_provider: Any,
        loaded_entry: AssetEntry,
        target_rig: bpy.types.Object,
        target_collection: bpy.types.Collection,
    ) -> None:
        """Attaches matching head, hair, hands, and feet to a modular humanoid cloth/torso mesh."""
        pfx = MannequinProvider.detect_humanoid_prefix(loaded_entry.model_path)
        if not pfx:
            return

        base_parts = MannequinProvider.get_base_body_paths(pfx, "pl")
        mpath = loaded_entry.model_path.lower()

        needed_slots = []
        if "head" not in mpath and "helm" not in mpath:
            needed_slots.append(("Head", base_parts.get("head")))
            needed_slots.append(("Hair", base_parts.get("hair")))
        if "foot" not in mpath and "feet" not in mpath:
            needed_slots.append(("Feet", base_parts.get("feet")))
        if "hand" not in mpath and "glove" not in mpath:
            needed_slots.append(("Hands", base_parts.get("hands")))
        if "leg" not in mpath and "pants" not in mpath and "body" in mpath and pfx in ("LF", "LM", "DF", "DM"):
            needed_slots.append(("Legs", base_parts.get("legs")))

        for slot_name, part_path in needed_slots:
            if not part_path:
                continue
            entry = AssetEntry(
                asset_id=f"auto_{pfx}_{slot_name.lower()}",
                name=f"{pfx}_{slot_name}",
                category="CHARACTER" if slot_name in ("Head", "Hair") else "ARMOR",
                model_path=part_path,
            )
            model_provider.load_model(
                entry,
                target_collection,
                load_animation=False,
                target_rig=target_rig,
            )
