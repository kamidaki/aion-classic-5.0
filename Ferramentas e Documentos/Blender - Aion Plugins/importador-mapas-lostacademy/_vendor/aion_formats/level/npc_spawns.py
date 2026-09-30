"""
Aion NPC Spawns and Templates Parser for Level and World Data.

Provides pure-Python parsers for:
1. Data/world/world.pak -> client_world_<map>.xml authoritative spawn locations
   (Supports BXML for Client 1, UTF-16 XML for Client 2/3, UTF-8 XML)
2. Data/npcs/npcs.pak -> client_npcs.xml NPC templates, names, and 3D CGF model bindings
   (Supports BXML for Client 1, UTF-8 XML for Client 2, UTF-16 XML for Client 3)
3. Supplementary placeables from mission_mission0.xml
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class NpcSpawn:
    """Represents a single world NPC/monster spawn point."""
    npc_id: str
    position: Tuple[float, float, float]
    heading_degrees: float = 0.0
    has_explicit_z: bool = True
    raw_coords: Tuple[float, ...] = ()
    source: str = "world_xml"


@dataclass(frozen=True)
class NpcTemplate:
    """Represents an NPC or monster archetype definition."""
    id: str
    name: str
    title: str = ""
    cgf_reference: str = ""
    scale: float = 1.0
    category: str = "npc"  # 'npc', 'monster', 'ambient', 'shugo', 'object'
    race: str = ""  # 'DM', 'DF', 'LM', 'LF', etc.
    idle_animation: str = ""


# Fallback archetype models when specific mesh is omitted or dynamic
DEFAULT_HUMANOID_MODELS = {
    "DM": "objects/pc/dm/mesh/dm.cgf",
    "DF": "objects/pc/df/mesh/df.cgf",
    "LM": "objects/pc/lm/mesh/lm.cgf",
    "LF": "objects/pc/lf/mesh/lf.cgf",
    "SHUGO_M": "objects/npc/shugomale/shugomale.cgf",
    "SHUGO_F": "objects/npc/shugofemale/shugofemale.cgf",
}

# Known ambient critters / monsters
KNOWN_MONSTER_MODELS: Dict[str, str] = {
    "brax": "objects/monster/brax/brax.cgf",
    "zaif": "objects/monster/zaif/zaif.cgf",
    "teraphant": "objects/monster/teraphant/teraphant.cgf",
    "whistleboids": "objects/npc/monster/whistleboids/whistleboids.cgf",
    "qooqoo": "objects/npc/monster/qooqoo/qooqoo.cgf",
    "cherubim": "objects/monster/cherubim/cherubim.cgf",
    "krall": "objects/monster/krall/krall.cgf",
    "worm": "objects/monster/worm/worm.cgf",
    "porguss": "objects/monster/porguss/porguss.cgf",
    "mepiguss": "objects/monster/mepiguss/mepiguss.cgf",
}


def _decode_xml_bytes(raw: bytes) -> Tuple[str, bool]:
    """
    Decodes raw bytes into string and returns (text, is_standard_xml).
    Detects UTF-16LE with BOM, standard UTF-16, and UTF-8.
    """
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16", errors="replace"), True
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be", errors="replace"), True

    # Check for <?xml declaration
    prefix = raw[:60].lower()
    if b"<?xml" in prefix:
        if b"utf-16" in prefix:
            return raw.decode("utf-16", errors="replace"), True
        return raw.decode("utf-8", errors="replace"), True

    return "", False


def parse_world_npc_spawns(
    world_xml_bytes_or_path: bytes | str | Path,
    map_name: str = "",
) -> List[NpcSpawn]:
    """
    Parses client_world_<map>.xml (BXML or standard XML) to extract all authoritative NPC spawn positions.
    """
    raw: bytes
    if isinstance(world_xml_bytes_or_path, (str, Path)):
        p = Path(world_xml_bytes_or_path)
        if not p.is_file():
            return []
        raw = p.read_bytes()
    else:
        raw = bytes(world_xml_bytes_or_path)

    if not raw or len(raw) < 50:
        return []

    # 1. Try Standard XML (Client 2 & Client 3)
    text, is_xml = _decode_xml_bytes(raw)
    if is_xml and "<npc_info>" in text:
        try:
            root = ET.fromstring(text)
            spawns: List[NpcSpawn] = []
            for info in root.iter("npc_info"):
                nid = info.findtext("nameid")
                pos = info.find("pos")
                if nid and pos is not None:
                    try:
                        x = float(pos.findtext("x", "0"))
                        y = float(pos.findtext("y", "0"))
                        z = float(pos.findtext("z", "0"))
                        spawns.append(
                            NpcSpawn(
                                npc_id=str(nid).strip(),
                                position=(x, y, z),
                                heading_degrees=0.0,
                                has_explicit_z=True,
                                raw_coords=(x, y, z),
                                source="world_xml_standard",
                            )
                        )
                    except (ValueError, TypeError):
                        continue
            if spawns:
                return spawns
        except Exception:
            pass  # Fall back to regex / BXML

    # 2. Try CryEngine BXML (Client 1)
    target = "npc_infos".encode("utf-16le")
    pos = raw.find(target)
    if pos == -1:
        target = "npc_info".encode("utf-16le")
        pos = raw.find(target)
        if pos == -1:
            return []

    text_bxml = raw[pos:].decode("utf-16le", errors="ignore")
    tokens = [
        t.strip()
        for t in text_bxml.split("\x00")
        if t.strip() and all(ord(c) >= 32 or c in "\r\n\t" for c in t.strip())
    ]

    spawns_bxml: List[NpcSpawn] = []
    i = 0
    num_tokens = len(tokens)

    while i < num_tokens - 1:
        token = tokens[i]
        if token == "nameid" and i + 1 < num_tokens:
            npc_id = tokens[i + 1]
            if npc_id.isdigit():
                coords = []
                j = i + 2
                while j < min(num_tokens, i + 35):
                    sub = tokens[j]
                    if sub == "nameid":
                        break
                    try:
                        val = float(sub)
                        coords.append(val)
                    except ValueError:
                        pass
                    j += 1

                if len(coords) >= 2:
                    x = coords[0]
                    y = coords[1]
                    z = coords[2] if len(coords) >= 3 else 0.0
                    spawns_bxml.append(
                        NpcSpawn(
                            npc_id=npc_id,
                            position=(x, y, z),
                            heading_degrees=0.0,
                            has_explicit_z=len(coords) >= 3,
                            raw_coords=tuple(coords),
                            source="world_bxml",
                        )
                    )
                i = j
                continue
        i += 1

    return spawns_bxml


def parse_npc_templates(
    npc_xml_bytes_or_path: bytes | str | Path,
) -> Dict[str, NpcTemplate]:
    """
    Parses client_npcs.xml (BXML, UTF-8 XML, or UTF-16LE XML) to extract
    NPC templates, names, titles, categories, and 3D CGF model paths.
    """
    raw: bytes
    if isinstance(npc_xml_bytes_or_path, (str, Path)):
        p = Path(npc_xml_bytes_or_path)
        if not p.is_file():
            return {}
        raw = p.read_bytes()
    else:
        raw = bytes(npc_xml_bytes_or_path)

    if not raw or len(raw) < 50:
        return {}

    templates: Dict[str, NpcTemplate] = {}

    # 1. Try Standard XML (Client 2 & Client 3)
    text, is_xml = _decode_xml_bytes(raw)
    if is_xml and ("<npc_client>" in text or "<npc_clients>" in text):
        # Use regex pattern for ultra-fast parsing without loading 200MB into DOM
        pattern = re.compile(
            r"<npc_client>.*?<id>(\d+)</id>.*?<name>([^<]*)</name>(?:.*?<desc>([^<]*)</desc>)?(?:.*?<ui_race_type>([^<]*)</ui_race_type>)?(?:.*?<idle_animation>([^<]*)</idle_animation>)?(?:.*?<dir>([^<]*)</dir>)?(?:.*?<mesh>([^<]*)</mesh>)?",
            re.DOTALL | re.IGNORECASE,
        )
        for m in pattern.finditer(text):
            nid, name, desc, race, idle_anim, dir_val, mesh_val = m.groups()
            cgf = ""
            if dir_val and mesh_val:
                cgf = f"{dir_val.strip()}/{mesh_val.strip()}".replace("\\", "/")
                if not cgf.endswith(".cgf"):
                    cgf += ".cgf"
            elif race:
                race_clean = race.strip().upper()
                if "DARK" in race_clean:
                    cgf = DEFAULT_HUMANOID_MODELS.get("DM", "")
                elif "LIGHT" in race_clean:
                    cgf = DEFAULT_HUMANOID_MODELS.get("LM", "")

            templates[nid.strip()] = NpcTemplate(
                id=nid.strip(),
                name=name.strip() if name else f"NPC_{nid}",
                title="",
                cgf_reference=cgf,
                scale=1.0,
                category="npc",
                race=race.strip() if race else "",
                idle_animation=idle_anim.strip() if idle_anim else "",
            )

        if templates:
            return templates

    # 2. Try CryEngine BXML (Client 1)
    target = "npc_client".encode("utf-16le")
    pos = raw.find(target)
    if pos == -1:
        return {}

    text_bxml = raw[pos:].decode("utf-16le", errors="ignore")
    tokens = [
        t.strip()
        for t in text_bxml.split("\x00")
        if t.strip() and all(ord(c) >= 32 or c in "\r\n\t" for c in t.strip())
    ]

    i = 0
    num_tokens = len(tokens)
    while i < num_tokens - 1:
        if tokens[i] == "id" and i + 1 < num_tokens:
            npc_id = tokens[i + 1]
            if npc_id.isdigit():
                name = ""
                cgf_ref = ""
                race = ""
                idle_anim = ""

                j = i + 2
                while j < min(num_tokens, i + 35):
                    tok = tokens[j]
                    if tok == "id":
                        break
                    if tok == "name" and j + 1 < num_tokens:
                        name = tokens[j + 1]
                    elif tok == "ui_race_type" and j + 1 < num_tokens:
                        race = tokens[j + 1]
                    elif tok == "idle_animation" and j + 1 < num_tokens:
                        idle_anim = tokens[j + 1]
                    elif tok == "mesh" and j + 1 < num_tokens:
                        mesh_val = tokens[j + 1]
                        if mesh_val.endswith(".cgf"):
                            cgf_ref = mesh_val
                    j += 1

                if not cgf_ref and race:
                    race_upper = race.upper()
                    if "DARK" in race_upper:
                        cgf_ref = DEFAULT_HUMANOID_MODELS.get("DM", "")
                    elif "LIGHT" in race_upper:
                        cgf_ref = DEFAULT_HUMANOID_MODELS.get("LM", "")

                templates[npc_id] = NpcTemplate(
                    id=npc_id,
                    name=name if name else f"NPC_{npc_id}",
                    title="",
                    cgf_reference=cgf_ref,
                    scale=1.0,
                    category="npc",
                    race=race,
                    idle_animation=idle_anim,
                )
                i = j
                continue
        i += 1

    return templates


# Backward compatibility alias
parse_client_npc_templates = parse_npc_templates
