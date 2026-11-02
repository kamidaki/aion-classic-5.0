"""
Aion Multi-Client Dynamic Provider & Detection Layer.
Supports:
- Client 1: Classic 5.0 (GameForge EU / Classic)
- Client 2: Retail 4.8 (Aion Live Clássico América do Sul / LostAcademy)
- Client 3: Retail 4.6 (OriginAion)
- Client 4: Retail 7.7 (Lab Aion 7.7)
- Generic CryEngine / Aion clients
"""

from __future__ import annotations

import enum
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .pak_engine import AionCatalogIndex, AionPakArchive


class ClientFlavor(enum.Enum):
    CLASSIC_50 = "Classic 5.0 (GameForge)"
    RETAIL_48 = "Retail 4.8 (Live Clássico América do Sul)"
    RETAIL_46 = "Retail 4.6 (OriginAion)"
    RETAIL_77 = "Retail 7.7 (Lab Aion)"
    GENERIC = "Generic Aion Client"

    # Backward compatibility aliases
    GAMEFORGE_CLASSIC = "Classic 5.0 (GameForge)"
    LIVE_CLASSICO_SA = "Retail 4.8 (Live Clássico América do Sul)"
    AION_39_LEGACY = "Retail 4.6 (OriginAion)"


class AionClientProvider:
    """
    Unified client abstraction layer providing version-independent access to:
    - PAK catalogs and resource resolution
    - Levels and maps discovery
    - NPC world spawns (XML and BXML)
    - NPC archetype templates and metadata
    - Localized string resolution (client_strings_*.xml)
    - Meshes, Skeletons, and Animations (.cal, .caf)
    """

    def __init__(self, client_root: str | Path):
        self.root = Path(client_root).resolve()
        self.flavor = self._detect_flavor()

        self.levels_dir = self._resolve_subpath("levels", "Levels")
        self.data_dir = self._resolve_subpath("data", "Data")
        self.objects_dir = self._resolve_subpath("objects", "Objects")
        self.textures_dir = self._resolve_subpath("textures", "Textures")
        self.shaders_dir = self._resolve_subpath("shaders", "Shaders")
        self.l10n_dir = self._resolve_subpath("l10n", "L10N")

        self.catalog = AionCatalogIndex(self.root)
        self._catalog_initialized: bool = False

        # Cache of parsed templates, world spawns, and localization strings
        self._templates_cache: Optional[Dict[str, Any]] = None
        self._world_spawns_cache: Dict[str, List[Any]] = {}
        self._string_tables: Dict[str, str] = {}
        self._string_tables_loaded: bool = False

    def _ensure_catalog_initialized(self) -> None:
        """Indexes common PAKs across client structure lazily on first access."""
        if self._catalog_initialized:
            return
        self._init_catalog()
        self._catalog_initialized = True

    def ensure_catalog(self) -> None:
        """Public alias to guarantee catalog index is ready."""
        self._ensure_catalog_initialized()

    def _resolve_subpath(self, *candidates: str) -> Optional[Path]:
        for c in candidates:
            p = self.root / c
            if p.is_dir():
                return p
        return None

    def _detect_flavor(self) -> ClientFlavor:
        """
        Detects client flavor using robust evidence from internal files,
        binary headers, system configs, and directory structures.
        """
        b64 = self.root / "bin64" / "aion.bin"
        b32 = self.root / "bin32" / "aion.bin"

        has_lostacademy = (
            (self.root / "LostAcademy").is_dir()
            or (self.root / "Data" / "NPCs" / "Npcs_LostAcademy.pak").is_file()
            or (self.root / "data" / "npcs" / "Npcs_LostAcademy.pak").is_file()
        )

        # 1. Retail 7.7: Only 64-bit client (~5.8MB aion.bin), server.bat, or 200+ maps with 7.x event maps
        if (self.root / "server.bat").is_file() or (
            b64.is_file() and not b32.is_file() and b64.stat().st_size > 5_000_000
        ):
            return ClientFlavor.RETAIL_77

        # 2. Retail 4.8: LostAcademy distribution or custom NPC tables
        if has_lostacademy:
            return ClientFlavor.RETAIL_48

        # 3. Retail 4.6 (OriginAion): 32-bit (~3.0MB) and 64-bit (~615KB) with heavy Objects PAKs
        if (
            b32.is_file()
            and b32.stat().st_size < 3_500_000
            and (
                (self.root / "Objects").is_dir()
                and len(list((self.root / "Objects").glob("*.pak"))) > 20
                or (self.root / "SystemOptionGraphics.cfg").is_file()
            )
        ):
            return ClientFlavor.RETAIL_46

        # 4. Classic 5.0 (GameForge): 32-bit (~4.2MB) and 64-bit (~6.2MB), gficon.ico, cc.ini
        if (
            (self.root / "gficon.ico").is_file()
            or (self.root / "aiongraopdeck.dat").is_file()
            or (
                b64.is_file()
                and b64.stat().st_size > 6_000_000
                and b32.is_file()
                and b32.stat().st_size > 4_000_000
            )
        ):
            return ClientFlavor.CLASSIC_50

        # Secondary fallback heuristics based on path string if files were moved
        root_str = str(self.root).lower()
        if "7.7" in root_str or "retail 7" in root_str:
            return ClientFlavor.RETAIL_77
        if "live cl" in root_str or "am" in root_str or "lostacademy" in root_str:
            return ClientFlavor.RETAIL_48
        if "originaion" in root_str or "4.6" in root_str:
            return ClientFlavor.RETAIL_46
        if "gameforge" in root_str or "aionclassic" in root_str:
            return ClientFlavor.CLASSIC_50

        return ClientFlavor.GENERIC

    def _init_catalog(self) -> None:
        """Indexes common PAKs across the detected client structure."""
        # 1. Shaders
        if self.shaders_dir and self.shaders_dir.is_dir():
            for p in self.shaders_dir.glob("*.pak"):
                self.catalog.index_pak(p)

        # 2. Levels common
        if self.levels_dir and self.levels_dir.is_dir():
            common_p = self.levels_dir / "common"
            if common_p.is_dir():
                for p in common_p.glob("*.pak"):
                    self.catalog.index_pak(p)

        # 3. Textures
        if self.textures_dir and self.textures_dir.is_dir():
            for p in self.textures_dir.glob("*.pak"):
                self.catalog.index_pak(p)

        # 4. L10N Textures and common data
        if self.l10n_dir and self.l10n_dir.is_dir():
            for lang_dir in self.l10n_dir.iterdir():
                if lang_dir.is_dir():
                    for pak in lang_dir.glob("*.pak"):
                        self.catalog.index_pak(pak)

    def get_world_pak_path(self) -> Optional[Path]:
        """Resolves the authoritative world.pak file path."""
        if not self.data_dir:
            return None
        world_dirs = [self.data_dir / "world", self.data_dir / "World"]
        for wd in world_dirs:
            if wd.is_dir():
                for p in wd.glob("*.pak"):
                    if "world" in p.name.lower():
                        return p
        return None

    def get_npcs_pak_paths(self) -> List[Path]:
        """Resolves all authoritative NPC PAK file paths."""
        if not self.data_dir:
            return []
        npc_dirs = [
            self.data_dir / "npcs",
            self.data_dir / "NPCs",
            self.data_dir / "npc",
            self.data_dir / "Npc",
        ]
        paks: List[Path] = []
        for nd in npc_dirs:
            if nd.is_dir():
                for p in nd.glob("*.pak"):
                    paks.append(p)
        return paks

    @property
    def is_encrypted(self) -> bool:
        """True if the client or its World.pak is protected with proprietary encryption (e.g. OriginAion OADTENC1)."""
        wp = self.get_world_pak_path()
        if wp and wp.is_file():
            try:
                with open(wp, "rb") as f:
                    if f.read(8) == b"OADTENC1":
                        return True
            except Exception:
                pass
        return self.flavor == ClientFlavor.RETAIL_46

    @property
    def encryption_scheme(self) -> str:
        return "OADTENC1" if self.is_encrypted else "NONE"

    def get_available_maps(self) -> List[str]:
        """Discovers all valid map names in the client levels directory."""
        if not self.levels_dir or not self.levels_dir.is_dir():
            return []
        maps = []
        for d in self.levels_dir.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                if (
                    (d / "Level.pak").is_file()
                    or (d / ".aion_cache").is_dir()
                    or (d / "terrain").is_dir()
                ):
                    maps.append(d.name)
        return sorted(maps)

    def read_world_spawns_data(self, map_name: str) -> Optional[bytes]:
        """Reads client_world_<map>.xml or .bxml bytes from World.pak or local map dir."""
        self._ensure_catalog_initialized()
        clean_map = map_name.strip().lower()

        # 1. Check world.pak
        wp = self.get_world_pak_path()
        if wp and wp.is_file():
            # Check for OriginAion OADTENC1 signature
            try:
                head = wp.read_bytes()[:8]
                if head == b"OADTENC1":
                    print(
                        f"[AionClientProvider] Warning: {wp.name} is protected with OriginAion OADTENC1 encryption."
                    )
                    return None
            except Exception:
                pass

            try:
                arc = self.catalog.get_archive(wp)
                for cand in (f"client_world_{clean_map}.xml", f"client_world_{clean_map}.bxml"):
                    data = arc.read_file(cand)
                    if data:
                        return data
            except Exception as exc:
                print(f"[AionClientProvider] Error reading world.pak: {exc}")

        # 2. Check local level directory
        if self.levels_dir:
            local_map = self.levels_dir / clean_map
            for cand in (f"client_world_{clean_map}.xml", f"client_world_{clean_map}.bxml"):
                lp = local_map / cand
                if lp.is_file():
                    return lp.read_bytes()

        return None

    def read_npc_templates_data(self) -> List[Tuple[str, bytes]]:
        """Reads NPC archetype templates XML/BXML data from available NPC PAK archives."""
        self._ensure_catalog_initialized()
        paks = self.get_npcs_pak_paths()
        results: List[Tuple[str, bytes]] = []

        for pak_path in paks:
            # Check for OriginAion OADTENC1 signature
            try:
                head = pak_path.read_bytes()[:8]
                if head == b"OADTENC1":
                    print(
                        f"[AionClientProvider] Skipping {pak_path.name}: OriginAion OADTENC1 encrypted."
                    )
                    continue
            except Exception:
                pass

            try:
                arc = self.catalog.get_archive(pak_path)
                for name in arc.entries.keys():
                    if "client_npc" in name and (name.endswith(".xml") or name.endswith(".bxml")):
                        data = arc.read_file(name)
                        if data:
                            results.append((name, data))
            except Exception as exc:
                print(f"[AionClientProvider] Error reading NPC PAK {pak_path.name}: {exc}")

        return results

    def load_string_tables(self, preferred_lang: str = "ENG") -> int:
        """
        Loads localization strings (client_strings_npc.xml, client_strings_monster.xml)
        from L10N/<LANG>/data/data.pak or Data/Strings/Strings.pak.
        Populates _string_tables mapping string keys/IDs to localized display names.
        """
        if self._string_tables_loaded:
            return len(self._string_tables)

        self._string_tables.clear()

        # Candidate archives in order of preference
        cand_paks: List[Path] = []

        # 1. L10N folder (e.g. l10n/ENG/data/data.pak or L10N/ENG/Data/data.pak)
        if self.l10n_dir and self.l10n_dir.is_dir():
            for lang in (preferred_lang, "ENG", "BRA", "DEU", "FRA"):
                for sub in (
                    self.l10n_dir / lang / "data" / "data.pak",
                    self.l10n_dir / lang / "Data" / "data.pak",
                    self.l10n_dir / lang / f"{lang}.pak",
                ):
                    if sub.is_file() and sub not in cand_paks:
                        cand_paks.append(sub)

        # 2. Data/Strings/Strings.pak
        if self.data_dir and self.data_dir.is_dir():
            for sp in (
                self.data_dir / "Strings" / "Strings.pak",
                self.data_dir / "strings" / "strings.pak",
            ):
                if sp.is_file() and sp not in cand_paks:
                    cand_paks.append(sp)

        # Parse string tables
        for pak_path in cand_paks:
            try:
                arc = self.catalog.get_archive(pak_path)
                for entry_name in list(arc.entries.keys()):
                    entry_lower = entry_name.lower()
                    if "client_strings_npc" in entry_lower or "client_strings_monster" in entry_lower:
                        raw = arc.read_file(entry_name)
                        if raw:
                            self._parse_string_xml(raw)
            except Exception as exc:
                print(f"[AionClientProvider] Warning reading strings from {pak_path}: {exc}")

        self._string_tables_loaded = True
        return len(self._string_tables)

    def _parse_string_xml(self, raw: bytes) -> None:
        """Parses standard XML or BXML string entries into _string_tables."""
        # 1. Check if standard XML
        if b"<?xml" in raw[:60].lower() or raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            try:
                text = (
                    raw.decode("utf-16", errors="replace")
                    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"utf-16" in raw[:60].lower()
                    else raw.decode("utf-8", errors="replace")
                )
                re_entry = re.compile(
                    r"<string>\s*<id>([^<]+)</id>\s*<name>([^<]+)</name>\s*<body>([^<]*)</body>",
                    re.DOTALL,
                )
                for m in re_entry.finditer(text):
                    s_id = m.group(1).strip()
                    s_name = m.group(2).strip()
                    s_body = m.group(3).strip()
                    if s_body:
                        self._string_tables[s_id] = s_body
                        self._string_tables[s_name] = s_body
                return
            except Exception:
                pass

        # 2. Parse CryEngine BXML string stream
        pos = -1
        for target in ("strings".encode("utf-16le"), "string".encode("utf-16le")):
            found = raw.find(target)
            if found != -1:
                pos = found
                break

        if pos != -1:
            tokens = [
                t.strip()
                for t in raw[pos:].decode("utf-16le", errors="ignore").split("\x00")
                if t.strip()
            ]
            i = 0
            n = len(tokens)
            while i < n - 3:
                tok = tokens[i]
                if tok.isdigit() and len(tok) >= 5:
                    s_id = tok
                    s_name = tokens[i + 1] if (i + 1 < n and not tokens[i + 1].isdigit()) else ""
                    # Next token might be 'body' or the actual body value
                    j = i + 2
                    if j < n and tokens[j].lower() == "body":
                        j += 1
                    s_body = tokens[j] if (j < n and not tokens[j].isdigit()) else ""
                    if s_body:
                        self._string_tables[s_id] = s_body
                        if s_name:
                            self._string_tables[s_name] = s_body
                    i = j
                i += 1

    def resolve_localized_string(self, key_or_id: str | int) -> str:
        """Looks up a localized display string by ID or STR_* key."""
        if not self._string_tables_loaded:
            self.load_string_tables()
        k = str(key_or_id).strip()
        return self._string_tables.get(k, k)

    def ensure_category_paks_indexed(self, relative_path: str) -> None:
        """Dynamically indexes candidate PAK files relevant to the resource directory."""
        clean_path = relative_path.replace("\\", "/").strip().lstrip("/")
        parent_dir = Path(clean_path).parent

        cand_dirs = [
            self.root / parent_dir,
            self.root / "objects" / parent_dir,
            self.root / "Objects" / parent_dir,
        ]

        clean_lower = clean_path.lower()
        if "monster" in clean_lower:
            cand_dirs.extend([
                self.root / "objects" / "monster",
                self.root / "Objects" / "monster",
            ])
        if (
            "level_object" in clean_lower
            or "npc" in clean_lower
            or "human" in clean_lower
            or "cam" in clean_lower
            or "caf" in clean_lower
            or "cem" in clean_lower
            or "cff" in clean_lower
            or "shugo" in clean_lower
        ):
            cand_dirs.extend([
                self.root / "objects" / "npc" / "level_object",
                self.root / "Objects" / "npc" / "level_object",
                self.root / "objects" / "npc" / "human",
                self.root / "Objects" / "npc" / "human",
                self.root / "objects" / "npc",
                self.root / "Objects" / "npc",
            ])

        for cd in cand_dirs:
            if cd.is_dir():
                for p in cd.glob("*.pak"):
                    self.catalog.index_pak(p)

    def resolve_cgf_bytes(
        self, cgf_relative_path: str, target_lod: int = 0
    ) -> Optional[bytes]:
        """
        Resolves and extracts CGF model bytes dynamically.
        Supports LOD companion files (<stem>_lod<N>.cgf) when target_lod > 0.
        """
        if not cgf_relative_path:
            return None
        self.ensure_category_paks_indexed(cgf_relative_path)
        clean_path = cgf_relative_path.replace("\\", "/").strip().lstrip("/")

        # Check for LOD companion if requested
        if target_lod > 0 and clean_path.endswith(".cgf"):
            stem = clean_path[:-4]
            for lod_lvl in range(target_lod, 0, -1):
                lod_cand = f"{stem}_lod{lod_lvl}.cgf"
                b = self.catalog.extract_file(lod_cand)
                if not b:
                    b = self.catalog.extract_file(Path(lod_cand).name)
                if b:
                    return b

        # Base CGF
        b = self.catalog.extract_file(clean_path)
        if not b:
            b = self.catalog.extract_file(Path(clean_path).name)
        return b

    def resolve_animation_asset(
        self, cgf_relative_path: str
    ) -> Tuple[Optional[Dict[str, str]], Optional[bytes]]:
        """
        Given a character model path (e.g. 'objects/npc/shugomale/shugomale.cgf' or 'Monster/brax/brax.cgf'):
        1. Finds and parses the corresponding .cal file
        2. Resolves and extracts the idle .caf animation bytes
        Returns (cal_mapping, caf_bytes) or (None, None).
        """
        from formats.cgf.cal_parser import find_default_idle_animation, parse_cal

        if not cgf_relative_path:
            return None, None

        self.ensure_category_paks_indexed(cgf_relative_path)

        clean_path = cgf_relative_path.replace("\\", "/").strip().lstrip("/")
        base_name = Path(clean_path).stem
        parent_dir = Path(clean_path).parent

        cal_bytes: Optional[bytes] = None

        # 1. Try reading .cal directly via catalog
        cal_cands = [
            f"{parent_dir}/{base_name}.cal",
            f"{clean_path[:-4]}.cal",
            f"{base_name}.cal",
        ]
        for c in cal_cands:
            cal_bytes = self.catalog.extract_file(c)
            if cal_bytes:
                break

        # 2. Try looking into Meshes.pak in parent dir
        if not cal_bytes and self.root:
            cand_parents = [
                self.root / parent_dir,
                self.root / "objects" / parent_dir,
                self.root / "Objects" / parent_dir,
            ]
            for full_parent in cand_parents:
                if full_parent.is_dir():
                    for mpak in full_parent.glob("*Mesh*.pak"):
                        arc = self.catalog.get_archive(mpak)
                        for cand in (
                            f"{base_name}.cal",
                            f"{base_name.split('_')[0]}.cal",
                            f"{parent_dir.name}/{base_name}.cal",
                        ):
                            cal_bytes = arc.read_file(cand)
                            if cal_bytes:
                                break
                        if cal_bytes:
                            break
                if cal_bytes:
                    break

        if not cal_bytes:
            return None, None

        cal_mapping = parse_cal(cal_bytes)
        if not cal_mapping:
            return None, None

        idle_caf_rel = find_default_idle_animation(cal_mapping)
        if not idle_caf_rel:
            return cal_mapping, None

        # Resolve CAF file
        self.ensure_category_paks_indexed(idle_caf_rel)
        caf_bytes = self.catalog.extract_file(idle_caf_rel)
        if not caf_bytes:
            caf_name = Path(idle_caf_rel).name
            caf_bytes = self.catalog.extract_file(caf_name)

        if not caf_bytes and self.root:
            cand_parents = [
                self.root / parent_dir,
                self.root / "objects" / parent_dir,
                self.root / "Objects" / parent_dir,
            ]
            for full_parent in cand_parents:
                if full_parent.is_dir():
                    for apak in full_parent.glob("*Anim*.pak"):
                        arc = self.catalog.get_archive(apak)
                        caf_name = Path(idle_caf_rel).name
                        caf_bytes = arc.read_file(caf_name)
                        if not caf_bytes:
                            caf_bytes = arc.read_file(idle_caf_rel)
                        if caf_bytes:
                            break
                if caf_bytes:
                    break

        return cal_mapping, caf_bytes
