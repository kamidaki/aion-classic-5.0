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
    "THUNDERER": {
        "armor_type": "lt",
        "weapon_main": "objects/items/ts_idarena01t.cgf",
        "weapon_sub": None,
        "weapon_bone": "Bip01 R Hand",
    },
    "RUNEBLADE": {
        "armor_type": "rb",
        "weapon_main": "objects/items/sw_yunnpc01.cgf",
        "weapon_sub": None,
        "weapon_bone": "Bip01 R Hand",
    },
    "BATTLEMASTER": {
        "armor_type": "lt",
        "weapon_main": None,
        "weapon_sub": None,
        "weapon_bone": "Bip01 R Hand",
    },
    "LUMINES": {
        "armor_type": "rb",
        "weapon_main": "objects/items/or_idelemental01ac.cgf",
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
        # Note: DF uses df004_hair.cgf as canonical centered hair (df001 is asymmetrical accessory)
        hair_name = "df004_hair.cgf" if rg == "df" else f"{rg}001_hair.cgf"
        return {
            "head": f"objects/pc/{rg}/mesh/{rg}001_head.cgf",
            "hair": f"objects/pc/{rg}/mesh/{hair_name}",
            "body": f"objects/pc/{rg}/mesh/{rg}{at}_a001_body.cgf",
            "legs": f"objects/pc/{rg}/mesh/{rg}{at}_a001_leg.cgf",
            "feet": f"objects/pc/{rg}/mesh/{rg}{at}_a001_foot.cgf",
            "hands": f"objects/pc/{rg}/mesh/{rg}{at}_a001_hand.cgf",
        }

    @staticmethod
    def get_class_animations(race_gender: str, class_name: str) -> List[Tuple[str, str]]:
        """Returns standard CAL animation state names and CAF file paths for the given class and race."""
        rg = race_gender.lower()
        cn = class_name.upper()

        if cn == "GLADIATOR":
            wtype = "2hand"
        elif cn in ("TEMPLAR", "CLERIC", "RUNEBLADE"):
            wtype = "1hand"
        elif cn == "RANGER":
            wtype = "bow"
        elif cn in ("ASSASSIN", "GUNSLINGER"):
            wtype = "2weapon"
        elif cn in ("SORCERER", "SPIRITMASTER", "LUMINES"):
            wtype = "orb"
        elif cn == "CHANTER":
            wtype = "staff"
        elif cn in ("THUNDERER", "BATTLEMASTER"):
            wtype = "2hand"
        else:
            wtype = "2hand"

        pfx = "lf" if "f" in rg else "lm"
        asmo_pfx = "df" if "f" in rg else "dm"
        is_asmo = rg.startswith("d")

        asmo_idle_map = {
            "GLADIATOR": f"{asmo_pfx}_nidle_warrior_001_loop.caf",
            "TEMPLAR": f"{asmo_pfx}_nidle_warrior_001_loop.caf",
            "RANGER": f"{asmo_pfx}_nidle_scout_001_loop.caf",
            "ASSASSIN": f"{asmo_pfx}_nidle_scout_001_loop.caf",
            "GUNSLINGER": f"{asmo_pfx}_nidle_scout_001_loop.caf",
            "SORCERER": f"{asmo_pfx}_nidle_mage_001_loop.caf",
            "SPIRITMASTER": f"{asmo_pfx}_nidle_mage_001_loop.caf",
            "CLERIC": f"{asmo_pfx}_nidle_cleric_001_loop.caf",
            "CHANTER": f"{asmo_pfx}_nidle_cleric_001_loop.caf",
            "THUNDERER": f"{asmo_pfx}_nidle_warrior_001_loop.caf",
            "RUNEBLADE": f"{asmo_pfx}_nidle_mage_001_loop.caf",
            "BATTLEMASTER": f"{asmo_pfx}_nidle_warrior_001_loop.caf",
            "LUMINES": f"{asmo_pfx}_nidle_mage_001_loop.caf",
        }

        normal_idle = asmo_idle_map.get(cn, f"{pfx}_nidle_001_loop.caf") if is_asmo else f"{pfx}_nidle_001_loop.caf"
        combat_idle = f"{pfx}_cidle_{wtype}_001_loop.caf"
        walk = f"{pfx}_nwalk_001_loop.caf"
        run = f"{pfx}_crun_{wtype}_001_loop.caf"
        attack1 = f"{pfx}_cattack_{wtype}_001.caf"
        attack2 = f"{pfx}_cattack_{wtype}_002.caf"
        jump = f"{asmo_pfx if is_asmo else pfx}_cjump_air_{wtype}_run_001.caf"
        glide = f"{pfx}_fglide_001_loop.caf"
        death = f"{pfx}_ndie_001.caf"

        return [
            ("Idle (Combate)", combat_idle),
            ("Idle (Normal)", normal_idle),
            ("Andar (Walk)", walk),
            ("Correr (Run)", run),
            ("Ataque 1", attack1),
            ("Ataque 2", attack2),
            ("Pulo (Jump)", jump),
            ("Planar (Glide)", glide),
            ("Morte (Death)", death),
        ]

    @staticmethod
    def assemble_class_character(
        client_provider: Any,
        model_provider: Any,
        race_gender: str,
        class_name: str,
        target_collection: bpy.types.Collection,
    ) -> Optional[bpy.types.Object]:
        """Loads and equips an entire class preset with default armor, weapons, and animations."""
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
        master_rig = model_provider.load_model(
            body_entry,
            target_collection,
            load_animation=False,
            slot_override="torso",
            replace_slot=False,
        )
        if not master_rig:
            return None

        if master_rig.type != "ARMATURE" and master_rig.parent and master_rig.parent.type == "ARMATURE":
            master_rig = master_rig.parent

        master_rig.name = f"Aion_{rg}_{class_name}_Rig"

        # 2. Equip other body parts on the same rig
        other_parts = [
            ("Head", parts.get("head"), "head"),
            ("Hair", parts.get("hair"), "hair"),
            ("Legs", parts.get("legs"), "legs"),
            ("Feet", parts.get("feet"), "feet"),
            ("Hands", parts.get("hands"), "hands"),
        ]

        for slot_name, part_path, slot_tag in other_parts:
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
                slot_override=slot_tag,
                replace_slot=False,
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
                slot_override="weapon_main",
                replace_slot=False,
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
                slot_override="weapon_sub",
                replace_slot=False,
            )

        # 5. Load and apply default combat/idle animation
        try:
            anims = MannequinProvider.get_class_animations(rg, class_name)
            if anims:
                def_name, def_caf = anims[0]
                caf_bytes = client_provider.find_caf_bytes(def_caf)

                if caf_bytes:
                    b_names, b_pos, b_anim = model_provider.skel_prov.extract_armature(master_rig)
                    action = model_provider.anim_prov.load_animation(
                        rig_obj=master_rig,
                        caf_bytes=caf_bytes,
                        action_name=f"{rg}_{class_name}_Idle",
                        bone_names=b_names,
                        bone_anim=b_anim,
                    )
                    if action:
                        start = int(action.frame_range[0])
                        end = int(action.frame_range[1])
                        bpy.context.scene.frame_start = start
                        bpy.context.scene.frame_end = end
                        bpy.context.scene.frame_set(start)
        except Exception as e:
            logger.warning("Could not auto-apply class idle animation: %s", e)

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
        # Torso / Body: essential for chest, arms, shoulders!
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
        if not any(k in mpath for k in ("leg", "pants", "trouser", "skirt")) and pfx in ("LF", "LM", "DF", "DM"):
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
