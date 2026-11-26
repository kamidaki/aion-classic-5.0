"""
CryEngine 1 CAL (Character Animation List) Parser.
Parses text files defining state-to-CAF mappings for characters and NPCs.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional


def parse_cal(cal_content: str | bytes) -> Dict[str, str]:
    """
    Parses a CAL animation list file.
    Returns dict mapping animation state name (e.g. 'nidle_001', 'nwalk_001')
    to relative CAF file path (e.g. 'NPC/ShugoMale/ShugoMale_nidle_001_loop.caf').
    """
    if isinstance(cal_content, bytes):
        text = cal_content.decode("latin-1", errors="replace")
    else:
        text = str(cal_content)

    mapping: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("#"):
            continue

        # Strip inline comments
        if "//" in line:
            line = line.split("//", 1)[0].strip()

        if "=" in line:
            state, caf_path = line.split("=", 1)
            state = state.strip().lower()
            caf_path = caf_path.strip().replace("\\", "/")
            if state and caf_path:
                mapping[state] = caf_path

    return mapping


def find_default_idle_animation(cal_mapping: Dict[str, str]) -> Optional[str]:
    """
    Finds the most authoritative idle animation from a CAL mapping.
    Priority order:
    1. 'nidle_001' (NPC idle loop 1)
    2. 'nidle_002'
    3. Any state starting with 'nidle'
    4. 'idle_001' / 'idle'
    5. 'cidle_noweapon_001_loop' / combat idle
    6. 'stand'
    7. First available entry
    """
    if not cal_mapping:
        return None

    # Exact matches first
    for candidate in ("nidle_001", "nidle_002", "nidle", "idle_001", "idle", "stand_001", "stand"):
        if candidate in cal_mapping:
            return cal_mapping[candidate]

    # Prefix match
    for state, path in cal_mapping.items():
        if state.startswith("nidle") or state.startswith("idle"):
            return path

    for state, path in cal_mapping.items():
        if "idle" in state or "stand" in state:
            return path

    # Fallback to first
    return next(iter(cal_mapping.values()))
