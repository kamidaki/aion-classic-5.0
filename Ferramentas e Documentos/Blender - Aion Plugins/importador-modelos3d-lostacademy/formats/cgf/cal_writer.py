"""
CryEngine 1 CAL (Character Animation List) Serializer.
Writes clean, authoritative .cal animation list files mapping animation state names
to relative CAF paths.
"""

from __future__ import annotations
from typing import Dict, Optional


def write_cal(mapping: Dict[str, str], header_comment: Optional[str] = None) -> bytes:
    """
    Serializes a dictionary of state_name -> caf_path into CAL text format.
    Returns bytes encoded in latin-1 (Aion standard).
    """
    lines = []
    if header_comment:
        for c_line in header_comment.strip().splitlines():
            lines.append(f"// {c_line}")
    lines.append("// Aion Model Library Character Animation List")
    lines.append("")

    # Sort keys for deterministic output, prioritizing idle animations first
    def _sort_key(item):
        k = item[0].lower()
        if "idle" in k:
            return (0, k)
        if "walk" in k or "run" in k:
            return (1, k)
        if "attack" in k:
            return (2, k)
        return (3, k)

    sorted_items = sorted(mapping.items(), key=_sort_key)

    for state, caf_path in sorted_items:
        clean_state = state.strip()
        clean_path = caf_path.strip().replace("\\", "/")
        lines.append(f"{clean_state} = {clean_path}")

    lines.append("")
    text = "\r\n".join(lines)
    return text.encode("latin-1")
