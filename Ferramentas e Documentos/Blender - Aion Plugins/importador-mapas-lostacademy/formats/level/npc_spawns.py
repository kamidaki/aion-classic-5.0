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
    "DM": "objects/npc/human/cam/cam.cgf",
    "DF": "objects/npc/human/caf/caf.cgf",
    "LM": "objects/npc/human/cem/cem.cgf",
    "LF": "objects/npc/human/cff/cff.cgf",
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
    Handles Client 1 (CryEngine BXML token streaming), Client 2 (UTF-8 XML), and Client 3 (UTF-16LE XML).
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

    # 2. CryEngine BXML (Client 1) - Multi-token stream parsing
    pos = -1
    for target in ("nameid".encode("utf-16le"), "npc_infos".encode("utf-16le"), "npc_info".encode("utf-16le")):
        found = raw.find(target)
        if found != -1:
            pos = found
            break

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

    while i < num_tokens:
        tok = tokens[i]
        # In Aion world BXML, NPC spawns are 6-digit IDs (starting with 2, 7, or 8) followed by float coordinates
        if tok.isdigit() and len(tok) == 6 and tok[0] in ("2", "7", "8"):
            npc_id = tok
            coords = []
            j = i + 1
            while j < min(num_tokens, i + 8):
                sub = tokens[j]
                if sub.isdigit() and len(sub) == 6 and sub[0] in ("2", "7", "8"):
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
                        source="world_bxml_stream",
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
    Supports Client 1 (CryEngine BXML streaming), Client 2 (UTF-8 XML), and Client 3 (UTF-16LE XML).
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
        re_id = re.compile(r"<id>(\d+)</id>")
        re_name = re.compile(r"<name>([^<]+)</name>")
        re_desc = re.compile(r"<desc>([^<]+)</desc>")
        re_dir = re.compile(r"<dir>([^<]+)</dir>")
        re_mesh = re.compile(r"<mesh>([^<]+)</mesh>")
        re_pc = re.compile(r"<pc_type>([^<]+)</pc_type>")
        re_race = re.compile(r"<ui_race_type>([^<]+)</ui_race_type>")
        re_anim = re.compile(r"<idle_animation>([^<]+)</idle_animation>")

        blocks = text.split("</npc_client>")
        for b in blocks:
            m_id = re_id.search(b)
            if not m_id:
                continue
            nid = m_id.group(1).strip()
            m_name = re_name.search(b)
            name = m_name.group(1).strip() if m_name else f"NPC_{nid}"
            m_desc = re_desc.search(b)
            desc = m_desc.group(1).strip() if m_desc else ""

            m_dir = re_dir.search(b)
            m_mesh = re_mesh.search(b)
            cgf = ""
            if m_dir and m_mesh:
                cgf = f"{m_dir.group(1).strip()}/{m_mesh.group(1).strip()}".replace("\\", "/")
                if not cgf.endswith(".cgf"):
                    cgf += ".cgf"
            else:
                m_pc = re_pc.search(b)
                pc_type = m_pc.group(1).strip().upper() if m_pc else ""
                if "LIGHT_M" in pc_type or "LM" in pc_type:
                    cgf = DEFAULT_HUMANOID_MODELS.get("LM", "")
                elif "LIGHT_F" in pc_type or "LF" in pc_type:
                    cgf = DEFAULT_HUMANOID_MODELS.get("LF", "")
                elif "DARK_M" in pc_type or "DM" in pc_type:
                    cgf = DEFAULT_HUMANOID_MODELS.get("DM", "")
                elif "DARK_F" in pc_type or "DF" in pc_type:
                    cgf = DEFAULT_HUMANOID_MODELS.get("DF", "")

            m_anim = re_anim.search(b)
            idle_anim = m_anim.group(1).strip() if m_anim else ""

            m_race = re_race.search(b)
            race = m_race.group(1).strip() if m_race else ""

            category = "monster" if "monster" in b.lower() or "mat_mob" in b.lower() else "npc"

            templates[nid] = NpcTemplate(
                id=nid,
                name=name,
                title=desc if not desc.startswith("STR_") else "",
                cgf_reference=cgf,
                scale=1.0,
                category=category,
                race=race,
                idle_animation=idle_anim,
            )

        if templates:
            return templates

    # 2. Try CryEngine BXML (Client 1) - Multi-token stream parsing
    pos = raw.find("npc_client".encode("utf-16le"))
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

    while i < num_tokens:
        tok = tokens[i]
        # In Aion BXML, each template begins with a 6-digit ID (starting with 2, 7, or 8)
        if tok.isdigit() and len(tok) == 6 and tok[0] in ("2", "7", "8"):
            nid = tok
            name = tokens[i + 1] if i + 1 < num_tokens and not tokens[i + 1].isdigit() else f"NPC_{nid}"
            cgf_ref = ""
            race = ""
            idle_anim = ""
            category = "npc"

            j = i + 1
            while j < min(num_tokens, i + 35):
                sub = tokens[j]
                if sub.isdigit() and len(sub) == 6 and sub[0] in ("2", "7", "8"):
                    break
                if "/" in sub and not cgf_ref:
                    if j + 1 < num_tokens and not tokens[j + 1].isdigit() and "/" not in tokens[j + 1]:
                        cgf_ref = f"{sub}/{tokens[j + 1]}.cgf"
                    elif sub.endswith(".cgf"):
                        cgf_ref = sub
                if "idle" in sub.lower() and not idle_anim:
                    idle_anim = sub
                if sub in ("DM", "DF", "LM", "LF", "SHUGO_M", "SHUGO_F"):
                    race = sub
                if "monster" in sub.lower():
                    category = "monster"
                j += 1

            if not cgf_ref and race:
                race_upper = race.upper()
                if "DARK" in race_upper or race_upper == "DM":
                    cgf_ref = DEFAULT_HUMANOID_MODELS.get("DM", "")
                elif "LIGHT" in race_upper or race_upper == "LM":
                    cgf_ref = DEFAULT_HUMANOID_MODELS.get("LM", "")

            templates[nid] = NpcTemplate(
                id=nid,
                name=name,
                title="",
                cgf_reference=cgf_ref,
                scale=1.0,
                category=category,
                race=race,
                idle_animation=idle_anim,
            )
            i = j
            continue
        i += 1

    return templates


# Backward compatibility alias
parse_client_npc_templates = parse_npc_templates


def update_world_npc_spawns_xml(
    xml_path: Path | str,
    modified_npcs: Dict[str, Tuple[float, float, float]],
) -> int:
    """Updates or creates client_world_<map>.xml with modified NPC spawn coordinates."""
    target = Path(xml_path)
    if not modified_npcs:
        return 0

    if target.is_file():
        try:
            raw = target.read_bytes()
            text, is_xml = _decode_xml_bytes(raw)
            if is_xml and "<npc_info>" in text:
                root = ET.fromstring(text)
                updated = 0
                for info in root.iter("npc_info"):
                    nid = str(info.findtext("nameid", "")).strip()
                    if nid in modified_npcs:
                        pos_elem = info.find("pos")
                        if pos_elem is None:
                            pos_elem = ET.SubElement(info, "pos")
                        new_pos = modified_npcs[nid]
                        x_elem = pos_elem.find("x")
                        if x_elem is None:
                            x_elem = ET.SubElement(pos_elem, "x")
                        x_elem.text = f"{new_pos[0]:.4f}"
                        y_elem = pos_elem.find("y")
                        if y_elem is None:
                            y_elem = ET.SubElement(pos_elem, "y")
                        y_elem.text = f"{new_pos[1]:.4f}"
                        z_elem = pos_elem.find("z")
                        if z_elem is None:
                            z_elem = ET.SubElement(pos_elem, "z")
                        z_elem.text = f"{new_pos[2]:.4f}"
                        updated += 1
                if updated > 0:
                    target.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
                    return updated
        except Exception:
            pass

    # If file did not exist or was BXML, generate standard clean XML
    root = ET.Element("client_world")
    infos_elem = ET.SubElement(root, "npc_infos")
    for nid, pos in modified_npcs.items():
        info = ET.SubElement(infos_elem, "npc_info")
        nid_elem = ET.SubElement(info, "nameid")
        nid_elem.text = str(nid)
        pos_elem = ET.SubElement(info, "pos")
        x_elem = ET.SubElement(pos_elem, "x")
        x_elem.text = f"{pos[0]:.4f}"
        y_elem = ET.SubElement(pos_elem, "y")
        y_elem.text = f"{pos[1]:.4f}"
        z_elem = ET.SubElement(pos_elem, "z")
        z_elem.text = f"{pos[2]:.4f}"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    return len(modified_npcs)
