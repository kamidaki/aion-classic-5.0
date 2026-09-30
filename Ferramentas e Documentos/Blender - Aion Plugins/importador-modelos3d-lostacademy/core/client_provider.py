"""
Aion Multi-Client Dynamic Provider & Detection Layer.
Supports:
- Client 1: GameForge Classic (EU) - BXML, XOR-32 PAKs
- Client 2: Aion Live Clássico (América do Sul) - UTF-8 / UTF-16 XML, ZIP PAKs, custom NPC tables
- Client 3: Aion 3.9 (This Aion Brasil) - UTF-16LE XML with BOM, ZIP / XOR PAKs
"""

from __future__ import annotations

import enum
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .pak_engine import AionCatalogIndex, AionPakArchive


class ClientFlavor(enum.Enum):
    GAMEFORGE_CLASSIC = "GameForge Classic (EU)"
    LIVE_CLASSICO_SA = "Aion Live Clássico (América do Sul)"
    AION_39_LEGACY = "Aion 3.9 (This Aion Brasil)"
    GENERIC = "Generic Aion Client"


class AionClientProvider:
    """
    Unified client abstraction layer providing version-independent access to:
    - PAK catalogs
    - Levels and maps
    - NPC world spawns
    - NPC archetype templates
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

        self.catalog = AionCatalogIndex(self.root)
        # Catálogo de PAKs é inicializado de forma lazy — __init__ deve ser instantâneo.
        self._catalog_initialized: bool = False

        # Cache of parsed templates and world spawns
        self._templates_cache: Optional[Dict[str, Any]] = None
        self._world_spawns_cache: Dict[str, List[Any]] = {}

    def _ensure_catalog_initialized(self) -> None:
        """Garante que o catálogo de PAKs foi indexado (lazy, executa apenas uma vez)."""
        if self._catalog_initialized:
            return
        self._init_catalog()
        self._catalog_initialized = True


    def _resolve_subpath(self, *candidates: str) -> Optional[Path]:
        for c in candidates:
            p = self.root / c
            if p.is_dir():
                return p
        return None

    def _detect_flavor(self) -> ClientFlavor:
        root_str = str(self.root).lower()
        if "gameforge" in root_str or "aionclassic" in root_str:
            return ClientFlavor.GAMEFORGE_CLASSIC
        if "live cl" in root_str or "am" in root_str or "lostacademy" in root_str:
            return ClientFlavor.LIVE_CLASSICO_SA
        if "3. 9" in root_str or "3.9" in root_str or "this aion" in root_str:
            return ClientFlavor.AION_39_LEGACY

        # Inspect indicators on disk
        data_p = self.root / "Data" if (self.root / "Data").is_dir() else self.root / "data"
        if data_p.is_dir():
            npcs_p = data_p / "NPCs" if (data_p / "NPCs").is_dir() else data_p / "npcs"
            if npcs_p.is_dir():
                if (npcs_p / "Npcs_LostAcademy.pak").is_file():
                    return ClientFlavor.LIVE_CLASSICO_SA
                if (npcs_p / "Npcs.pak").is_file():
                    return ClientFlavor.AION_39_LEGACY

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
            for p in self.textures_dir.rglob("*.pak"):
                self.catalog.index_pak(p)

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
        npc_dirs = [self.data_dir / "npcs", self.data_dir / "NPCs", self.data_dir / "npc", self.data_dir / "Npc"]
        paks: List[Path] = []
        for nd in npc_dirs:
            if nd.is_dir():
                for p in nd.glob("*.pak"):
                    paks.append(p)
        return paks

    def get_available_maps(self) -> List[str]:
        """Discovers all valid map names in the client levels directory."""
        if not self.levels_dir or not self.levels_dir.is_dir():
            return []
        maps = []
        for d in self.levels_dir.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                if (d / "Level.pak").is_file() or (d / ".aion_cache").is_dir() or (d / "terrain").is_dir():
                    maps.append(d.name)
        return sorted(maps)

    def read_world_spawns_data(self, map_name: str) -> Optional[bytes]:
        """Reads client_world_<map>.xml or .bxml bytes from World.pak or local map dir."""
        self._ensure_catalog_initialized()
        clean_map = map_name.strip().lower()


        # 1. Check world.pak
        wp = self.get_world_pak_path()
        if wp and wp.is_file():
            arc = self.catalog.get_archive(wp)
            for cand in (f"client_world_{clean_map}.xml", f"client_world_{clean_map}.bxml"):
                data = arc.read_file(cand)
                if data:
                    return data

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
            arc = self.catalog.get_archive(pak_path)
            for name in arc.entries.keys():
                if "client_npc" in name and (name.endswith(".xml") or name.endswith(".bxml")):
                    data = arc.read_file(name)
                    if data:
                        results.append((name, data))

        return results

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
        if "level_object" in clean_lower or "npc" in clean_lower or "human" in clean_lower or "cam" in clean_lower or "caf" in clean_lower or "cem" in clean_lower or "cff" in clean_lower:
            cand_dirs.extend([
                self.root / "objects" / "npc" / "level_object",
                self.root / "Objects" / "npc" / "level_object",
                self.root / "objects" / "npc" / "human",
                self.root / "Objects" / "npc" / "human",
                self.root / "objects" / "npc",
                self.root / "Objects" / "npc",
            ])
        if "animation" in clean_lower or clean_lower.endswith(".caf") or clean_lower.startswith(("lf_", "df_", "lm_", "dm_", "clf", "clm")):
            for r in ("lf", "lm", "df", "dm"):
                for obj_p in ("objects/pc", "Objects/pc"):
                    cand_dirs.append(self.root / obj_p / r / "animation")

        for cd in cand_dirs:
            if cd.is_dir():
                for p in cd.glob("*.pak"):
                    self.catalog.index_pak(p)

    def resolve_cgf_bytes(self, cgf_relative_path: str) -> Optional[bytes]:
        """Resolves and extracts CGF model bytes dynamically."""
        if not cgf_relative_path:
            return None
        self._ensure_catalog_initialized()
        self.ensure_category_paks_indexed(cgf_relative_path)

        clean_path = cgf_relative_path.replace("\\", "/").strip().lstrip("/")
        b = self.catalog.extract_file(clean_path)
        if not b:
            b = self.catalog.extract_file(Path(clean_path).name)
        return b

    def resolve_animation_asset(self, cgf_relative_path: str) -> Tuple[Optional[Dict[str, str]], Optional[bytes]]:
        """
        Given a character model path (e.g. 'objects/npc/shugomale/shugomale.cgf' or 'Monster/brax/brax.cgf'):
        1. Finds and parses the corresponding .cal file
        2. Resolves and extracts the idle .caf animation bytes
        Returns (cal_mapping, caf_bytes) or (None, None).
        """
        try:
            from formats.cgf.cal_parser import parse_cal, find_default_idle_animation
        except (ImportError, ValueError):
            from ..formats.cgf.cal_parser import parse_cal, find_default_idle_animation

        if not cgf_relative_path:
            return None, None

        self._ensure_catalog_initialized()
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
                        for cand in (f"{base_name}.cal", f"{base_name.split('_')[0]}.cal", f"{parent_dir.name}/{base_name}.cal"):
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

    def find_caf_bytes(self, caf_relative_path: str, source_model_path: str = "") -> Optional[bytes]:
        """
        Resolves CAF animation bytes with multi-tier fallback:
        1. Checks in the same PAK/folder where source_model_path is located.
        2. Checks catalog for exact relative path and bare filename.
        3. Scans & indexes known candidate PAK folders (objects/npc, objects/monster, data/animations, etc.).
        4. Retries catalog extraction.
        """
        if not caf_relative_path:
            return None

        self._ensure_catalog_initialized()

        clean_caf = caf_relative_path.replace("\\", "/").strip().lstrip("/")
        caf_name = Path(clean_caf).name

        # 1. Check parent folder / PAK of source model if provided
        if source_model_path and self.root:
            clean_source = source_model_path.replace("\\", "/").strip().lstrip("/")
            parent_dir = Path(clean_source).parent
            cand_parents = [
                self.root / parent_dir,
                self.root / "objects" / parent_dir,
                self.root / "Objects" / parent_dir,
            ]
            for full_parent in cand_parents:
                if full_parent.is_dir():
                    paks = list(full_parent.glob("*Mesh*.pak")) + list(full_parent.glob("*Anim*.pak")) + list(full_parent.glob("*.pak"))
                    for pak in paks:
                        arc = self.catalog.get_archive(pak)
                        for cand in (clean_caf, caf_name, f"{parent_dir.name}/{caf_name}"):
                            data = arc.read_file(cand)
                            if data:
                                return data

        # 2. Check catalog directly
        data = self.catalog.extract_file(clean_caf)
        if data:
            return data
        data = self.catalog.extract_file(caf_name)
        if data:
            return data

        # 3. Ensure candidate PAKs indexed
        self.ensure_category_paks_indexed(clean_caf)
        if source_model_path:
            self.ensure_category_paks_indexed(source_model_path)

        anim_search_folders = [
            "objects/npc",
            "objects/monster",
            "data/animations",
            "animations",
            "npc",
            "monster",
        ]
        for folder in anim_search_folders:
            f_path = self.root / folder
            if f_path.is_dir():
                for p in f_path.glob("*.pak"):
                    self.catalog.index_pak(p)

        # 4. Retry catalog extraction
        data = self.catalog.extract_file(clean_caf)
        if data:
            return data
        data = self.catalog.extract_file(caf_name)
        return data

    def get_available_classes(self) -> List[Tuple[str, str, str]]:
        """
        Dynamically extracts available character classes from the client's PC.pak (client_character_class_info.xml).
        Returns list of (id, display_name, description) tuples formatted for Blender EnumProperty.
        Falls back to canonical 8 classic classes if client data is not available.
        """
        CLASS_MAP = {
            "Fighter": ("GLADIATOR", "Gladiador", "Gladiador (Placas, Espadão / Lança)"),
            "Knight": ("TEMPLAR", "Templário", "Templário (Placas, Espada + Escudo)"),
            "Ranger": ("RANGER", "Arqueiro", "Arqueiro (Couro, Arco)"),
            "Assassin": ("ASSASSIN", "Assassino", "Assassino (Couro, Duplas Adagas)"),
            "Wizard": ("SORCERER", "Feiticeiro", "Feiticeiro (Tecido, Orbe / Livro)"),
            "Elementallist": ("SPIRITMASTER", "Espiritualista", "Espiritualista (Tecido, Orbe / Livro)"),
            "Priest": ("CLERIC", "Clérigo", "Clérigo (Malha, Maça + Escudo)"),
            "Chanter": ("CHANTER", "Cantor", "Cantor (Malha, Cajado)"),
            "Thunderer": ("THUNDERER", "Carrasco / Executor", "Carrasco / Thunderer (Couro, Correntes)"),
            "Gunner": ("GUNSLINGER", "Atirador", "Atirador (Couro, Pistolas Mágicas)"),
            "Runeblade": ("RUNEBLADE", "Lâmina Rúnica", "Lâmina Rúnica (Tecido, Espada Mágica)"),
            "BattleMaster": ("BATTLEMASTER", "Mestre da Batalha", "Mestre da Batalha (Combate Físico)"),
            "Lumines": ("LUMINES", "Lumines", "Lumines (Canalizador Luminoso)"),
        }

        # Fallback 8 classic classes
        FALLBACK_CLASSES = [
            ("GLADIATOR", "Gladiador", "Gladiador (Placas, Espadão / Lança)"),
            ("TEMPLAR", "Templário", "Templário (Placas, Espada + Escudo)"),
            ("RANGER", "Arqueiro", "Arqueiro (Couro, Arco)"),
            ("ASSASSIN", "Assassino", "Assassino (Couro, Duplas Adagas)"),
            ("SORCERER", "Feiticeiro", "Feiticeiro (Tecido, Orbe / Livro)"),
            ("SPIRITMASTER", "Espiritualista", "Espiritualista (Tecido, Orbe / Livro)"),
            ("CLERIC", "Clérigo", "Clérigo (Malha, Maça + Escudo)"),
            ("CHANTER", "Cantor", "Cantor (Malha, Cajado)"),
        ]

        if not self.data_dir:
            return FALLBACK_CLASSES

        self._ensure_catalog_initialized()
        pc_paks = []

        for pd in [self.data_dir / "PC", self.data_dir / "pc"]:
            if pd.is_dir():
                pc_paks.extend(pd.glob("*.pak"))

        found_classes: List[Tuple[str, str, str]] = []
        seen_keys = set()

        for pak in pc_paks:
            try:
                arc = self.catalog.get_archive(pak)
                for name in arc.entries:
                    if "class" in name.lower() and name.endswith(".xml"):
                        raw = arc.read_file(name)
                        if not raw:
                            continue
                        # Scan BXML or plain XML
                        idx = raw.find(b"c\x00h\x00a\x00r\x00a\x00c\x00t\x00e\x00r\x00_\x00c\x00l\x00a\x00s\x00s\x00")
                        if idx != -1:
                            text = raw[idx:].decode("utf-16le", errors="replace")
                            items = [it.strip() for it in text.split("\x00") if it.strip()]
                            for token in items:
                                if token in CLASS_MAP and CLASS_MAP[token][0] not in seen_keys:
                                    seen_keys.add(CLASS_MAP[token][0])
                                    found_classes.append(CLASS_MAP[token])
                        else:
                            # Plain XML
                            text = raw.decode("utf-8", errors="ignore")
                            for k, v in CLASS_MAP.items():
                                if k in text and v[0] not in seen_keys:
                                    seen_keys.add(v[0])
                                    found_classes.append(v)
            except Exception:
                pass

        return found_classes if found_classes else FALLBACK_CLASSES

    def get_npc_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Parses client_npcs.xml (BXML and XML) from npcs.pak and resolves string tags from Strings.pak.
        Returns a dictionary mapping normalized CGF paths and stems to {id, name, clean_name, mesh, model_path}.
        """
        if self._templates_cache is not None:
            return self._templates_cache

        self._ensure_catalog_initialized()
        import re


        # 1. Load string translations from Strings.pak or Translation directory
        str_map: Dict[str, str] = {}
        str_paks = []
        if self.data_dir:
            for sd in [self.data_dir / "Strings", self.data_dir / "strings"]:
                if sd.is_dir():
                    str_paks.extend(sd.glob("*.pak"))

        for str_pak in str_paks:
            try:
                arc = self.catalog.get_archive(str_pak)
                for fname in ("client_strings_monster.xml", "client_strings_npc.xml", "client_strings_dic_monster.xml"):
                    raw = arc.read_file(fname)
                    if not raw:
                        continue
                    idx = raw.find(b"s\x00t\x00r\x00i\x00n\x00g\x00")
                    if idx != -1:
                        text = raw[idx:].decode("utf-16le", errors="replace")
                        items = [it.strip() for it in text.split("\x00") if it.strip()]
                        for i in range(len(items) - 1):
                            t = items[i]
                            if t.startswith("STR_"):
                                val = items[i + 1]
                                if val and not val.startswith("STR_") and not val.isdigit():
                                    str_map[t] = val
            except Exception:
                pass

        # 2. Parse client_npcs.xml
        templates: Dict[str, Dict[str, Any]] = {}
        npc_paks = self.get_npcs_pak_paths()

        def clean_name(raw: str) -> str:
            n = re.sub(r"_\d+_[a-zA-Z]+$", "", raw)
            n = re.sub(r"_\d+$", "", n)
            return n.replace("_", " ").strip().title()

        for pak in npc_paks:
            try:
                arc = self.catalog.get_archive(pak)
                for fname in arc.entries:
                    if "client_npc" in fname.lower() and (fname.endswith(".xml") or fname.endswith(".bxml")):
                        raw = arc.read_file(fname)
                        if not raw:
                            continue

                        # Check BXML
                        idx = raw.find(b"n\x00p\x00c\x00_\x00c\x00l\x00i\x00e\x00n\x00t\x00")
                        if idx != -1:
                            text = raw[idx:].decode("utf-16le", errors="replace")
                            items = [it.strip() for it in text.split("\x00") if it.strip()]
                            i = 0
                            n_items = len(items)
                            while i < n_items:
                                token = items[i]
                                if token.isdigit() and len(token) in (6, 7):
                                    npc_id = token
                                    raw_n = items[i + 1] if i + 1 < n_items and not items[i + 1].isdigit() and not items[i + 1].startswith("STR_") and "/" not in items[i + 1] else ""
                                    desc_tag = ""
                                    for j in range(i + 1, min(i + 25, n_items)):
                                        if items[j].startswith("STR_"):
                                            desc_tag = items[j]
                                        elif "/" in items[j] and any(items[j].lower().startswith(p) for p in ("monster", "npc", "pc", "skill_object", "level_object", "event_object")):
                                            mesh_dir = items[j]
                                            if j + 1 < n_items and not items[j + 1].isdigit() and not items[j + 1].startswith("STR_") and "/" not in items[j + 1]:
                                                mesh_file = items[j + 1]
                                                cgf_rel = f"objects/{mesh_dir.lower()}/{mesh_file.lower()}.cgf"

                                                # Resolve display name
                                                string_val = str_map.get(desc_tag, "")
                                                # Use string translation if ASCII/Roman, otherwise clean English internal name
                                                if string_val and string_val.isascii() and string_val.lower() != "body":
                                                    display_base = string_val.strip()
                                                elif raw_n:
                                                    display_base = clean_name(raw_n)
                                                else:
                                                    display_base = clean_name(mesh_file)

                                                display_name = f"{display_base} [{npc_id}]"

                                                info = {
                                                    "id": npc_id,
                                                    "name": display_name,
                                                    "clean_name": display_base,
                                                    "raw_name": raw_n,
                                                    "mesh": mesh_file,
                                                    "model_path": cgf_rel,
                                                }

                                                if cgf_rel not in templates:
                                                    templates[cgf_rel] = info
                                                stem_key = mesh_file.lower()
                                                if stem_key not in templates:
                                                    templates[stem_key] = info
                                            break
                                    i += 2
                                else:
                                    i += 1
            except Exception:
                pass

        self._templates_cache = templates
        return templates
