"""
Sound Provider for Aion Assets.
Discovers, extracts, caches, and plays sound effects (vox, combat, footstep, magic, dialogue)
associated with 3D models and animations in Blender using the native Audaspace (aud) engine.
"""

from __future__ import annotations
import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import bpy
from ..core.pak_engine import AionCatalogIndex, AionPakArchive
from ..indexer.asset_entry import AssetEntry

logger = logging.getLogger("AionModelLibrary.SoundProvider")


class SoundProvider:
    """Manages audio extraction from Aion Sound PAKs and real-time playback via Blender aud."""

    _instance: Optional["SoundProvider"] = None

    def __init__(self, catalog: AionCatalogIndex, client_root: Path):
        self.catalog = catalog
        self.client_root = client_root
        self._temp_sound_dir = Path(tempfile.mkdtemp(prefix="aion_sound_cache_"))
        self._sound_path_cache: Dict[str, Path] = {}
        self._model_sounds_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._marker_xml_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._indexed_sound_paks: Set[str] = set()
        self._device: Optional[Any] = None
        self._active_handles: List[Any] = []
        self._markers_pak_archive: Optional[AionPakArchive] = None

    @classmethod
    def get(cls, catalog: Optional[AionCatalogIndex] = None, client_root: Optional[Path] = None) -> "SoundProvider":
        if cls._instance is None:
            if catalog is None or client_root is None:
                raise ValueError("SoundProvider requires catalog and client_root for initial instantiation.")
            cls._instance = cls(catalog, client_root)
        return cls._instance

    def _get_device(self) -> Any:
        """Returns the shared audaspace device."""
        if self._device is None:
            try:
                import aud
                self._device = aud.Device()
            except Exception as e:
                logger.warning("Could not initialize audaspace device: %s", e)
        return self._device

    def _get_markers_archive(self) -> Optional[AionPakArchive]:
        """Lazy-loads the AnimationMarkers.pak archive."""
        if self._markers_pak_archive is not None:
            return self._markers_pak_archive

        cand = self.client_root / "data" / "AnimationMarkers.pak"
        if not cand.is_file():
            found = list(self.client_root.glob("**/AnimationMarkers.pak"))
            if found:
                cand = found[0]

        if cand.is_file():
            try:
                self._markers_pak_archive = AionPakArchive(cand)
            except Exception as e:
                logger.warning("Failed to open AnimationMarkers.pak: %s", e)

        return self._markers_pak_archive

    def _index_candidate_sound_paks(self, hint: str = "") -> None:
        """Dynamically indexes relevant sound PAKs based on model or sound hint."""
        sounds_dir = self.client_root / "Sounds"
        hint_clean = hint.lower().replace("\\", "/").strip()
        stem = Path(hint_clean).stem

        # Priority 1: Model-specific monster or pet folder
        search_dirs: List[Path] = []
        if stem:
            search_dirs.extend([
                sounds_dir / "monster" / stem,
                sounds_dir / "pet" / stem,
                sounds_dir / "monster" / stem.split("_")[0],
                sounds_dir / "pet" / stem.split("_")[0],
            ])

        # Priority 2: Common combat, footsteps, effects, voices
        search_dirs.extend([
            sounds_dir / "monster" / "common",
            sounds_dir / "monster",
            sounds_dir / "effect",
            sounds_dir / "step",
            sounds_dir / "motion",
            sounds_dir / "voice" / "attack",
            sounds_dir / "voice" / "motion",
            sounds_dir / "voice" / "damage",
            sounds_dir / "voice" / "defence",
            sounds_dir / "voice" / "cast",
            sounds_dir,
            self.client_root / "l10n" / "BRA" / "sounds" / "npc",
            self.client_root / "l10n" / "ENG" / "sounds" / "npc",
        ])

        for s_dir in search_dirs:
            if s_dir.is_dir():
                key = str(s_dir).lower()
                if key not in self._indexed_sound_paks:
                    self._indexed_sound_paks.add(key)
                    for pak_p in s_dir.glob("*.pak"):
                        try:
                            self.catalog.index_pak(pak_p)
                        except Exception:
                            pass

    def resolve_sound_file(self, sound_rel_path: str) -> Optional[Path]:
        """Resolves a sound file (e.g. 'Sounds\\monster\\baku_voice_01_attack.ogg') to a local disk path."""
        if not sound_rel_path:
            return None

        clean_rel = sound_rel_path.replace("\\", "/").strip().lstrip("/")
        clean_key = clean_rel.lower()
        bare_name = Path(clean_rel).name.lower()

        # Check path cache
        if clean_key in self._sound_path_cache:
            p = self._sound_path_cache[clean_key]
            if p.is_file():
                return p

        # Check catalog
        entry_info = self.catalog.find_file(clean_rel)
        if not entry_info:
            entry_info = self.catalog.find_file(bare_name)

        if not entry_info:
            self._index_candidate_sound_paks(clean_rel)
            entry_info = self.catalog.find_file(clean_rel) or self.catalog.find_file(bare_name)

        if entry_info:
            dest_file = self._temp_sound_dir / bare_name
            if dest_file.is_file():
                self._sound_path_cache[clean_key] = dest_file
                return dest_file

            data = self.catalog.extract_file(entry_info[1].name)
            if data:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                dest_file.write_bytes(data)
                self._sound_path_cache[clean_key] = dest_file
                return dest_file

        return None

    def _parse_animation_marker_bxml(self, xml_name: str) -> List[Dict[str, Any]]:
        """Parses an animation marker XML/BXML from AnimationMarkers.pak to extract sound and timing data."""
        if xml_name in self._marker_xml_cache:
            return self._marker_xml_cache[xml_name]

        arc = self._get_markers_archive()
        if not arc or xml_name not in arc.entries:
            return []

        data = arc.read_file(xml_name)
        if not data or len(data) < 10:
            return []

        # Check if BXML (0x80 header) or plain XML
        results: List[Dict[str, Any]] = []

        if data[0] == 0x80:
            # BXML: null-separated UTF-16LE string table starts after 5-byte header
            text = data[5:].decode("utf-16le", errors="ignore")
            tokens = [t.strip() for t in text.split("\x00") if t.strip()]

            current_anim = ""
            i = 0
            n = len(tokens)
            while i < n:
                token = tokens[i]
                if token == "name" and i + 1 < n:
                    current_anim = tokens[i + 1]
                    i += 2
                    continue

                if token.lower().endswith((".ogg", ".wav")):
                    sound_file = token
                    when_val = 0.0
                    # Look backwards or forwards for 'when' timestamp
                    for check_idx in range(max(0, i - 8), min(n, i + 8)):
                        if tokens[check_idx] == "when" and check_idx + 1 < n:
                            try:
                                when_val = float(tokens[check_idx + 1])
                            except ValueError:
                                pass
                            break
                        elif re.match(r"^\d+\.\d+$", tokens[check_idx]):
                            try:
                                when_val = float(tokens[check_idx])
                            except ValueError:
                                pass

                    results.append({
                        "file": sound_file,
                        "anim_name": current_anim,
                        "when": when_val,
                    })

                i += 1
        else:
            # Plain XML
            text = data.decode("utf-8", errors="ignore")
            for anim_match in re.finditer(r'<animation[^>]*name="([^"]+)"[^>]*>(.*?)</animation>', text, re.DOTALL):
                anim_name, block = anim_match.groups()
                for s_match in re.finditer(r'<sound[^>]*file="([^"]+)"[^>]*when="([0-9\.]+)"', block):
                    s_file, s_when = s_match.groups()
                    results.append({
                        "file": s_file,
                        "anim_name": anim_name,
                        "when": float(s_when),
                    })

        self._marker_xml_cache[xml_name] = results
        return results

    def get_sounds_for_model(self, entry: AssetEntry) -> List[Dict[str, Any]]:
        """
        Discovers all sound effects and voice clips available for the specified model asset.
        Returns a sorted, deduplicated list of sound descriptors.
        """
        cache_key = entry.asset_id or entry.name
        if cache_key in self._model_sounds_cache:
            return self._model_sounds_cache[cache_key]

        sounds: List[Dict[str, Any]] = []
        seen_files: Set[str] = set()

        # Extract model identifiers
        model_p = entry.model_path.lower().replace("\\", "/")
        stem = Path(model_p).stem.lower()
        parts = stem.split("_")
        base_name = parts[0]

        # 1. Check AnimationMarkers.pak
        marker_candidates = [
            f"{stem}.xml",
            f"{'_'.join(parts[:3])}.xml" if len(parts) >= 3 else "",
            f"{'_'.join(parts[:2])}.xml" if len(parts) >= 2 else "",
            f"{base_name}.xml",
        ]
        for mc in marker_candidates:
            if mc:
                parsed_markers = self._parse_animation_marker_bxml(mc)
                for item in parsed_markers:
                    s_file = item["file"]
                    if s_file.lower() not in seen_files:
                        seen_files.add(s_file.lower())
                        category = self._classify_sound(s_file)
                        display_name = self._make_sound_display_name(s_file, item.get("anim_name"))
                        sounds.append({
                            "id": f"marker_{len(sounds)}",
                            "name": display_name,
                            "file": s_file,
                            "category": category,
                            "when": item.get("when", 0.0),
                            "anim_name": item.get("anim_name", ""),
                        })
                if sounds:
                    break

        # 2. Check model-specific monster / pet PAK directly
        self._index_candidate_sound_paks(stem)
        pak_name_cands = [stem, "_".join(parts[:2]) if len(parts) >= 2 else "", base_name]
        for pnc in pak_name_cands:
            if not pnc:
                continue
            monster_pak_p = self.client_root / "Sounds" / "monster" / pnc / f"{pnc}.pak"
            pet_pak_p = self.client_root / "Sounds" / "pet" / pnc / f"{pnc}.pak"

            for cand_pak in (monster_pak_p, pet_pak_p):
                if cand_pak.is_file():
                    try:
                        arc = AionPakArchive(cand_pak)
                        for entry_name in sorted(arc.entries.keys()):
                            if entry_name.lower().endswith((".ogg", ".wav")):
                                full_rel = f"Sounds/{cand_pak.parent.name}/{pnc}/{entry_name}"
                                if entry_name.lower() not in seen_files:
                                    seen_files.add(entry_name.lower())
                                    seen_files.add(full_rel.lower())
                                    display_name = self._make_sound_display_name(entry_name)
                                    sounds.append({
                                        "id": f"pak_{len(sounds)}",
                                        "name": display_name,
                                        "file": entry_name,
                                        "category": self._classify_sound(entry_name),
                                        "when": 0.0,
                                        "anim_name": "",
                                    })
                    except Exception:
                        pass

        # 3. If still empty, supply common archetype monster/character movement & attack sounds
        if not sounds:
            common_pak = self.client_root / "Sounds" / "monster" / "common" / "common.pak"
            if common_pak.is_file():
                try:
                    arc = AionPakArchive(common_pak)
                    for e in list(arc.entries.keys())[:15]:
                        if e.lower().endswith(".ogg") and e.lower() not in seen_files:
                            seen_files.add(e.lower())
                            sounds.append({
                                "id": f"com_{len(sounds)}",
                                "name": self._make_sound_display_name(e),
                                "file": e,
                                "category": self._classify_sound(e),
                                "when": 0.0,
                                "anim_name": "",
                            })
                except Exception:
                    pass

        self._model_sounds_cache[cache_key] = sounds
        return sounds

    @staticmethod
    def _classify_sound(filepath: str) -> str:
        """Classifies sound into a clean user-facing category."""
        fn = Path(filepath).stem.lower()
        if any(k in fn for k in ("vox", "voice", "scream", "laugh", "talk")):
            return "VOZ"
        if any(k in fn for k in ("atk", "attack", "hit", "swish", "strike", "swing", "slash")):
            return "ATAQUE"
        if any(k in fn for k in ("die", "dead", "death")):
            return "MORTE"
        if any(k in fn for k in ("dmg", "damage", "hurt", "groan", "pain")):
            return "DANO"
        if any(k in fn for k in ("step", "walk", "run", "jump", "land", "bodyfall", "foot")):
            return "PASSOS"
        if any(k in fn for k in ("cast", "fire", "magic", "skill", "spell", "buff")):
            return "MAGIA"
        return "EFEITO"

    @staticmethod
    def _make_sound_display_name(filepath: str, anim_name: str = "") -> str:
        """Converts raw sound file name and animation context to a clean, human-readable label."""
        stem = Path(filepath).stem
        clean = stem.replace("_", " ").title()
        # Remove repeated prefix words if redundant
        tokens = [t for t in clean.split() if t.lower() not in ("sounds", "monster", "common")]
        name = " ".join(tokens)
        if anim_name:
            clean_anim = anim_name.replace("_", " ").title()
            return f"{name} ({clean_anim})"
        return name

    def play_sound(self, sound_rel_or_file: str, volume: float = 1.0, pitch: float = 1.0) -> bool:
        """
        Plays the specified sound file asynchronously via Blender's native aud engine.
        Returns True on success.
        """
        resolved_path = self.resolve_sound_file(sound_rel_or_file)
        if not resolved_path or not resolved_path.is_file():
            logger.warning("Could not resolve sound file: %s", sound_rel_or_file)
            return False

        dev = self._get_device()
        if dev is None:
            return False

        try:
            import aud
            sound = aud.Sound(str(resolved_path))
            handle = dev.play(sound)
            if handle is not None:
                handle.volume = max(0.0, min(2.0, volume))
                handle.pitch = max(0.1, min(3.0, pitch))
                self._active_handles.append(handle)
                # Keep active handles list pruned
                self._active_handles = [h for h in self._active_handles if getattr(h, "status", True)]
                return True
        except Exception as e:
            logger.error("Error playing audio with aud: %s", e)
            return False

        return False

    def stop_all_sounds(self) -> None:
        """Stops all active audio playback handles immediately."""
        dev = self._get_device()
        if dev is not None:
            try:
                dev.stopAll()
            except Exception:
                pass
        self._active_handles.clear()

    def clear_cache(self) -> None:
        """Clears transient caches."""
        self._sound_path_cache.clear()
        self._model_sounds_cache.clear()

    def cleanup(self) -> None:
        """Cleanly releases audio resources and removes temp extracted files."""
        self.stop_all_sounds()
        self.clear_cache()
        import shutil
        shutil.rmtree(self._temp_sound_dir, ignore_errors=True)
