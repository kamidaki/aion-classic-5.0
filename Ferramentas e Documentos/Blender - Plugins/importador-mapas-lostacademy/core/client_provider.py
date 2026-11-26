"""
Aion Multi-Client Dynamic Provider & Detection Layer.
Supports:
- Classic 5.0
- Retail 4.8
- Retail 4.6
- Retail 7.7
- Generic CryEngine / Aion clients
"""

from __future__ import annotations

import enum
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .pak_engine import AionCatalogIndex, AionPakArchive, cryengine_pak_sort_key


class ClientFlavor(enum.Enum):
    CLASSIC_50 = "Classic 5.0"
    RETAIL_48 = "Retail 4.8"
    RETAIL_46 = "Retail 4.6"
    RETAIL_77 = "Retail 7.7"
    RETAIL_39 = "Retail 3.9"
    GENERIC = "Generic Client"

    # Backward compatibility aliases
    CLASSIC_CLIENT = "Classic 5.0"
    RETAIL_CLIENT = "Retail 4.8"
    LEGACY_CLIENT = "Retail 4.6"


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

    def __enter__(self) -> "AionClientProvider":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Closes underlying PAK archive handles held by the provider catalog."""
        if getattr(self, "catalog", None) is not None:
            try:
                self.catalog.close()
            except Exception:
                pass

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
        Strictly classifies into CLASSIC and RETAIL versions.
        """
        b64 = self.root / "bin64" / "aion.bin"
        b32 = self.root / "bin32" / "aion.bin"

        # 1. Retail 7.7: Only 64-bit client (~5.8MB aion.bin) or 7.x server bat
        if (self.root / "server.bat").is_file() or (
            b64.is_file() and not b32.is_file() and b64.stat().st_size > 5_000_000
        ):
            return ClientFlavor.RETAIL_77

        # 2. Classic 5.0: 32-bit (~4.2MB) and 64-bit (~6.2MB), cc.ini, aiongraopdeck.dat
        if (
            (self.root / "aiongraopdeck.dat").is_file()
            or (self.root / "cc.ini").is_file()
            or (
                b64.is_file()
                and b64.stat().st_size > 6_000_000
                and b32.is_file()
                and b32.stat().st_size > 4_000_000
            )
        ):
            return ClientFlavor.CLASSIC_50

        # 3. Retail 4.6: 32-bit (~3.0MB) and 64-bit (~615KB)
        if b32.is_file() and b32.stat().st_size < 3_500_000:
            return ClientFlavor.RETAIL_46

        # 4. Retail 4.8: Client with dxvk.conf or 4.8 markers
        if (
            (self.root / "dxvk.conf").is_file()
            or "4.8" in str(self.root).lower()
        ):
            return ClientFlavor.RETAIL_48

        # Secondary fallback heuristics based on path
        root_str = str(self.root).lower()
        if "7.7" in root_str or "retail 7" in root_str:
            return ClientFlavor.RETAIL_77
        if "classic" in root_str:
            return ClientFlavor.CLASSIC_50
        if "4.8" in root_str or "live" in root_str:
            return ClientFlavor.RETAIL_48
        if "4.6" in root_str:
            return ClientFlavor.RETAIL_46

        return ClientFlavor.GENERIC

    def _init_catalog(self) -> None:
        """
        Indexes common PAKs across the detected client structure using official CryEngine precedence:
        Base PAKs are indexed first, and patch/override PAKs (z_*, Z_*, *patch*) are indexed last,
        allowing patch textures, meshes, and shaders to override base assets.
        """
        # 1. Shaders
        if self.shaders_dir and self.shaders_dir.is_dir():
            for p in sorted(self.shaders_dir.glob("*.pak"), key=cryengine_pak_sort_key):
                self.catalog.index_pak(p)

        # 2. Levels common
        if self.levels_dir and self.levels_dir.is_dir():
            common_p = self.levels_dir / "common"
            if common_p.is_dir():
                for p in sorted(common_p.glob("*.pak"), key=cryengine_pak_sort_key):
                    self.catalog.index_pak(p)

        # 3. Textures (sorting ensures z_Textures.pak overrides base Textures.pak)
        if self.textures_dir and self.textures_dir.is_dir():
            for p in sorted(self.textures_dir.glob("*.pak"), key=cryengine_pak_sort_key):
                self.catalog.index_pak(p)

        # 4. L10N Textures and common data
        if self.l10n_dir and self.l10n_dir.is_dir():
            for lang_dir in sorted(self.l10n_dir.iterdir(), key=cryengine_pak_sort_key):
                if lang_dir.is_dir():
                    for pak in sorted(lang_dir.glob("*.pak"), key=cryengine_pak_sort_key):
                        self.catalog.index_pak(pak)

    def get_world_pak_paths(self) -> List[Path]:
        """
        Discovers all PAK files in the World directory, sorted by CryEngine patch precedence.
        Base PAKs are first; z_* / patch PAKs (e.g. z_Patch001_World.pak) are last.
        """
        if not self.data_dir:
            return []
        world_dirs = [self.data_dir / "world", self.data_dir / "World"]
        paks: List[Path] = []
        for wd in world_dirs:
            if wd.is_dir():
                for p in wd.glob("*.pak"):
                    if p not in paks:
                        paks.append(p)
        return sorted(paks, key=cryengine_pak_sort_key)

    def get_world_pak_path(self) -> Optional[Path]:
        """Returns the primary or highest-priority patch world PAK."""
        paks = self.get_world_pak_paths()
        return paks[-1] if paks else None

    def get_npcs_pak_paths(self) -> List[Path]:
        """
        Discovers ALL PAK files in the NPCs directory, sorted by CryEngine patch precedence.
        Never assumes hardcoded PAK names: any PAK in Data/npcs is valid (e.g. Npcs.pak,
        Npcs_Custom.pak, z_*.pak).
        """
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
                    if p not in paks:
                        paks.append(p)
        return sorted(paks, key=cryengine_pak_sort_key)

    @property
    def is_encrypted(self) -> bool:
        """True if the client or its World.pak is protected with proprietary encryption (e.g. Retail 4.6 OADTENC1)."""
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

        # 1. Check World PAKs (highest patch priority first)
        for wp in reversed(self.get_world_pak_paths()):
            if not wp.is_file():
                continue
            # Check for OADTENC1 encryption signature (read only 8 bytes, never full PAK!)
            try:
                with open(wp, "rb") as _f:
                    head = _f.read(8)
                if head == b"OADTENC1":
                    print(
                        f"[AionClientProvider] Warning: {wp.name} has OADTENC1 signature (encrypted)."
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
            # Check for OADTENC1 encryption signature (read only 8 bytes, never full PAK!)
            try:
                with open(pak_path, "rb") as _f:
                    head = _f.read(8)
                if head == b"OADTENC1":
                    print(
                        f"[AionClientProvider] Skipping {pak_path.name}: OADTENC1 encrypted."
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

    def load_string_tables(self, preferred_lang: str = "BRA") -> int:
        """
        Loads localization strings (client_strings_npc.xml, client_strings_monster.xml, etc.)
        from the highest-priority L10N/<LANG>/data/*.pak (respecting z_Patch*.pak overrides),
        falling back to Data/Strings/Strings.pak only if no L10N table was found.
        """
        if self._string_tables_loaded:
            return len(self._string_tables)

        self._string_tables.clear()

        lang_order: List[str] = []
        for lang in (preferred_lang, "BRA", "ENG", "DEU", "FRA"):
            clean_l = str(lang or "").strip()
            if clean_l and clean_l not in lang_order:
                lang_order.append(clean_l)

        string_targets = (
            "client_strings_npc",
            "client_strings_monster",
            "client_strings_dic_monster",
            "client_strings_etc",
        )

        # 1. Try L10N/<LANG>/data/*.pak in strict language preference order
        if self.l10n_dir and self.l10n_dir.is_dir():
            l10n_subdirs = {d.name.upper(): d for d in self.l10n_dir.iterdir() if d.is_dir()}
            for lang in lang_order:
                lang_dir = l10n_subdirs.get(lang.upper())
                if lang_dir is None:
                    continue
                lang_paks: List[Path] = []
                for sub_data in (lang_dir / "data", lang_dir / "Data"):
                    if sub_data.is_dir():
                        lang_paks.extend(sorted(sub_data.glob("*.pak"), key=cryengine_pak_sort_key))
                root_pak = lang_dir / f"{lang_dir.name}.pak"
                if root_pak.is_file() and root_pak not in lang_paks:
                    lang_paks.append(root_pak)

                for pak_path in lang_paks:
                    try:
                        arc = self.catalog.get_archive(pak_path)
                        for entry_name in sorted(arc.entries.keys()):
                            entry_lower = entry_name.lower()
                            if entry_lower.endswith(".xml") and any(t in entry_lower for t in string_targets):
                                raw = arc.read_file(entry_name)
                                if raw:
                                    self._parse_string_xml(raw)
                    except Exception as exc:
                        print(f"[AionClientProvider] Warning reading strings from {pak_path}: {exc}")

                if self._string_tables:
                    break

        # 2. Fallback to Data/Strings/Strings.pak ONLY if no L10N string tables loaded
        if not self._string_tables and self.data_dir and self.data_dir.is_dir():
            for sp in (
                self.data_dir / "Strings" / "Strings.pak",
                self.data_dir / "strings" / "strings.pak",
            ):
                if not sp.is_file():
                    continue
                try:
                    arc = self.catalog.get_archive(sp)
                    for entry_name in sorted(arc.entries.keys()):
                        entry_lower = entry_name.lower()
                        if any(t in entry_lower for t in string_targets):
                            raw = arc.read_file(entry_name)
                            if raw:
                                self._parse_string_xml(raw)
                except Exception as exc:
                    print(f"[AionClientProvider] Warning reading strings from {sp}: {exc}")

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
                        self._string_tables[s_name.upper()] = s_body
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
                            self._string_tables[s_name.upper()] = s_body
                    i = j
                i += 1

    def resolve_localized_string(self, key_or_id: str | int) -> str:
        """Looks up a localized display string by ID or STR_* key."""
        if not self._string_tables_loaded:
            self.load_string_tables()
        k = str(key_or_id).strip()
        if not k:
            return k
        return self._string_tables.get(k) or self._string_tables.get(k.upper(), k)

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
            or "pc/" in clean_lower
            or "human" in clean_lower
            or "shugo" in clean_lower
        ):
            cand_dirs.extend([
                self.root / "objects" / "npc" / "level_object",
                self.root / "Objects" / "npc" / "level_object",
                self.root / "objects" / "npc" / "human",
                self.root / "Objects" / "npc" / "human",
                self.root / "objects" / "npc",
                self.root / "Objects" / "npc",
                self.root / "objects" / "pc",
                self.root / "Objects" / "pc",
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
        self,
        cgf_relative_path: str,
        preferred_kind: str = "idle",
    ) -> Tuple[Optional[Dict[str, str]], Optional[bytes]]:
        """
        Given a character model path (e.g. 'objects/pc/lm/mesh/lm.cgf' or 'objects/monster/brax/brax.cgf'):
        1. Finds and parses the corresponding .cal file
        2. Resolves and extracts the requested .caf animation bytes ('idle' or 'walk')
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

        if preferred_kind == "walk":
            idle_caf_rel = None
            for token in ("nwalk", "normal_walk", "walk", "nrun", "move", "run"):
                for anim_k, caf_rel in cal_mapping.items():
                    if token in anim_k.lower() or token in str(caf_rel).lower():
                        idle_caf_rel = caf_rel
                        break
                if idle_caf_rel:
                    break
            if not idle_caf_rel:
                idle_caf_rel = find_default_idle_animation(cal_mapping)
        else:
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
