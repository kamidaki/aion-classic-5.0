"""
Aion Client-Side Hardcoded NPCs, Monsters & Spawn Entities Resolver.

In Aion, NPCs, monsters, ambient critters, and local entities are defined in
mission_mission0.xml, client_npcs.xml, and Data/npcs/npcs.pak.

This module resolves NPC IDs, spawn template names (SP), and ambient fauna to
their appropriate 3D .cgf models (monsters, PC/NPC mannequins, fauna, furniture).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional, Tuple

# Pre-compiled lookup table for standard Aion Classic client_npc and monster definitions
KNOWN_CLIENT_NPCS: Dict[str, Tuple[str, float]] = {
    # Whistleboids (ambient flying creatures in Poeta LF1 and other zones)
    "298011": ("objects/npc/monster/whistleboids/whistleboids.cgf", 1.0),
    "298012": ("objects/npc/monster/whistleboids/whistleboids.cgf", 1.5),
    "client_npc_whistleboids": ("objects/npc/monster/whistleboids/whistleboids.cgf", 1.0),
    # Teraphant (large ambient behemoths)
    "298001": ("objects/npc/monster/teraphant/teraphant.cgf", 1.2),
    "298002": ("objects/npc/monster/teraphant/teraphant.cgf", 0.7),
    "298013": ("objects/npc/monster/teraphant/teraphant.cgf", 1.0),
    "298014": ("objects/npc/monster/teraphant/teraphant.cgf", 1.5),
    # Teraphant Dark variants
    "298015": ("objects/npc/monster/teraphant_d/teraphant_d.cgf", 0.7),
    "298016": ("objects/npc/monster/teraphant_d/teraphant_d.cgf", 1.0),
    "298017": ("objects/npc/monster/teraphant_d/teraphant_d.cgf", 1.2),
    # Rhabdodon
    "298007": ("objects/npc/monster/rhabdodon/rhabdodon.cgf", 0.6),
    # Brax (wild cattle)
    "298018": ("objects/monster/brax/Brax.cgf", 1.0),
    # Qooqoo (chickens/dodos)
    "298019": ("objects/npc/monster/qooqoo/qooqoo.cgf", 1.0),
    # Mepiguss & Porguss (pigs)
    "298020": ("objects/monster/mepiguss/mepiguss.cgf", 1.0),
    "298021": ("objects/monster/porguss/porguss.cgf", 1.0),
}

# General monster name mapping for live world spawns
KNOWN_MONSTER_TEMPLATES: Dict[str, Tuple[str, float]] = {
    "cherubim": ("objects/monster/cherubim/cherubim.cgf", 1.0),
    "braxbaby": ("objects/monster/brax/Brax.cgf", 0.6),
    "brax": ("objects/monster/brax/Brax.cgf", 1.0),
    "zaif": ("objects/monster/Zaif/Zaif.cgf", 1.0),
    "browniem": ("objects/monster/browniem/DBrownieMWa.cgf", 1.0),
    "browniew": ("objects/monster/browniew/DBrownieWWa.cgf", 1.0),
    "dbrownie": ("objects/monster/browniem/DBrownieMWa.cgf", 1.0),
    "krall": ("objects/monster/krall/krall.cgf", 1.0),
    "tkrall": ("objects/monster/krall/krall.cgf", 1.0),
    "fungus": ("objects/monster/Fungus/fungus.cgf", 1.0),
    "fungo": ("objects/monster/Fungus/fungus.cgf", 1.0),
    "fungchu": ("objects/monster/Fungus/fungus.cgf", 1.0),
    "fungky": ("objects/monster/Fungus/fungus.cgf", 1.0),
    "lepisma": ("objects/monster/lepisma/lepisma.cgf", 1.0),
    "hiiv": ("objects/monster/hiiv/hiiv.cgf", 1.0),
    "merdion": ("objects/monster/merdion/merdion.cgf", 1.0),
    "porguss": ("objects/monster/porguss/porguss.cgf", 1.0),
    "mepiguss": ("objects/monster/mepiguss/mepiguss.cgf", 1.0),
    "spaky": ("objects/monster/spaky/Spaky.cgf", 1.0),
    "fethlot": ("objects/monster/fethlot/fethlot.cgf", 1.0),
    "griffon": ("objects/monster/griffon/griffon.cgf", 1.0),
    "training_dummy": ("objects/monster/training_dummy/training_dummy.cgf", 1.0),
    "whistleboids": ("objects/npc/monster/whistleboids/whistleboids.cgf", 1.0),
    "teraphant": ("objects/npc/monster/teraphant/teraphant.cgf", 1.0),
    "rhabdodon": ("objects/npc/monster/rhabdodon/rhabdodon.cgf", 0.6),
    "qooqoo": ("objects/npc/monster/qooqoo/qooqoo.cgf", 1.0),
    "shugo": ("objects/npc/shugo/shugo.cgf", 1.0),
}

FEMALE_NPC_KEYWORDS = (
    "aello", "esera", "feira", "lonia", "mune", "naeru", "polinia", "pranoa", "pula", "seril", "cfm", "female"
)
MALE_NPC_KEYWORDS = (
    "ager", "ampeis", "amus", "asteros", "auron", "ben", "brutus", "daines", "elpis", "ino",
    "kagas", "kales", "kalio", "kunandes", "kustanon", "melampus", "melpone", "mires", "muranes",
    "namus", "navid", "ozzz", "pernos", "poa", "toleo", "tula", "uno", "uteiron", "mercenary",
    "farmer", "clm", "male", "guard"
)

_DYNAMIC_CLIENT_NPCS_CACHE: Dict[str, Tuple[str, float]] = {}
_DYNAMIC_CACHE_INITIALIZED = False


def _parse_dynamic_client_npcs(client_root: Path) -> None:
    """Dynamically parses Data/npcs/npcs.pak -> client_npcs.xml string pool."""
    global _DYNAMIC_CACHE_INITIALIZED
    if _DYNAMIC_CACHE_INITIALIZED:
        return
    _DYNAMIC_CACHE_INITIALIZED = True

    try:
        from core.pak_engine import AionPakArchive

        pak_path = client_root / "Data" / "npcs" / "npcs.pak"
        if not pak_path.is_file():
            return

        arc = AionPakArchive(pak_path)
        entry = arc.entries.get("client_npcs.xml")
        if not entry:
            return

        raw = arc.read_entry(entry)
        if not raw or len(raw) < 100:
            return

        # Aion BXML string table is null-terminated UTF-16LE starting at offset 7
        text = raw[7:5104000].decode("utf-16le", errors="replace")
        items = text.split("\x00")

        last_id = None
        last_name = None

        for i, item in enumerate(items):
            cleaned = item.strip()
            if not cleaned:
                continue
            if cleaned.isdigit() and len(cleaned) in (6, 7):
                last_id = cleaned
                if i + 1 < len(items):
                    nxt = items[i + 1].strip()
                    if nxt and not nxt.startswith("STR_") and not nxt.isdigit() and "/" not in nxt:
                        last_name = nxt
            elif "/" in cleaned and any(
                cleaned.lower().startswith(p) for p in ("monster", "npc", "pc", "misc", "skill_object")
            ):
                last_dir = cleaned
                if i + 1 < len(items):
                    mesh = items[i + 1].strip()
                    if mesh and not mesh.isdigit() and not mesh.startswith("STR_") and "/" not in mesh:
                        cgf_path = f"objects/{last_dir.lower()}/{mesh.lower()}.cgf"
                        if last_id and last_id not in _DYNAMIC_CLIENT_NPCS_CACHE:
                            _DYNAMIC_CLIENT_NPCS_CACHE[last_id] = (cgf_path, 1.0)
                        if last_name and last_name not in _DYNAMIC_CLIENT_NPCS_CACHE:
                            _DYNAMIC_CLIENT_NPCS_CACHE[last_name] = (cgf_path, 1.0)
    except Exception:
        pass


def resolve_client_npc_asset(
    npc_name_or_id: str,
    client_root: Path | None = None,
) -> Optional[Tuple[str, float]]:
    """
    Resolves an NPC ID or template name (e.g. '210259', 'Brax_3_n', 'Ager') to (cgf_path, scale).
    """
    clean_id = str(npc_name_or_id or "").strip()
    if not clean_id:
        return None

    # 1. Exact match in built-in client NPC table
    if clean_id in KNOWN_CLIENT_NPCS:
        return KNOWN_CLIENT_NPCS[clean_id]

    lower_id = clean_id.lower()

    # 2. Check general monster template patterns (e.g. Cherubim, Brax, Zaif, Brownie, Krall)
    for key, val in KNOWN_MONSTER_TEMPLATES.items():
        if key in lower_id:
            return val

    # 3. Check dynamic cache if client_root is available
    if client_root is not None:
        _parse_dynamic_client_npcs(Path(client_root))
        if clean_id in _DYNAMIC_CLIENT_NPCS_CACHE:
            return _DYNAMIC_CLIENT_NPCS_CACHE[clean_id]
        if lower_id in _DYNAMIC_CLIENT_NPCS_CACHE:
            return _DYNAMIC_CLIENT_NPCS_CACHE[lower_id]

    # 4. Check human villager / guard / farmer mannequin fallbacks
    if any(female in lower_id for female in FEMALE_NPC_KEYWORDS):
        return ("objects/npc/cfm/cfm.cgf", 1.0)
    elif any(male in lower_id for male in MALE_NPC_KEYWORDS):
        return ("objects/npc/clm/clm.cgf", 1.0)

    return None
