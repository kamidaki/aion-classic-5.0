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
    walker_id: str = ""


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
    desc_key: str = ""
    title_key: str = ""
    walk_speed: float = 2.2


@dataclass(frozen=True)
class WalkerStep:
    """Single waypoint step along an NPC walker patrol route."""
    x: float
    y: float
    z: float
    rest_time: int = 0


@dataclass(frozen=True)
class WalkerRoute:
    """Authoritative patrol route parsed from emulator npc_walker.xml."""
    route_id: str
    steps: Tuple[WalkerStep, ...]
    loop: bool = True


# Fallback archetype models using verified Aion Classic PC/NPC PAK paths
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
    re_walk_speed = re.compile(r"<move_speed_normal_walk>([^<]+)</move_speed_normal_walk>")
    re_scale = re.compile(r"<scale>([^<]+)</scale>")

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
            desc_raw = m_desc.group(1).strip() if m_desc else ""
            desc_key = desc_raw if desc_raw.upper().startswith("STR_") and desc_raw.upper() != "STR_NPC_NO_NAME" else ""

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
                if "LIGHT_M" in pc_type or pc_type.startswith("LM"):
                    cgf = DEFAULT_HUMANOID_MODELS.get("LM", "")
                elif "LIGHT_F" in pc_type or pc_type.startswith("LF"):
                    cgf = DEFAULT_HUMANOID_MODELS.get("LF", "")
                elif "DARK_M" in pc_type or pc_type.startswith("DM"):
                    cgf = DEFAULT_HUMANOID_MODELS.get("DM", "")
                elif "DARK_F" in pc_type or pc_type.startswith("DF"):
                    cgf = DEFAULT_HUMANOID_MODELS.get("DF", "")

            m_anim = re_anim.search(b)
            idle_anim = m_anim.group(1).strip() if m_anim else ""

            m_race = re_race.search(b)
            race = m_race.group(1).strip() if m_race else ""

            walk_speed = 2.2
            m_ws = re_walk_speed.search(b)
            if m_ws:
                try:
                    ws = float(m_ws.group(1))
                    if 0.4 <= ws <= 15.0:
                        walk_speed = ws
                except ValueError:
                    pass

            scale_val = 1.0
            m_sc = re_scale.search(b)
            if m_sc:
                try:
                    sv = float(m_sc.group(1))
                    if sv > 10.0:
                        sv = sv / 100.0
                    if 0.3 <= sv <= 4.0:
                        scale_val = sv
                except ValueError:
                    pass

            is_monster = (
                (nid.startswith("2") and len(nid) == 6 and int(nid) >= 210000)
                or "monster" in b.lower()
                or "mat_mob" in b.lower()
            )
            category = "monster" if is_monster else "npc"

            templates[nid] = NpcTemplate(
                id=nid,
                name=name,
                title="" if desc_raw.upper().startswith("STR_") else desc_raw,
                cgf_reference=cgf,
                scale=scale_val,
                category=category,
                race=race,
                idle_animation=idle_anim,
                desc_key=desc_key or (name if name.upper().startswith("STR_") else ""),
                title_key="",
                walk_speed=walk_speed,
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
    _pc_prefix_map = ("LM", "LF", "DM", "DF")
    _non_mesh_words = (
        "idle", "guard", "sale", "misc", "teleport", "airlines",
        "searcher", "looting", "im_", "lf1_", "df1_", "mat_", "foot_",
        "erect", "general", "none", "bip01", "skill", "summon",
    )

    while i < num_tokens:
        tok = tokens[i]
        # In Aion BXML, each template begins with a 6-digit ID (starting with 2, 7, or 8)
        if tok.isdigit() and len(tok) == 6 and tok[0] in ("2", "7", "8"):
            nid = tok
            name = tokens[i + 1] if i + 1 < num_tokens and not tokens[i + 1].isdigit() else f"NPC_{nid}"
            cgf_ref = ""
            race = ""
            idle_anim = ""
            desc_key = ""
            title_key = ""
            category = "monster" if (nid[0] == "2" and int(nid) >= 210000) else "npc"

            j = i + 1
            while j < min(num_tokens, i + 35):
                sub = tokens[j]
                if sub.isdigit() and len(sub) == 6 and sub[0] in ("2", "7", "8"):
                    break
                sub_up = sub.upper()
                sub_low = sub.lower()

                if sub_up.startswith("STR_NPCTITLE_"):
                    if not title_key:
                        title_key = sub
                elif sub_up.startswith("STR_") and sub_up != "STR_NPC_NO_NAME":
                    if not desc_key:
                        desc_key = sub
                elif "/" in sub and not cgf_ref:
                    if j + 1 < num_tokens and not tokens[j + 1].isdigit() and "/" not in tokens[j + 1]:
                        cgf_ref = f"{sub}/{tokens[j + 1]}.cgf"
                    elif sub_low.endswith(".cgf"):
                        cgf_ref = sub
                elif "shugomale" in sub_low or "shugo_m" in sub_low:
                    race = "SHUGO_M"
                elif "shugofemale" in sub_low or "shugo_f" in sub_low:
                    race = "SHUGO_F"
                elif any(sub_up.startswith(p) and (len(sub) == 2 or any(k in sub_low for k in ("normal", "slim", "small", "fat", "muscle"))) for p in _pc_prefix_map):
                    race = sub_up[:2]

                if "idle" in sub_low and not idle_anim:
                    idle_anim = sub
                if sub_up in ("DM", "DF", "LM", "LF", "SHUGO_M", "SHUGO_F"):
                    race = sub_up
                if "monster" in sub_low:
                    category = "monster"
                elif any(amb in sub_low for amb in ("critter", "bird", "squirrel", "rabbit", "butterfly", "frog", "fish")) and category != "monster":
                    category = "ambient"
                j += 1

            if not cgf_ref:
                if race and race in DEFAULT_HUMANOID_MODELS:
                    cgf_ref = DEFAULT_HUMANOID_MODELS[race]
                elif category != "monster" and any(t in name.lower() for t in ("shugo",)):
                    cgf_ref = DEFAULT_HUMANOID_MODELS.get("SHUGO_M", "")
                elif nid[0] in ("7", "8") and category == "npc" and desc_key.upper().startswith("STR_NPC_"):
                    cgf_ref = DEFAULT_HUMANOID_MODELS.get("LM", "")

            if not desc_key:
                desc_key = f"STR_NPC_{name}" if category == "npc" else f"STR_{name}"

            templates[nid] = NpcTemplate(
                id=nid,
                name=name,
                title="",
                cgf_reference=cgf_ref,
                scale=1.0,
                category=category,
                race=race,
                idle_animation=idle_anim,
                desc_key=desc_key,
                title_key=title_key,
                walk_speed=2.2,
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


def find_emulator_static_data_dir(
    explicit_dir: str | Path | None = None,
    client_root: str | Path | None = None,
) -> Optional[Path]:
    """
    Locates the Aion Classic emulator `data/static_data` directory cleanly without
    hardcoded user-specific paths.
    """
    candidates: List[Path] = []
    if explicit_dir:
        p = Path(explicit_dir)
        candidates.extend([p, p / "data" / "static_data", p / "static_data"])

    rel_suffixes = (
        Path("Código Fonte - Emulador") / "game-server-gameforge" / "data" / "static_data",
        Path("game-server-gameforge") / "data" / "static_data",
        Path("Emulador - Produto Final") / "GameServer" / "data" / "static_data",
        Path("data") / "static_data",
    )

    search_roots: List[Path] = [Path(__file__).resolve()]
    if client_root:
        search_roots.append(Path(client_root).resolve())

    for root in search_roots:
        for parent in (root, *root.parents):
            for suffix in rel_suffixes:
                cand = parent / suffix
                if cand not in candidates:
                    candidates.append(cand)

    for cand in candidates:
        try:
            if cand.is_dir() and (cand / "world_maps.xml").is_file():
                return cand
        except OSError:
            continue
    return None


def resolve_world_id_for_map(static_data_dir: str | Path, map_name: str) -> Optional[str]:
    """Resolves numeric world map ID (e.g. '210010000' for 'lf1') from world_maps.xml."""
    static_data_dir = Path(static_data_dir)
    wm_path = static_data_dir / "world_maps.xml"
    if not wm_path.is_file():
        return None
    target = map_name.strip().lower()
    if not target:
        return None
    try:
        root = ET.fromstring(wm_path.read_text(encoding="utf-8", errors="ignore"))
        for elem in root.iter("map"):
            cname = str(elem.attrib.get("cName") or "").strip().lower()
            if cname == target:
                wid = str(elem.attrib.get("id") or "").strip()
                if wid:
                    return wid
    except Exception:
        pass
    return None


def parse_emulator_map_spawns(static_data_dir: str | Path, map_name: str) -> List[NpcSpawn]:
    """
    Parses emulator `spawns/Npcs/**/<world_id>_*.xml` to obtain exact spawns, headings
    and `walker_id` routes for a map (preferring `New/` definitions when present).
    """
    static_data_dir = Path(static_data_dir)
    world_id = resolve_world_id_for_map(static_data_dir, map_name)
    if not world_id:
        return []
    spawns_dir = static_data_dir / "spawns" / "Npcs"
    if not spawns_dir.is_dir():
        return []

    xml_files = sorted(spawns_dir.rglob(f"{world_id}*.xml"))
    if not xml_files:
        return []

    # Prefer `New/` folder files first so updated spawn spots take precedence over legacy duplicates
    xml_files.sort(key=lambda p: (0 if "new" in {part.lower() for part in p.parts} else 1, str(p).lower()))

    spawns: List[NpcSpawn] = []
    seen_keys = set()
    for xf in xml_files:
        try:
            root = ET.fromstring(xf.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for sp_elem in root.iter("spawn"):
            npc_id = str(sp_elem.attrib.get("npc_id") or "").strip()
            if not npc_id:
                continue
            for spot in sp_elem.findall("spot"):
                try:
                    x = float(spot.attrib.get("x", "0"))
                    y = float(spot.attrib.get("y", "0"))
                    z_raw = spot.attrib.get("z")
                    z = float(z_raw) if z_raw is not None else 0.0
                    h_raw = float(spot.attrib.get("h", "0") or 0.0)
                    heading_deg = (h_raw * 3.0) % 360.0
                    walker_id = str(spot.attrib.get("walker_id") or "").strip()
                    key = (npc_id, round(x, 1), round(y, 1), round(z, 1))
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    spawns.append(
                        NpcSpawn(
                            npc_id=npc_id,
                            position=(x, y, z),
                            heading_degrees=heading_deg,
                            has_explicit_z=(z_raw is not None and abs(z) > 1e-4),
                            raw_coords=(x, y, z, h_raw),
                            source="emulator_spawns_xml",
                            walker_id=walker_id,
                        )
                    )
                except (ValueError, TypeError):
                    continue
    return spawns


def parse_walker_routes(
    static_data_dir: str | Path,
    needed_route_ids: Optional[set[str]] = None,
) -> Dict[str, WalkerRoute]:
    """
    Streams `npc_walker/npc_walker.xml` and `npc_walker/custom_npc_walker.xml` via `iterparse`,
    returning structured `WalkerRoute` objects for `needed_route_ids`.
    """
    static_data_dir = Path(static_data_dir)
    routes: Dict[str, WalkerRoute] = {}
    if needed_route_ids is not None and len(needed_route_ids) == 0:
        return routes

    walker_dir = static_data_dir / "npc_walker"
    if not walker_dir.is_dir():
        return routes

    for fname in ("npc_walker.xml", "custom_npc_walker.xml"):
        wf = walker_dir / fname
        if not wf.is_file():
            continue
        try:
            for event, elem in ET.iterparse(wf, events=("end",)):
                if elem.tag != "walker_template":
                    continue
                rid = str(elem.attrib.get("route_id") or "").strip()
                if rid and (needed_route_ids is None or rid in needed_route_ids):
                    loop = str(elem.attrib.get("loop", "true")).strip().lower() != "false"
                    steps: List[WalkerStep] = []
                    for step in elem.findall("routestep"):
                        try:
                            steps.append(
                                WalkerStep(
                                    x=float(step.attrib.get("x", "0")),
                                    y=float(step.attrib.get("y", "0")),
                                    z=float(step.attrib.get("z", "0")),
                                    rest_time=int(float(step.attrib.get("rest_time", "0") or 0)),
                                )
                            )
                        except (ValueError, TypeError):
                            continue
                    if len(steps) >= 2:
                        routes[rid] = WalkerRoute(route_id=rid, steps=tuple(steps), loop=loop)
                elem.clear()
                if needed_route_ids is not None and len(routes) >= len(needed_route_ids) and fname == "npc_walker.xml":
                    # Still scan custom_npc_walker if overrides might exist
                    break
        except Exception:
            continue
    return routes
