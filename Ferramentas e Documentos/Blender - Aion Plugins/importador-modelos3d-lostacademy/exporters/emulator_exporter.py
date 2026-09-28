"""
Emulator NPC Template Exporter for LostAcademy Aion Model Library.
Automatically creates matching npc_template entries in the emulator's game-server
static data when a new NPC is created in Blender.
"""
from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
import xml.etree.ElementTree as ET


EMULATOR_NPC_TEMPLATES_PATH = Path(
    r"D:\AION CLASSIC 5.0 - EMULADOR\Código Fonte - Emulador"
    r"\game-server\data\static_data\npcs\npc_templates.xml"
)

# Mapping from client tribe names to emulator enum names (XSD)
TRIBE_MAP: Dict[str, str] = {
    "general": "GENERAL",
    "guard_dark": "GUARD_DARK",
    "guard_light": "GUARD_LIGHT",
    "monster": "MONSTER_AGGRESSIVE",
    "npc": "PC",
}

# AI name normalisation: client name -> emulator ai attribute
AI_MAP: Dict[str, str] = {
    "General": "general",
    "SkillArea": "skillarea",
    "SummonSkillArea": "skillarea",
    "Aggressive": "homing",
    "Merchant": "merchant",
    "Quest": "npc",
    "Static": "stand",
}


class EmulatorExporter:
    """Exports NPC metadata to the emulator ``npc_templates.xml``.

    Usage example::

        exp = EmulatorExporter()
        if not exp.npc_id_exists(900042):
            exp.export_npc(npc_id=900042, name="Test NPC", name_id=799042)
    """

    def __init__(self, emulator_npc_templates_path: Optional[Path] = None) -> None:
        self.npc_templates_path: Path = (
            emulator_npc_templates_path or EMULATOR_NPC_TEMPLATES_PATH
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_tree(self) -> ET.ElementTree:
        """Loads and returns the :class:`xml.etree.ElementTree.ElementTree`
        from ``npc_templates.xml``.

        Raises:
            FileNotFoundError: When the path does not point to a regular file.
        """
        if not self.npc_templates_path.is_file():
            raise FileNotFoundError(
                f"npc_templates.xml not found: {self.npc_templates_path}"
            )
        ET.register_namespace("", "")
        return ET.parse(str(self.npc_templates_path))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def npc_id_exists(self, npc_id: int) -> bool:
        """Returns ``True`` if *npc_id* already exists in the template file."""
        try:
            tree = self._load_tree()
            root = tree.getroot()
            for elem in root.findall("npc_template"):
                if int(elem.get("npc_id", -1)) == npc_id:
                    return True
        except Exception:
            pass
        return False

    def export_npc(
        self,
        npc_id: int,
        name: str,
        name_id: int,
        level: int = 1,
        height: float = 1.0,
        max_hp: int = 1000,
        race: str = "",
        tribe: str = "GENERAL",
        npc_type: str = "GENERAL",
        ai: str = "general",
        srange: int = 10,
        sangle: int = 240,
        attack_speed: int = 2000,
        hpgauge: int = 3,
        rank: str = "NOVICE",
        rating: str = "NORMAL",
        walk_speed: float = 2.0,
        run_speed: float = 6.0,
        bound_front: float = 0.5,
        bound_side: float = 0.5,
        bound_upper: float = 2.0,
        extra_attrs: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Inserts a new ``<npc_template>`` entry into ``npc_templates.xml``.

        A ``.bak`` backup is created (once, on first write) before the file is
        modified.  Subsequent saves overwrite the file directly.

        Args:
            npc_id: Unique numeric NPC identifier.
            name: Display name used in-game.
            name_id: Numeric key into the client string table.
            level: NPC combat level (1–100).
            height: Model height multiplier (world units).
            max_hp: Maximum hit points.
            race: Aion race string (e.g. ``"LYCAN"``); omitted if empty.
            tribe: Tribe / faction enum (e.g. ``"GENERAL"``, ``"GUARD_DARK"``).
            npc_type: NPC type classification enum.
            ai: AI behaviour key; see :data:`AI_MAP`.
            srange: Vision/aggro range in metres.
            sangle: Vision cone half-angle in degrees.
            attack_speed: Base attack speed in milliseconds.
            hpgauge: HP-bar display level (0 = hidden, higher = more bars).
            rank: Power rank string (``"NOVICE"`` … ``"MASTER"``).
            rating: Quality rating (``"NORMAL"``, ``"ELITE"`` …).
            walk_speed: Walk movement speed (m/s).
            run_speed: Run movement speed (m/s).
            bound_front: Front bounding-sphere radius.
            bound_side: Side bounding-sphere radius.
            bound_upper: Upper bounding-sphere radius.
            extra_attrs: Optional dict of additional XML attributes to append
                to the ``<npc_template>`` element verbatim.

        Returns:
            ``True`` on success.

        Raises:
            ValueError: If *npc_id* already exists in the file.
            FileNotFoundError: If the XML file is not found.
        """
        if self.npc_id_exists(npc_id):
            raise ValueError(
                f"NPC ID {npc_id} already exists in npc_templates.xml"
            )

        # Backup (created once; subsequent calls keep the original backup)
        bak_path = self.npc_templates_path.with_suffix(".xml.bak")
        if not bak_path.exists():
            shutil.copy2(str(self.npc_templates_path), str(bak_path))

        tree = self._load_tree()
        root = tree.getroot()

        # Build XML attributes dictionary
        attrs: Dict[str, str] = {
            "npc_id": str(npc_id),
            "level": str(level),
            "name": name,
            "name_id": str(name_id),
            "height": str(round(height, 4)),
            "rank": rank.upper(),
            "rating": rating.upper(),
            "tribe": tribe.upper(),
            "type": npc_type.upper(),
            "ai": AI_MAP.get(ai, ai.lower()),
            "srange": str(srange),
            "sangle": str(sangle),
            "attack_speed": str(attack_speed),
            "hpgauge": str(hpgauge),
        }
        if race:
            attrs["race"] = race.upper()
        if extra_attrs:
            for k, v in extra_attrs.items():
                attrs[k] = str(v)

        template_elem = ET.SubElement(root, "npc_template", attrs)
        template_elem.tail = "\n\t"

        # Stats sub-element
        stats_elem = ET.SubElement(template_elem, "stats", {"maxHp": str(max_hp)})
        if walk_speed > 0 or run_speed > 0:
            ET.SubElement(
                stats_elem,
                "speeds",
                {
                    "walk": str(round(walk_speed, 1)),
                    "group_walk": str(round(walk_speed, 1)),
                    "run": str(round(run_speed, 1)),
                    "run_fight": str(round(run_speed, 1)),
                    "group_run_fight": str(round(run_speed, 1)),
                },
            )

        # Bounding radius sub-element
        ET.SubElement(
            template_elem,
            "bound_radius",
            {
                "front": str(round(bound_front, 4)),
                "side": str(round(bound_side, 4)),
                "upper": str(round(bound_upper, 4)),
            },
        )

        # Write back to disk
        tree.write(
            str(self.npc_templates_path),
            encoding="utf-8",
            xml_declaration=True,
        )
        return True

    @staticmethod
    def get_max_npc_id(emulator_path: Optional[Path] = None) -> int:
        """Returns the highest existing ``npc_id`` in ``npc_templates.xml``.

        Falls back to ``900000`` if the file cannot be read.

        Args:
            emulator_path: Override path to ``npc_templates.xml``.  Defaults
                to :data:`EMULATOR_NPC_TEMPLATES_PATH`.
        """
        path = emulator_path or EMULATOR_NPC_TEMPLATES_PATH
        try:
            tree = ET.parse(str(path))
            max_id = 0
            for elem in tree.getroot().findall("npc_template"):
                try:
                    nid = int(elem.get("npc_id", 0))
                    max_id = max(max_id, nid)
                except (ValueError, TypeError):
                    pass
            return max_id
        except Exception:
            return 900000
