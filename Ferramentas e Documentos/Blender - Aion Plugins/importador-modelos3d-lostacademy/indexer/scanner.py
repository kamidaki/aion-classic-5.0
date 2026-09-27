"""
High-Performance Aion Client Asset Scanner.
Discovers models, NPCs, monsters, characters, weapons, armor, props, vegetation,
skeletons, animations, materials, and textures without loading full meshes into Blender memory.
"""

from __future__ import annotations
import io
import re
import struct
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

try:
    from config.settings import (
        FLAVOR_GAMEFORGE,
        FLAVOR_LIVE_CLASSICO,
        FLAVOR_AION_39,
        FLAVOR_GENERIC,
    )
    from core.client_detector import detect_client_flavor
    from core.pak_engine import AionCatalogIndex, AionPakArchive
except ImportError:
    from ..config.settings import (
        FLAVOR_GAMEFORGE,
        FLAVOR_LIVE_CLASSICO,
        FLAVOR_AION_39,
        FLAVOR_GENERIC,
    )
    from ..core.client_detector import detect_client_flavor
    from ..core.pak_engine import AionCatalogIndex, AionPakArchive

from .asset_entry import AssetEntry
from .dependency_graph import DependencyGraph


RE_WINGS = re.compile(r'(?i)(?:^|[_/.\-\d])wings?(?:[_/.\-\d]|$)')
RE_WEAPONS = re.compile(r'(?i)(?:^|[_/.\-\d])(?:weapon|weapons|sword|shield|bow|dagger|spear|polearm|staff|mace|orb|book|gun|cannon|harp|keyblade|keyhammer|pistol|rifle|2hsword|gladius|greatsword|warhammer|cipherblade)(?:[_/.\-\d]|$)')
RE_WEAPON_PREFIX = re.compile(r'^(?:wp|sw|ts|da|sh|mc|st|or|bk|sp|pa|2h|gun|cn|hp|wh|cb|gt|ds|bw|bo|ma|gu)_', re.I)

RE_ARMOR_KEYWORDS = re.compile(r'(?i)(?:^|[_/.\-\d])(?:torso|body|pants|glove|gloves|foot|feet|boots|shoes|shoulder|shoulders|helm|helmet|robe|cloth|leather|plate|chain|costume|costumes|armor|armors|outfit|dress|swimsuit|uniform|hat|cap|mantle|cloak)(?:[_/.\-\d]|$)')
RE_ARMOR_PREFIX = re.compile(r'^(?:ch|lt|pl|rb|gl|ft|hd|pt)_[a-z0-9]', re.I)
RE_PC_PARTS = re.compile(r'^(?:lf|lm|df|dm)(?:cl|pl|lt|ch|rb|wa|sh|gl|ft|hd)_[a-z0-9]', re.I)

RE_PET_MOUNT = re.compile(r'(?i)(?:^|[_/.\-\d])(?:pet|pets|ride|rides|mount|mounts)(?:[_/.\-\d]|$)')
RE_BUILDING = re.compile(r'(?i)(?:^|[_/.\-\d])(?:building|buildings|structure|structures|fortress|castle|bunker|tower|bridge|house|wall|gate|temple|ruin|ruins|pillar)(?:[_/.\-\d]|$)')
RE_VEGETATION = re.compile(r'(?i)(?:^|[_/.\-\d])(?:vegetation|tree|trees|plant|plants|cliff|rock|rocks|bush|bushes|grass|flower|flowers|mushroom|leaf|leaves|wood|stone)(?:[_/.\-\d]|$)')


def classify_asset_category(rel_path: str) -> str:
    """Classifies an asset into an authoritative category based on directory structure and name."""
    p_norm = rel_path.lower().replace("\\", "/")
    fn = p_norm.split("/")[-1]

    # 1. Wings
    if (RE_WINGS.search(p_norm) or fn.startswith(("dfwing_", "lfwing_", "dmwing_", "lmwing_", "wing_"))) and not any(k in p_norm for k in ("building", "sewing", "drawing", "growing", "wingchair")):
        return "WINGS"

    # 2. Weapons & Shields
    if "/weapon/" in p_norm or "/weapons/" in p_norm or RE_WEAPON_PREFIX.match(fn) or RE_WEAPONS.search(p_norm):
        return "WEAPON"

    # 3. Armor & Costumes & PC equipment
    if ("/armor/" in p_norm or "/costume/" in p_norm or "/cloth/" in p_norm or 
        RE_ARMOR_PREFIX.match(fn) or RE_PC_PARTS.match(fn) or 
        (RE_ARMOR_KEYWORDS.search(fn) and not any(k in p_norm for k in ("/building/", "/prop/")))):
        return "ARMOR"

    # 4. Pets & Mounts
    if RE_PET_MOUNT.search(p_norm):
        return "PET_MOUNT"

    # 5. Monsters
    if "/monster/" in p_norm or "monster" in fn:
        return "MONSTER"

    # 6. NPCs
    if "/npc/" in p_norm or "npc" in fn or fn.startswith(("npc_", "clf", "clm", "caf", "cam")):
        return "NPC"

    # 7. Characters (Base naked meshes, hair, heads)
    if "/pc/" in p_norm or "/character/" in p_norm or fn.startswith(("lf_", "lm_", "df_", "dm_", "lf0", "lm0", "df0", "dm0")):
        return "CHARACTER"

    # 8. World & Environment
    if RE_BUILDING.search(p_norm):
        return "BUILDING"

    if RE_VEGETATION.search(p_norm):
        return "VEGETATION"

    if "/effect/" in p_norm or "/effects/" in p_norm or "/fx/" in p_norm:
        return "EFFECT"

    if "/prop/" in p_norm or "/props/" in p_norm or "furniture" in p_norm:
        return "PROP"

    return "OBJECT"


def inspect_cgf_header_metadata(cgf_bytes: bytes) -> Dict[str, Any]:
    """
    Lightly inspects the chunk table of a CGF without loading vertex arrays.
    Returns: bone_count, vertex_count, triangle_count, material_count, has_skeleton.
    """
    meta = {
        "has_skeleton": False,
        "bone_count": 0,
        "vertex_count": 0,
        "triangle_count": 0,
        "material_count": 0,
    }
    if len(cgf_bytes) < 32:
        return meta

    try:
        stream = io.BytesIO(cgf_bytes)
        # Skip signature null-terminated string
        while True:
            b = stream.read(1)
            if not b or b == b"\x00":
                break
        stream.read(1)  # terminator
        type_of_file = struct.unpack("<I", stream.read(4))[0]
        if type_of_file != 0xFFFF0000:
            return meta

        version = struct.unpack("<I", stream.read(4))[0]
        table_offset = struct.unpack("<I", stream.read(4))[0]

        stream.seek(table_offset)
        num_chunks = struct.unpack("<I", stream.read(4))[0]

        for _ in range(min(num_chunks, 128)):
            raw_type, ver, off, cid = struct.unpack("<IIII", stream.read(16))
            if raw_type == 0xCCCC0005:  # BoneNameList
                meta["has_skeleton"] = True
                curr = stream.tell()
                stream.seek(off)
                meta["bone_count"] = struct.unpack("<I", stream.read(4))[0]
                stream.seek(curr)
            elif raw_type == 0xCCCC0000:  # Mesh
                curr = stream.tell()
                # 16-byte header + 2 bytes bools + 2 bytes reserved = 20 bytes
                stream.seek(off + 20)
                nv, nuv, nf = struct.unpack("<3I", stream.read(12))
                meta["vertex_count"] = max(meta["vertex_count"], nv)
                meta["triangle_count"] = max(meta["triangle_count"], nf)
                stream.seek(curr)
            elif raw_type == 0xCCCC000C:  # Mtl
                meta["material_count"] += 1

    except Exception:
        pass

    return meta


class ClientScanner:
    """Scans an Aion client to discover all models and their dependency relationships."""

    def __init__(self, client_root: str | Path):
        self.root = Path(client_root).resolve()
        self.flavor = detect_client_flavor(self.root)
        self.catalog = AionCatalogIndex(self.root)
        self.dep_graph = DependencyGraph()
        self._cal_cache: Dict[str, Tuple[List[str], Optional[str]]] = {}

    def scan(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        max_assets: Optional[int] = None,
    ) -> Tuple[List[AssetEntry], DependencyGraph]:
        """
        Executes comprehensive client scanning.
        Returns list of AssetEntry items and the populated DependencyGraph.
        """
        self.dep_graph.clear()
        t0 = time.time()

        # 1. Index common PAKs and Category PAKs
        cand_dirs = [
            self.root / "levels" / "common",
            self.root / "Levels" / "common",
            self.root / "objects",
            self.root / "Objects",
            self.root / "data" / "npcs",
            self.root / "Data" / "NPCs",
            self.root / "data" / "items",
            self.root / "Data" / "items",
            self.root / "textures",
            self.root / "Textures",
        ]

        pak_files: List[Path] = []
        for cd in cand_dirs:
            if cd.is_dir():
                for p in cd.rglob("*.pak"):
                    pak_files.append(p)
                    self.catalog.index_pak(p)

        # 2. Extract NPC templates mapping (ID -> Name, Model)
        from ..core.client_provider import AionClientProvider
        client_provider = AionClientProvider(self.root)
        npc_templates = client_provider.get_npc_templates()

        # 3. Discover all CGF / CGA models in the catalog and loose on disk
        model_entries: Dict[str, Tuple[str, Optional[str], bool]] = {}  # norm_lower -> (full_rel, pak_name, is_loose)

        # Catalog entries
        for lower_name, (pak_path, entry) in self.catalog._path_to_pak_entry.items():
            if lower_name.endswith(".cgf") or lower_name.endswith(".cga"):
                try:
                    rel_dir = Path(pak_path).parent.relative_to(self.root).as_posix()
                except ValueError:
                    rel_dir = ""

                clean_entry = entry.name.replace("\\", "/").strip().lstrip("/")
                if rel_dir and not clean_entry.lower().startswith(rel_dir.lower()):
                    full_rel = f"{rel_dir}/{clean_entry}"
                else:
                    full_rel = clean_entry

                norm_key = full_rel.lower()
                if norm_key not in model_entries:
                    model_entries[norm_key] = (full_rel, Path(pak_path).name, False)

        # Loose files
        for obj_dir_name in ("objects", "Objects"):
            obj_p = self.root / obj_dir_name
            if obj_p.is_dir():
                for f in obj_p.rglob("*.cgf"):
                    rel = f.relative_to(self.root).as_posix()
                    norm_key = rel.lower()
                    if norm_key not in model_entries:
                        model_entries[norm_key] = (rel, None, True)

        total_models = len(model_entries)
        assets: List[AssetEntry] = []
        scanned_count = 0

        def _model_priority(item):
            rel_lower = item[0].lower()
            if "/npc/" in rel_lower or "npc" in rel_lower:
                return (0, rel_lower)
            if "/monster/" in rel_lower or "monster" in rel_lower:
                return (1, rel_lower)
            if "/pc/" in rel_lower or "/character/" in rel_lower:
                return (2, rel_lower)
            if "/weapon/" in rel_lower or "/shield/" in rel_lower:
                return (3, rel_lower)
            if "/armor/" in rel_lower or "/item/" in rel_lower:
                return (4, rel_lower)
            return (5, rel_lower)

        sorted_models = sorted(model_entries.values(), key=_model_priority)
        if max_assets:
            sorted_models = sorted_models[:max_assets]

        for rel_path, pak_name, is_loose in sorted_models:
            scanned_count += 1
            if progress_callback and scanned_count % 100 == 0:
                progress_callback(scanned_count, total_models, rel_path)

            clean_rel = rel_path.replace("\\", "/").strip().lstrip("/")
            base_name = Path(clean_rel).stem
            category = classify_asset_category(clean_rel)

            # Match with NPC template if available
            npc_match = npc_templates.get(clean_rel.lower()) or npc_templates.get(base_name.lower())
            if npc_match:
                asset_id = str(npc_match["id"])
                asset_name = npc_match["name"]
            else:
                asset_id = f"item_{base_name.lower()}"
                asset_name = base_name.replace("_", " ").title()

            # Find matching .cal animation list
            cal_path = self._find_matching_cal(clean_rel)
            animations: List[str] = []
            idle_anim: Optional[str] = None

            if cal_path:
                animations, idle_anim = self._inspect_cal(cal_path)

            # Read lightweight chunk metadata from CGF (optimized: only for characters/creatures/rigged models)
            header_meta = {}
            if cal_path or category in {"NPC", "MONSTER", "CHARACTER", "WINGS", "PET_MOUNT", "WEAPON", "ARMOR"}:
                cgf_bytes = self.catalog.extract_file(clean_rel)
                if not cgf_bytes and is_loose:
                    loose_f = self.root / clean_rel
                    if loose_f.is_file():
                        cgf_bytes = loose_f.read_bytes()
                if cgf_bytes:
                    header_meta = inspect_cgf_header_metadata(cgf_bytes)

            entry = AssetEntry(
                asset_id=asset_id,
                name=asset_name,
                category=category,
                model_path=clean_rel,
                client_flavor=self.flavor,
                source_pak=pak_name,
                is_loose=is_loose,
                has_skeleton=header_meta.get("has_skeleton", bool(animations)),
                bone_count=header_meta.get("bone_count", 0),
                skeleton_path=clean_rel if header_meta.get("has_skeleton") else None,
                cal_path=cal_path,
                idle_animation=idle_anim,
                animations=animations,
                animation_count=len(animations),
                vertex_count=header_meta.get("vertex_count", 0),
                triangle_count=header_meta.get("triangle_count", 0),
                file_size=len(cgf_bytes) if cgf_bytes else 0,
            )

            self._register_dependencies(entry)
            assets.append(entry)

        return assets, self.dep_graph

    def scan_all(self, max_assets: Optional[int] = None) -> List[AssetEntry]:
        """Convenience method returning just the list of scanned AssetEntry objects."""
        return self.scan(max_assets=max_assets)[0]

    def _find_matching_cal(self, cgf_rel: str) -> Optional[str]:
        """Finds the corresponding .cal file for a model path."""
        p = Path(cgf_rel)
        parent = p.parent.as_posix()
        stem = p.stem

        cands = [
            f"{parent}/{stem}.cal",
            f"{stem}.cal",
            f"{parent}/{stem.split('_')[0]}.cal",
        ]
        # Fast path: check catalog first
        for c in cands:
            entry = self.catalog.find_file(c)
            if entry:
                return entry[1].name

        # Fallback: check loose files
        for c in cands:
            loose = self.root / c
            if loose.is_file():
                return c
        return None

    def _inspect_cal(self, cal_rel: str) -> Tuple[List[str], Optional[str]]:
        """Parses state names and default idle animation from a CAL file (cached)."""
        clean_key = cal_rel.lower()
        if clean_key in self._cal_cache:
            return self._cal_cache[clean_key]

        try:
            from formats.cgf.cal_parser import parse_cal, find_default_idle_animation
        except ImportError:
            from ..formats.cgf.cal_parser import parse_cal, find_default_idle_animation

        data = self.catalog.extract_file(cal_rel)
        if not data:
            loose = self.root / cal_rel
            if loose.is_file():
                data = loose.read_bytes()

        if not data:
            self._cal_cache[clean_key] = ([], None)
            return [], None

        cal_map = parse_cal(data)
        states = list(cal_map.keys())
        idle = find_default_idle_animation(cal_map)
        res = (states, idle)
        self._cal_cache[clean_key] = res
        return res

    def _load_npc_templates(self) -> Dict[str, Dict[str, str]]:
        """Loads NPC names and mesh references from client_npcs.xml or client_npcs.bxml."""
        results: Dict[str, Dict[str, str]] = {}
        for pak_path, arc in self.catalog._archives.items():
            for name in arc.entries.keys():
                if "client_npc" in name.lower() and (name.endswith(".xml") or name.endswith(".bxml")):
                    raw_bytes = arc.read_file(name)
                    if raw_bytes:
                        self._parse_npc_xml_chunk(raw_bytes, results)
        return results

    def _parse_npc_xml_chunk(self, raw_bytes: bytes, out_dict: Dict[str, Dict[str, str]]) -> None:
        """Extracts (id, name, mesh) tuples from XML/BXML bytes."""
        text = raw_bytes.decode("utf-16le", errors="ignore")
        if "<npc_client" not in text:
            text = raw_bytes.decode("latin-1", errors="ignore")

        # Regex for id, name, mesh
        for match in re.finditer(r'<npc_client[^>]*id="(\d+)"[^>]*name="([^"]+)"[^>]*mesh="([^"]+)"', text):
            nid, name, mesh = match.groups()
            clean_mesh = mesh.replace("\\", "/").strip().lower()
            mesh_stem = Path(clean_mesh).stem.lower()
            item = {"id": nid, "name": name, "mesh": mesh}
            out_dict[clean_mesh] = item
            out_dict[mesh_stem] = item

    def _register_dependencies(self, entry: AssetEntry) -> None:
        """Links asset nodes in the dependency graph."""
        # Asset -> Model
        self.dep_graph.add_dependency(entry.asset_id, entry.model_path)
        # Model -> Skeleton
        if entry.skeleton_path:
            self.dep_graph.add_dependency(entry.model_path, entry.skeleton_path)
        # Model -> CAL
        if entry.cal_path:
            self.dep_graph.add_dependency(entry.model_path, entry.cal_path)
            # CAL -> Idle CAF
            if entry.idle_animation:
                self.dep_graph.add_dependency(entry.cal_path, entry.idle_animation)


Scanner = ClientScanner
